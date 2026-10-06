# Hospital Organ Request and Government Approval Management System (OrganSync)

A full-stack, transparent, and statutory-compliant web application prototype built with **Python (Django Framework)**, **Bootstrap 5**, **JavaScript**, and **SQLite/MySQL**. 

OrganSync connects **Patients**, **Medical Doctors**, **Government Authorization Officials**, **Host Hospitals**, and **Mortuary Staff** into a single centralized digital ledger adhering to the **Transplantation of Human Organs and Tissues Act**.

---

## 🏛️ System Architecture & 4 Core User Roles

```
                      ┌──────────────────────────────────────┐
                      │    OrganSync Central State Ledger    │
                      └──────────────────┬───────────────────┘
                                         │
        ┌──────────────────┬─────────────┴────────────┬──────────────────┐
        │                  │                          │                  │
        ▼                  ▼                          ▼                  ▼
1. Patient Module   2. Medical & Govt          3. Hospital Host   4. Mortuary Module
   - Registration      - Doctor Verification      - Organ Stock      - Deceased Intake
   - Request Form      - Priority Triage          - Cold Ischemia    - Cadaveric Donor
   - Visual Stepper    - Govt Authorization       - Matching Engine    Screening
   - In-App Alerts     - PDF Certificates         - Direct Binding   - Urgent Alerts
```

### 1. Patient Module (User Portal)
- **Authentication & Profile:** Patient registration, secure authentication, personal clinical profile, emergency contacts, national identification (Aadhar/SSN).
- **Organ Request Form:** Clinical organ requirement selection, strict blood group indicator, detailed diagnosis, admitting transplant hospital selection, and file upload for diagnostic laboratory/radiological reports.
- **Real-Time Status Stepper:** Live 4-stage visual progress tracker:
  $$\text{Submitted} \longrightarrow \text{Doctor Verified} \longrightarrow \text{Govt Approved} \longrightarrow \text{Allocated}$$
- **Notification Center:** Real-time in-app alerts notifying the patient at each phase of review.

### 2. Admin & Government Authorization Module (Authorization Portal)
- **Doctor View:** Review incoming clinical requests, inspect attached medical reports/histories, assign medical priority levels (**Emergency**, **High**, **Normal**), add clinical justification notes, and toggle Approve or Reject.
- **Government Official View:** State Authorization Committee scrutiny under Section 9 of the Organ Act. Verifies statutory residency, ethical clearances, and absence of commercial dealings.
- **Official Approval Certificate Generator:** Generates a downloadable formal **PDF Approval Certificate** (built via ReportLab) and an **Interactive Printable HTML Certificate** with digital seals, verification QR code mockups, and legal validity notices.
- **Legal Audit Log:** Immutable chronological ledger logging every state change, actor, and timestamp for legal transparency.

### 3. Hospital Host Module (Host & Transplant Unit)
- **Organ Inventory & Cold Ischemia Monitor:** Real-time tracking of harvested organs with automated remaining viability hour countdowns (Heart: 4–6h, Liver: 12h, Kidney: 24–36h).
- **Donor Registry:** Living and cadaveric donor records with family consent and legal clearance tracking.
- **Automated Matching Engine:** Interactive algorithm dashboard evaluating waiting pool candidates for any organ in stock.

### 4. Mortuary Module (Unit Operations & Donor Triggers)
- **Deceased Intake Logging:** Time of demise, cause of death, identity credentials, and cold storage location (Bay/Vault/Rack).
- **Organ Donation Trigger:** Screen deceased for brain death criteria and preserved organ viability.
- **Rapid Hospital Alert Dispatch:** Instantiates a formal `DonorRecord` and dispatches immediate high-priority alerts to hospital transplant surgical boards.

---

## 🧮 Automated Allocation Algorithm

Whenever an organ becomes available, the system calculates a composite allocation score for all candidates in the central registry using weighted parameters:

### Algorithmic Formula:
$$\text{Allocation Score} = \text{Priority Score} + \text{Waiting Score}$$

1. **Medical Priority Weights:**
   - **Emergency (Tier 1):** `1000 points` *(Critical ICU, acute organ failure, vascular exhaustion)*
   - **High Priority (Tier 2):** `500 points` *(Decompensated organ condition, high MELD / NYHA score)*
   - **Normal Priority (Tier 3):** `100 points` *(Stable on maintenance therapy)*
2. **Strict Blood Group Compatibility:**
   - Strict match required: $\text{Candidate Blood Group} == \text{Organ Blood Group}$. Incompatible candidates are filtered out.
3. **Statutory Government Approval Status:**
   - Must satisfy: $\text{Status} == \text{GOVT\_APPROVED}$. Unapproved requests cannot receive allocations.
4. **Waiting Time Accrual & FIFO Tie-Breaker:**
   - $\text{Waiting Score} = \text{Waiting Days} \times 5.0\text{ points}$.
   - For identical priority levels, earlier submission date acts as the strict FIFO tie-breaker.

---

## 🔄 End-to-End Workflow (State Machine)

