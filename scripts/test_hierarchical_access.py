import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api"

def get_token(username, password):
    url = f"{BASE_URL}/auth/token/"
    req = urllib.request.Request(url, data=json.dumps({"username": username, "password": password}).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))["access"]

def get_facilities(token):
    url = f"{BASE_URL}/facilities/"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        return data.get("results", data)

print("========================================================================")
print("HIERARCHICAL FACILITY ACCESS CONTROL AUDIT TEST")
print("========================================================================\n")

# 1. Test Hospital User (Main Hospital Hub)
token_hospital = get_token("hospital", "hospital123")
facs_hospital = get_facilities(token_hospital)
hosp_names = [f["facility_name"] for f in facs_hospital]
print("1. MAIN HOSPITAL USER ('hospital'):")
print(f"   Accessible Facilities Count: {len(facs_hospital)}")
print("   Facilities List:")
for name in hosp_names:
    print(f"    - {name}")

# 2. Test Doctor User (Child Facility - Rural Clinic A4)
token_doctor = get_token("doctor", "doctor123")
facs_doctor = get_facilities(token_doctor)
doc_names = [f["facility_name"] for f in facs_doctor]
print("\n2. CHILD FACILITY DOCTOR ('doctor' @ Rural Clinic A4):")
print(f"   Accessible Facilities Count: {len(facs_doctor)}")
print("   Facilities List:")
for name in doc_names:
    print(f"    - {name}")

# 3. Test Admin User (Super Admin / District)
token_admin = get_token("admin", "admin123")
facs_admin = get_facilities(token_admin)
print(f"\n3. SUPER ADMIN USER ('admin'):")
print(f"   Accessible Facilities Count: {len(facs_admin)} (Full Network Access)")

print("\n========================================================================")
print("ACCESS CONTROL RULE VERIFICATION:")
has_victoria_in_doctor = any("Victoria" in n for n in doc_names)
has_rural_in_hospital = any("Rural" in n for n in hosp_names)

if not has_victoria_in_doctor and has_rural_in_hospital:
    print("SUCCESS: Hierarchical Access Control Enforced!")
    print(" - Main Hospital ('hospital') CAN see Child Facility ('Rural Clinic A4') data.")
    print(" - Child Facility ('doctor') CANNOT see Main Hospital ('Victoria Hospital') data.")
else:
    print("FAIL: Scoping rule violation detected.")
print("========================================================================")
