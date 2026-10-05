"""
Namma Clinic — Client Application Reference PDF Generator
Generates docs/client/NAMMA_CLINIC_CLIENT_REFERENCE.pdf using reportlab.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PDF = os.path.join(BASE_DIR, "docs", "client", "NAMMA_CLINIC_CLIENT_REFERENCE.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#065F46"))
            self.drawString(36, 762, "NAMMA CLINIC DIGITAL HEALTHCARE PLATFORM")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(576, 762, "Client Application Reference")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 756, 576, 756)

            # Footer
            self.line(36, 36, 576, 36)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(36, 24, "Urban Primary Healthcare Network • Application Reference")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(576, 24, page_text)
        self.restoreState()

def build_pdf():
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    PRIMARY = colors.HexColor("#065F46")
    SECONDARY = colors.HexColor("#0284C7")
    DARK_TEXT = colors.HexColor("#0F172A")
    MUTED_TEXT = colors.HexColor("#475569")
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=PRIMARY, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16,
        textColor=SECONDARY, spaceAfter=14
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=PRIMARY, spaceBefore=14, spaceAfter=6, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=DARK_TEXT, spaceBefore=10, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=DARK_TEXT, spaceBefore=3, spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style,
        leftIndent=14, firstLineIndent=-8, spaceBefore=2, spaceAfter=2
    )
    caption_style = ParagraphStyle(
        'Caption', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8, leading=11,
        textColor=MUTED_TEXT, alignment=1, spaceBefore=3, spaceAfter=10
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("NAMMA CLINIC", title_style))
    story.append(Paragraph("Digital Healthcare & Clinic Management Platform — Client Application Reference", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    meta_data = [
        [Paragraph("<b>Platform:</b> Integrated Primary Healthcare Network", body_style),
         Paragraph("<b>Target Audience:</b> Health Administrators & Clinical Staff", body_style)],
        [Paragraph("<b>Execution Environment:</b> Local Laptop / Clinic Workstation", body_style),
         Paragraph("<b>Date:</b> October 2026 (Phase 28B-0 Approved)", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # Executive Overview
    story.append(Paragraph("1. Executive Overview", h1_style))
    story.append(Paragraph(
        "The <b>Namma Clinic Platform</b> is a purpose-built, role-governed healthcare operations suite designed specifically for "
        "urban primary health centers (PHCs, Namma Clinics, and Urban Health Centers). It provides end-to-end digital lifecycle governance "
        "covering citizen intake, vital signs triage, clinician examinations, laboratory investigation processing, electronic prescribing, "
        "and pharmaceutical dispensing with First-Expired, First-Out (FEFO) stock control.", body_style
    ))
    story.append(Spacer(1, 8))

    # Architecture Overview
    story.append(Paragraph("2. High-Level Architecture", h1_style))
    story.append(Paragraph(
        "The system follows a three-tier local architecture optimized for high performance and offline resilience on local clinic workstations:", body_style
    ))
    story.append(Paragraph("• <b>Presentation Layer:</b> React 18, TypeScript, and Tailwind CSS client shell delivering dedicated workstations for each role.", bullet_style))
    story.append(Paragraph("• <b>Application & API Layer:</b> Django 4.2 LTS and Django REST Framework providing authoritative RBAC enforcement and facility-scoped querying.", bullet_style))
    story.append(Paragraph("• <b>Data Layer:</b> PostgreSQL 16 relational engine enforcing referential integrity, double-entry inventory movements, and audit logging.", bullet_style))
    story.append(Spacer(1, 10))

    # Helper function to add images cleanly
    def add_screenshot(img_rel_path, caption_text, width=500, height=260):
        full_path = os.path.join(BASE_DIR, img_rel_path)
        if os.path.exists(full_path):
            try:
                story.append(Image(full_path, width=width, height=height))
                story.append(Paragraph(caption_text, caption_style))
                story.append(Spacer(1, 6))
            except Exception as e:
                print(f"Error adding image {full_path}: {e}")
        else:
            print(f"Warning: Image path not found: {full_path}")

    # Role-Based Workstations
    story.append(Paragraph("3. Role-Based Workstations", h1_style))

    story.append(Paragraph("3.1 District Health Officer (DHO)", h2_style))
    story.append(Paragraph(
        "Responsible for regional healthcare network governance, monitoring public health disease incidence, tracking facility quality indicators, "
        "managing staff postings across clinics, and supervising ARS development fund utilization.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/dho/01_dashboard_district.png",
                   "Figure 1 — District Health Officer Dashboard — District-wide overview of patient volumes, clinic uptime, and regional health indicators.")

    story.append(Paragraph("3.2 Hospital / Clinic Administrator", h2_style))
    story.append(Paragraph(
        "Manages clinic facility operations, staff directory lifecycle (onboarding, operational role assignments, transfers, suspensions), "
        "and facility operational throughput.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/admin/01_dashboard_admin.png",
                   "Figure 2 — Hospital Administrator Dashboard — Facility operational KPIs, doctor availability, queue occupancy, and stock alerts.")

    story.append(Paragraph("3.3 Medical Officer (Doctor)", h2_style))
    story.append(Paragraph(
        "Conducts outpatient consultations, reviews nurse triage vitals, documents formal diagnoses, requisitions diagnostic laboratory tests, "
        "and writes structured electronic prescriptions.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/doctor/consultation_form_detailed.png",
                   "Figure 3 — Doctor Consultation & E-Prescription Form — Comprehensive clinical recording showing diagnosis, vitals review, and e-prescription inputs.")

    story.append(Paragraph("3.4 Staff Nurse", h2_style))
    story.append(Paragraph(
        "Conducts frontline patient triage, measures vital signs (BP, pulse, SpO2, temperature, respiratory rate), calculates derived BMI, "
        "and assigns clinical acuity levels to prioritize urgent care.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/nurse/triage_form_detailed.png",
                   "Figure 4 — Nurse Vitals Triage Form — Vitals capture form with automated BMI computation and clinical acuity prioritization.")

    story.append(Paragraph("3.5 Front Desk Officer", h2_style))
    story.append(Paragraph(
        "Handles reception intake, searches the demographic registry, registers new citizens with address and vulnerability tags, and generates "
        "sequential daily OPD tokens. Front desk officers are strictly isolated from clinical consultation and diagnostic records.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/compounder/01_dashboard_compounder.png",
                   "Figure 5 — Front Desk Intake Console — Reception workstation displaying intake metrics, quick demographic search, and daily OPD token stats.")

    story.append(Paragraph("3.6 Diagnostic Lab Technician", h2_style))
    story.append(Paragraph(
        "Manages the diagnostic testing queue, collects laboratory specimens, inputs investigation values, and issues verified diagnostic reports.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/lab_technician/03_lab.png",
                   "Figure 6 — Diagnostic Investigation Workstation — Diagnostic specimen intake table allowing technicians to verify samples and publish results.")

    story.append(Paragraph("3.7 Pharmacist", h2_style))
    story.append(Paragraph(
        "Verifies doctor electronic prescriptions, reviews automated FEFO (First-Expired, First-Out) batch selections, dispenses medications, "
        "and tracks facility pharmacy stock.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png",
                   "Figure 7 — Pharmacy Dispensing Workstation — Prescription verification table showing doctor orders, recommended FEFO batches, and dispense actions.")

    story.append(Paragraph("3.8 Inventory Officer", h2_style))
    story.append(Paragraph(
        "Manages facility pharmaceutical procurement, creates supplier purchase orders, processes Goods Receipt Notes (GRN), and reconciles "
        "physical warehouse stock balances.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/inventory/01_inventory.png",
                   "Figure 8 — Inventory Workstation & Batch Balances — Real-time facility inventory ledger displaying batch quantities, expiry dates, and unit prices.")

    story.append(Paragraph("3.9 Dual-Role Configuration (Small-Clinic Rule)", h2_style))
    story.append(Paragraph(
        "Provides operational flexibility for small clinics where a single staff member fulfills multiple duties (e.g., Nurse + Front Desk Officer "
        "or Pharmacist + Inventory) as separate authoritative role records without creating hybrid roles.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/dual_role/01_dashboard_pharmacy.png",
                   "Figure 9 — Dual-Role Pharmacy & Procurement Console — Workstation providing unified access to both dispensary and inventory operations.")

    # Patient Journey
    story.append(PageBreak())
    story.append(Paragraph("4. Patient Journey & Workflow Stages", h1_style))
    story.append(Paragraph(
        "The patient journey moves sequentially through five auditable stages: Citizen Registration → OPD Token Issuance → Nurse Vitals Triage "
        "→ Doctor Consultation & Prescription → Diagnostic Lab / Pharmacy Dispensing.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png",
                   "Figure 10 — Citizen Registration Modal — Front Desk Officer registers newly presenting citizens with demographic and emergency details.")
    add_screenshot("scratch/ui_audit_screenshots/compounder/03_queue.png",
                   "Figure 11 — OPD Token & Waiting Queue — Live queue displaying sequential tokens, patient names, and priority classifications.")

    # Separation of Duties
    story.append(Paragraph("5. Inventory & Pharmacy Separation of Duties", h1_style))
    story.append(Paragraph(
        "Warehouse procurement and clinical medication dispensing are architecturally isolated. Storekeepers cannot dispense medications, "
        "and pharmacists cannot directly mutate warehouse stock. All balance updates flow through an immutable double-entry movement ledger.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/inventory/inventory_01_po_tab.png",
                   "Figure 12 — Warehouse Purchase Orders Tab — Procurement table managing external supplier orders and Goods Receipt Notes.")

    # Security & RBAC
    story.append(Paragraph("6. Security & Role-Based Access Control (RBAC)", h1_style))
    story.append(Paragraph(
        "Every client route and API endpoint is strictly protected by authoritative backend role and facility-scoping checks. Unauthorized access "
        "attempts are intercepted by clean security cards and logged to the tamper-evident audit trail.", body_style
    ))
    add_screenshot("scratch/ui_audit_screenshots/nurse/unauth_consultation.png",
                   "Figure 13 — Security Boundary Enforcement — Clean Forbidden Card displayed when an operational role attempts to navigate outside its authorized boundary.")

    # Implementation Scope Table
    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Current Application Scope", h1_style))
    scope_data = [
        [Paragraph("<b>Capability / Domain</b>", body_style), Paragraph("<b>Implementation Status</b>", body_style), Paragraph("<b>Operational Scope</b>", body_style)],
        [Paragraph("Authentication & RBAC", body_style), Paragraph("Fully Implemented", body_style), Paragraph("8 canonical roles, JWT auth, facility scoping", body_style)],
        [Paragraph("Front Desk Intake & Tokens", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Citizen registration, deduplication, token queue", body_style)],
        [Paragraph("Nurse Vitals & Triage", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Vitals entry, BMI calculation, acuity scoring", body_style)],
        [Paragraph("Doctor Consultation & E-Rx", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Diagnoses, clinical notes, e-prescriptions, lab orders", body_style)],
        [Paragraph("Laboratory Diagnostics", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Diagnostic queue, specimen intake, result publishing", body_style)],
        [Paragraph("Pharmacy & FEFO Dispensing", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Rx verification, hold notes, FEFO stock deduction", body_style)],
        [Paragraph("Warehouse Inventory", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Purchase orders, GRN, double-entry movement ledger", body_style)],
        [Paragraph("Staff Lifecycle Admin", body_style), Paragraph("Fully Implemented", body_style), Paragraph("Staff directory, role assignments, transfers", body_style)],
        [Paragraph("Local Laptop Execution", body_style), Paragraph("Active Standard", body_style), Paragraph("PostgreSQL 16, Django 4.2 LTS, React 18 / Vite", body_style)],
        [Paragraph("External Integrations", body_style), Paragraph("Readiness Mode", body_style), Paragraph("ABDM/ABHA data models ready; mock endpoints", body_style)],
    ]
    t_scope = Table(scope_data, colWidths=[150, 120, 270])
    t_scope.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#065F46")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_scope)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Generated PDF: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
