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
    if any(k in msg_lower for k in ["instead", "update", "change", "batch number is", "quantity is", "actually", "correct the", "change batch", "change quantity"]):
        return "EDIT_COMPLAINT"
    elif any(k in msg_lower for k in [
        "complaint", "pharmacy", "received", "box", "strip", "discolor", "broken", 
        "capsule", "tablet", "defect", "contamination", "particles", "damaged", "paracetamol", "amoxicillin", "aspirin"
    ]):
        return "NEW_COMPLAINT"
    else:
        return "GENERAL_CHAT"

COMMON_DRUGS = [
    "Paracetamol", "Amoxicillin", "Ibuprofen", "Aspirin", "Metformin", "Omeprazole",
    "Ciprofloxacin", "Atorvastatin", "Losartan", "Azithromycin", "Gabapentin",
    "Cetirizine", "Pantoprazole", "Lisinopril", "Levothyroxine", "Amlodipine"
]

def run_mock_extraction(message: str) -> ComplaintSchema:
    msg_clean = message.strip()
    msg_lower = message.lower()
    
    # ---------------- 1. PRODUCT NAME ----------------
    product = ""
    # A. Check for explicit labeled field (e.g. "Product Name:\nPremium Cooking Oil" or "Product: Paracetamol")
    prod_label_match = re.search(
        r'(?:^|\n)\s*(?:product\s*name|item\s*name|drug\s*name|product)\s*:\s*\n?\s*([^\n\r]+)',
        message,
        re.IGNORECASE
    )
    if prod_label_match:
        candidate = prod_label_match.group(1).strip()
        # Avoid matching generic category headers like "Product Quality / Packaging"
        if not re.search(r'quality\s*/\s*packaging|complaint\s*type', candidate, re.IGNORECASE):
            product = candidate
            
    # B. If not found via label, check known drug/product keywords
    if not product:
        for drug in COMMON_DRUGS:
            if drug.lower() in msg_lower:
                product = drug
                break
                
    # C. Check dynamic medicine/product pattern like "CoughSyrup 100 mg" or "Cooking Oil"
    if not product:
        dynamic_match = re.search(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+\d+\s*(?:mg|g|mcg|ml|l\b)', message)
        if dynamic_match and dynamic_match.group(1).lower() not in ("batch", "quantity", "exp", "mfg", "manufactured", "expires"):
            product = dynamic_match.group(1).title()
            
    if not product:
        product = "Unknown Product"

    # ---------------- 2. STRENGTH / VOLUME / PACK SIZE ----------------
    strength = ""
    strength_label = re.search(
        r'(?:^|\n)\s*(?:strength|potency|dosage|volume|pack\s*size|package\s*size|size)\s*:\s*\n?\s*([^\n\r]+)',
        message,
        re.IGNORECASE
    )
    if strength_label:
        strength = strength_label.group(1).strip()
    else:
        strength_match = re.search(
            r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|kg|ml|l|liter|liters|litre|litres|iu|%)(?:\s*(?:bottle|strip|vial|pack|box|tablets?|capsules?))?)',
            message,
            re.IGNORECASE
        )
        if strength_match:
            strength = strength_match.group(1).strip()
            
    # Clean product name if it repeats the extracted pack size/strength e.g. "Premium Cooking Oil – 1L Bottle"
    if product and strength:
        clean_prod = re.sub(r'[\s–\-]+' + re.escape(strength) + r'.*$', '', product, flags=re.IGNORECASE).strip()
        if clean_prod and len(clean_prod) > 2:
            product = clean_prod

    # ---------------- 3. BATCH NUMBER ----------------
    batch = ""
    batch_label = re.search(
        r'(?:^|\n)\s*(?:batch\s*(?:number|no|#)?|lot\s*(?:number|no|#)?)\s*:\s*\n?\s*([^\n\r]+)',
        message,
        re.IGNORECASE
    )
    if batch_label:
        batch = batch_label.group(1).strip().upper()
    else:
        batch_match = re.search(r'batch\s*(?:number|no|#)?\s*[:\s=]?\s*([a-zA-Z0-9\-_/]+)', msg_lower)
        if batch_match:
            batch = batch_match.group(1).upper()
            
    # ---------------- 4. QUANTITY ----------------
    qty = ""
    qty_aff = re.search(r'(?:^|\n)\s*quantity\s*affected\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
    qty_rec = re.search(r'(?:^|\n)\s*quantity\s*received\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
    if qty_aff and qty_rec:
        qty = f"{qty_aff.group(1).strip()} affected ({qty_rec.group(1).strip()} received)"
    elif qty_aff:
        qty = qty_aff.group(1).strip()
    elif qty_rec:
        qty = qty_rec.group(1).strip()
    else:
        qty_label = re.search(r'(?:^|\n)\s*(?:quantity|qty)\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
        if qty_label:
            qty = qty_label.group(1).strip()
        else:
            qty_match = re.search(r'(\d+\s*(?:strips|boxes|packs|units|capsules|tablets|bottles|vials|blisters|cartons|pieces|cans)(?:\s+affected)?)', msg_lower)
            if qty_match:
                qty = qty_match.group(1).strip()

    # ---------------- 5. DATES (MFG / EXP / PURCHASE) ----------------
    mfg = ""
    mfg_label = re.search(r'(?:^|\n)\s*(?:manufactur(?:ed|ing)?\s*date|mfg\s*date|date\s*of\s*mfg|mfg)\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
    if mfg_label:
        mfg = mfg_label.group(1).strip()
    else:
        mfg_free = re.search(r'(?:manufactured|mfg|mfg\s*date)\s*[:\s=]?\s*([a-z]+\s*\d{4}|\d{2}/\d{4}|\d{4}-\d{2})', msg_lower)
        if mfg_free:
            mfg = mfg_free.group(1).title()
            
    if not mfg:
        purch_label = re.search(r'(?:^|\n)\s*date\s*(?:of\s*(?:purchase|receipt|incident|delivery))?\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
        if purch_label:
            mfg = f"{purch_label.group(1).strip()} (Purchased)"

    exp = ""
    exp_label = re.search(r'(?:^|\n)\s*(?:expir(?:y|ation|ed)?\s*date|exp\s*date|date\s*of\s*exp|exp)\s*:\s*\n?\s*([^\n\r]+)', message, re.IGNORECASE)
    if exp_label:
        exp = exp_label.group(1).strip()
    else:
        exp_free = re.search(r'(?:expires|expiry|exp|exp\s*date)\s*[:\s=]?\s*([a-z]+\s*\d{4}|\d{2}/\d{4}|\d{4}-\d{2})', msg_lower)
        if exp_free:
            exp = exp_free.group(1).title()

    # ---------------- 6. COMPLAINT DESCRIPTION ----------------
    desc = ""
    desc_label = re.search(
        r'(?:^|\n)\s*(?:complaint\s*description|description|defect\s*details|problem\s*description|issue\s*details)\s*:\s*\n?([\s\S]+?)(?=\n\s*(?:immediate|action|requested|priority|potential|status|reported|\Z))',
        message,
        re.IGNORECASE
    )
    if desc_label:
        desc = " ".join(desc_label.group(1).split())
    else:
        if "broken" in msg_lower:
            desc = "Broken and crushed capsules detected inside blister strips."
        elif "discolor" in msg_lower:
            desc = "Discolored and mottled tablets observed upon customer inspection."
        elif "contaminat" in msg_lower or "partic" in msg_lower or "glass" in msg_lower:
            desc = "Foreign particulate matter / potential contamination detected in product batch."
        elif "leak" in msg_lower:
            desc = "Leaking containers and compromised packaging seals identified upon inspection."
        elif "damage" in msg_lower or "box" in msg_lower:
            desc = "External packaging crushed and torn during transit."
        else:
            desc = msg_clean
            
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
        match = re.search(r"batch\s*(?:number|no|#)?\s*(?:is|to|be|=|:)?\s*([a-z0-9\-]+)", msg_lower)
        if match:
            updated.batch_number = match.group(1).upper()
            
    # Update Quantity
    if any(k in msg_lower for k in ["qty", "quantity", "strips", "boxes", "actually"]):
        match = re.search(r"(?:qty|quantity|is|be|to|=)\s*(\d+\s*(?:strips|boxes|packs|units|capsules|tablets)?)", msg_lower)
        if not match:
            match = re.search(r"(\d+\s*(?:strips|boxes|packs|units|capsules|tablets)?)", msg_lower)
        if match:
            val = match.group(1).strip()
            new_qty_str = ""
            if val.isdigit():
                prev_suffix = "".join([c for c in (current.quantity or "") if not c.isdigit()]).strip()
                new_qty_str = f"{val} {prev_suffix}".strip()
                updated.quantity = new_qty_str
            else:
                new_qty_str = val
                updated.quantity = val
                
            # If the description contains the old quantity digits, replace them to maintain consistency
            if current.quantity and current.complaint_description:
                old_numbers = re.findall(r'\d+', current.quantity)
                new_numbers = re.findall(r'\d+', new_qty_str)
                if old_numbers and new_numbers:
                    old_num = old_numbers[0]
                    new_num = new_numbers[0]
                    if old_num in current.complaint_description:
                        updated.complaint_description = current.complaint_description.replace(old_num, new_num)
                        
    # Update MFG Date
    if "mfg" in msg_lower or "manufactur" in msg_lower:
        match = re.search(r"(?:mfg|manufactur)\w*\s*(?:date|no)?\s*(?:is|to|be|=|:)?\s*([a-z0-9/\s]+?)(?:\s+instead|\.|$|,)", msg_lower)
        if match:
            updated.manufacturing_date = match.group(1).strip().title()
            
    # Update EXP Date
    if "exp" in msg_lower or "expiry" in msg_lower or "expire" in msg_lower:
        match = re.search(r"(?:exp|expiry|expire)\w*\s*(?:date|no)?\s*(?:is|to|be|=|:)?\s*([a-z0-9/\s]+?)(?:\s+instead|\.|$|,)", msg_lower)
        if match:
            updated.expiry_date = match.group(1).strip().title()
            
    # Update Product
    if "product" in msg_lower or "name" in msg_lower:
        match = re.search(r"(?:product|name)\s*(?:is|to|be|=|:)?\s*([a-zA-Z0-9\s–\-]+?)(?:\s+instead|\.|$|,)", message, re.IGNORECASE)
        if match:
            updated.product_name = match.group(1).strip().title()
            
    # Update Complaint Description
    if any(k in msg_lower for k in ["description", "complaint", "defect", "details", "issue", "problem"]):
        match = re.search(r"(?:description|complaint|defect|details|issue|problem)\s*(?:is|to|be|=|:)?\s*(?:actually)?\s*([a-z0-9\s,\.]+?)(?:\s+instead|\.|$|,)", msg_lower)
        if match:
            updated.complaint_description = match.group(1).strip().capitalize()
    elif any(k in msg_lower for k in ["discolor", "broken", "crack", "damage", "smell", "spots", "crushed", "particulate", "contaminat", "leak"]):
        clean_msg = re.sub(r'\s+instead|\.|$|,', '', message).strip()
        updated.complaint_description = clean_msg[0].upper() + clean_msg[1:] if clean_msg else clean_msg
            
    return updated

def run_mock_risk(complaint: ComplaintSchema) -> RiskAssessmentSchema:
    desc = (complaint.complaint_description or "").lower()
    
    # 1. Critical defects (sterility, particulate, contamination, adverse events)
    if any(k in desc for k in ["contaminat", "partic", "glass", "foreign", "subpotent", "steril", "toxic"]):
        return RiskAssessmentSchema(
            severity="Critical",
            priority="Immediate",
            reason="Contamination or foreign matter poses a direct threat to safety and violates cGMP sterility/safety standards.",
            impact="Immediate patient safety hazard; risk of regulatory warning letter or mandatory class-I product recall.",
            recommended_action="Execute immediate warehouse quarantine for batch. Notify Quality Unit Head. Initiate Class-I recall assessment & CAPA within 24 hours."
        )
    # 2. Fluid leakage / Seal failure / Container breach
    elif any(k in desc for k in ["leak", "leaking", "leakage", "cap area", "seal breach", "seal broken", "visibly wet"]):
        return RiskAssessmentSchema(
            severity="Major",
            priority="High",
            reason="Primary packaging seal breach resulting in fluid leakage, container damage, and potential product contamination or spoilage.",
            impact="Loss of hermetic seal compromises product integrity and shelf-life, and causes outer carton damage.",
            recommended_action="Maintain batch quarantine. Request supplier investigation into cap torque and carton cushioning. Issue replacement shipment."
        )
    # 3. Chemical degradation / Discoloration
    elif "discolor" in desc:
        return RiskAssessmentSchema(
            severity="Major",
            priority="High",
            reason="Product discoloration can indicate chemical degradation, active ingredient loss, oxidation, or microbial growth.",
            impact="Potential patient safety concern; reduced therapeutic efficacy and compromised stability.",
            recommended_action="Route to QA Laboratory for HPLC assay and stability testing. Quarantine batch inventory. Issue customer replacement."
        )
    # 4. Fracturing / Broken units
    elif "broken" in desc or "crack" in desc:
        return RiskAssessmentSchema(
            severity="Major",
            priority="Medium",
            reason="Physical fracturing or broken capsules compromises dose accuracy and exposes active ingredients to atmospheric humidity.",
            impact="Incomplete or incorrect dosing; accelerated moisture degradation.",
            recommended_action="Initiate packaging line QA investigation. Replace customer stock. Request return samples for physical defect analysis."
        )
    # 5. Secondary Packaging damage
    elif "damage" in desc or "box" in desc or "carton" in desc:
        return RiskAssessmentSchema(
            severity="Minor",
            priority="Low",
            reason="Secondary packaging damage without breach of primary container barrier does not affect product substance stability.",
            impact="Aesthetic / cosmetic non-conformance; low risk to drug safety or efficacy.",
            recommended_action="Review shipping carton strength SOPs. Log in carrier quality scorecard and send replacement packaging."
        )
    else:
        return RiskAssessmentSchema(
            severity="Minor",
            priority="Low",
            reason="Standard complaint without acute safety breach. Baseline quality evaluation applied.",
            impact="Low expected patient impact under routine monitoring.",
            recommended_action="Log complaint in QMS register. Track batch trending metrics and close within standard 30-day window."
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
        from app.services.groq import mark_circuit_broken
        mark_circuit_broken(f"LLM unreachable or quota exceeded: {e}")
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
        chat_res = "Extracted new complaint details into the registration form."
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
            from app.services.groq import mark_circuit_broken
            mark_circuit_broken(f"LLM extraction failed: {e}")
            extracted = run_mock_extraction(user_msg)
            chat_res = "Extracted complaint fields via intelligent local parsing."
            
    return {
        "current_form": extracted,
        "chat_response": chat_res
    }

def edit_complaint_node(state: AgentState):
    user_msg = state["user_message"]
    curr_form = state["current_form"] or ComplaintSchema()
    
    if state.get("is_mock"):
        updated = run_mock_edit(user_msg, curr_form)
        chat_res = "Updated specified complaint fields."
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
            from app.services.groq import mark_circuit_broken
            mark_circuit_broken(f"LLM edit failed: {e}")
            updated = run_mock_edit(user_msg, curr_form)
            chat_res = "Updated complaint fields via local parsing."
            
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
            from app.services.groq import mark_circuit_broken
            mark_circuit_broken(f"LLM risk assessment failed: {e}")
            risk = run_mock_risk(curr_form)
            
    return {
        "current_risk": risk
    }

def general_chat_node(state: AgentState):
    user_msg = state["user_message"]
    
    if state.get("is_mock"):
        chat_res = ("Hello! I am your AI QMS Assistant. I can help you log product complaints, "
                    "update details in conversation, evaluate batch risks, or process complaint PDF reports.")
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
            from app.services.groq import mark_circuit_broken
            mark_circuit_broken(f"LLM chat failed: {e}")
            chat_res = ("Hello! I am your AI QMS Assistant. I can help you log product complaints, "
                        "update details in conversation, evaluate batch risks, or process complaint PDF reports.")
            
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
