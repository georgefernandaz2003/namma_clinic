import os
import sys
import django
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from playwright.sync_api import sync_playwright

def verify_clinical_personas():
    print("=== Namma Clinic Role-Based Clinical Station Verification ===")
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'audits', 'screenshots_populated'))
    os.makedirs(screenshots_dir, exist_ok=True)

    personas = [
        ('e2e_nurse_user', 'Password123!', '/triage', '10_nurse_triage_active.png'),
        ('e2e_doctor_user', 'Password123!', '/consultation', '11_doctor_consultation_active.png'),
        ('e2e_lab_user', 'Password123!', '/dashboard/lab', '14_lab_dashboard_active.png'),
        ('e2e_pharmacist_user', 'Password123!', '/pharmacy', '13_pharmacy_dispensing_active.png'),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)

        for username, password, target_path, filename in personas:
            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            page = context.new_page()

            print(f"Logging in as {username} for {target_path}...")
            page.goto('http://localhost:3000/login', wait_until='networkidle')
            page.fill('input#username, input[type="text"]', username)
            page.fill('input#password, input[type="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(2500)

            print(f"Navigating to {target_path} as {username}...")
            page.goto(f"http://localhost:3000{target_path}", wait_until='networkidle')
            page.wait_for_timeout(2500)
            page.screenshot(path=os.path.join(screenshots_dir, filename))
            print(f"Captured {filename}")
            context.close()

        browser.close()
        print("=== Clinical Personas UI Verification Complete ===")

if __name__ == '__main__':
    verify_clinical_personas()
