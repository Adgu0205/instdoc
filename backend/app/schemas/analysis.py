from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., description="The raw plain text of the legal contract to be analyzed.")

class RiskItem(BaseModel):
    clauseName: str = Field(..., description="The name of the clause containing risk.")
    severity: str = Field(..., description="Risk severity: CRITICAL, HIGH, MEDIUM, SAFE.")
    text: str = Field(..., description="The matching excerpt/sentence from the contract.")
    explanation: str = Field(..., description="Explanation of why this clause presents a risk.")
    suggestion: str = Field(..., description="Renegotiation recommendation or mitigation advice.")

class MissingClauseItem(BaseModel):
    clause: str = Field(..., description="The name of the protection clause that is missing.")
    severity: str = Field(..., description="Severity of the vulnerability: CRITICAL, HIGH, MEDIUM.")
    explanation: str = Field(..., description="Why the absence of this clause is problematic.")
    suggestion: str = Field(..., description="Proposed text or term to insert.")

class ScamSignalItem(BaseModel):
    pattern: str = Field(..., description="Mischievous or manipulative pattern, e.g. hidden fees.")
    explanation: str = Field(..., description="How it operates and targets the signee.")
    severity: str = Field(..., description="Severity level.")

class SimulationItem(BaseModel):
    scenario: str = Field(..., description="Hypothetical situation, e.g. early termination.")
    consequence: str = Field(..., description="Outcome under the contract's current terms.")
    mitigation: str = Field(..., description="Recommended amendment to minimize the risk.")

class AnalysisResponse(BaseModel):
    contractType: str = Field(..., description="Detected type of legal document.")
    overallRisk: int = Field(..., description="Overall risk rating from 0 (Safe) to 100 (Dangerous).")
    riskLevel: str = Field(..., description="Mapped risk level category.")
    confidence: int = Field(..., description="AI confidence score percentage.")
    summary: str = Field(..., description="Plain-English legal overview of the contract.")
    risks: List[RiskItem] = Field(default=[], description="List of identified risks in the document.")
    missingClauses: List[MissingClauseItem] = Field(default=[], description="Important clauses absent from the agreement.")
    scamSignals: List[ScamSignalItem] = Field(default=[], description="Manipulative, scam, or hidden terms detected.")
    simulations: List[SimulationItem] = Field(default=[], description="Simulated scenarios and outcomes.")
    thingsToKnow: List[str] = Field(default=[], description="Exactly 5 key facts the signee must know.")
    deterministicMatches: Optional[List[Dict[str, Any]]] = Field(default=[], description="Underlying keyword engine matches.")
    apiWarning: Optional[str] = Field(None, description="System warnings, e.g., missing API keys.")

class TaskStatusResponse(BaseModel):
    taskId: str = Field(..., description="The unique ID of the background task.")
    status: str = Field(..., description="The current status of the analysis: pending, processing, completed, failed.")
