import os
import sys
import django
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from playwright.sync_api import sync_playwright

def verify_clean_slate_ui():
    print("=== Namma Clinic Clean Slate UI Verification ===")
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'audits', 'screenshots_clean_slate'))
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # Login as admin
        print("Logging in to http://localhost:3000/login...")
        page.goto('http://localhost:3000/login', wait_until='networkidle')
        if page.locator('input#username, input[type="text"]').count() > 0:
            page.fill('input#username, input[type="text"]', 'admin')
            page.fill('input#password, input[type="password"]', 'admin123')
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

        # 1. Front Desk Dashboard
        print("Checking /dashboard/front-desk...")
        page.goto('http://localhost:3000/dashboard/front-desk', wait_until='networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(screenshots_dir, '01_front_desk_empty.png'))
        print("Captured 01_front_desk_empty.png")

        # 2. Patients Directory
        print("Checking /patients...")
        page.goto('http://localhost:3000/patients', wait_until='networkidle')
        page.wait_for_timeout(1500)
        pat_rows = page.locator('table tbody tr').count()
        print(f"Patients directory rows: {pat_rows} (Expected 0 or 'No patients')")
        page.screenshot(path=os.path.join(screenshots_dir, '02_patients_directory_empty.png'))
        print("Captured 02_patients_directory_empty.png")

        # 3. OPD Queue
        print("Checking /queue...")
        page.goto('http://localhost:3000/queue', wait_until='networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(screenshots_dir, '03_opd_queue_empty.png'))
        print("Captured 03_opd_queue_empty.png")

        # 4. Triage
        print("Checking /triage...")
        page.goto('http://localhost:3000/triage', wait_until='networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(screenshots_dir, '04_triage_empty.png'))
        print("Captured 04_triage_empty.png")

        # 5. NCD Registry
        print("Checking /ncd...")
        page.goto('http://localhost:3000/ncd', wait_until='networkidle')
        page.wait_for_timeout(1500)
        ncd_rows = page.locator('table tbody tr').count()
        print(f"NCD registry rows: {ncd_rows} (Expected 0)")
        page.screenshot(path=os.path.join(screenshots_dir, '05_ncd_registry_empty.png'))
        print("Captured 05_ncd_registry_empty.png")

        # 6. Follow-up Tracker
        print("Checking /followups...")
        page.goto('http://localhost:3000/followups', wait_until='networkidle')
        page.wait_for_timeout(1500)
        fu_rows = page.locator('table tbody tr').count()
        print(f"Follow-ups tracker rows: {fu_rows} (Expected 0)")
        page.screenshot(path=os.path.join(screenshots_dir, '06_followups_tracker_empty.png'))
        print("Captured 06_followups_tracker_empty.png")

        browser.close()

    print("\n=== CLEAN SLATE UI VERIFICATION COMPLETE ===")

if __name__ == '__main__':
    verify_clean_slate_ui()
