import re
import os
from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.schemas.complaint_schema import ComplaintSchema, RiskAssessmentSchema
from app.services.groq import get_llm

# Define Graph State
class AgentState(TypedDict):
    messages: List[dict]
    current_form: ComplaintSchema
    current_risk: RiskAssessmentSchema
    intent: str
    user_message: str
    is_mock: bool
    chat_response: str

# Schema for Intent Detection LLM structured output
class IntentOutput(BaseModel):
    intent: Literal["NEW_COMPLAINT", "EDIT_COMPLAINT", "GENERAL_CHAT"] = Field(
        description="The classified intent of the user's message."
    )
    explanation: str = Field(description="Short rationale for classification.")

# ----------------- Helper Mock Rules for Local Sandbox -----------------
def run_mock_intent_detection(message: str) -> str:
    msg_lower = message.lower()
    if any(k in msg_lower for k in ["instead", "update", "change", "batch number is", "quantity is", "actually"]):
        return "EDIT_COMPLAINT"
    elif any(k in msg_lower for k in ["complaint", "pharmacy", "received", "box", "strip", "discolor", "broken", "capsule", "tablet"]):
        return "NEW_COMPLAINT"
    else:
        return "GENERAL_CHAT"

def run_mock_extraction(message: str) -> ComplaintSchema:
    msg_lower = message.lower()
    
    # Simple regex matchers
    product = "Paracetamol" if "paracetamol" in msg_lower else ("Amoxicillin" if "amoxicillin" in msg_lower else "Unknown Product")
    
    strength_match = re.search(r"(\d+\s*(?:mg|g))", msg_lower)
    strength = strength_match.group(1).upper() if strength_match else "500 mg"
    
    batch_match = re.search(r"batch\s*:?\s*([a-z0-9]+)", msg_lower)
    batch = batch_match.group(1).upper() if batch_match else "PCM24015"
    
    qty_match = re.search(r"(\d+\s*(?:strips|boxes|packs|units|capsules|tablets|strips affected))", msg_lower)
    qty = qty_match.group(1) if qty_match else "300 strips"
    
    # Try dates
    mfg_match = re.search(r"(?:manufactured|mfg)\s*:?\s*([a-z]+\s*\d{4}|\d{2}/\d{4})", msg_lower)
    mfg = mfg_match.group(1).title() if mfg_match else "January 2026"
    
    exp_match = re.search(r"(?:expires|expiry|exp)\s*:?\s*([a-z]+\s*\d{4}|\d{2}/\d{4})", msg_lower)
    exp = exp_match.group(1).title() if exp_match else "December 2028"
    
    desc = "Discolored tablets"
    if "broken" in msg_lower:
        desc = "Broken capsules"
    elif "damage" in msg_lower:
        desc = "Damaged packaging"
    elif "complaint" in msg_lower:
        # Extract everything after "complaint:" or similar
        desc = message
        
    return ComplaintSchema(
        product_name=product,
        strength=strength,
        batch_number=batch,
        manufacturing_date=mfg,
        expiry_date=exp,
        quantity=qty,
        complaint_description=desc
    )

def run_mock_edit(message: str, current: ComplaintSchema) -> ComplaintSchema:
    msg_lower = message.lower()
    updated = ComplaintSchema(**current.model_dump())
    
    # Update Batch
    if "batch" in msg_lower:
        match = re.search(r"batch\s*(?:number|no)?\s*(?:is|to|be)?\s*([a-z0-9]+)", msg_lower)
        if match:
            updated.batch_number = match.group(1).upper()
            
    # Update Quantity
    if any(k in msg_lower for k in ["qty", "quantity", "strips", "boxes", "actually"]):
        match = re.search(r"(?:qty|quantity|is|be|to)\s*(\d+\s*(?:strips|boxes|packs|units|capsules|tablets)?)", msg_lower)
        if not match:
            match = re.search(r"(\d+\s*(?:strips|boxes|packs|units|capsules|tablets)?)", msg_lower)
        if match:
            val = match.group(1)
            if val.isdigit():
                prev_suffix = "".join([c for c in (current.quantity or "") if not c.isdigit()]).strip()
                updated.quantity = f"{val} {prev_suffix}".strip()
            else:
                updated.quantity = val
                
    # Update MFG Date
    if "mfg" in msg_lower or "manufactur" in msg_lower:
        match = re.search(r"(?:mfg|manufactur)\w*\s*(?:date|no)?\s*(?:is|to|be)?\s*([a-z0-9/\s]+?)(?:\s+instead|\.|$|,)", msg_lower)
        if match:
            updated.manufacturing_date = match.group(1).strip().title()
            
    # Update EXP Date
    if "exp" in msg_lower or "expiry" in msg_lower or "expire" in msg_lower:
        match = re.search(r"(?:exp|expiry|expire)\w*\s*(?:date|no)?\s*(?:is|to|be)?\s*([a-z0-9/\s]+?)(?:\s+instead|\.|$|,)", msg_lower)
        if match:
            updated.expiry_date = match.group(1).strip().title()
            
    # Update Product
    if "product" in msg_lower or "name" in msg_lower:
        match = re.search(r"(?:product|name)\s*(?:is|to|be)?\s*([a-z]+)", msg_lower)
        if match:
            updated.product_name = match.group(1).strip().title()
            
    return updated

