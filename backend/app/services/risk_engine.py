import re
from typing import Dict, List, Any

# Predefined keywords/regexes with weights and explanations
KEYWORD_RULES = [
    {
        "id": "unlimited_liability",
        "pattern": r"(?i)unlimited\s+liability|no\s+limitation\s+of\s+liability|liability\s+shall\s+be\s+unlimited|without\s+limitation\s+as\s+to\s+liability|liable\s+for\s+any\s+and\s+all\s+damages",
        "name": "Unlimited Liability",
        "score_impact": 25,
        "severity": "CRITICAL",
        "explanation": "Exposes you to potentially infinite financial damages. Commercial contracts should cap liability to a reasonable multiplier of fees.",
        "suggestion": "Why it matters: Unlimited liability exposes you to infinite financial damages for any breach. Suggested change: Consider requesting a cap on liability, typically limited to the total fees paid under the contract or a specific commercial limit. Example wording: 'Each party's total aggregate liability under this Agreement shall be limited to the total fees paid by the Client in the twelve (12) months preceding the claim.'"
    },
    {
        "id": "binding_arbitration",
        "pattern": r"(?i)binding\s+arbitration|shall\s+be\s+resolved\s+by\s+arbitration|subject\s+to\s+arbitration|arbitration\s+association|waive\s+any\s+right\s+to\s+a\s+jury|class\s+action\s+waiver",
        "name": "Binding Arbitration & Jury Waiver",
        "score_impact": 20,
        "severity": "HIGH",
        "explanation": "Bypasses the public court system in favor of private arbitration and waives your right to a trial by jury or class actions.",
        "suggestion": "Why it matters: Binding arbitration waives your right to trial by jury and class actions. Suggested change: Consider requesting that the arbitration venue be mutual and convenient, costs shared equally, and small claims carved out. Example wording: 'Any dispute arising out of this Agreement shall be resolved by binding arbitration in [City, State] under the JAMS rules, with costs shared equally between the parties.'"
    },
    {
        "id": "non_compete",
        "pattern": r"(?i)non-compete|covenant\s+not\s+to\s+compete|shall\s+not\s+compete|restriction\s+on\s+employment|not\s+solicit\s+customers|prevent\s+from\s+engaging",
        "name": "Non-Compete Restriction",
        "score_impact": 20,
        "severity": "HIGH",
        "explanation": "Restricts your ability to work for competitors or start a similar business after this agreement terminates.",
        "suggestion": "Why it matters: Non-compete restrictions can prevent you from working in your field after the agreement ends. Suggested change: Consider requesting clarification to narrow the geographic and temporal scope, or limit duration to 6 months or less. Example wording: 'The Contractor shall not engage in a competing business within a 10-mile radius of the Client's office for a period of six (6) months following termination.'"
    },
    {
        "id": "indemnification",
        "pattern": r"(?i)indemnify\s+and\s+hold\s+harmless|shall\s+indemnify|indemnity\s+obligation|indemnification\s+by\s+the\s+contractor",
        "name": "One-Sided Indemnification",
        "score_impact": 15,
        "severity": "HIGH",
        "explanation": "Requires you to pay the legal costs and damages incurred by the other party due to standard performance issues.",
        "suggestion": "Why it matters: One-sided indemnification forces you to pay for the other party's legal liabilities and costs. Suggested change: Consider adding mutual obligations and limiting indemnity to third-party claims arising from gross negligence. Example wording: 'Each party shall indemnify and hold the other party harmless from third-party claims arising out of the indemnifying party's gross negligence or willful misconduct.'"
    },
    {
        "id": "automatic_renewal",
        "pattern": r"(?i)automatic\s+renewal|auto-renew|automatically\s+renew|auto\s+renewal|renews\s+successive|renewal\s+term\s+of",
        "name": "Automatic Renewal",
        "score_impact": 15,
        "severity": "MEDIUM",
        "explanation": "The contract automatically extends itself unless cancelled in writing within a narrow window (e.g., 30-90 days before expiration).",
        "suggestion": "Why it matters: Automatic renewal can lock you into another term before you can negotiate or review. Suggested change: Consider defining notice requirements or requiring mutual written consent to renew. Example wording: 'This Agreement shall renew for successive terms only upon the mutual written agreement of both parties at least thirty (30) days prior to the expiration of the current term.'"
    },
    {
        "id": "liquidated_damages",
        "pattern": r"(?i)liquidated\s+damages|pre-determined\s+damages|forfeiture\s+of\s+deposit|shall\s+forfeit|fee\s+as\s+damages",
        "name": "Liquidated Damages Penalty",
        "score_impact": 15,
        "severity": "HIGH",
        "explanation": "Establishes a fixed, pre-agreed penalty fee for breaches. These can be punitive and higher than actual damages.",
        "suggestion": "Why it matters: Predetermined penalties can be punitive and disproportionate to actual harm. Suggested change: Consider requesting that any damages be proven in court rather than pre-agreed. Example wording: 'In the event of a breach, the non-breaching party shall be entitled to recover actual, proven damages incurred as a direct result of such breach.'"
    },
    {
        "id": "termination_convenience",
        "pattern": r"(?i)terminate\s+for\s+convenience|termination\s+without\s+cause|terminate\s+at\s+any\s+time\s+without|may\s+terminate\s+this\s+agreement\s+upon\s+\d+\s+days",
        "name": "Termination for Convenience",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Allows a party to walk away from the contract at any time for no reason, leading to high business instability.",
        "suggestion": "Why it matters: Unilateral termination for convenience can lead to sudden contract ends without recourse. Suggested change: Consider adding mutual obligations and ensuring a reasonable notice window. Example wording: 'Either party may terminate this Agreement for convenience upon sixty (60) days' prior written notice to the other party.'"
    },
    {
        "id": "ip_assignment",
        "pattern": r"(?i)ownership\s+of\s+intellectual\s+property|intellectual\s+property\s+rights|assignment\s+of\s+inventions|work\s+made\s+for\s+hire|all\s+rights\s+title\s+and\s+interest",
        "name": "Intellectual Property Transfer",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Transfers the ownership rights of all materials, inventions, or codes created during the engagement to the other party.",
        "suggestion": "Why it matters: Transferring all rights without carve-outs may cause you to lose ownership of your pre-existing tools or methods. Suggested change: Consider narrowing the scope to exclude pre-existing IP and conditioning transfer on full payment. Example wording: 'Upon receipt of full payment, Contractor hereby assigns to Client all right, title, and interest in deliverables created under this Agreement, excluding Contractor's pre-existing materials.'"
    },
    {
        "id": "late_penalties",
        "pattern": r"(?i)late\s+payment|late\s+fee|interest\s+rate\s+of|finance\s+charge|penalty\s+for\s+late|overdue\s+invoice",
        "name": "Late Payment Interest & Penalties",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Imposes heavy penalties or high annual interest rates for invoices that are paid late.",
        "suggestion": "Why it matters: Immediate interest charges and late fees can accrue due to minor processing delays. Suggested change: Consider requesting a written notice and cure grace period before penalties apply. Example wording: 'Late payments shall bear interest at 1% per month starting fifteen (15) days after written notice from Contractor that payment is past due.'"
    },
    {
        "id": "governing_law",
        "pattern": r"(?i)governing\s+law\s+in|governed\s+by\s+and\s+construed\s+in\s+accordance\s+with|jurisdiction\s+of\s+the\s+courts\s+of",
        "name": "Governing Law / Jurisdiction",
        "score_impact": 5,
        "severity": "NEUTRAL",
        "explanation": "Determines which state or country's laws govern the contract and where disputes must be filed.",
        "suggestion": "Why it matters: Choice of law dictates which state's statutes apply and where lawsuits must be brought, potentially increasing costs. Suggested change: Consider requesting clarification to specify a mutual or reasonable jurisdiction. Example wording: 'This Agreement shall be governed by and construed in accordance with the laws of [Your State], without regard to conflict of law principles.'"
    }
]

