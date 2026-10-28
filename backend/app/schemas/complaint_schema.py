from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RiskAssessmentSchema(BaseModel):
    severity: str = Field(description="The risk severity level (e.g., Critical, Major, Minor). Critical for potential life threatening, Major for active product degradation/defects, Minor for minor package damages.")
    priority: str = Field(description="The priority level (e.g., High, Medium, Low)")
    reason: str = Field(description="The detailed logical reasoning for this risk classification")
    impact: str = Field(description="Potential impact on patient safety or product efficacy")
    recommended_action: str = Field(description="Suggested next steps/SOP actions (e.g. Hold stock, QA investigation, replace item)")

class ComplaintSchema(BaseModel):
    product_name: Optional[str] = Field(
        None, 
        description="Generic or brand name of the drug or medical product (e.g. 'Ceftriaxone', 'Paracetamol', 'Amoxicillin'). NEVER use batch or lot codes."
    )
    strength: Optional[str] = Field(None, description="Strength or dosage form of the product (e.g. 1g, 500 mg, 250mg, 100ml)")
    batch_number: Optional[str] = Field(
        None, 
        description="The alphanumeric manufacturing batch or lot number (e.g. 'CEFT-2024-99', 'LOT-9812'). Never the drug name."
    )
    manufacturing_date: Optional[str] = Field(None, description="Manufacturing date (MFG)")
    expiry_date: Optional[str] = Field(None, description="Expiry date (EXP)")
    quantity: Optional[str] = Field(None, description="Number/amount of items affected (e.g. 80 vials, 300 strips, 15 boxes)")
    complaint_description: Optional[str] = Field(None, description="Detailed description of the customer complaint (e.g., visible black particulate matter floating in reconstituted solution)")

class ComplaintCreate(BaseModel):
    form: ComplaintSchema
    risk: RiskAssessmentSchema

class RiskAssessmentResponse(BaseModel):
    id: int
    complaint_id: int
    severity: Optional[str] = None
    priority: Optional[str] = None
    reason: Optional[str] = None
    impact: Optional[str] = None
    recommended_action: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintResponse(BaseModel):
    id: int
    product_name: Optional[str] = None
    strength: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity: Optional[str] = None
    complaint_description: Optional[str] = None
    created_at: datetime
    risk_assessment: Optional[RiskAssessmentResponse] = None

    class Config:
        from_attributes = True
        
class ChatRequest(BaseModel):
    message: str
    current_form: Optional[ComplaintSchema] = None
    current_risk: Optional[RiskAssessmentSchema] = None
