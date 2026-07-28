import sys
import os

# Adjust import path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from services.langgraph import run_agent_workflow
from schemas.complaint_schema import ComplaintSchema, RiskAssessmentSchema

def test_qms_workflow():
    print("==================================================")
    print("STARTING QMS AI CO-PILOT INTEGRATION TEST")
    print("==================================================")
    
    # 1. Test Initial Extraction
    initial_message = (
        "A pharmacy reported that Paracetamol 500 mg tablets from batch PCM24015 are discolored. "
        "Around 300 strips are affected. Manufactured January 2026 and expires December 2028."
    )
    print(f"\n[Test 1] Initial Logging Message:\n' {initial_message} '")
    
    result = run_agent_workflow(message=initial_message)
    
    print("\n--- Extracted Complaint Form ---")
    form = result["form"]
    for key, value in form.model_dump().items():
        print(f"  {key:25}: {value}")
        
    print("\n--- Risk Assessment ---")
    risk = result["risk"]
    for key, value in risk.model_dump().items():
        print(f"  {key:25}: {value}")
        
    print(f"\n  Intent Detected: {result['intent']}")
    print(f"  Chat Response  : {result['chat_response']}")
    print(f"  Is Mock Mode   : {result['is_mock']}")
    
    assert form.product_name == "Paracetamol", "Product name extraction mismatch"
    assert form.batch_number == "PCM24015", "Batch number extraction mismatch"
    assert "300" in form.quantity, "Quantity extraction mismatch"
    assert risk.severity == "Major", "Severity assessment mismatch"
    
    # 2. Test Editing Batch
    edit_batch_message = "Batch number is PCM24018 instead."
    print(f"\n[Test 2] Editing Batch Message:\n' {edit_batch_message} '")
    
    result2 = run_agent_workflow(
        message=edit_batch_message,
        current_form=form,
        current_risk=risk
    )
    
    form2 = result2["form"]
    risk2 = result2["risk"]
    print("\n--- Updated Complaint Form ---")
    for key, value in form2.model_dump().items():
        print(f"  {key:25}: {value}")
        
    print(f"\n  Intent Detected: {result2['intent']}")
    print(f"  Chat Response  : {result2['chat_response']}")
    
    assert form2.batch_number == "PCM24018", "Batch number was not updated"
    assert form2.product_name == "Paracetamol", "Product name was not preserved"
    assert "300" in form2.quantity, "Quantity was not preserved"
    
    # 3. Test Editing Quantity
    edit_qty_message = "Quantity is actually 520 strips."
    print(f"\n[Test 3] Editing Quantity Message:\n' {edit_qty_message} '")
    
    result3 = run_agent_workflow(
        message=edit_qty_message,
        current_form=form2,
        current_risk=risk2
    )
    
    form3 = result3["form"]
    print("\n--- Final Complaint Form ---")
    for key, value in form3.model_dump().items():
        print(f"  {key:25}: {value}")
        
    print(f"\n  Intent Detected: {result3['intent']}")
    print(f"  Chat Response  : {result3['chat_response']}")
    
    assert "520" in form3.quantity, "Quantity was not updated"
    assert form3.batch_number == "PCM24018", "Batch number was not preserved"
    
    print("\n==================================================")
    print("ALL QMS CO-PILOT WORKFLOW TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_qms_workflow()
