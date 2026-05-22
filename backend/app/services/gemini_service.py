import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, List
from app.services.risk_engine import run_hybrid_risk_engine

logger = logging.getLogger("uvicorn.error")

def get_fallback_analysis(text: str, deterministic: Dict[str, Any], api_warning: str = None) -> Dict[str, Any]:
    """
    Constructs a high-quality structured analysis response using smart heuristics and
    deterministic keyword findings. Extracts actual matching paragraphs from the text
    to generate realistic, contract-tailored clauses, missing clauses, and simulations.
    """
    # Detect contract type
    contract_type = "Legal Document"
    text_lower = text.lower()
    if "employment" in text_lower or "employee" in text_lower:
        contract_type = "Employment Agreement"
    elif "non-disclosure" in text_lower or "confidentiality" in text_lower or "nda" in text_lower:
        contract_type = "Non-Disclosure Agreement (NDA)"
    elif "lease" in text_lower or "tenant" in text_lower or "landlord" in text_lower or "rental" in text_lower:
        contract_type = "Rental/Lease Agreement"
    elif "saas" in text_lower or "software as a service" in text_lower or "terms of service" in text_lower:
        contract_type = "SaaS Terms of Service"
    elif "freelance" in text_lower or "independent contractor" in text_lower or "consulting" in text_lower:
        contract_type = "Freelance/Contractor Agreement"
    elif "partnership" in text_lower or "partner" in text_lower:
        contract_type = "Partnership Agreement"

    # Helper to find matching paragraph
    def find_matching_paragraph(keywords: list) -> str:
        raw_paras = [p.strip() for p in text.split("\n") if p.strip()]
        paragraphs = []
        
        # If the text is formatted as one single block (or very few paragraphs),
        # split by sentence to locate precise matching snippets.
        if len(raw_paras) <= 3 or any(len(p) > 600 for p in raw_paras):
            import re
            for p in raw_paras:
                sentences = re.split(r'(?<=[.!?])\s+', p)
                paragraphs.extend([s.strip() for s in sentences if s.strip()])
        else:
            paragraphs = raw_paras

        for p in paragraphs:
            p_lower = p.lower()
            if any(kw in p_lower for kw in keywords):
                if len(p) > 280:
                    return p[:277] + "..."
                return p
        return ""

    # Smart heuristic topics
    HEURISTIC_TOPICS = [
        {
            "clauseName": "Confidentiality Obligations",
            "keywords": ["confidential", "non-disclosure", "proprietary information"],
            "default_severity": "SAFE",
            "explanation": "Imposes strict requirements to keep proprietary business information and client records confidential.",
            "suggestion": "Why it matters: Mutual confidentiality protects your own proprietary ideas or business disclosures. Suggested change: Request that the confidentiality obligation be made fully mutual. Example wording: 'Each party agrees to keep the other party's proprietary information confidential and use it only for the purposes of this Agreement.'"
        },
        {
            "clauseName": "Intellectual Property Assignment",
            "keywords": ["intellectual property", "inventions", "work made for hire", "assigns rights"],
            "default_severity": "NEUTRAL",
            "explanation": "Assigns ownership rights of work products, inventions, and designs created during the contract to the other party.",
            "suggestion": "Why it matters: Transferring all rights without carve-outs may cause you to lose ownership of your pre-existing tools or methods. Suggested change: Ensure pre-existing intellectual property and personal tools are explicitly excluded from this assignment. Example wording: 'Contractor retains ownership of all pre-existing tools, methodologies, and code used to perform the services.'"
        },
        {
            "clauseName": "Termination notice period",
            "keywords": ["terminate", "termination", "without cause", "notice period"],
            "default_severity": "MEDIUM",
            "explanation": "Defines the period and conditions required for either party to terminate the contract.",
            "suggestion": "Why it matters: Short notice periods or unilateral termination rights can cause unexpected business disruption. Suggested change: Verify that notice periods are balanced and provide adequate time to transition. Example wording: 'Either party may terminate this Agreement upon thirty (30) days' prior written notice to the other party.'"
        },
        {
            "clauseName": "Indemnification Obligations",
            "keywords": ["indemnify", "indemnification", "hold harmless", "indemnity"],
            "default_severity": "HIGH",
            "explanation": "Requires you to pay the other party's legal costs and damages arising from standard performance issues or claims.",
            "suggestion": "Why it matters: Unilateral indemnification forces you to absorb the other party's legal liabilities. Suggested change: Make the indemnification mutual. Limit liability to claims arising solely from your gross negligence or breach. Example wording: 'Each party shall indemnify and hold the other party harmless from third-party claims arising out of the indemnifying party's breach or negligence.'"
        },
        {
            "clauseName": "Dispute Resolution & Arbitration",
            "keywords": ["arbitration", "arbitrate", "jury waiver", "class action waiver"],
            "default_severity": "HIGH",
            "explanation": "Mandates resolving disputes via binding private arbitration and waives your rights to a jury trial or class action.",
            "suggestion": "Why it matters: Arbitration clauses restrict your access to public courts and jury trials. Suggested change: Ensure arbitration venue is mutual/convenient, costs are shared equally, and carve-outs exist for small claims. Example wording: 'Any dispute arising out of this Agreement shall be resolved by binding arbitration in a mutually agreeable location, with costs shared equally.'"
        },
        {
            "clauseName": "Governing Law Boilerplate",
            "keywords": ["governing law", "governed by", "jurisdiction", "venue"],
            "default_severity": "NEUTRAL",
            "explanation": "Determines which state's or country's laws govern contract interpretation and where disputes must be filed.",
            "suggestion": "Why it matters: Choice of law and venue can force you to travel and hire out-of-state legal counsel. Suggested change: Verify the designated jurisdiction is local or reasonable to prevent travel and foreign legal expenses. Example wording: 'This Agreement shall be governed by the laws of [State/Country] and any disputes shall be resolved in the courts of [State/Country].'"
        },
        {
            "clauseName": "Compensation & Payment Terms",
            "keywords": ["salary", "payment", "compensation", "bonus", "invoice", "fee"],
            "default_severity": "SAFE",
            "explanation": "Specifies salaries, hourly wages, payment cycles, invoices, and expense reimbursements.",
            "suggestion": "Why it matters: Clear payment terms avoid payment delays and disputes over late charges. Suggested change: Ensure invoice payment terms are clear and there is a grace period before late interest/penalties apply. Example wording: 'Client shall pay all undisputed invoice amounts within thirty (30) days of receipt.'"
        },
        {
            "clauseName": "Non-Compete Restrictions",
            "keywords": ["non-compete", "not compete", "non-solicitation", "solicit"],
            "default_severity": "HIGH",
            "explanation": "Restricts your ability to work for competitors or solicit clients after contract termination.",
            "suggestion": "Why it matters: Broad non-compete covenants can severely restrict your employment options after leaving. Suggested change: Negotiate to remove non-compete clauses. If required, limit duration to less than 6 months and narrow the scope. Example wording: 'For a period of six (6) months following termination, the Contractor shall not provide competing services to direct competitors of the Client within [Specific Region].'"
        }
    ]

    risks = []
    seen_clauses = set()

    # 1. First add matches from the deterministic hybrid risk engine
    for match in deterministic["matches"]:
        risks.append({
            "clauseName": match["name"],
            "severity": match["severity"],
            "text": match["snippet"],
            "explanation": match["explanation"],
            "suggestion": match["suggestion"]
        })
        seen_clauses.add(match["name"])

    # 2. Then scan for smart heuristics to fill out the analysis and extract exact paragraphs
    for topic in HEURISTIC_TOPICS:
        # Avoid duplicate topics if deterministic engine already flagged it
        if topic["clauseName"] in seen_clauses:
            continue
            
        excerpt = find_matching_paragraph(topic["keywords"])
        if excerpt:
            risks.append({
                "clauseName": topic["clauseName"],
                "severity": topic["default_severity"],
                "text": excerpt,
                "explanation": topic["explanation"],
                "suggestion": topic["suggestion"]
            })
            seen_clauses.add(topic["clauseName"])

    # 3. Handle missing clauses based on what is absent
    missing_clauses = []
    
    # Limitation of liability check
    has_liability_cap = any("liability" in r["clauseName"].lower() for r in risks)
    if not has_liability_cap:
        missing_clauses.append({
            "clause": "Limitation of Liability Cap",
            "severity": "HIGH",
            "explanation": "No clause caps your liability in this document. You could be sued for unlimited damages.",
            "suggestion": "Why it matters: Without a liability cap, you face unlimited financial risk for breaches. Suggested change: Request a mutual cap on liability equal to fees paid or a set dollar limit. Example wording: 'Neither party's liability under this agreement shall exceed the total amount paid in the preceding 12 months.'"
        })
        
    # Mutual termination check
    has_termination_conv = any("terminate" in r["clauseName"].lower() and "convenience" in r["clauseName"].lower() for r in risks)
    if not has_termination_conv:
        missing_clauses.append({
            "clause": "Mutual Termination for Convenience",
            "severity": "MEDIUM",
            "explanation": "There is no flexible exit clause. You are locked in unless a material breach occurs.",
            "suggestion": "Why it matters: Lock-in periods prevent flexible termination when circumstances change. Suggested change: Request mutual termination for convenience with 30 days notice. Example wording: 'Either party may terminate this agreement without cause upon thirty (30) days' prior written notice.'"
        })

    # Payment grace period check
    has_payment_grace = any("payment" in r["clauseName"].lower() and "grace" in r["clauseName"].lower() for r in risks)
    if not has_payment_grace:
        missing_clauses.append({
            "clause": "Payment Grace Period Notice",
            "severity": "MEDIUM",
            "explanation": "Missing a standard buffer period for late payments, leaving you vulnerable to immediate penalties or suspension.",
            "suggestion": "Why it matters: Lack of a cure period can lead to immediate penalties or suspension for minor delays. Suggested change: Request a 10-day notice and cure window for payments. Example wording: 'Client shall have ten (10) business days from receipt of late notice to cure any payment default before interest or penalties apply.'"
        })

    # 4. Scam signals
    scam_signals = []
    # If we have unilateral terms or unlimited liability, flag it
    for r in risks:
        if r["severity"] == "CRITICAL":
            scam_signals.append({
                "pattern": f"Critical Exposure: {r['clauseName']}",
                "explanation": f"The clause contains disproportionate, high-risk terms regarding {r['clauseName'].lower()}.",
                "severity": "CRITICAL"
            })
        elif r["severity"] == "HIGH" and r["clauseName"] in ["Non-Compete Restrictions", "Indemnification Obligations", "Non-Compete Restriction", "One-Sided Indemnification"]:
            scam_signals.append({
                "pattern": f"One-Sided {r['clauseName']}",
                "explanation": f"The contract places high post-relationship or financial risk on you regarding {r['clauseName'].lower()}.",
                "severity": "HIGH"
            })

    # 5. Simulations
    simulations = [
        {
            "scenario": "What happens if I terminate early?",
            "consequence": "Since no termination for convenience clause was found, early termination might be considered a breach of contract, subjecting you to full damages." if not has_termination_conv else "You can exit the agreement by providing the specified written notice without breach.",
            "mitigation": "Insert a mutual termination clause allowing exit with 30 or 60 days written notice." if not has_termination_conv else "Ensure you follow the written notice rules precisely."
        },
        {
            "scenario": "What happens if I miss a payment?",
            "consequence": "Standard interest rates and late fees will apply. If overdue, the other party may suspend services or declare a default." if not has_payment_grace else "You will have a standard cure period to resolve the balance without penalty.",
            "mitigation": "Add a 10-day payment cure period notice before interest begins accruing." if not has_payment_grace else "Make sure to pay within the notice grace window."
        }
    ]

    # 6. Things to know (always exactly 5)
    things_to_know = []
    for r in risks:
        if len(things_to_know) >= 5:
            break
        things_to_know.append(f"{r['clauseName']}: {r['explanation']}")
        
    while len(things_to_know) < 5 and missing_clauses:
        mc = missing_clauses[0]
        things_to_know.append(f"Missing {mc['clause']}: {mc['explanation']}")
        
    while len(things_to_know) < 5:
        things_to_know.append(f"Standard clause review required (Takeaway #{len(things_to_know)+1}).")
        
    things_to_know = things_to_know[:5]

    # 7. Calculate score dynamically (Task 2)
    # Start at baseline 40
    overall_score = 40
    severe_count = 0
    for r in risks:
        sev = r["severity"].upper()
        if sev == "CRITICAL":
            overall_score += 15
            severe_count += 1
        elif sev == "HIGH":
            overall_score += 10
            severe_count += 1
        elif sev == "MEDIUM":
            overall_score += 5
        elif sev == "SAFE":
            overall_score -= 6
        # NEUTRAL: no effect (0)

    # Apply caps (evidence-based limits)
    if overall_score >= 86:
        if severe_count < 2:
            overall_score = 85
        elif severe_count < 3:
            overall_score = 89  # Map to high end of DANGEROUS but not 90+

    # Clamp between 0 and 100
    overall_score = max(0, min(100, overall_score))

    # Map score to risk level (Task 6)
    if overall_score <= 25:
        risk_level = "SAFE"
    elif overall_score <= 45:
        risk_level = "LOW RISK"
    elif overall_score <= 65:
        risk_level = "MODERATE RISK"
    elif overall_score <= 85:
        risk_level = "HIGH RISK"
    else:
        risk_level = "DANGEROUS"

    # Calculate confidence dynamically based on text length and structure (Task 5)
    text_len = len(text)
    if text_len < 300:
        confidence = 35
    elif text_len < 1000:
        confidence = 50
    elif text_len < 3000:
        confidence = 70
    elif text_len < 8000:
        confidence = 80
    else:
        confidence = 85
        
    # Reduce confidence based on missing clauses
    confidence -= len(missing_clauses) * 3
    
    # Check structure/vocabulary
    contract_vocab = ["shall", "agree", "party", "contract", "hereby", "termination", "liability", "confidential"]
    vocab_matches = sum(1 for word in contract_vocab if word in text_lower)
    
    if vocab_matches <= 1:
        confidence = max(35, confidence - 15)
    elif vocab_matches <= 3:
        confidence = max(35, confidence - 5)
    else:
        confidence = min(90, confidence + 5)
        
    # Bound confidence strictly between 35 and 90
    confidence = max(35, min(90, confidence))

    # Build 11-point report structure for summary (Task 9)
    protections_count = sum(1 for r in risks if r["severity"] == "SAFE")
    neutral_count = sum(1 for r in risks if r["severity"] == "NEUTRAL")
    risks_count = sum(1 for r in risks if r["severity"] in ["CRITICAL", "HIGH", "MEDIUM"])

    if risks:
        key_findings_text = f"The contract contains {len(risks)} identified provisions, showing a balance of rights and obligations."
    else:
        key_findings_text = "The contract does not match any deterministic risk signatures, suggesting a standard baseline agreement."

    identified_risks_list = [f"- {r['clauseName']}: {r['explanation']}" for r in risks if r["severity"] in ["CRITICAL", "HIGH", "MEDIUM"]]
    identified_risks_text = "\n".join(identified_risks_list) if identified_risks_list else "None detected."

    missing_protections_list = [f"- {mc['clause']}: {mc['explanation']}" for mc in missing_clauses]
    missing_protections_text = "\n".join(missing_protections_list) if missing_protections_list else "None identified."

    negotiation_opps = []
    for r in risks:
        if r["suggestion"]:
            negotiation_opps.append(f"- {r['clauseName']}: {r['suggestion']}")
    for mc in missing_clauses:
        negotiation_opps.append(f"- Missing {mc['clause']}: {mc['suggestion']}")
    negotiation_opps_text = "\n".join(negotiation_opps) if negotiation_opps else "None."

    simulations_text = "\n".join([f"- Scenario: {s['scenario']}\n  Consequence: {s['consequence']}\n  Mitigation: {s['mitigation']}" for s in simulations])

    if overall_score <= 25:
        final_rec = "Safe to Sign"
        rec_reason = "The contract contains strong user protections, minimal risk clauses, and standard governing provisions. It is safe to sign as written."
    elif overall_score <= 45:
        final_rec = "Sign with Clarifications"
        rec_reason = "The contract is generally fair but contains minor ambiguities or neutral boilerplate. Consider requesting clarification on key terms before signing."
    elif overall_score <= 65:
        final_rec = "Negotiate Before Signing"
        rec_reason = "The contract exhibits a moderate risk profile, featuring multiple one-sided clauses or missing protections. Active negotiation is advised to restore balance."
    else:
        final_rec = "Seek Professional Review"
        rec_reason = "The contract contains severe risk exposures, unlimited liabilities, or critical missing safeguards. We highly recommend professional legal counsel review before proceeding."

    summary = f"""REPORT SUMMARY:

1. Contract Type: {contract_type}
2. Overall Classification: {risk_level}
3. Risk Score: {overall_score}/100
4. Confidence Score: {confidence}%

5. Clause Balance:
   - Protections: {protections_count}
   - Neutral Terms: {neutral_count}
   - Risks: {risks_count}

6. Key Findings:
{key_findings_text}

7. Identified Risks:
{identified_risks_text}

8. Missing Protections:
{missing_protections_text}

9. Negotiation Opportunities:
{negotiation_opps_text}

10. What Happens If...
{simulations_text}

11. Final Recommendation:
[{final_rec}] {rec_reason}"""

    # Sanitize api_warning for user display to remove leaked key or raw errors
    user_api_warning = None
    if api_warning:
        api_warning_lower = api_warning.lower()
        if "key" in api_warning_lower or "403" in api_warning_lower or "leaked" in api_warning_lower or "unauthorized" in api_warning_lower:
            user_api_warning = "Running in offline mode. Displaying rule-based signature analysis."
        else:
            user_api_warning = api_warning

    return {
        "contractType": contract_type,
        "overallRisk": overall_score,
        "riskLevel": risk_level,
        "confidence": confidence,
        "summary": summary,
        "risks": risks,
        "missingClauses": missing_clauses,
        "scamSignals": scam_signals,
        "simulations": simulations,
        "thingsToKnow": things_to_know,
        "apiWarning": user_api_warning
    }

