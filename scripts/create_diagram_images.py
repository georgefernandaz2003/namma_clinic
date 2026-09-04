import os
from PIL import Image, ImageDraw, ImageFont

# Ultra High-DPI Dimensions (1800 x 1200) for crystal clear PDF rendering
WIDTH = 1800
HEIGHT = 1200

# Color Palette (High-Contrast Professional Healthcare Theme)
COLOR_BG = (255, 255, 255)
COLOR_HEADER_BG = (6, 95, 70) # Deep Emerald
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_MAIN = (15, 23, 42) # Slate 900
COLOR_TEXT_MUTED = (51, 65, 85) # Slate 700
COLOR_BORDER = (148, 163, 184) # Slate 400

# Accent Colors
COLOR_TEAL_BG = (236, 253, 245)
COLOR_TEAL_BORDER = (16, 185, 129)
COLOR_TEAL_TEXT = (4, 120, 87)

COLOR_BLUE_BG = (240, 249, 255)
COLOR_BLUE_BORDER = (14, 165, 233)
COLOR_BLUE_TEXT = (3, 105, 161)

COLOR_AMBER_BG = (254, 243, 199)
COLOR_AMBER_BORDER = (245, 158, 11)
COLOR_AMBER_TEXT = (180, 83, 9)

COLOR_PURPLE_BG = (245, 243, 255)
COLOR_PURPLE_BORDER = (168, 85, 247)
COLOR_PURPLE_TEXT = (109, 40, 217)

COLOR_ROSE_BG = (255, 241, 242)
COLOR_ROSE_BORDER = (244, 63, 94)
COLOR_ROSE_TEXT = (190, 18, 60)