def run_mock_risk(complaint: ComplaintSchema) -> RiskAssessmentSchema:
    desc = (complaint.complaint_description or "").lower()
    
    if "discolor" in desc:
        return RiskAssessmentSchema(
            severity="Major",
            priority="High",
            reason="Product discoloration can indicate chemical degradation, active ingredient loss, or bacterial contamination.",
            impact="Potential patient safety concern; reduced therapeutic efficacy.",
            recommended_action="Route to QA Investigation. Hold remaining inventory. Initiate replacement shipment for affected customer."
        )
    elif "broken" in desc or "crack" in desc:
        return RiskAssessmentSchema(
            severity="Major",
            priority="Medium",
            reason="Physical fracturing or broken capsules compromises dose accuracy and exposes active ingredients to environmental moisture.",
            impact="Incomplete dosing; potential product instability.",
            recommended_action="Initiate QA Investigation. Replace customer stock. Request return samples for inspection."
        )
    elif "damage" in desc or "box" in desc:
        return RiskAssessmentSchema(
            severity="Minor",
            priority="Low",
            reason="External packaging damage without compromise of internal blister seals does not impact product quality directly.",
            impact="Cosmetic/aesthetic issue only; low risk to patient safety.",
            recommended_action="Inspect secondary packaging SOPs. Provide feedback to logistics provider."
        )
    else:
        return RiskAssessmentSchema(
            severity="Minor",
            priority="Low",
            reason="General complaint or unknown hazard category. Standard baseline assessment applied.",
            impact="Low initial impact suspected.",
            recommended_action="Log and monitor. Route to customer support."
        )

# ----------------- LangGraph Node Functions -----------------

def detect_intent_node(state: AgentState):
    user_msg = state["user_message"]
    
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(IntentOutput)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent QMS assistant. Classify the user's intent: "
                       "- NEW_COMPLAINT: If the user is submitting a new product defect/complaint. "
                       "- EDIT_COMPLAINT: If the user wants to update or correct a specific field in the current complaint (e.g. batch, qty). "
                       "- GENERAL_CHAT: Greeting, QMS queries, general chatter, or explanations. "
                       "Provide the classification in the required schema."),
            ("user", "{message}")
        ])
        chain = prompt | structured_llm
        res = chain.invoke({"message": user_msg})
        intent = res.intent
        is_mock = False
    except Exception as e:
        print(f"Fallback to Mock Intent Detection: {e}")
        intent = run_mock_intent_detection(user_msg)
        is_mock = True
        
    return {
        "intent": intent,
        "is_mock": is_mock
    }

def extract_complaint_node(state: AgentState):
    user_msg = state["user_message"]
    
    if state.get("is_mock"):
        extracted = run_mock_extraction(user_msg)
        chat_res = "⚠️ Mock Mode: Extracted new complaint details from text."
    else:
        try:
            llm = get_llm()
            structured_llm = llm.with_structured_output(ComplaintSchema)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a QMS extraction assistant. Extract complaint information into the fields. "
                           "If a field cannot be found, leave it as null. Do not hallucinate values. "
                           "Fields to extract: Product Name, Strength, Batch Number, Manufacturing Date, Expiry Date, Quantity, Complaint Description."),
                ("user", "{message}")
            ])
            chain = prompt | structured_llm
            extracted = chain.invoke({"message": user_msg})
            chat_res = "I have extracted the complaint information and filled the form."
        except Exception as e:
            print(f"Extraction failed: {e}")
            extracted = run_mock_extraction(user_msg)
            chat_res = "⚠️ Mock Mode: Extracted complaint fields via local parsing."
            
    return {
        "current_form": extracted,
        "chat_response": chat_res
    }

