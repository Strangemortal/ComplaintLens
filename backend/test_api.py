import urllib.request
import json

def test_api():
    print("==================================================")
    print("STARTING QMS API ENDPOINTS VERIFICATION")
    print("==================================================")
    
    # 1. Health Check
    try:
        req = urllib.request.urlopen("http://localhost:8000/")
        res = json.loads(req.read().decode())
        print(f"[API Check 1] Health Check: SUCCESS -> {res}")
    except Exception as e:
        print(f"[API Check 1] Health Check: FAILED -> {e}")
        return

    # 2. Chat workflow
    chat_payload = {
        "message": "A pharmacy reported that Paracetamol 500 mg tablets from batch PCM24015 are discolored. Around 300 strips are affected. Manufactured January 2026 and expires December 2028.",
        "current_form": None,
        "current_risk": None
    }
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/chat",
            data=json.dumps(chat_payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print("\n[API Check 2] Chat Endpoint: SUCCESS")
            print(f"  Intent: {res['intent']}")
            print(f"  Mock: {res['is_mock']}")
            print(f"  Form Product: {res['form']['product_name']}")
            print(f"  Severity: {res['risk']['severity']}")
            
            extracted_form = res["form"]
            extracted_risk = res["risk"]
    except Exception as e:
        print(f"[API Check 2] Chat Endpoint: FAILED -> {e}")
        return

    # 3. Chat Edit workflow
    edit_payload = {
        "message": "Batch number is PCM24018 instead.",
        "current_form": extracted_form,
        "current_risk": extracted_risk
    }
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/chat",
            data=json.dumps(edit_payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print("\n[API Check 3] Chat Edit Endpoint: SUCCESS")
            print(f"  Updated Batch: {res['form']['batch_number']}")
            assert res['form']['batch_number'] == "PCM24018", "Batch was not updated to PCM24018"
            
            final_form = res["form"]
            final_risk = res["risk"]
    except Exception as e:
        print(f"[API Check 3] Chat Edit Endpoint: FAILED -> {e}")
        return

    # 4. Save Complaint to DB
    save_payload = {
        "form": final_form,
        "risk": final_risk
    }
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/complaints",
            data=json.dumps(save_payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print("\n[API Check 4] Save Endpoint: SUCCESS")
            print(f"  Saved DB ID: {res['id']}")
            print(f"  Product Name: {res['product_name']}")
            print(f"  Risk Severity: {res['risk_assessment']['severity']}")
            saved_id = res["id"]
    except Exception as e:
        print(f"[API Check 4] Save Endpoint: FAILED -> {e}")
        return

    # 5. List Complaints from DB
    try:
        req = urllib.request.urlopen("http://localhost:8000/api/complaints")
        res = json.loads(req.read().decode())
        print(f"\n[API Check 5] List Endpoint: SUCCESS -> Found {len(res)} records in database.")
        assert len(res) >= 1, "Database complaints list is empty"
    except Exception as e:
        print(f"[API Check 5] List Endpoint: FAILED -> {e}")
        return

    # 6. Delete Complaint
    try:
        req = urllib.request.Request(
            f"http://localhost:8000/api/complaints/{saved_id}",
            method="DELETE"
        )
        with urllib.request.urlopen(req) as response:
            print(f"\n[API Check 6] Delete Endpoint: SUCCESS -> Deleted record #{saved_id}")
    except Exception as e:
        print(f"[API Check 6] Delete Endpoint: FAILED -> {e}")
        return

    print("\n==================================================")
    print("ALL QMS API ENDPOINTS VERIFIED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_api()