def get_font(size=16, bold=False):
    font_names = ["arialbd.ttf" if bold else "arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, box, bg_color, border_color, radius=10, width=2):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=bg_color, outline=border_color, width=int(width))

def draw_arrow_flow(draw, start, end, label="", color=(51, 65, 85), width=4, arrow_size=14):
    x1, y1 = start
    x2, y2 = end
    draw.line([x1, y1, x2, y2], fill=color, width=int(width))
    
    if x1 == x2: # Vertical
        if y2 > y1:
            draw.polygon([(x2 - arrow_size, y2 - arrow_size), (x2 + arrow_size, y2 - arrow_size), (x2, y2)], fill=color)
        else:
            draw.polygon([(x2 - arrow_size, y2 + arrow_size), (x2 + arrow_size, y2 + arrow_size), (x2, y2)], fill=color)
    elif y1 == y2: # Horizontal
        if x2 > x1:
            draw.polygon([(x2 - arrow_size, y2 - arrow_size), (x2 - arrow_size, y2 + arrow_size), (x2, y2)], fill=color)
        else:
            draw.polygon([(x2 + arrow_size, y2 - arrow_size), (x2 + arrow_size, y2 + arrow_size), (x2, y2)], fill=color)

    if label:
        font_lbl = get_font(12, bold=True)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        draw_rounded_rect(draw, (mx - 110, my - 14, mx + 110, my + 14), (255, 255, 255), color, radius=6, width=2)
        draw.text((mx - 95, my - 9), label, fill=color, font=font_lbl)


def create_architecture_diagram(output_path):
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    draw_rounded_rect(draw, (25, 25, WIDTH - 25, 110), COLOR_HEADER_BG, COLOR_HEADER_BG, radius=10)
    draw.text((50, 40), "NAMMA CLINIC — 4-TIER SYSTEM ARCHITECTURE & ACCESS BOUNDARIES", fill=COLOR_TEXT_WHITE, font=get_font(28, bold=True))
    draw.text((50, 78), "High-Availability Platform Architecture: Role Portals, Core Application Services, Data Security Isolation & Database Layer", fill=(209, 250, 229), font=get_font(15, bold=False))

    # --- LAYER 1: PRESENTATION & USER ACCESS PORTALS ---
    y1 = 135
    draw_rounded_rect(draw, (40, y1, WIDTH - 40, y1 + 200), (248, 250, 252), COLOR_BORDER, radius=12, width=2)
    draw_rounded_rect(draw, (60, y1 + 14, 520, y1 + 46), COLOR_HEADER_BG, COLOR_HEADER_BG, radius=6)
    draw.text((75, y1 + 20), "LAYER 1: USER ACCESS ROLE PORTALS & WORKSTATIONS", fill=COLOR_TEXT_WHITE, font=get_font(14, bold=True))

    portals = [
        ("Nurse & Reception Desk", "• Registration & ABHA Linkage\n• OPD Priority Token Engine\n• Nurse Triage Vitals Capture", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("Doctor EMR Workstation", "• ICD-10 Diagnoses Entry\n• Digital Rx Prescribing\n• 1-Click Specialist Referral", COLOR_BLUE_BG, COLOR_BLUE_BORDER, COLOR_BLUE_TEXT),
        ("Lab & FEFO Pharmacy", "• 14 Essential Tests Workflow\n• FEFO Drug Batch Dispense\n• Inventory Stock Ledgers", COLOR_PURPLE_BG, COLOR_PURPLE_BORDER, COLOR_PURPLE_TEXT),
        ("Command Analytics Center", "• District Analytics Console\n• Ward Outbreak Surveillance\n• Facility Infra Work Orders", COLOR_AMBER_BG, COLOR_AMBER_BORDER, COLOR_AMBER_TEXT)
    ]

    pw = (WIDTH - 170) // 4
    for idx, (p_t, p_d, bg_c, brd_c, txt_c) in enumerate(portals):
        bx = 60 + idx * (pw + 16)
        by = y1 + 60
        draw_rounded_rect(draw, (bx, by, bx + pw, by + 125), bg_c, brd_c, radius=10, width=2)
        draw.text((bx + 16, by + 14), p_t, fill=txt_c, font=get_font(15, bold=True))
        for l_i, l_t in enumerate(p_d.split('\n')):
            draw.text((bx + 16, by + 44 + l_i * 24), l_t, fill=COLOR_TEXT_MAIN, font=get_font(13, bold=False))

    # Connector Arrow Down to Layer 2
    draw_arrow_flow(draw, (WIDTH // 2, y1 + 200), (WIDTH // 2, y1 + 245), label="REST API (SimpleJWT Token Auth)", color=(4, 120, 87), width=4)

    # --- LAYER 2: CORE APPLICATION & BUSINESS LOGIC ENGINES ---
    y2 = 380
    draw_rounded_rect(draw, (40, y2, WIDTH - 40, y2 + 200), COLOR_TEAL_BG, COLOR_TEAL_BORDER, radius=12, width=2)
    draw_rounded_rect(draw, (60, y2 + 14, 550, y2 + 46), COLOR_TEAL_TEXT, COLOR_TEAL_TEXT, radius=6)
    draw.text((75, y2 + 20), "LAYER 2: FUNCTIONAL SERVICES & CORE WORKFLOW ENGINES", fill=COLOR_TEXT_WHITE, font=get_font(14, bold=True))

    services = [
        "Patient Master & ABHA Gateway", "OPD Priority Token Queue", "Nurse Vitals Risk Stratifier",
        "Doctor EMR & Digital Prescribing", "14 Diagnostic Tests Engine", "FEFO Pharmacy Stock Ledger",
        "Two-Way Hospital Referrals", "Oxygen, Beds & Infra Tracker", "IDSP Epidemic Outbreak Alerts"
    ]

    sw = (WIDTH - 180) // 3
    for idx, s_name in enumerate(services):
        r = idx // 3
        c = idx % 3
        bx = 60 + c * (sw + 20)
        by = y2 + 60 + r * 44
        draw_rounded_rect(draw, (bx, by, bx + sw, by + 38), COLOR_BG, COLOR_TEAL_BORDER, radius=8, width=2)
        draw.text((bx + 16, by + 9), f"⚙  {s_name}", fill=COLOR_TEXT_MAIN, font=get_font(14, bold=True))

    # Connector Arrow Down to Layer 3
    draw_arrow_flow(draw, (WIDTH // 2, y2 + 200), (WIDTH // 2, y2 + 245), label="RBAC & Sub-Facility Privacy Rules", color=(180, 83, 9), width=4)

    # --- LAYER 3: SECURITY, RBAC & SUB-FACILITY DATA BOUNDARIES ---
    y3 = 625
    draw_rounded_rect(draw, (40, y3, WIDTH - 40, y3 + 290), COLOR_AMBER_BG, COLOR_AMBER_BORDER, radius=12, width=2)
    draw_rounded_rect(draw, (60, y3 + 14, 620, y3 + 46), COLOR_AMBER_TEXT, COLOR_AMBER_TEXT, radius=6)
    draw.text((75, y3 + 20), "LAYER 3: SECURITY BOUNDARIES & ROLE-BASED ACCESS CONTROL (RBAC)", fill=COLOR_TEXT_WHITE, font=get_font(14, bold=True))

    # Left Box: 8 Roles Matrix
    bx_rbac = 60
    by_rbac = y3 + 60
    bw_rbac = (WIDTH - 170) // 2
    draw_rounded_rect(draw, (bx_rbac, by_rbac, bx_rbac + bw_rbac, by_rbac + 215), COLOR_BG, COLOR_AMBER_BORDER, radius=10, width=2)
    draw.text((bx_rbac + 20, by_rbac + 16), "8 Specialized Operational Roles Matrix", fill=COLOR_AMBER_TEXT, font=get_font(16, bold=True))

    rbac_items = (
        "• Medical Officer: Full clinical EMR, Rx prescribing, lab orders & hospital referrals\n"
        "• Staff Nurse: Patient registration, OPD queue tokens, vitals triage & bed allocation\n"
        "• Pharmacist: FEFO drug inventory dispensing, stock ledgers & low-stock alerts\n"
        "• Lab Technician: Test specimen collection, lab report entry & result verification\n"
        "• District Health Officer: Command analytics, epidemic alerts & administrative oversight"
    )
    for l_i, l_t in enumerate(rbac_items.split('\n')):
        draw.text((bx_rbac + 20, by_rbac + 48 + l_i * 32), l_t, fill=COLOR_TEXT_MAIN, font=get_font(13, bold=False))

    # Right Box: Sub-Facility Hierarchy Privacy Rules
    bx_hier = bx_rbac + bw_rbac + 30
    draw_rounded_rect(draw, (bx_hier, by_rbac, bx_hier + bw_rbac, by_rbac + 215), COLOR_BG, COLOR_AMBER_BORDER, radius=10, width=2)
    draw.text((bx_hier + 20, by_rbac + 16), "Sub-Facility Hierarchy Data Isolation Rules", fill=COLOR_AMBER_TEXT, font=get_font(16, bold=True))

    hier_items = (
        "• Sub-Facility Isolation Rule (Child Namma Clinics):\n"
        "  Clinic staff can ONLY view & manage patient data created in their own clinic.\n"
        "  Child clinics CANNOT access parent hospital records or other clinic data.\n\n"
        "• Parent Hospital Specialist Oversight (Referral Hubs):\n"
        "  Parent referral hospitals view incoming clinic referrals & aggregated statistics."
    )
    for l_i, l_t in enumerate(hier_items.split('\n')):
        draw.text((bx_hier + 20, by_rbac + 48 + l_i * 30), l_t, fill=COLOR_TEXT_MAIN, font=get_font(13, bold=False))

    # Connector Arrow Down to Layer 4
    draw_arrow_flow(draw, (WIDTH // 2, y3 + 290), (WIDTH // 2, y3 + 335), label="ACID Transactions & Encryption", color=(3, 105, 161), width=4)

    # --- LAYER 4: DATABASE, STORAGE & NATIONAL ECOSYSTEM STANDARDS ---
    y4 = 960
    draw_rounded_rect(draw, (40, y4, WIDTH - 40, y4 + 200), (248, 250, 252), COLOR_BORDER, radius=12, width=2)
    draw_rounded_rect(draw, (60, y4 + 14, 630, y4 + 46), COLOR_TEXT_MAIN, COLOR_TEXT_MAIN, radius=6)
    draw.text((75, y4 + 20), "LAYER 4: DATABASE, STORAGE & NATIONAL HEALTH STANDARDS", fill=COLOR_TEXT_WHITE, font=get_font(14, bold=True))

    db_items = [
        ("Relational SQLite Storage", "Centralized SQLite Health DB\nACID Compliant Transactions & Indexes", COLOR_BLUE_BG, COLOR_BLUE_BORDER, COLOR_BLUE_TEXT),
        ("Offline Queue & Sync Engine", "Local Storage Queue & Cache\nAutomatic Re-connection Sync Engine", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("National Ecosystem Standards", "ABDM Health Account Gateway\ne-Aushadhi & RCH Standards Sync", COLOR_PURPLE_BG, COLOR_PURPLE_BORDER, COLOR_PURPLE_TEXT)
    ]

    db_w = (WIDTH - 170) // 3
    for idx, (db_t, db_d, bg_c, brd_c, txt_c) in enumerate(db_items):
        bx = 60 + idx * (db_w + 25)
        by = y4 + 60
        draw_rounded_rect(draw, (bx, by, bx + db_w, by + 125), bg_c, brd_c, radius=10, width=2)
        draw.text((bx + 20, by + 16), db_t, fill=txt_c, font=get_font(16, bold=True))
        for l_i, l_t in enumerate(db_d.split('\n')):
            draw.text((bx + 20, by + 48 + l_i * 28), l_t, fill=COLOR_TEXT_MAIN, font=get_font(13.5, bold=False))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"High-res Architecture Diagram saved to: {output_path}")


def create_control_flow_diagram(output_path):
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    draw_rounded_rect(draw, (25, 25, WIDTH - 25, 110), COLOR_HEADER_BG, COLOR_HEADER_BG, radius=10)
    draw.text((50, 40), "NAMMA CLINIC — OPERATIONAL CONTROL FLOW & PATIENT JOURNEY", fill=COLOR_TEXT_WHITE, font=get_font(28, bold=True))
    draw.text((50, 78), "End-to-End Clinical & Administrative Workflow Handoffs from Reception Registration to Follow-up Care", fill=(209, 250, 229), font=get_font(15, bold=False))

    # Flow Steps List (6 Step Flowchart Cards)
    steps = [
        ("STEP 1", "Patient Arrival & Registration", "• Registration Clerk / Nurse Desk\n• Demographic Entry & Search\n• ABHA Digital Health ID Linkage\n• Automated Duplicate Alert Check\n• Issue Digital Patient Card", COLOR_BLUE_BG, COLOR_BLUE_BORDER, COLOR_BLUE_TEXT),
        ("STEP 2", "Smart OPD Queueing", "• Priority Token Assignment\n• Categorize: Emergency / Elderly / Normal\n• Real-Time Queue Console Update\n• Route Patient to Nurse Triage Desk\n• Token Display Board Update", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("STEP 3", "Nurse Vitals & Triage", "• Staff Nurse Vitals Recording\n• BP, Pulse, SpO2, Temp, Glucose\n• Auto-Calculate BMI & Risk Flags\n• Flag High BP (>140/90) & Diabetes\n• Prioritize Critical Patients", COLOR_AMBER_BG, COLOR_AMBER_BORDER, COLOR_AMBER_TEXT),
        ("STEP 4", "Doctor EMR Consultation", "• Medical Officer Workstation\n• Review Complaints & History\n• ICD-10 Diagnosis Selection\n• Electronic Prescribing (Rx)\n• Order Lab Tests & 1-Click Referral", COLOR_PURPLE_BG, COLOR_PURPLE_BORDER, COLOR_PURPLE_TEXT),
        ("STEP 5", "Diagnostics & Pharmacy", "• Lab Tech: Sample & Test Processing\n• Pharmacist: FEFO Batch Dispense\n• Auto-Deduct Inventory Ledgers\n• Low-Stock Alert Triggering\n• Printed Prescriptions & Reports", COLOR_TEAL_BG, COLOR_TEAL_BORDER, COLOR_TEAL_TEXT),
        ("STEP 6", "Referral & Follow-up", "• 2-Way Referral to Specialist Hospital\n• Hospital Specialist Treatment Advice\n• Schedule Review Visit in Tracker\n• Field Worker Community Sync\n• Post-Care Continuity Tracking", COLOR_BLUE_BG, COLOR_BLUE_BORDER, COLOR_BLUE_TEXT)
    ]

    card_w = (WIDTH - 150) // 3
    card_h = 440

    for idx, (s_num, s_title, s_body, bg_c, brd_c, txt_c) in enumerate(steps):
        r = idx // 3
        c = idx % 3

        bx = 50 + c * (card_w + 25)
        by = 150 + r * (card_h + 70)

        # Draw Step Card
        draw_rounded_rect(draw, (bx, by, bx + card_w, by + card_h), bg_c, brd_c, radius=12, width=2)

        # Step Badge
        draw_rounded_rect(draw, (bx + 20, by + 20, bx + 130, by + 56), txt_c, txt_c, radius=8)
        draw.text((bx + 32, by + 25), s_num, fill=COLOR_TEXT_WHITE, font=get_font(16, bold=True))

        # Title
        draw.text((bx + 20, by + 70), s_title, fill=txt_c, font=get_font(17, bold=True))
        draw.line([bx + 20, by + 105, bx + card_w - 20, by + 105], fill=brd_c, width=2)

        # Body List
        lines = s_body.split('\n')
        for l_i, l_t in enumerate(lines):
            draw.text((bx + 20, by + 120 + l_i * 35), l_t, fill=COLOR_TEXT_MAIN, font=get_font(14, bold=False))

        # Horizontal Directional Flow Arrows
        if c < 2 and idx < 5:
            ax_start = bx + card_w
            ax_end = ax_start + 25
            ay = by + card_h // 2
            draw_arrow_flow(draw, (ax_start, ay), (ax_end, ay), color=(51, 65, 85), width=4, arrow_size=12)

    # Downward Flow Arrow from Row 1 (Step 3) to Row 2 (Step 4)
    ax3 = 50 + 2 * (card_w + 25) + card_w // 2
    ay1 = 150 + card_h
    ay2 = 150 + card_h + 70
    draw_arrow_flow(draw, (ax3, ay1), (ax3, ay2), label="Doctor Consultation Handoff", color=(4, 120, 87), width=4, arrow_size=12)

    # Bottom Operational Assurance Banner
    y_b = 1100
    draw_rounded_rect(draw, (25, y_b, WIDTH - 25, y_b + 75), (248, 250, 252), COLOR_BORDER, radius=10, width=2)
    draw.text((45, y_b + 14), "Operational Quality Assurance:", fill=COLOR_TEXT_MAIN, font=get_font(15, bold=True))
    draw.text((310, y_b + 14), "Enforces 100% Digital Data Continuity, FEFO Inventory Protection, and Real-Time Care Tracking.", fill=COLOR_TEAL_TEXT, font=get_font(14, bold=False))
    draw.text((45, y_b + 44), "Multi-Role Collaboration:", fill=COLOR_TEXT_MAIN, font=get_font(15, bold=True))
    draw.text((310, y_b + 44), "Seamless digital handoffs between Reception, Staff Nurses, Doctors, Lab Techs, Pharmacists & Specialists.", fill=COLOR_BLUE_TEXT, font=get_font(14, bold=False))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"High-res Control Flow Diagram saved to: {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    create_architecture_diagram(os.path.join(docs_dir, "system_architecture_diagram.png"))
    create_control_flow_diagram(os.path.join(docs_dir, "control_flow_diagram.png"))