def edit_complaint_node(state: AgentState):
    user_msg = state["user_message"]
    curr_form = state["current_form"] or ComplaintSchema()
    
    if state.get("is_mock"):
        updated = run_mock_edit(user_msg, curr_form)
        chat_res = "⚠️ Mock Mode: Updated specified fields."
    else:
        try:
            llm = get_llm()
            structured_llm = llm.with_structured_output(ComplaintSchema)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a QMS editing assistant. The user wants to update fields of the current complaint. "
                           "Update ONLY the fields the user explicitly requests to change. PRESERVE all other fields. "
                           "Current Complaint Status:\n{current_state}\n\nUpdate requested:"),
                ("user", "{message}")
            ])
            chain = prompt | structured_llm
            updated = chain.invoke({
                "current_state": curr_form.json(),
                "message": user_msg
            })
            chat_res = "I have updated the specified complaint fields as requested."
        except Exception as e:
            print(f"Edit failed: {e}")
            updated = run_mock_edit(user_msg, curr_form)
            chat_res = "⚠️ Mock Mode: Updated complaint fields via local parsing."
            
    return {
        "current_form": updated,
        "chat_response": chat_res
    }

def risk_assessment_node(state: AgentState):
    curr_form = state["current_form"] or ComplaintSchema()
    
    if state.get("is_mock"):
        risk = run_mock_risk(curr_form)
    else:
        try:
            llm = get_llm()
            structured_llm = llm.with_structured_output(RiskAssessmentSchema)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a pharmaceutical Quality Assurance Officer evaluating product complaints. "
                           "Perform a risk assessment based on the complaint fields. Classify severity (Critical, Major, Minor), "
                           "priority, reasoning, safety impact, and recommended QA actions."),
                ("user", "{complaint}")
            ])
            chain = prompt | structured_llm
            risk = chain.invoke({"complaint": curr_form.json()})
        except Exception as e:
            print(f"Risk Assessment failed: {e}")
            risk = run_mock_risk(curr_form)
            
    return {
        "current_risk": risk
    }

def general_chat_node(state: AgentState):
    user_msg = state["user_message"]
    
    if state.get("is_mock"):
        chat_res = ("⚠️ Mock Mode: I am your QMS Assistant. I can help you log product complaints, "
                    "update details in conversation, or assess risks. "
                    "Please configure GROQ_API_KEY in your backend/.env to connect to the active LLM workflow.")
    else:
        try:
            llm = get_llm()
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful, professional QMS assistant. Provide brief, concise responses to the user "
                           "about complaints, severity scoring, or general greetings. Do not try to extract forms here. "
                           "Keep it under 3 sentences."),
                ("user", "{message}")
            ])
            chain = prompt | llm
            res = chain.invoke({"message": user_msg})
            chat_res = res.content
        except Exception as e:
            print(f"Chat failed: {e}")
            chat_res = "⚠️ Mock Mode: Hello, how can I assist you with QMS complaints today?"
            
    return {
        "chat_response": chat_res
    }

# ----------------- Router Logic -----------------
def route_intent(state: AgentState):
    intent = state.get("intent")
    if intent == "NEW_COMPLAINT":
        return "extract"
    elif intent == "EDIT_COMPLAINT":
        return "edit"
    else:
        return "chat"

# ----------------- Build StateGraph -----------------
builder = StateGraph(AgentState)

builder.add_node("detect_intent", detect_intent_node)
builder.add_node("extract", extract_complaint_node)
builder.add_node("edit", edit_complaint_node)
builder.add_node("risk_assess", risk_assessment_node)
builder.add_node("chat", general_chat_node)

builder.set_entry_point("detect_intent")

builder.add_conditional_edges(
    "detect_intent",
    route_intent,
    {
        "extract": "extract",
        "edit": "edit",
        "chat": "chat"
    }
)

builder.add_edge("extract", "risk_assess")
builder.add_edge("edit", "risk_assess")
builder.add_edge("risk_assess", END)
builder.add_edge("chat", END)

# Compile Graph
graph = builder.compile()

def run_agent_workflow(message: str, current_form: Optional[ComplaintSchema] = None, current_risk: Optional[RiskAssessmentSchema] = None) -> dict:
    """
    Runner helper to feed the state graph and return the updated complaint/risk models and chat response.
    """
    initial_state = {
        "messages": [],
        "current_form": current_form or ComplaintSchema(),
        "current_risk": current_risk or RiskAssessmentSchema(severity="", priority="", reason="", impact="", recommended_action=""),
        "intent": "",
        "user_message": message,
        "is_mock": False,
        "chat_response": ""
    }
    
    result = graph.invoke(initial_state)
    return {
        "form": result.get("current_form"),
        "risk": result.get("current_risk"),
        "chat_response": result.get("chat_response"),
        "is_mock": result.get("is_mock", False),
        "intent": result.get("intent")
    }
