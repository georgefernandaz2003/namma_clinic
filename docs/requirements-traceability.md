# Requirement Traceability Matrix
## Namma Clinic Integrated Digital Healthcare Network

| Requirement ID | Requirement Summary | Source Document | Source Section / Page | Classification | System Module | Implementation Status | Notes / Demo Behavior |
|---|---|---|---|---|---|---|---|
| REQ-OFF-001 | Provide comprehensive primary health care in urban areas | ULB ROK Booklet | Page 2-3 | OFFICIAL BOOKLET REQUIREMENT | Consultation / General OPD | FULLY COVERED | 12 service packages covered |
| REQ-OFF-002 | Target 15,000 - 20,000 population per Urban HWC (Namma Clinic) | ULB ROK Booklet | Page 3 | OFFICIAL BOOKLET REQUIREMENT | Facility Master | FULLY COVERED | Captured in facility demographics |
| REQ-OFF-003 | 12 Service Packages delivery (Maternal, Child, Adolescent, FP/RCH, Communicable, NCD, Mental, Eye/ENT, Dental, Geriatric, Emergency, Oral) | ULB ROK Booklet | Page 6, 31 | OFFICIAL BOOKLET REQUIREMENT | Clinical & Consultation | FULLY COVERED | Selectable service workflows & clinical templates |
| REQ-OFF-004 | HR Staffing: 1 Medical Officer, 1 Staff Nurse, 1 LDC/Lab Tech, 1 Group D | ULB ROK Booklet | Page 10-15 | OFFICIAL BOOKLET REQUIREMENT | User Roles & Facilities | FULLY COVERED | RBAC matrix mapped to official roles |
| REQ-OFF-005 | Teleconsultation facility setup (Desktop, Camera, Printer, UPS) | ULB ROK Booklet | Page 9 | OFFICIAL BOOKLET REQUIREMENT | Telemedicine Module | FULLY COVERED | Simulated local teleconsultation workflow |
| REQ-OFF-006 | Essential Drug List (EDL) and E-Aushada mechanism tracking | ULB ROK Booklet | Page 16-17 | OFFICIAL BOOKLET REQUIREMENT | Pharmacy & Inventory | FULLY COVERED | Generic medicine master & stock ledgers |
| REQ-OFF-007 | Drug Registers: Stock & Issue, Indent, Dispense, Bin Cards, Expiry Register | ULB ROK Booklet | Page 17 | OFFICIAL BOOKLET REQUIREMENT | Pharmacy & Inventory | FULLY COVERED | Digital logs for all 5 official registers |
| REQ-OFF-008 | Arogya Raksha Samiti (ARS) constitution and monthly meetings | ULB ROK Booklet | Page 19 | OFFICIAL BOOKLET REQUIREMENT | ARS Module | FULLY COVERED | Tracks committee, agendas, attendance & action plans |
| REQ-OFF-009 | Wellness Activities (Yoga / Meditation, 8 sessions per month) | ULB ROK Booklet | Page 18 | OFFICIAL BOOKLET REQUIREMENT | Wellness Module | FULLY COVERED | Instructor & session attendance tracking |
| REQ-OFF-010 | Kayakalpa, Bio-Medical Waste & Infection Control tracking | ULB ROK Booklet | Page 17 | OFFICIAL BOOKLET REQUIREMENT | Quality & BM Waste | FULLY COVERED | Quality checklists & waste segregation logs |
| REQ-OFF-011 | Referral continuum of care to UPHCs, Secondary/Tertiary Hospitals | ULB ROK Booklet | Page 2, 24 | OFFICIAL BOOKLET REQUIREMENT | Referral Network | FULLY COVERED | Cross-facility bi-directional referrals |
| REQ-KM-001 | Unified Digital Health Platform for GBA / BBMP Namma Clinics | K Mati Proposal | Page 2 | K MATI PROPOSAL | Core Platform | FULLY COVERED | Full-stack digital operating system |
| REQ-KM-002 | EMR-lite for rapid primary care documentation (3-6 min target) | K Mati Proposal | Page 7-8 | K MATI PROPOSAL | Doctor Console | FULLY COVERED | Structured templates & quick-picks |
| REQ-KM-003 | First-Expiry First-Out (FEFO) batch management & stock alerts | K Mati Proposal | Page 7 | K MATI PROPOSAL | Pharmacy / FEFO | FULLY COVERED | Batch expiry tracking & auto-selection |
| REQ-KM-004 | Rule-Based AI Decision Support (Stock-out prediction, Disease Anomaly detection) | K Mati Proposal | Page 9 | K MATI PROPOSAL | Demo Analytics | FULLY COVERED | Local rule-based alerts (no external AI) |
| REQ-KM-005 | Command Dashboards (Clinic, Zone, Commissioner, Public Health) | K Mati Proposal | Page 10, 18 | K MATI PROPOSAL | Dashboards | FULLY COVERED | Role-specific dynamic dashboards |
| REQ-KM-006 | ABDM / ABHA Readiness and eHospital referral compatibility | K Mati Proposal | Page 9-10 | K MATI PROPOSAL | Integrations | FULLY COVERED | Local mock integration screens |
| REQ-TEC-001 | Offline-first execution (SQLite + Django REST + React) | Master Prompt | N/A | DERIVED TECHNICAL REQUIREMENT | System Architecture | FULLY COVERED | Completely offline self-contained demo |
| REQ-TEC-002 | Dynamic facility hierarchy & independent referral graph | Master Prompt | N/A | DERIVED TECHNICAL REQUIREMENT | Facility / Network | FULLY COVERED | Database-driven parent-child & multi-referral links |
| REQ-TEC-003 | JWT Authentication & Audit Logging | Master Prompt | N/A | DERIVED TECHNICAL REQUIREMENT | Security / Audit | FULLY COVERED | Role-based token access & full event logging |
| REQ-DEM-001 | Demo Reset (`seed_demo` and `reset_demo` management commands) | Master Prompt | N/A | DEMO ENHANCEMENT | Admin / Seeding | FULLY COVERED | One-click demo data reset to pristine state |
| REQ-DEM-002 | Visual Network Graph Canvas (SVG visualizer) | Master Prompt | N/A | DEMO ENHANCEMENT | Healthcare Network | FULLY COVERED | Interactive node map without external maps API |
| REQ-DEM-003 | Complete Demo Scenario Flow (Nurse -> Doctor -> Lab -> Pharmacy -> Referral -> Hospital -> Followup) | Master Prompt | N/A | DEMO ENHANCEMENT | End-to-End Flow | FULLY COVERED | Seamless multi-role walkthrough |
