import urllib.request
import urllib.parse
import json
import os
import mimetypes

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "ComplaintLensTest/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get_json(endpoint):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        headers={"User-Agent": "ComplaintLensTest/1.0"},
        method="GET"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def delete_req(endpoint):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        headers={"User-Agent": "ComplaintLensTest/1.0"},
        method="DELETE"
    )
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8").strip()
        data = json.loads(content) if content else {"status": "success"}
        return resp.status, data

def upload_file(endpoint, file_path):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "ComplaintLensTest/1.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def run_tests():
    passed = 0
    failed = 0

    def record_pass(test_name):
        nonlocal passed
        passed += 1
        print(f"  [PASS] {test_name}")

    def record_fail(test_name, reason):
        nonlocal failed
        failed += 1
        print(f"  [FAIL] {test_name}: {reason}")

    print("======================================================================")
    print(" COMPLAINTLENS COMPREHENSIVE END-TO-END TEST SUITE")
    print("======================================================================")

    # 1. Health check
    print("\n--- Test Suite 1: Health & Connectivity ---")
    try:
        st, res = get_json("/")
        assert st == 200 and res["status"] == "healthy"
        record_pass("Root health check (/)")
    except Exception as e:
        record_fail("Root health check (/)", str(e))

    try:
        st, res = get_json("/api/health")
        assert st == 200 and "llm" in res
        print(f"       LLM Status: Live={res['llm']['llm_live']}, Provider={res['llm']['provider']}")
        record_pass("API health & LLM status (/api/health)")
    except Exception as e:
        record_fail("API health & LLM status (/api/health)", str(e))

    try:
        st, res = post_json("/api/chat/reset-circuit", {})
        assert st == 200 and res["status"] == "ok"
        record_pass("Circuit breaker reset (/api/chat/reset-circuit)")
    except Exception as e:
        record_fail("Circuit breaker reset", str(e))

    # 2. Chat Extraction (New Complaint)
    print("\n--- Test Suite 2: AI Intent & Field Extraction (Live LLM) ---")
    extracted_form = None
    extracted_risk = None
    try:
        msg = "Hospital emergency reported that Ibuprofen 400 mg oral suspension batch IBU-2024-88 has visible sediment and mold growth. 200 bottles involved. Reported by Nurse Kelly."
        st, res = post_json("/api/chat", {"message": msg, "current_form": None, "current_risk": None})
        assert st == 200
        assert res["intent"] == "NEW_COMPLAINT"
        assert "Ibuprofen" in (res["form"]["product_name"] or "")
        assert "IBU-2024-88" in (res["form"]["batch_number"] or "")
        assert res["risk"]["severity"] in ["Critical", "Major"]
        print(f"       Product: {res['form']['product_name']}, Batch: {res['form']['batch_number']}, Severity: {res['risk']['severity']}")
        extracted_form = res["form"]
        extracted_risk = res["risk"]
        record_pass("New complaint extraction with live LLM")
    except Exception as e:
        record_fail("New complaint extraction with live LLM", str(e))

    # 3. Chat Multi-turn Editing
    print("\n--- Test Suite 3: Multi-turn State Preservation & Field Editing ---")
    if extracted_form:
        try:
            edit_msg = "Correction: the batch number is IBU-2024-99 instead, and quantity is 350 bottles."
            st, res = post_json("/api/chat", {"message": edit_msg, "current_form": extracted_form, "current_risk": extracted_risk})
            assert st == 200
            assert res["intent"] == "EDIT_COMPLAINT"
            assert res["form"]["batch_number"] == "IBU-2024-99"
            assert "350" in res["form"]["quantity"]
            assert "Ibuprofen" in (res["form"]["product_name"] or "")  # Preserved!
            print(f"       Updated Batch: {res['form']['batch_number']}, Quantity: {res['form']['quantity']}, Product preserved: {res['form']['product_name']}")
            extracted_form = res["form"]
            record_pass("Field editing while preserving existing fields")
        except Exception as e:
            record_fail("Field editing while preserving existing fields", str(e))

    # 4. General QA intent (no form corruption)
    print("\n--- Test Suite 4: General Knowledge Routing (Zero State Tampering) ---")
    if extracted_form:
        try:
            qa_msg = "What is the standard regulatory reporting timeline for a Class II recall under 21 CFR 7?"
            st, res = post_json("/api/chat", {"message": qa_msg, "current_form": extracted_form, "current_risk": extracted_risk})
            assert st == 200
            assert res["intent"] == "GENERAL_CHAT"
            assert res["form"]["batch_number"] == extracted_form["batch_number"]  # Unaltered!
            assert len(res["chat_response"]) > 20
            print(f"       AI Response: {res['chat_response'][:100]}...")
            record_pass("General QA dialogue without corrupting form state")
        except Exception as e:
            record_fail("General QA dialogue without corrupting form state", str(e))

    # 5. Database CRUD Lifecycle
    print("\n--- Test Suite 5: Database CRUD Lifecycle ---")
    saved_id = None
    try:
        save_payload = {
            "form": extracted_form or {
                "product_name": "Ciprofloxacin",
                "strength": "500 mg",
                "batch_number": "CIP-4401",
                "quantity": "50 boxes",
                "manufacturing_date": "March 2026",
                "expiry_date": "March 2028",
                "complaint_description": "Cracked blister foil causing exposed tablets."
            },
            "risk": extracted_risk or {
                "severity": "Major",
                "priority": "High",
                "reason": "Compromised barrier integrity.",
                "impact": "Moisture exposure and potency degradation.",
                "recommended_action": "Quarantine stock and initiate CAPA."
            }
        }
        st, res = post_json("/api/complaints", save_payload)
        assert st in (200, 201) and res["id"] is not None
        saved_id = res["id"]
        assert res["product_name"] == save_payload["form"]["product_name"]
        print(f"       Saved record ID: #{saved_id}, Risk loaded: {res['risk_assessment'] is not None}")
        record_pass("Create complaint in database (POST /api/complaints)")
    except Exception as e:
        record_fail("Create complaint in database", str(e))

    # List complaints
    try:
        st, res = get_json("/api/complaints")
        assert st in (200, 201) and isinstance(res, list) and len(res) > 0
        matching = [item for item in res if item["id"] == saved_id]
        assert len(matching) == 1
        record_pass(f"Retrieve all complaints list (GET /api/complaints) -> {len(res)} total records")
    except Exception as e:
        record_fail("Retrieve all complaints list", str(e))

    # Delete complaint
    if saved_id:
        try:
            st, res = delete_req(f"/api/complaints/{saved_id}")
            assert st in (200, 204) and res.get("status") == "success"
            record_pass(f"Delete complaint record (DELETE /api/complaints/{saved_id})")

            # Verify it's actually deleted
            st, res = get_json("/api/complaints")
            remaining = [item for item in res if item["id"] == saved_id]
            assert len(remaining) == 0
            record_pass("Verify record is permanently removed from DB")
        except Exception as e:
            record_fail("Delete complaint record", str(e))

    # 6. PDF Ingestion Test
    print("\n--- Test Suite 6: PDF Ingestion & OCR Pipeline ---")
    pdf_path = r"c:\Users\BharatBK\Documents\okay new project for ilp\ComplaintLens\sample_data\sample_complaint_paracetamol.pdf"
    if os.path.exists(pdf_path):
        try:
            st, res = upload_file("/api/upload", pdf_path)
            assert st == 200
            assert "form" in res and "risk" in res
            assert res["form"]["product_name"] is not None
            print(f"       Extracted from PDF -> Product: {res['form']['product_name']}, Severity: {res['risk']['severity']}")
            record_pass("PDF document upload and automated QMS extraction (/api/upload)")
        except Exception as e:
            record_fail("PDF document upload", str(e))
    else:
        print(f"       [SKIP] Sample PDF not found at {pdf_path}")

    # 7. Edge Cases & Resilience
    print("\n--- Test Suite 7: Edge Cases & Robustness ---")
    # Empty message
    try:
        st, res = post_json("/api/chat", {"message": "   ", "current_form": None, "current_risk": None})
        assert st == 200
        record_pass("Handles empty whitespace message gracefully")
    except Exception as e:
        record_fail("Handles empty whitespace message", str(e))

    # Special characters and unicode
    try:
        special_msg = "Complaint: 'Acetaminophen & Codeine' #100-Tabs @Pharmacy#42 (Batch: AC-2024$!*). 100% defective!"
        st, res = post_json("/api/chat", {"message": special_msg, "current_form": None, "current_risk": None})
        assert st == 200
        record_pass("Handles complex punctuation, quotes, and symbols (#, @, $, %)")
    except Exception as e:
        record_fail("Handles complex punctuation", str(e))

    # Long verbose message (1000+ chars)
    try:
        long_msg = "A detailed quality report was submitted by the clinical supplies department regarding batch XYZ-9988. " * 15
        st, res = post_json("/api/chat", {"message": long_msg, "current_form": None, "current_risk": None})
        assert st == 200
        record_pass("Handles large paragraph inputs without truncation or timeout")
    except Exception as e:
        record_fail("Handles large paragraph inputs", str(e))

    print("\n======================================================================")
    print(f" TEST RUN RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {passed + failed})")
    print("======================================================================")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
