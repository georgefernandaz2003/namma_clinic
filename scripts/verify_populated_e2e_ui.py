import os
import sys
import django
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from playwright.sync_api import sync_playwright

def verify_populated_ui():
    print("=== Namma Clinic Populated Clean Dataset UI Verification ===")
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'audits', 'screenshots_populated'))
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # 0. Front-Desk Console Verification
        print("Testing Front-Desk Console as frontdesk...")
        fd_context = browser.new_context(viewport={'width': 1440, 'height': 900})
        fd_page = fd_context.new_page()
        fd_page.goto('http://localhost:3000/login', wait_until='networkidle')
        if fd_page.locator('input#username, input[type="text"]').count() > 0:
            fd_page.fill('input#username, input[type="text"]', 'frontdesk')
            fd_page.fill('input#password, input[type="password"]', 'frontdesk123')
            fd_page.click('button[type="submit"]')
            fd_page.wait_for_timeout(2500)
        fd_page.goto('http://localhost:3000/dashboard/front-desk', wait_until='networkidle')
        fd_page.wait_for_timeout(2000)
        fd_page.screenshot(path=os.path.join(screenshots_dir, '00_front_desk_console_60_patients.png'))
        print("Captured 00_front_desk_console_60_patients.png")
        fd_context.close()

        # Login as admin
        print("Logging in to http://localhost:3000/login...")
        page.goto('http://localhost:3000/login', wait_until='networkidle')
        if page.locator('input#username, input[type="text"]').count() > 0:
            page.fill('input#username, input[type="text"]', 'admin')
            page.fill('input#password, input[type="password"]', 'admin123')
            page.click('button[type="submit"]')
            page.wait_for_timeout(2500)

        # 1. Main Dashboard
        print("Checking /dashboard...")
        page.goto('http://localhost:3000/dashboard', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '01_dashboard_populated.png'))
        print("Captured 01_dashboard_populated.png")

        # 2. Patients Directory
        print("Checking /patients...")
        page.goto('http://localhost:3000/patients', wait_until='networkidle')
        page.wait_for_timeout(2000)
        pat_rows = page.locator('table tbody tr').count()
        print(f"Patients directory rows: {pat_rows}")
        page.screenshot(path=os.path.join(screenshots_dir, '02_patients_directory_populated.png'))
        print("Captured 02_patients_directory_populated.png")

        # 3. OPD Queue
        print("Checking /queue...")
        page.goto('http://localhost:3000/queue', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '03_opd_queue_populated.png'))
        print("Captured 03_opd_queue_populated.png")

        # 4. Nurse Triage
        print("Checking /triage...")
        page.goto('http://localhost:3000/triage', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '04_triage_populated.png'))
        print("Captured 04_triage_populated.png")

        # 5. Doctor Consultation
        print("Checking /consultation...")
        page.goto('http://localhost:3000/consultation', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '05_consultation_populated.png'))
        print("Captured 05_consultation_populated.png")

        # 6. Laboratory
        print("Checking /laboratory...")
        page.goto('http://localhost:3000/laboratory', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '06_laboratory_populated.png'))
        print("Captured 06_laboratory_populated.png")

        # 7. Pharmacy
        print("Checking /pharmacy...")
        page.goto('http://localhost:3000/pharmacy', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(screenshots_dir, '07_pharmacy_populated.png'))
        print("Captured 07_pharmacy_populated.png")

        browser.close()
        print("=== Populated Clean Dataset UI Verification Complete ===")

if __name__ == '__main__':
    verify_populated_ui()
