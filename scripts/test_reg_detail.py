import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()

    page.on('console', lambda msg: print(f"[CONSOLE] {msg.text}"))
    page.on('response', lambda res: print(f"[HTTP {res.status}] {res.url}") if '/api/' in res.url else None)

    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", "e2e_compounder_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/front-desk", timeout=10000)
    page.wait_for_load_state("networkidle")

    # Check active facility from AuthContext / localStorage
    auth_state = page.evaluate("() => localStorage.getItem('token')")
    print("Token present:", bool(auth_state))

    # Click Register New Patient
    page.click("button:has-text('Register New Patient')")
    time.sleep(1)

    page.fill("input[placeholder='e.g. Ramesh Kumar']", "Suma Devi")
    page.fill("input[placeholder='e.g. 35']", "29")
    page.select_option("select:has(option[value='FEMALE'])", "FEMALE")
    page.fill("input[placeholder='10-digit mobile number']", "9845012345")
    page.fill("input[placeholder='Ward/Street/Area']", "Ulsoor, Bengaluru")

    page.click("button[type='submit']:has-text('Register Patient')")
    time.sleep(2)

    # Check what is displayed
    errors = page.locator("[role='alert'], .text-rose-600, .bg-rose-50, .border-red-500, .border-rose-300").all_inner_texts()
    print("Errors found on screen:", errors)
    alerts = page.locator(".text-emerald-800, .bg-emerald-50").all_inner_texts()
    print("Success found on screen:", alerts)

    browser.close()
