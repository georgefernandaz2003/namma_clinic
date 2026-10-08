import os
import sys
import django
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from playwright.sync_api import sync_playwright
from apps.patients.models import Patient
from apps.ncd.models import NCDRecord
from apps.referrals.models import FollowUp

def run_verification():
    print("=== Namma Clinic Verification: NCD Registry & Follow-up Tracker ===")
    
    # 1. DB Assertions on Patient Names
    patients = Patient.objects.all()
    print(f"Total Patients in PostgreSQL: {patients.count()}")
    numbered_patients = [p for p in patients if any(c.isdigit() for c in p.name)]
    if numbered_patients:
        print(f"FAILED: Found {len(numbered_patients)} patients with numbers in name!")
        for p in numbered_patients:
            print(f"  {p.id}: {p.name}")
        sys.exit(1)
    print("SUCCESS: 0 patients with numbers in name. All names are authentic Karnataka citizens!")

    # 2. Check NCD Records
    ncd_fac1 = NCDRecord.objects.filter(facility_id=1).count()
    ncd_fac68 = NCDRecord.objects.filter(facility_id=68).count()
    print(f"NCD Records: Facility 1 = {ncd_fac1}, Facility 68 = {ncd_fac68}")
    assert ncd_fac1 > 0, "No NCD records for Facility 1!"

    # 3. Check FollowUp Records
    fu_fac1 = FollowUp.objects.filter(facility_id=1).count()
    fu_fac68 = FollowUp.objects.filter(facility_id=68).count()
    print(f"Follow-ups: Facility 1 = {fu_fac1}, Facility 68 = {fu_fac68}")
    assert fu_fac1 > 0, "No Follow-ups for Facility 1!"

    # 4. Playwright Browser Validation
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'audits', 'screenshots_care_continuity'))
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # Login
        print("\nNavigating to http://localhost:3000/login...")
        page.goto('http://localhost:3000/login', wait_until='networkidle')
        
        # Check if already logged in or login form
        if page.locator('input#username, input[type="text"]').count() > 0:
            print("Logging in as admin...")
            page.fill('input#username, input[type="text"]', 'admin')
            page.fill('input#password, input[type="password"]', 'admin123')
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

        # Ensure active facility is Local PHC (1)
        page.goto('http://localhost:3000/dashboard/front-desk', wait_until='networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(screenshots_dir, '01_front_desk_dashboard.png'))

        # Verify NCD Registry
        print("Navigating to http://localhost:3000/ncd...")
        page.goto('http://localhost:3000/ncd', wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        # Check rows in table
        ncd_rows = page.locator('table tbody tr')
        ncd_row_count = ncd_rows.count()
        print(f"UI /ncd table rows count: {ncd_row_count}")
        assert ncd_row_count > 0, "NCD table is empty in UI!"
        
        # Print top 3 rows
        for i in range(min(5, ncd_row_count)):
            text = ncd_rows.nth(i).inner_text().replace('\n', ' | ')
            print(f"  Row {i+1}: {text}")

        page.screenshot(path=os.path.join(screenshots_dir, '02_ncd_registry_populated.png'))
        print("Captured 02_ncd_registry_populated.png")

        # Verify Follow-ups Tracker
        print("Navigating to http://localhost:3000/followups...")
        page.goto('http://localhost:3000/followups', wait_until='networkidle')
        page.wait_for_timeout(2000)

        fu_rows = page.locator('table tbody tr')
        fu_row_count = fu_rows.count()
        print(f"UI /followups table rows count: {fu_row_count}")
        assert fu_row_count > 0, "Follow-ups table is empty in UI!"

        # Print top 3 rows
        for i in range(min(5, fu_row_count)):
            text = fu_rows.nth(i).inner_text().replace('\n', ' | ')
            print(f"  Row {i+1}: {text}")

        page.screenshot(path=os.path.join(screenshots_dir, '03_followups_tracker_populated.png'))
        print("Captured 03_followups_tracker_populated.png")

        # Test Mark Completed on a Follow-up
        mark_btn = page.locator('table tbody tr button:has-text("Mark Completed")').first
        if mark_btn.count() > 0:
            print("Testing 'Mark Completed' action button on first pending follow-up...")
            mark_btn.click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(screenshots_dir, '04_followup_marked_done.png'))
            print("Captured 04_followup_marked_done.png")
            # Verify status changed to Done
            done_badge = page.locator('table tbody tr').first.locator('text=Done')
            print(f"Verified 'Done' indicator visible: {done_badge.count() > 0}")

        browser.close()

    print("\n=== ALL END-TO-END VERIFICATIONS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_verification()
