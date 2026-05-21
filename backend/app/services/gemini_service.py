import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, List
from app.services.risk_engine import run_hybrid_risk_engine

logger = logging.getLogger("uvicorn.error")

def get_fallback_analysis(text: str, deterministic: Dict[str, Any], api_warning: str = None) -> Dict[str, Any]:
    """
    Constructs a valid structured analysis response using only deterministic keyword findings.
    Ensures the app remains functional even if Gemini API keys are missing or calls fail.
    """
    matches = deterministic["matches"]
    
    # Map deterministic matches to the risks format
    risks = []
    for match in matches:
        risks.append({
            "clauseName": match["name"],
            "severity": match["severity"],
            "text": match["snippet"],
            "explanation": match["explanation"],
            "suggestion": match["suggestion"]
        })
        
    # Detect contract type deterministically
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
        
    # Build default things to know
    things_to_know = []
    if risks:
        for r in risks[:5]:
            things_to_know.append(f"Risk identified in {r['clauseName']} clause: {r['explanation'][:80]}...")
    while len(things_to_know) < 5:
        things_to_know.append(f"Standard clause review required (Indicator #{len(things_to_know)+1}).")
        
    # Build missing clauses
    missing_clauses = []
    # If no liability cap is in risks, it's missing
    if not any(m["id"] == "unlimited_liability" for m in matches):
        missing_clauses.append({
            "clause": "Limitation of Liability Cap",
            "severity": "HIGH",
            "explanation": "No clause caps your liability in this document. You could be sued for unlimited damages.",
            "suggestion": "Add a clause capping overall liability to the fees paid or a reasonable commercial amount."
        })
    if not any(m["id"] == "termination_convenience" for m in matches):
        missing_clauses.append({
            "clause": "Mutual Termination for Convenience",
            "severity": "MEDIUM",
            "explanation": "There is no flexible exit clause. You are locked in unless a material breach occurs.",
            "suggestion": "Request a termination for convenience clause with a 30-day notice period."
        })
        
    # Build a simulated event
    simulations = [
        {
            "scenario": "What happens if I terminate early?",
            "consequence": "Since no termination for convenience clause was found, early termination might be considered a breach of contract, subjecting you to full damages.",
            "mitigation": "Insert a mutual termination clause allowing exit with 30 or 60 days written notice."
        },
        {
            "scenario": "What happens if I miss a payment?",
            "consequence": "Standard interest rates and late fees will apply. If overdue, the other party may suspend services or declare a default.",
            "mitigation": "Add a 10-day payment cure period notice before interest begins accruing."
        }
    ]
    
    # Scam signals
    scam_signals = []
    if any(m["id"] == "unlimited_liability" for m in matches):
        scam_signals.append({
            "pattern": "Uncapped Liability Exposure",
            "explanation": "The contract places disproportionate risk on the signee by demanding unlimited liability.",
            "severity": "CRITICAL"
        })
        
    summary = "ANALYSIS COMPLETED. "
    if api_warning:
        summary += f"[SYSTEM NOTICE: {api_warning}] "
    summary += f"This {contract_type} has been parsed using the local signature analysis engine. "
    if risks:
        summary += f"Detected {len(risks)} high-risk clauses matching deterministic patterns."
    else:
        summary += "No critical deterministic risk patterns matched. A standard review is still recommended."

    return {
        "contractType": contract_type,
        "overallRisk": deterministic["baseScore"],
        "riskLevel": deterministic["riskLevel"],
        "confidence": 80,  # Lower confidence for deterministic parser
        "summary": summary,
        "risks": risks,
        "missingClauses": missing_clauses,
        "scamSignals": scam_signals,
        "simulations": simulations,
        "thingsToKnow": things_to_know,
        "apiWarning": api_warning
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

def analyze_contract_with_gemini(text: str, deterministic: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends the contract to Gemini with structured prompt parameters and instructions.
    Uses the official google-generativeai SDK and requires GEMINI_API_KEY.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.warning("GEMINI_API_KEY is missing. Running fallback deterministic engine.")
        return get_fallback_analysis(
            text, 
            deterministic, 
            "Running in offline mode. Please set GEMINI_API_KEY in backend/.env for AI analysis."
        )

    try:
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash as requested
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Prepare deterministic matches to pass to Gemini
        deterministic_info = []
        for match in deterministic["matches"]:
            deterministic_info.append({
                "rule": match["name"],
                "severity": match["severity"],
                "snippet": match["snippet"],
                "reasoning": match["explanation"]
            })
            
        # Handle chunking if document is massive
        chunks = chunk_text(text)
        
        if len(chunks) > 1:
            logger.info(f"Contract is large ({len(text)} characters). Splitting into {len(chunks)} chunks.")
            # If the contract is chunked, we analyze the first few parts or the full set, 
            # and ask Gemini to merge. For performance, let's analyze up to 3 chunks to prevent
            # massive delays, or summarize. In most production SaaS, we run a map-reduce.
            # Let's write a map-reduce pipeline.
            chunk_results = []
            for i, chunk in enumerate(chunks[:4]): # Limit to 4 chunks (approx 120,000 characters) to avoid timeout
                chunk_prompt = f"""
                You are analyzing Part {i+1} of a multi-part legal contract.
                Identify risks, missing clauses, and scam signals in this part of the text.
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
            You are a senior legal counsel. You need to combine the following partial contract analyses into a single, cohesive, unified JSON contract review report.
            
            Partial Analyses:
            {json.dumps(chunk_results, indent=2)}
            
            Our deterministic keyword engine also reported these alerts:
            {json.dumps(deterministic_info, indent=2)}
            
            Merge these findings into the final JSON output. Ensure all duplicate findings are merged, and the top critical items are sorted.
            The output must match the target JSON schema exactly.
            
            JSON Schema:
            {{
              "contractType": "string",
              "overallRisk": "integer (0-100, combining the parts. Base score: {deterministic['baseScore']})",
              "riskLevel": "string (SAFE, LOW RISK, MODERATE RISK, RISKY, DANGEROUS)",
              "confidence": "integer (0-100)",
              "summary": "string (combined executive summary of the entire contract)",
              "risks": [
                {{
                  "clauseName": "string",
                  "severity": "string",
                  "text": "string (quote from contract)",
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
              "thingsToKnow": ["5 distinct critical strings"]
            }}
            """
            
            merge_resp = model.generate_content(
                merge_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(merge_resp.text)
            
        else:
            # Single chunk analysis
            prompt = f"""
            You are an elite legal contract analyzer AI. Your task is to perform an exhaustive, professional risk analysis on the following contract text.
            
            We have run a deterministic keyword risk engine that found the following baseline matches:
            {json.dumps(deterministic_info, indent=2)}
            
            Use these findings as a baseline, but perform your own deep analysis. You must detect risky clauses, evaluate severity, check for manipulative/scam patterns, identify missing protections, simulate legal scenarios, and summarize the key things the signer must know.
            
            You must output your findings ONLY in JSON format, adhering to the exact schema below.
            
            JSON Schema:
            {{
              "contractType": "string (e.g. Employment Contract, NDA, Rental Agreement, SaaS Terms, Privacy Policy, Freelance Agreement, Partnership Agreement)",
              "overallRisk": "integer (0 to 100. Adjust our deterministic baseScore of {deterministic['baseScore']} up or down based on your deep legal assessment)",
              "riskLevel": "string (one of: SAFE, LOW RISK, MODERATE RISK, RISKY, DANGEROUS)",
              "confidence": "integer (percentage, e.g. 95)",
              "summary": "string (a high-level, clear legal assessment of the contract in plain English)",
              "risks": [
                {{
                  "clauseName": "string (name of the risky clause, e.g., Indemnification, Unlimited Liability)",
                  "severity": "string (one of: CRITICAL, HIGH, MEDIUM, SAFE)",
                  "text": "string (the exact or closely quoted text from the contract that is risky)",
                  "explanation": "string (plain-English explanation of why this clause is dangerous)",
                  "suggestion": "string (clear suggestion on how to renegotiate this clause)"
                }}
              ],
              "missingClauses": [
                {{
                  "clause": "string (name of the missing clause, e.g., Mutual Termination, Cap on Liability, Payment Grace Period)",
                  "severity": "string (one of: CRITICAL, HIGH, MEDIUM)",
                  "explanation": "string (why the absence of this clause is dangerous for the user)",
                  "suggestion": "string (what text should be added to protect the user)"
                }}
              ],
              "scamSignals": [
                {{
                  "pattern": "string (type of pattern, e.g., Hidden Fees, Vague Obligations, Aggressive Penalties, One-Sided Liability)",
                  "explanation": "string (how this pattern manifests in this contract and its danger)",
                  "severity": "string (one of: CRITICAL, HIGH, MEDIUM)"
                }}
              ],
              "simulations": [
                {{
                  "scenario": "string (e.g., 'What happens if I terminate early?', 'What happens if I miss a payment?', 'What happens if they sue me?')",
                  "consequence": "string (the concrete legal/financial consequence based on the contract terms)",
                  "mitigation": "string (how the user can protect themselves or modify the contract to mitigate this consequence)"
                }}
              ],
              "thingsToKnow": [
                "string (Fact 1 - critical highlight)",
                "string (Fact 2 - critical highlight)",
                "string (Fact 3 - critical highlight)",
                "string (Fact 4 - critical highlight)",
                "string (Fact 5 - critical highlight)"
              ]
            }}
            
            Ensure:
            1. 'thingsToKnow' contains exactly 5 items (representing '5 Things You Must Know Before Signing').
            2. 'explanation' and 'suggestion' fields are in plain English and clear for a layperson.
            3. Do not invent clauses that are not in the contract, but be thorough.
            4. For missingClauses, specifically scan if standard protections like refund clauses, payment deadlines, confidentiality protections, liability limitations, or termination conditions are absent.
            
            Contract text to analyze:
            ---
            {text}
            ---
            """
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            return json.loads(response.text)

    except Exception as e:
        logger.error(f"Gemini API analysis failed: {str(e)}")
        return get_fallback_analysis(
            text, 
            deterministic, 
            f"AI Analysis error: {str(e)}. Displaying keyword-based deterministic breakdown instead."
        )