def chunk_text(text: str, max_chars: int = 30000) -> List[str]:
    """
    Splits long contract text into chunks, respecting paragraph endings to avoid cutting sentences.
    """
    if len(text) <= max_chars:
        return [text]
        
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_len = len(para) + 2
        if current_length + para_len > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = para_len
        else:
            current_chunk.append(para)
            current_length += para_len
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def recalculate_and_clean_scores(result: Dict[str, Any], text: str) -> Dict[str, Any]:
    """
    Programmatically calculates and enforces the balanced scoring model, risk level mapping,
    and structured report formats on the Gemini output to guarantee absolute mathematical
    accuracy and schema adherence.
    """
    try:
        risks = result.get("risks", [])
        missing_clauses = result.get("missingClauses", [])
        
        # 1. Enforce 3-part suggestion structure
        def format_suggestion(sug: str, clause_name: str, is_missing: bool = False) -> str:
            sug = sug or ""
            if "Why it matters:" in sug and "Suggested change:" in sug:
                return sug
            # If not in 3-part format, format it helper-style
            why = f"Unbalanced or unclear terms in {clause_name}."
            change = f"Request clarification or mutual obligations."
            example = "Consult legal counsel for specific wording."
            return f"Why it matters: {why} Suggested change: {change} Example wording: {example}"

        for r in risks:
            r["suggestion"] = format_suggestion(r.get("suggestion", ""), r.get("clauseName", "this"))
            
        for mc in missing_clauses:
            mc["suggestion"] = format_suggestion(mc.get("suggestion", ""), mc.get("clause", "this"), is_missing=True)
            
        # 2. Balanced Scoring Model (Task 2)
        overall_score = 40
        severe_count = 0
        for r in risks:
            sev = str(r.get("severity", "")).upper()
            if sev == "CRITICAL":
                overall_score += 15
                severe_count += 1
            elif sev == "HIGH":
                overall_score += 10
                severe_count += 1
            elif sev == "MEDIUM":
                overall_score += 5
            elif sev == "SAFE":
                overall_score -= 6
                
        # Apply caps
        if overall_score >= 86:
            if severe_count < 2:
                overall_score = 85
            elif severe_count < 3:
                overall_score = 89
                
        overall_score = max(0, min(100, overall_score))
        result["overallRisk"] = overall_score
        
        # 3. Risk Level Mapping (Task 6)
        if overall_score <= 25:
            risk_level = "SAFE"
        elif overall_score <= 45:
            risk_level = "LOW RISK"
        elif overall_score <= 65:
            risk_level = "MODERATE RISK"
        elif overall_score <= 85:
            risk_level = "HIGH RISK"
        else:
            risk_level = "DANGEROUS"
        result["riskLevel"] = risk_level
        
        # 4. Limit confidence score (Task 5)
        confidence = result.get("confidence", 85)
        confidence = max(35, min(90, confidence))
        result["confidence"] = confidence
        
        # 5. Extract counts for Clause Balance
        protections_count = sum(1 for r in risks if str(r.get("severity", "")).upper() == "SAFE")
        neutral_count = sum(1 for r in risks if str(r.get("severity", "")).upper() == "NEUTRAL")
        risks_count = sum(1 for r in risks if str(r.get("severity", "")).upper() in ["CRITICAL", "HIGH", "MEDIUM"])
        
        # 6. Rebuild structured summary if it's not structured, or update it
        summary = result.get("summary", "")
        import re
        if "1. Contract Type:" in summary:
            # Update the existing structured summary in-place
            summary = re.sub(
                r"(2\.\s+Overall\s+Classification:\s*)[^\n]+",
                rf"\g<1>{risk_level}",
                summary
            )
            summary = re.sub(
                r"(3\.\s+Risk\s+Score:\s*)[^\n]+",
                rf"\g<1>{overall_score}/100",
                summary
            )
            summary = re.sub(
                r"(4\.\s+Confidence\s+Score:\s*)[^\n]+",
                rf"\g<1>{confidence}%",
                summary
            )
            summary = re.sub(
                r"(-\s+Protections:\s*)\d+",
                rf"\g<1>{protections_count}",
                summary
            )
            summary = re.sub(
                r"(-\s+Neutral\s+Terms:\s*)\d+",
                rf"\g<1>{neutral_count}",
                summary
            )
            summary = re.sub(
                r"(-\s+Risks:\s*)\d+",
                rf"\g<1>{risks_count}",
                summary
            )
            
            if overall_score <= 25:
                final_rec = "Safe to Sign"
                rec_reason = "The contract contains strong user protections, minimal risk clauses, and standard governing provisions. It is safe to sign as written."
            elif overall_score <= 45:
                final_rec = "Sign with Clarifications"
                rec_reason = "The contract is generally fair but contains minor ambiguities or neutral boilerplate. Consider requesting clarification on key terms before signing."
            elif overall_score <= 65:
                final_rec = "Negotiate Before Signing"
                rec_reason = "The contract exhibits a moderate risk profile, featuring multiple one-sided clauses or missing protections. Active negotiation is advised to restore balance."
            else:
                final_rec = "Seek Professional Review"
                rec_reason = "The contract contains severe risk exposures, unlimited liabilities, or critical missing safeguards. We highly recommend professional legal counsel review before proceeding."
                
            summary = re.sub(
                r"(11\.\s+Final\s+Recommendation:\s*).*$",
                rf"\g<1>[{final_rec}] {rec_reason}",
                summary,
                flags=re.DOTALL
            )
            if "REPORT SUMMARY:" not in summary:
                summary = "REPORT SUMMARY:\n\n" + summary
            result["summary"] = summary
        else:
            # Build structured summary from scratch
            contract_type = result.get("contractType", "Legal Document")
            key_findings_text = summary if summary else "Objective contract audit completed."
            
            identified_risks_list = [f"- {r['clauseName']}: {r['explanation']}" for r in risks if str(r.get("severity", "")).upper() in ["CRITICAL", "HIGH", "MEDIUM"]]
            identified_risks_text = "\n".join(identified_risks_list) if identified_risks_list else "None detected."
            
            missing_protections_list = [f"- {mc['clause']}: {mc['explanation']}" for mc in missing_clauses]
            missing_protections_text = "\n".join(missing_protections_list) if missing_protections_list else "None identified."
            
            negotiation_opps = []
            for r in risks:
                if r.get("suggestion"):
                    negotiation_opps.append(f"- {r['clauseName']}: {r['suggestion']}")
            for mc in missing_clauses:
                negotiation_opps.append(f"- Missing {mc['clause']}: {mc['suggestion']}")
            negotiation_opps_text = "\n".join(negotiation_opps) if negotiation_opps else "None."
            
            simulations = result.get("simulations", [])
            simulations_text = "\n".join([f"- Scenario: {s.get('scenario')}\n  Consequence: {s.get('consequence')}\n  Mitigation: {s.get('mitigation')}" for s in simulations])
            
            if overall_score <= 25:
                final_rec = "Safe to Sign"
                rec_reason = "The contract contains strong user protections, minimal risk clauses, and standard governing provisions. It is safe to sign as written."
            elif overall_score <= 45:
                final_rec = "Sign with Clarifications"
                rec_reason = "The contract is generally fair but contains minor ambiguities or neutral boilerplate. Consider requesting clarification on key terms before signing."
            elif overall_score <= 65:
                final_rec = "Negotiate Before Signing"
                rec_reason = "The contract exhibits a moderate risk profile, featuring multiple one-sided clauses or missing protections. Active negotiation is advised to restore balance."
            else:
                final_rec = "Seek Professional Review"
                rec_reason = "The contract contains severe risk exposures, unlimited liabilities, or critical missing safeguards. We highly recommend professional legal counsel review before proceeding."
                
            summary = f"""REPORT SUMMARY:

1. Contract Type: {contract_type}
2. Overall Classification: {risk_level}
3. Risk Score: {overall_score}/100
4. Confidence Score: {confidence}%

5. Clause Balance:
   - Protections: {protections_count}
   - Neutral Terms: {neutral_count}
   - Risks: {risks_count}

6. Key Findings:
{key_findings_text}

7. Identified Risks:
{identified_risks_text}

8. Missing Protections:
{missing_protections_text}

9. Negotiation Opportunities:
{negotiation_opps_text}

10. What Happens If...
{simulations_text}

11. Final Recommendation:
[{final_rec}] {rec_reason}"""
            result["summary"] = summary
            
    except Exception as e:
        logger.error(f"Error in recalculate_and_clean_scores: {str(e)}", exc_info=True)
        
    return result

