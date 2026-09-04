import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 600

COLOR_BG = (248, 250, 252) # Slate 50
COLOR_HEADER_BG = (255, 255, 255)
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_MUTED = (71, 85, 105)
COLOR_BORDER = (203, 213, 225)

COLOR_TEAL_BG = (236, 253, 245)
COLOR_TEAL_BORDER = (167, 243, 208)
COLOR_TEAL_TEXT = (4, 120, 87)

COLOR_BLUE_BG = (240, 249, 255)
COLOR_BLUE_BORDER = (186, 230, 253)
COLOR_BLUE_TEXT = (3, 105, 161)

COLOR_AMBER_BG = (254, 243, 199)
COLOR_AMBER_BORDER = (252, 211, 77)
COLOR_AMBER_TEXT = (180, 83, 9)

COLOR_ROSE_BG = (255, 241, 242)
COLOR_ROSE_BORDER = (254, 205, 211)
COLOR_ROSE_TEXT = (190, 18, 60)

def get_font(size=14, bold=False):
    font_names = ["arialbd.ttf" if bold else "arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, box, bg_color, border_color, radius=6, width=1):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=bg_color, outline=border_color, width=width)

def generate_infra_screenshot(output_path):
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Top Header Card
    draw_rounded_rect(draw, (20, 20, WIDTH - 20, 95), (255, 255, 255), COLOR_BORDER, radius=8)
    draw.text((40, 32), "Clinic Infrastructure & Maintenance Console", fill=COLOR_TEXT_MAIN, font=get_font(20, bold=True))
    draw.text((40, 62), "Live Utilities Status: Oxygen Cylinders & PSI, Ward Bed Capacity, Sanitation Consumables & Work Orders", fill=COLOR_TEXT_MUTED, font=get_font(12, bold=False))

    # Badge
    draw_rounded_rect(draw, (WIDTH - 180, 35, WIDTH - 40, 65), COLOR_TEAL_BG, COLOR_TEAL_BORDER, radius=15)
    draw.text((WIDTH - 165, 42), "LIVE SYSTEM ACTIVE", fill=COLOR_TEAL_TEXT, font=get_font(10, bold=True))

    # KPI Row (4 Cards)
    kpis = [
        ("OXYGEN MANIFOLD", "88% Fill (1850 PSI)", "9/12 Cylinders Active", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("WARD BED CAPACITY", "4/10 Beds Occupied", "6 Beds Available", COLOR_BLUE_BG, COLOR_BLUE_BORDER, COLOR_BLUE_TEXT),
        ("SANITATION SUPPLIES", "8 Consumables Logged", "1 Item Low Stock (Sanitizer)", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("MAINTENANCE WORK ORDERS", "1 Active Work Order", "Solar UPS Inverter In-Progress", COLOR_AMBER_BG, COLOR_AMBER_BORDER, COLOR_AMBER_TEXT)
    ]

    kw = (WIDTH - 100) // 4
    for idx, (k_title, k_val, k_sub, bg_c, brd_c, txt_c) in enumerate(kpis):
        bx = 20 + idx * (kw + 20)
        by = 115
        draw_rounded_rect(draw, (bx, by, bx + kw, by + 85), (255, 255, 255), COLOR_BORDER, radius=8)
        draw.text((bx + 12, by + 12), k_title, fill=COLOR_TEXT_MUTED, font=get_font(10, bold=True))
        draw.text((bx + 12, by + 32), k_val, fill=txt_c, font=get_font(14, bold=True))
        draw.text((bx + 12, by + 60), k_sub, fill=COLOR_TEXT_MUTED, font=get_font(10, bold=False))

    # Tabs Bar
    tabs = ["Oxygen Supply Station", "Ward Beds & Capacity", "Sanitation & Floor Consumables", "Electrical & Maintenance Tickets"]
    tw = (WIDTH - 40) // 4
    for idx, tab in enumerate(tabs):
        bx = 20 + idx * tw
        by = 220
        is_active = (idx == 0)
        bg = COLOR_TEAL_BG if is_active else (255, 255, 255)
        brd = COLOR_TEAL_BORDER if is_active else COLOR_BORDER
        txt = COLOR_TEAL_TEXT if is_active else COLOR_TEXT_MUTED
        draw_rounded_rect(draw, (bx, by, bx + tw - 5, by + 40), bg, brd, radius=4)
        draw.text((bx + 15, by + 12), tab, fill=txt, font=get_font(11, bold=True))

    # Main Details Card (Oxygen + Beds + Consumables Table Simulation)
    draw_rounded_rect(draw, (20, 275, WIDTH - 20, HEIGHT - 20), (255, 255, 255), COLOR_BORDER, radius=8)

    # Sub-box 1: Oxygen Gauge
    draw_rounded_rect(draw, (40, 295, 380, 560), COLOR_TEAL_BG, COLOR_TEAL_BORDER, radius=8)
    draw.text((55, 310), "Manifold Pressure Fill Gauge", fill=COLOR_TEAL_TEXT, font=get_font(12, bold=True))
    draw.text((55, 338), "88%", fill=COLOR_TEAL_TEXT, font=get_font(28, bold=True))
    draw_rounded_rect(draw, (55, 380, 365, 395), (209, 250, 229), COLOR_TEAL_BORDER, radius=6)
    draw_rounded_rect(draw, (55, 380, 325, 395), COLOR_TEAL_TEXT, COLOR_TEAL_TEXT, radius=6)
    draw.text((55, 410), "Current Pressure: 1850 PSI", fill=COLOR_TEAL_TEXT, font=get_font(11, bold=True))
    draw.text((55, 435), "Total Cylinders: 12 B-Type Cylinders", fill=COLOR_TEXT_MAIN, font=get_font(11, bold=False))
    draw.text((55, 460), "Active Cylinders: 9 Cylinders Online", fill=COLOR_TEAL_TEXT, font=get_font(11, bold=True))
    draw.text((55, 485), "Empty / Standby: 3 Cylinders", fill=COLOR_TEXT_MUTED, font=get_font(11, bold=False))

    # Sub-box 2: Ward Beds Table Simulation
    draw_rounded_rect(draw, (400, 295, WIDTH - 40, 560), (255, 255, 255), COLOR_BORDER, radius=8)
    draw.text((415, 310), "Ward Bed Allocation & Patient Admission Status", fill=COLOR_TEXT_MAIN, font=get_font(12, bold=True))

    headers = ["Bed Number", "Bed Category", "Patient Name", "Attending Doctor", "Status"]
    hx_positions = [415, 520, 670, 840, 1020]
    draw_rounded_rect(draw, (410, 335, WIDTH - 55, 365), COLOR_BG, COLOR_BORDER, radius=4)
    for h_txt, hx in zip(headers, hx_positions):
        draw.text((hx, 343), h_txt, fill=COLOR_TEXT_MUTED, font=get_font(10, bold=True))

    rows = [
        ("BED-OBS-01", "General OPD Observation", "Ramesh Kumar (45/M)", "Dr. Rajesh Kumar", "OCCUPIED", COLOR_ROSE_BG, COLOR_ROSE_TEXT),
        ("BED-OXY-01", "Oxygen Supported Bed", "Suresh Gowda (58/M)", "Dr. Rajesh Kumar", "OCCUPIED", COLOR_ROSE_BG, COLOR_ROSE_TEXT),
        ("BED-OBS-02", "General OPD Observation", "Unassigned", "—", "SANITIZING", COLOR_AMBER_BG, COLOR_AMBER_TEXT),
        ("BED-OBS-03", "General OPD Observation", "Unassigned", "—", "AVAILABLE", COLOR_TEAL_BG, COLOR_TEAL_TEXT),
        ("BED-EMG-01", "Emergency Resuscitation", "Anita M (32/F)", "Dr. Rajesh Kumar", "OCCUPIED", COLOR_ROSE_BG, COLOR_ROSE_TEXT)
    ]

    for idx, (b_num, b_cat, b_pat, b_doc, b_stat, bg_s, txt_s) in enumerate(rows):
        ry = 375 + idx * 36
        draw.line([410, ry + 30, WIDTH - 55, ry + 30], fill=COLOR_BORDER, width=1)
        draw.text((hx_positions[0], ry + 6), b_num, fill=COLOR_BLUE_TEXT, font=get_font(11, bold=True))
        draw.text((hx_positions[1], ry + 6), b_cat, fill=COLOR_TEXT_MAIN, font=get_font(10, bold=False))
        draw.text((hx_positions[2], ry + 6), b_pat, fill=COLOR_TEXT_MAIN, font=get_font(10, bold=True))
        draw.text((hx_positions[3], ry + 6), b_doc, fill=COLOR_TEXT_MUTED, font=get_font(10, bold=False))
        
        # Badge
        draw_rounded_rect(draw, (hx_positions[4], ry + 2, hx_positions[4] + 90, ry + 22), bg_s, bg_s, radius=4)
        draw.text((hx_positions[4] + 8, ry + 6), b_stat, fill=txt_s, font=get_font(9, bold=True))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Infra screenshot image saved to: {output_path}")

if __name__ == "__main__":
    art_dir = r"C:\Users\admin\.gemini\antigravity-ide\brain\9b134108-ff26-45dd-8f0e-3970908f6c96"
    generate_infra_screenshot(os.path.join(art_dir, "infra_page_1788426750000.png"))
