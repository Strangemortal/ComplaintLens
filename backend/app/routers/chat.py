from fastapi import APIRouter, HTTPException
from app.schemas.complaint_schema import ChatRequest, ComplaintSchema, RiskAssessmentSchema
from app.services.langgraph import run_agent_workflow

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("")
def chat_with_agent(request: ChatRequest):
    try:
        result = run_agent_workflow(
            message=request.message,
            current_form=request.current_form,
            current_risk=request.current_risk
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")
