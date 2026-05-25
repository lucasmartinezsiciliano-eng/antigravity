from playwright.sync_api import sync_playwright
from pathlib import Path

slides_dir = Path(__file__).parent
slides = [
    "01-embudo.html",
    "02-arquitectura-agentes.html",
    "03-stack-tecnico.html",
    "04-call-ia-flow.html",
    "05-pipeline-contenido.html",
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)

    for slide in slides:
        html_path = slides_dir / slide
        png_path = slides_dir / slide.replace(".html", ".png")
        page.goto(f"file:///{html_path.as_posix()}")
        page.wait_for_timeout(300)
        page.screenshot(path=str(png_path), full_page=False)
        print(f"OK: {png_path.name}")

    browser.close()
    print("\nListo. PNGs guardados en:", slides_dir)
