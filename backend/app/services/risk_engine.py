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
        "suggestion": "Request a cap on liability, typically limited to the total fees paid under the contract or a specific insurance-backed limit."
    },
    {
        "id": "binding_arbitration",
        "pattern": r"(?i)binding\s+arbitration|shall\s+be\s+resolved\s+by\s+arbitration|subject\s+to\s+arbitration|arbitration\s+association|waive\s+any\s+right\s+to\s+a\s+jury|class\s+action\s+waiver",
        "name": "Binding Arbitration & Jury Waiver",
        "score_impact": 20,
        "severity": "HIGH",
        "explanation": "Bypasses the public court system in favor of private arbitration and waives your right to a trial by jury or class actions.",
        "suggestion": "Ensure arbitration is mutual, located in a convenient jurisdiction, and contains carve-outs for injunctive relief or small claims."
    },
    {
        "id": "non_compete",
        "pattern": r"(?i)non-compete|covenant\s+not\s+to\s+compete|shall\s+not\s+compete|restriction\s+on\s+employment|not\s+solicit\s+customers|prevent\s+from\s+engaging",
        "name": "Non-Compete Restriction",
        "score_impact": 20,
        "severity": "HIGH",
        "explanation": "Restricts your ability to work for competitors or start a similar business after this agreement terminates.",
        "suggestion": "Request removal of the non-compete. If not possible, limit its duration to less than 6 months and narrow the geographic/industry scope."
    },
    {
        "id": "indemnification",
        "pattern": r"(?i)indemnify\s+and\s+hold\s+harmless|shall\s+indemnify|indemnity\s+obligation|indemnification\s+by\s+the\s+contractor",
        "name": "One-Sided Indemnification",
        "score_impact": 15,
        "severity": "HIGH",
        "explanation": "Requires you to pay the legal costs and damages incurred by the other party due to standard performance issues.",
        "suggestion": "Make the indemnification mutual. Limit your indemnity to third-party claims arising solely from your gross negligence or breach."
    },
    {
        "id": "automatic_renewal",
        "pattern": r"(?i)automatic\s+renewal|auto-renew|automatically\s+renew|auto\s+renewal|renews\s+successive|renewal\s+term\s+of",
        "name": "Automatic Renewal",
        "score_impact": 15,
        "severity": "MEDIUM",
        "explanation": "The contract automatically extends itself unless cancelled in writing within a narrow window (e.g., 30-90 days before expiration).",
        "suggestion": "Change the renewal clause to require mutual written agreement, or extend the termination notice window."
    },
    {
        "id": "liquidated_damages",
        "pattern": r"(?i)liquidated\s+damages|pre-determined\s+damages|forfeiture\s+of\s+deposit|shall\s+forfeit|fee\s+as\s+damages",
        "name": "Liquidated Damages Penalty",
        "score_impact": 15,
        "severity": "HIGH",
        "explanation": "Establishes a fixed, pre-agreed penalty fee for breaches. These can be punitive and higher than actual damages.",
        "suggestion": "Require that actual damages be proven in a dispute rather than relying on automatic predetermined penalties."
    },
    {
        "id": "termination_convenience",
        "pattern": r"(?i)terminate\s+for\s+convenience|termination\s+without\s+cause|terminate\s+at\s+any\s+time\s+without|may\s+terminate\s+this\s+agreement\s+upon\s+\d+\s+days",
        "name": "Termination for Convenience",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Allows a party to walk away from the contract at any time for no reason, leading to high business instability.",
        "suggestion": "Ensure the right is mutual, and request a notice period of at least 30 to 60 days to allow for transition."
    },
    {
        "id": "ip_assignment",
        "pattern": r"(?i)ownership\s+of\s+intellectual\s+property|intellectual\s+property\s+rights|assignment\s+of\s+inventions|work\s+made\s+for\s+hire|all\s+rights\s+title\s+and\s+interest",
        "name": "Intellectual Property Transfer",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Transfers the ownership rights of all materials, inventions, or codes created during the engagement to the other party.",
        "suggestion": "Retain ownership of pre-existing intellectual property and tools. Make sure IP transfer occurs only after full payment."
    },
    {
        "id": "late_penalties",
        "pattern": r"(?i)late\s+payment|late\s+fee|interest\s+rate\s+of|finance\s+charge|penalty\s+for\s+late|overdue\s+invoice",
        "name": "Late Payment Interest & Penalties",
        "score_impact": 10,
        "severity": "MEDIUM",
        "explanation": "Imposes heavy penalties or high annual interest rates for invoices that are paid late.",
        "suggestion": "Negotiate a grace period of 10-15 business days after invoice delivery and cap interest at standard commercial rates (e.g. 1% monthly)."
    },
    {
        "id": "governing_law",
        "pattern": r"(?i)governing\s+law\s+in|governed\s+by\s+and\s+construed\s+in\s+accordance\s+with|jurisdiction\s+of\s+the\s+courts\s+of",
        "name": "Governing Law / Jurisdiction",
        "score_impact": 5,
        "severity": "LOW",
        "explanation": "Determines which state or country's laws govern the contract and where disputes must be filed.",
        "suggestion": "Ensure governing law and jurisdiction are located in a convenient state or country to avoid travel and foreign legal costs."
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
    if overall_score < 25:
        risk_level = "SAFE"
    elif overall_score < 45:
        risk_level = "LOW RISK"
    elif overall_score < 70:
        risk_level = "MODERATE RISK"
    elif overall_score < 88:
        risk_level = "RISKY"
    else:
        risk_level = "DANGEROUS"
        
    return {
        "baseScore": overall_score,
        "riskLevel": risk_level,
        "matches": matches
    }