```
[Step 1: Patient Registration & Request]
   └─> Patient registers -> Submits organ request with medical reports -> Status: SUBMITTED
[Step 2: Physician Clinical Verification]
   └─> Doctor reviews dossier -> Assigns Priority Level (Emergency/High/Normal) -> Status: DOCTOR_VERIFIED
[Step 3: Government Statutory Clearance]
   └─> Govt official scrutinizes compliance -> Grants Approval -> Status: GOVT_APPROVED -> Certificate Issued
[Step 4: Mortuary / Donor Harvest]
   └─> Mortuary flags deceased donor -> Harvested organ registered with cold ischemia timer -> Status: AVAILABLE
[Step 5: Automated Allocation Engine]
   └─> Matching engine scores candidates strictly by Priority + Blood Match + FIFO wait time -> Ranks #1 Match
[Step 6: Allocation Execution & Emergency Dispatch]
   └─> Status: ALLOCATED -> Instant simulated alerts dispatched to Patient and Hospital Surgical Team
```

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Python 3.12 verified)
- `pip install django reportlab pillow`

### 2. Database Migration & Seeding
From the project root:
```bash
# Run database migrations
python manage.py migrate

# Populate test patients, doctors, hospitals, and available organs
python seed_data.py
```

### 3. Start the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 👥 Pre-Seeded Test Personas & Credentials

All test accounts share the password: `pass1234`

| Role | Username | Password | Persona Details & Verification Function |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient1` | `pass1234` | **John Doe (O+ Kidney):** Emergency priority, Government Approved. Ready to match `ORG-KID-O-001`! |
| **Patient** | `patient2` | `pass1234` | **Sarah Connor (A+ Liver):** High priority, Government Approved. Ready to match `ORG-LIV-A-002`! |
| **Patient** | `patient3` | `pass1234` | **David Miller (B+ Heart):** Doctor Verified; pending Government Authorization review. |
| **Patient** | `patient5` | `pass1234` | **Marcus Vance (AB+ Liver):** Newly Submitted; pending Doctor Medical review. |
| **Doctor** | `doctor1` | `pass1234` | **Dr. Evelyn Reed (Surgeon):** Reviews incoming submissions, assigns Priority levels. |
| **Govt Official**| `govt1` | `pass1234` | **Hon. Arthur Vance (Authority):** Grants statutory clearance, generates Approval Certificates. |
| **Hospital Host**| `hospital1` | `pass1234`| **Elena Rostova (Transplant Coordinator):** Monitors cold ischemia, runs Matching Engine. |
| **Mortuary** | `mortuary1` | `pass1234` | **Robert Hayes (Mortuary Staff):** Logs deceased intake, triggers cadaveric donor alerts. |
| **Admin** | `admin` | `pass1234` | **System Administrator:** Full access to Django admin and central audit ledger. |

> 💡 **Tip:** Use the **"Switch Role"** button in the navigation bar to jump between any of the 5 roles with 1 click during evaluation without typing passwords!

---

## 📂 Project Structure

```
sujay project/
│── manage.py
│── seed_data.py                    # Standalone database population script
│── README.md
│── db.sqlite3
│── organ_system/                   # Django Project Root
│   │── settings.py                 # Configured for SQLite / MySQL & media
│   │── urls.py                     # Main routing & media handlers
│   │── wsgi.py
│── organ_app/                      # Core Application
│   │── models.py                   # Hospital, UserProfile, OrganRequest, AvailableOrgan, Mortuary, AuditLog
│   │── views.py                    # Views for all 4 roles, matching engine, and certificates
│   │── urls.py                     # Feature routing
│   │── forms.py                    # Django ModelForms for registration, review, intake
│   │── admin.py                    # Admin panel registration with search/filters
│   │── matching_service.py         # Automated allocation scoring & ranking algorithm
│   │── certificate_service.py      # ReportLab PDF certificate generator
│   │── context_processors.py       # Global notifications & role context
│   │── tests.py                    # Complete test suite (6/6 tests passing)
│   │── management/commands/        # Django management command (python manage.py seed_data)
│── templates/                      # Bootstrap 5 Responsive Templates
│   │── base.html                   # Global layout, navbar, role switcher, notifications
│   │── landing.html                # Infographics, architecture breakdown, live counters
│   │── auth/                       # Login & Patient registration
│   │── patient/                    # Dashboard (visual stepper), request form, profile, dossier
│   │── doctor/                     # Medical review queue, clinical triage form
│   │── govt/                       # Legal authorization panel, review form, printable HTML certificate
│   │── hospital/                   # Inventory, cold ischemia timers, Matching Engine interface
│   │── mortuary/                   # Deceased intake ledger, donor trigger & alert dispatch
│   │── audit/                      # Statutory legal audit log ledger
│   │── admin_overview.html         # Executive system metrics
│── media/                          # Uploaded medical diagnostic reports
│── static/                         # Static CSS/JS assets
```

---

## 🧪 Testing

To run the automated test suite:
```bash
python manage.py test
```
The test suite validates:
1. Multi-parameter scoring calculations and priority weights
2. Strict blood group compatibility filtering
3. Government approval prerequisites
4. Allocation binding state transitions and automated notification generation
5. PDF certificate byte stream generation
6. HTTP 200 responses across all user role dashboards and public endpoints
