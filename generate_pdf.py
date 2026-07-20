import sys
import asyncio
import os

sys.stdout.reconfigure(encoding='utf-8')

async def convert_html_to_pdf():
    from playwright.async_api import async_playwright
    
    html_path = os.path.abspath("pdf_template.html").replace("\\", "/")
    pdf_path = os.path.abspath("BioPulse_AI_Executive_Blueprint.pdf")
    
    print(f"📄 Rendering {html_path} to PDF...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file:///{html_path}")
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
        )
        await browser.close()
        
    print(f"✅ Successfully generated PDF: [file:///{pdf_path.replace('\\', '/')}]", flush=True)

if __name__ == "__main__":
    asyncio.run(convert_html_to_pdf())
