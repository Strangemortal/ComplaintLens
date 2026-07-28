import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(255), nullable=True)
    strength = Column(String(100), nullable=True)
    batch_number = Column(String(100), nullable=True)
    manufacturing_date = Column(String(100), nullable=True)
    expiry_date = Column(String(100), nullable=True)
    quantity = Column(String(100), nullable=True)
    complaint_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    risk_assessment = relationship("RiskAssessment", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    severity = Column(String(100), nullable=True)
    priority = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="risk_assessment")