def analyze_contract_with_gemini(text: str, deterministic: Dict[str, Any], custom_api_key: str = None) -> Dict[str, Any]:
    """
    Sends the contract to Gemini with structured prompt parameters and instructions.
    Uses the official google-generativeai SDK and requires GEMINI_API_KEY.
    Optimizes performance by checking local cache and using large chunk sizes to minimize API calls.
    """
    import time
    from app.services.cache_service import get_cached_analysis, cache_analysis
    from app.utils.logger import log_ai_failure, log_processing_time
    
    # 1. Check local SHA-256 Cache
    cached_result = get_cached_analysis(text)
    if cached_result:
        return cached_result

    # Use custom api key if provided, otherwise check env
    api_key = custom_api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.warning("GEMINI_API_KEY is missing. Running fallback deterministic engine.")
        fallback = get_fallback_analysis(
            text, 
            deterministic, 
            "Running in offline mode. Using deterministic signature analysis."
        )
        return fallback

    start_time = time.time()
    try:
        genai.configure(api_key=api_key)
        system_instruction = (
            "You are an objective, neutral contract reviewer whose job is to identify protections, neutral terms, risks, ambiguities, and negotiation opportunities. "
            "You must NOT act as a risk-only scanner looking for problems. Perform a balanced, evidence-based assessment. "
            "Do not infer rights, liabilities, or outcomes that are not explicitly stated. Avoid exaggerated language, fear-based wording, and legal speculation. "
            "Only output valid JSON matching the requested schema exactly."
        )
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
        
        # Prepare deterministic matches to pass to Gemini
        deterministic_info = []
        for match in deterministic["matches"]:
            deterministic_info.append({
                "rule": match["name"],
                "severity": match["severity"],
                "snippet": match["snippet"],
                "reasoning": match["explanation"]
            })
            
        # 2. Optimize Chunking: Only chunk if document is exceptionally large (> 600,000 characters)
        chunks = chunk_text(text, max_chars=600000)
        
        if len(chunks) > 1:
            # If indeed larger than 600k, split into standard 300k chunks to preserve memory/API limit
            chunks = chunk_text(text, max_chars=300000)
            logger.info(f"Contract is exceptionally large ({len(text)} characters). Splitting into {len(chunks)} chunks.")
            
            chunk_results = []
            for i, chunk in enumerate(chunks[:4]): # Limit to 4 chunks to avoid timeout
                chunk_prompt = f"""
                You are analyzing Part {i+1} of a multi-part legal contract.
                Identify protections (SAFE), neutral boilerplate (NEUTRAL), and risks (CRITICAL/HIGH/MEDIUM).
                IMPORTANT: You MUST include ALL analyzed clauses—including protections (severity: SAFE) and neutral boilerplate (severity: NEUTRAL)—in the 'risks' array. The 'risks' array acts as the general list of all key clauses analyzed. Do NOT omit SAFE or NEUTRAL clauses from the 'risks' array.
                Return findings ONLY in valid JSON.
                
                Text block:
                ---
                {chunk}
                ---
                """
                resp = model.generate_content(
                    chunk_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                try:
                    chunk_results.append(json.loads(resp.text))
                except Exception:
                    pass
            
            # Now run a merge prompt
            merge_prompt = f"""
            You are an objective, neutral legal editor. Combine the following partial contract analyses into a single cohesive, evidence-based JSON report.
            
            Partial Analyses:
            {json.dumps(chunk_results, indent=2)}
            
            Our deterministic keyword engine reported these alerts:
            {json.dumps(deterministic_info, indent=2)}
            
            Instructions:
            1. Persona: Be a neutral, objective analyst. Identify protections for the user (SAFE), neutral standard terms (NEUTRAL), and actual risks (CRITICAL, HIGH, MEDIUM).
               IMPORTANT: You MUST include ALL analyzed clauses—including protections (severity: SAFE) and neutral boilerplate (severity: NEUTRAL)—in the 'risks' array. The 'risks' array acts as the general list of all key clauses analyzed. Do NOT omit SAFE or NEUTRAL clauses from the 'risks' array.
            2. Separation of Omissions: Do NOT treat missing clauses as risks in the 'risks' array. Place all missing safeguards strictly in the 'missingClauses' array.
            3. Balanced Scoring Formula:
               - Calculate 'overallRisk' starting from a baseline of 40.
               - Add/subtract weights for each unique clause in the final 'risks' array:
                 - Add +15 for CRITICAL
                 - Add +10 for HIGH
                 - Add +5 for MEDIUM
                 - Subtract -6 for SAFE
                 - Add 0 for NEUTRAL
               - Cap 'overallRisk' at 85 unless multiple severe (CRITICAL or HIGH) clauses exist in 'risks'. If exactly two severe clauses exist, cap at 89. Bound score between 0 and 100.
            4. Risk Level Mapping:
               - 0-25: SAFE
               - 26-45: LOW RISK
               - 46-65: MODERATE RISK
               - 66-85: HIGH RISK
               - 86-100: DANGEROUS
            5. Confidence Calculation: Dynamically assign confidence score in the typical range of 70-90% for complete contracts, and 35-70% for short snippets, incomplete agreements, or highly ambiguous wording. Do not exceed 90% unless the document is exceptionally detailed and complete.
            6. Suggestion Structure: For every suggestion in 'risks' and 'missingClauses', provide a professional, realistic recommendation in this exact 3-part format:
               "Why it matters: [reason] Suggested change: [change] Example wording: [wording]"
            7. Structured Report Summary: Format the 'summary' field of the JSON output as a structured 11-point report in this exact order:
               1. Contract Type: [Type]
               2. Overall Classification: [Risk Level]
               3. Risk Score: [Risk Score]/100
               4. Confidence Score: [Confidence Score]%
               5. Clause Balance:
                  - Protections: [Count of SAFE clauses]
                  - Neutral Terms: [Count of NEUTRAL clauses]
                  - Risks: [Count of CRITICAL+HIGH+MEDIUM clauses]
               6. Key Findings: [Concise paragraph highlighting primary findings]
               7. Identified Risks: [Bullet points list of key risks or 'None detected']
               8. Missing Protections: [Bullet points list of absent protections or 'None identified']
               9. Negotiation Opportunities: [Bullet points of opportunities or 'None']
               10. What Happens If...: [Bullet points summarizing scenario results]
               11. Final Recommendation: [[Recommendation Category]] [Professional advice]
               (The Recommendation Category must be one of: Safe to Sign, Sign with Clarifications, Negotiate Before Signing, Seek Professional Review).
            8. Ensure 'thingsToKnow' contains exactly 5 distinct, professional, non-speculative takeaways.
            
            JSON Schema:
            {{
              "contractType": "string",
              "overallRisk": "integer",
              "riskLevel": "string",
              "confidence": "integer",
              "summary": "string",
              "risks": [
                {{
                  "clauseName": "string",
                  "severity": "string (CRITICAL, HIGH, MEDIUM, NEUTRAL, SAFE)",
                  "text": "string (exact quote from contract)",
                  "explanation": "string",
                  "suggestion": "string"
                }}
              ],
              "missingClauses": [
                {{
                  "clause": "string",
                  "severity": "string",
                  "explanation": "string",
                  "suggestion": "string"
                }}
              ],
              "scamSignals": [
                {{
                  "pattern": "string",
                  "explanation": "string",
                  "severity": "string"
                }}
              ],
              "simulations": [
                {{
                  "scenario": "string",
                  "consequence": "string",
                  "mitigation": "string"
                }}
              ],
              "thingsToKnow": ["string", "string", "string", "string", "string"]
            }}
            """
            
            merge_resp = model.generate_content(
                merge_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            final_result = json.loads(merge_resp.text)
            final_result = recalculate_and_clean_scores(final_result, text)
            
        else:
            # Single chunk analysis
            prompt = f"""
            Perform an objective, professional, and balanced analysis on the following contract text.
            
            Deterministic baseline matches:
            {json.dumps(deterministic_info, indent=2)}
            
            Instructions:
            1. Persona: Be a neutral, objective analyst. Identify protections for the user (SAFE), neutral boilerplate (NEUTRAL), and actual risks (CRITICAL, HIGH, MEDIUM). Do not infer rights, liabilities, or outcomes that are not explicitly stated.
               IMPORTANT: You MUST include ALL analyzed clauses—including protections (severity: SAFE) and neutral boilerplate (severity: NEUTRAL)—in the 'risks' array. The 'risks' array acts as the general list of all key clauses analyzed. Do NOT omit SAFE or NEUTRAL clauses from the 'risks' array.
            2. Separation of Omissions: Do NOT treat missing clauses as risks in the 'risks' array. Place all missing safeguards strictly in the 'missingClauses' array.
            3. Balanced Scoring Formula:
               - Calculate 'overallRisk' starting from a baseline of 40.
               - Add/subtract weights for each unique clause in 'risks':
                 - Add +15 for CRITICAL
                 - Add +10 for HIGH
                 - Add +5 for MEDIUM
                 - Subtract -6 for SAFE
                 - Add 0 for NEUTRAL
               - Cap 'overallRisk' at 85 unless multiple severe (CRITICAL or HIGH) clauses exist in 'risks'. If exactly two severe clauses exist, cap at 89. Bound score between 0 and 100.
            4. Risk Level Mapping:
               - 0-25: SAFE
               - 26-45: LOW RISK
               - 46-65: MODERATE RISK
               - 66-85: HIGH RISK
               - 86-100: DANGEROUS
            5. Confidence Calculation: Dynamically assign confidence score in the typical range of 70-90% for complete contracts, and 35-70% for short snippets, incomplete agreements, or highly ambiguous wording. Do not exceed 90% unless the document is exceptionally detailed and complete.
            6. Suggestion Structure: For every suggestion in 'risks' and 'missingClauses', provide a professional, realistic recommendation in this exact 3-part format:
               "Why it matters: [reason] Suggested change: [change] Example wording: [wording]"
            7. Structured Report Summary: Format the 'summary' field of the JSON output as a structured 11-point report in this exact order:
               1. Contract Type: [Type]
               2. Overall Classification: [Risk Level]
               3. Risk Score: [Risk Score]/100
               4. Confidence Score: [Confidence Score]%
               5. Clause Balance:
                  - Protections: [Count of SAFE clauses]
                  - Neutral Terms: [Count of NEUTRAL clauses]
                  - Risks: [Count of CRITICAL+HIGH+MEDIUM clauses]
               6. Key Findings: [Concise paragraph highlighting primary findings]
               7. Identified Risks: [Bullet points list of key risks or 'None detected']
               8. Missing Protections: [Bullet points list of absent protections or 'None identified']
               9. Negotiation Opportunities: [Bullet points of opportunities or 'None']
               10. What Happens If...: [Bullet points summarizing scenario results]
               11. Final Recommendation: [[Recommendation Category]] [Professional advice]
               (The Recommendation Category must be one of: Safe to Sign, Sign with Clarifications, Negotiate Before Signing, Seek Professional Review).
            8. Ensure 'thingsToKnow' contains exactly 5 distinct, professional, non-speculative takeaways. Only use exact excerpts from the contract in the 'text' fields.
            
            Return the output STRICTLY in JSON format adhering to the following schema:
            
            JSON Schema:
            {{
              "contractType": "string (e.g. Employment Contract, NDA, Rental Agreement, SaaS Terms, Privacy Policy, Freelance Agreement, Partnership Agreement)",
              "overallRisk": "integer",
              "riskLevel": "string",
              "confidence": "integer",
              "summary": "string",
              "risks": [
                {{
                  "clauseName": "string",
                  "severity": "string (CRITICAL, HIGH, MEDIUM, NEUTRAL, SAFE)",
                  "text": "string (exact quote from contract)",
                  "explanation": "string",
                  "suggestion": "string"
                }}
              ],
              "missingClauses": [
                {{
                  "clause": "string",
                  "severity": "string (CRITICAL, HIGH, MEDIUM)",
                  "explanation": "string",
                  "suggestion": "string"
                }}
              ],
              "scamSignals": [
                {{
                  "pattern": "string",
                  "explanation": "string",
                  "severity": "string (CRITICAL, HIGH, MEDIUM)"
                }}
              ],
              "simulations": [
                {{
                  "scenario": "string",
                  "consequence": "string",
                  "mitigation": "string"
                }}
              ],
              "thingsToKnow": ["string", "string", "string", "string", "string"]
            }}
            
            Contract text to analyze:
            ---
            {text}
            ---
            """
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            final_result = json.loads(response.text)
            final_result = recalculate_and_clean_scores(final_result, text)

        # 3. Log success metrics and save to cache
        duration = time.time() - start_time
        log_processing_time("gemini_ai_analysis", duration, {"text_length_chars": len(text)})
        cache_analysis(text, final_result)
        return final_result

    except Exception as e:
        duration = time.time() - start_time
        log_ai_failure(str(e), duration)
        logger.error(f"Gemini AI Analysis failed: {str(e)}", exc_info=True)
        return get_fallback_analysis(
            text, 
            deterministic, 
            "AI analysis is currently unavailable. Using deterministic signature analysis."
        )
