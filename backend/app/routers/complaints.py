from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.complaint import Complaint, RiskAssessment
from app.schemas.complaint_schema import ComplaintCreate, ComplaintResponse, ComplaintSchema, RiskAssessmentSchema

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(data: ComplaintCreate, db: Session = Depends(get_db)):
    try:
        # Create Complaint
        new_complaint = Complaint(
            product_name=data.form.product_name,
            strength=data.form.strength,
            batch_number=data.form.batch_number,
            manufacturing_date=data.form.manufacturing_date,
            expiry_date=data.form.expiry_date,
            quantity=data.form.quantity,
            complaint_description=data.form.complaint_description
        )
        db.add(new_complaint)
        db.commit()
        db.refresh(new_complaint)
        
        # Create Risk Assessment
        new_risk = RiskAssessment(
            complaint_id=new_complaint.id,
            severity=data.risk.severity,
            priority=data.risk.priority,
            reason=data.risk.reason,
            impact=data.risk.impact,
            recommended_action=data.risk.recommended_action
        )
        db.add(new_risk)
        db.commit()
        db.refresh(new_complaint) # to load relation
        
        return new_complaint
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("", response_model=List[ComplaintResponse])
def list_complaints(db: Session = Depends(get_db)):
    try:
        complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
        return complaints
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint_record(complaint_id: int, data: ComplaintCreate, db: Session = Depends(get_db)):
    db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not db_complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    try:
        # Update Complaint
        db_complaint.product_name = data.form.product_name
        db_complaint.strength = data.form.strength
        db_complaint.batch_number = data.form.batch_number
        db_complaint.manufacturing_date = data.form.manufacturing_date
        db_complaint.expiry_date = data.form.expiry_date
        db_complaint.quantity = data.form.quantity
        db_complaint.complaint_description = data.form.complaint_description
        
        # Update Risk Assessment
        if db_complaint.risk_assessment:
            db_complaint.risk_assessment.severity = data.risk.severity
            db_complaint.risk_assessment.priority = data.risk.priority
            db_complaint.risk_assessment.reason = data.risk.reason
            db_complaint.risk_assessment.impact = data.risk.impact
            db_complaint.risk_assessment.recommended_action = data.risk.recommended_action
        else:
            new_risk = RiskAssessment(
                complaint_id=db_complaint.id,
                severity=data.risk.severity,
                priority=data.risk.priority,
                reason=data.risk.reason,
                impact=data.risk.impact,
                recommended_action=data.risk.recommended_action
            )
            db.add(new_risk)
            
        db.commit()
        db.refresh(db_complaint)
        return db_complaint
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint_record(complaint_id: int, db: Session = Depends(get_db)):
    db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not db_complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    try:
        db.delete(db_complaint)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
