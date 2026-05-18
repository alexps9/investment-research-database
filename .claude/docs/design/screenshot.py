from playwright.sync_api import sync_playwright
import sys
from pathlib import Path

def screenshot(html_file: str, output: str = None, width: int = 1600, height: int = 900):
    html_path = Path(html_file).resolve()
    if not html_path.exists():
        print(f"File not found: {html_path}")
        sys.exit(1)

    if output is None:
        output = str(html_path.with_suffix('.png'))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})
        page.goto(f'file://{html_path}', timeout=120000, wait_until='load')
        page.wait_for_timeout(3000)
        page.screenshot(path=output, full_page=True, timeout=60000)
        browser.close()

    print(f"Screenshot saved: {output}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'school-track.html'
    screenshot(target)
