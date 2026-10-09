import json
import urllib.request
import urllib.error

# Authenticate
auth_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/auth/token/",
    data=json.dumps({"username": "e2e_compounder_user", "password": "Password123!"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(auth_req) as res:
    token = json.loads(res.read().decode())["access"]

# Test POST to /api/v1/patients/
payload = {
    "name": "Test Citizen 123",
    "age": 32,
    "gender": "FEMALE",
    "mobile": "9911199111",
    "address": "Indiranagar",
    "ABHA_ID_DEMO": "",
    "vulnerability_information": "Slum Resident / Low Income Group",
    "registered_at_facility": 1
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/patients/",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)

try:
    with urllib.request.urlopen(req) as res:
        print("Success:", res.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}:", e.read().decode())