def extract_snippet(text: str, match: re.Match) -> str:
    """
    Extracts a contextual snippet of around 150 characters around the matching index.
    """
    start, end = match.span()
    
    # Expand boundaries by ~60 characters on each side
    snippet_start = max(0, start - 60)
    snippet_end = min(len(text), end + 60)
    
    snippet = text[snippet_start:snippet_end]
    
    # Format with ellipses if text was truncated
    prefix = "..." if snippet_start > 0 else ""
    suffix = "..." if snippet_end < len(text) else ""
    
    return f"{prefix}{snippet.strip()}{suffix}"

def run_hybrid_risk_engine(text: str) -> Dict[str, Any]:
    """
    Calculates deterministic risk scores, extracts snippets, and maps
    vulnerabilities based on keyword matching rules.
    """
    matches = []
    base_score = 10  # Baseline contract risk start
    
    for rule in KEYWORD_RULES:
        # Search for all matches of the pattern
        all_matches = list(re.finditer(rule["pattern"], text))
        if all_matches:
            # We match the rule!
            # Increase base score (but limit count impact to avoid capping at 100 too fast)
            count = len(all_matches)
            impact = rule["score_impact"]
            # First match adds 100% of impact, subsequent matches add 20% of impact
            calculated_impact = int(impact + (count - 1) * (impact * 0.2))
            base_score += calculated_impact
            
            # Extract first snippet for visualization
            snippet = extract_snippet(text, all_matches[0])
            
            matches.append({
                "id": rule["id"],
                "name": rule["name"],
                "severity": rule["severity"],
                "scoreImpact": rule["score_impact"],
                "occurrenceCount": count,
                "explanation": rule["explanation"],
                "suggestion": rule["suggestion"],
                "snippet": snippet
            })
            
    # Cap score at 99. A score of 100 is reserved for extremely dangerous situations validated by AI.
    overall_score = min(99, base_score)
    
    # Map score to risk level
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
        
    return {
        "baseScore": overall_score,
        "riskLevel": risk_level,
        "matches": matches
    }
