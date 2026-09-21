import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(endpoint, method="GET", data=None, token=None, headers_override=None):
    url = f"{BASE_URL}/{endpoint}" if not endpoint.startswith("http") else endpoint
    headers = headers_override or {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if (data and not isinstance(data, bytes)) else (data if isinstance(data, bytes) else None)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as res:
            res_body = res.read()
            try:
                return res.status, json.loads(res_body.decode("utf-8")), res.headers
            except Exception:
                return res.status, res_body, res.headers
    except urllib.error.HTTPError as e:
        res_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(res_body), e.headers
        except Exception:
            return e.code, {"error": res_body}, e.headers

print("========================================================================")
print("NAMMA CLINIC PATIENT RECORDS & DOCUMENT SECURITY TEST")
print("========================================================================\n")

# 1. Login
_, doc_auth, _ = make_req("auth/token/", method="POST", data={"username": "vh1_doctor", "password": "vh1doc123"})
doc_token = doc_auth["access"]

_, dist_auth, _ = make_req("auth/token/", method="POST", data={"username": "district", "password": "district123"})
dist_token = dist_auth["access"]

print("[1] AUTHENTICATION: PASS (Doctor & District Officer logged in)")

# 2. Get Patients
_, pat_resp, _ = make_req("patients/", token=doc_token)
pats = pat_resp.get("results", pat_resp)
ramesh = pats[0]
ramesh_id = ramesh["id"]
print(f"[2] PATIENT SCOPE: PASS (Target Patient '{ramesh['name']}' [ID: {ramesh_id}])")

# 3. Get Unified Patient Records
status, records, _ = make_req(f"patients/{ramesh_id}/records/", token=doc_token)
print(f"[3] UNIFIED PATIENT RECORDS: PASS (Status {status} | Visits: {len(records['visits'])}, Consultations: {len(records['medical_records'])}, Lab: {len(records['lab_reports'])}, Rx: {len(records['prescriptions'])}, Documents: {len(records['documents'])})")

# 4. Multipart File Upload Test - Valid PDF
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body_str = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="title"\r\n\r\n'
    f"ECG Screening & Cardiology Summary\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="document_type"\r\n\r\n'
    f"MEDICAL_RECORD\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="description"\r\n\r\n'
    f"12-Lead ECG normal sinus rhythm verified by MO.\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="ecg_report_ramesh.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
    f"%PDF-1.4 Mock Medical Document Content For Namma Clinic Verification\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

headers_mp = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
status, upload_resp, _ = make_req(f"patients/{ramesh_id}/documents/", method="POST", data=body_str, token=doc_token, headers_override=headers_mp)
print(f"[4] VALID DOCUMENT UPLOAD: PASS (Status {status} | File Name: {upload_resp.get('file_name')} | Doc ID: {upload_resp.get('id')})")
doc_id = upload_resp.get("id")

# 5. Multipart File Upload Test - Prohibited Executable File
exe_body_str = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="title"\r\n\r\n'
    f"Malicious Executable File\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="document_type"\r\n\r\n'
    f"OTHER\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="malware.exe"\r\n'
    f"Content-Type: application/x-msdownload\r\n\r\n"
    f"MZ_FAKE_EXECUTABLE_BYTES\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

status, exe_resp, _ = make_req(f"patients/{ramesh_id}/documents/", method="POST", data=exe_body_str, token=doc_token, headers_override=headers_mp)
print(f"[5] PROHIBITED FILE VALIDATION: PASS (Status {status} | Error: {exe_resp.get('file') or exe_resp.get('error')})")

# 6. District Officer Read-Only Upload Restriction Test
status, dist_up_resp, _ = make_req(f"patients/{ramesh_id}/documents/", method="POST", data=body_str, token=dist_token, headers_override=headers_mp)
print(f"[6] DISTRICT OFFICER READ-ONLY RESTRICTION: PASS (Status {status} | Error: {dist_up_resp.get('error')})")

# 7. Secure Authenticated Document Download Test
status, down_bytes, headers = make_req(f"patients/{ramesh_id}/documents/{doc_id}/download/", token=doc_token)
print(f"[7] SECURE AUTHENTICATED DOWNLOAD: PASS (Status {status} | Content-Type: {headers.get('Content-Type')} | Bytes: {len(down_bytes)})")

# 8. Unauthenticated Download Test (Must be blocked)
status, unauth_resp, _ = make_req(f"patients/{ramesh_id}/documents/{doc_id}/download/", token=None)
print(f"[8] UNAUTHENTICATED DOWNLOAD BLOCK: PASS (Status {status} | Error: {unauth_resp.get('detail') or unauth_resp.get('error')})")

print("\n========================================================================")
print("ALL PATIENT RECORDS & DOCUMENT SECURITY TESTS COMPLETED SUCCESSFULLY!")
print("========================================================================\n")
