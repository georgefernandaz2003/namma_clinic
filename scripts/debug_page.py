from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=True)
    page = b.new_page()
    page.on('console', lambda msg: print('CONSOLE:', msg.text))
    page.goto('http://localhost:3000/login')
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_url('**/dashboard/admin')
    page.goto('http://localhost:3000/admin/analytics')
    page.wait_for_timeout(3000)
    page.screenshot(path=r'C:\Users\admin\.gemini\antigravity-ide\brain\a6c795c2-dc94-4409-bfa1-ef40002933eb\analytics_debug.png')
    body_text = page.inner_text('body')
    print('FULL BODY TEXT:\n', body_text)
    b.close()
