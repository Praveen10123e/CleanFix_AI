# AI-Powered Smart Classroom AV Troubleshooting Assistant (Backend)

Welcome to the backend service for the **AI-Powered Smart Classroom AV Troubleshooting Assistant**. This system powers the AV diagnostics and maintenance workflow for college classrooms, supporting faculty members, AV technicians, and system administrators.

---       

## 1. System Requirements

- **Operating System:** Windows 10/11 (PowerShell)
- **Python Version:** Python 3.10 or higher (Tested with Python 3.13)
- **Database:** SQLite 3 (SQLAlchemy 2.x ORM with SQLite `PRAGMA foreign_keys=ON`)
- **API Framework:** FastAPI, Pydantic 2.x, Uvicorn
- **Base API URL:** `http://localhost:8000/api/v1` (Root health at `/health`)

---
   
## 2. Windows PowerShell Setup Guide

Follow these step-by-step instructions in Windows PowerShell to set up and run the backend locally.

### Step 1: Open PowerShell and Navigate to the Backend Directory
```powershell
cd server/backend
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
> **Tip for PowerShell Permission Error:** If you see `execution of scripts is disabled on this system`, run this once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then retry `.\venv\Scripts\Activate.ps1`.

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to create your local `.env` file (a starter `.env` has already been generated):
```powershell
Copy-Item .env.example .env
```
Key settings in `.env`:
- `DATABASE_URL`: `sqlite:///./smart_av.db` (local SQLite database)
- `GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Web Client ID from Google Cloud Console
- `JWT_SECRET_KEY`: 32+ character HMAC secret for application access tokens
- `CORS_ORIGINS`: Allowed frontend origins (e.g., `http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173`)

### Step 6: Initialize Database Schema (Creates all 12 tables and applies migrations)
```powershell
python -m backend.app.db.init_db
```
*Expected Output:*
```text
INFO: Database initialized successfully with tables: ['audit_logs', 'classrooms', 'complaints', 'device_history', 'devices', 'knowledge_chunks', 'knowledge_documents', 'knowledge_ingestion_jobs', 'repair_records', 'troubleshooting_sessions', 'troubleshooting_steps', 'users']
```

### Step 7: Seed Sample Demonstration Inventory
Populate exactly 10 classrooms (001 to 010), 30 verified devices, and the provisioned development role accounts:
```powershell
python -m backend.scripts.seed_data
```

### Step 8: Start the Backend Server with Uvicorn
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
*Server is now live at:* `http://127.0.0.1:8000`

---

## 3. Provisioned User Roles

The system uses a single `users` table with administrator-controlled account provisioning. Google OAuth links accounts on first login using verified email claims:

| Role | Account Email | Name | Capabilities |
|:---|:---|:---|:---|
| **ADMIN** | `praveenj.cs24@bitsathy.ac.in` | Praveen J (Admin) | User provisioning, room management, technician assignment, equipment reports |
| **FACULTY** | `dhanushm.cs24@bitsathy.ac.in` | Dhanush M (Faculty) | Classroom and device lookup, guided troubleshooting, escalating complaints |
| **TECHNICIAN** | `thiyaneshd.ad24@bitsathy.ac.in` | Thiyanesh D (Technician) | Device registration/status updates, managing assigned complaints, filing repair records |

*Additional local development/test accounts:*
- `admin.dev@classroom.edu` (`ADMIN`)
- `faculty.dev@classroom.edu` (`FACULTY`)
- `technician.dev@classroom.edu` (`TECHNICIAN`)
- `deactivated.dev@classroom.edu` (`FACULTY`, Deactivated)

---

## 4. Demonstration Inventory (10 Classrooms & 30 Devices)

- **Classrooms (10 total):** Identifiers `001, 002, 003, 004, 005, 006, 007, 008, 009, 010` in `Main Academic Block`.
- **Devices per room:** Exactly 1 Microphone, 1 Projector, 1 Smartboard (30 devices total).
- **Verified Manufacturers and Models:**
  - **Microphones:** Shure (`SM58`, `ULXD4`, `MXA910`), Sennheiser (`EW-D SKM-S`, `SL Handheld DW`, `e 835`), Audio-Technica (`ATW-1102`, `AT2020`, `System 10 Pro`).
  - **Projectors:** Epson (`PowerLite L615U`, `EB-2250U`, `PowerLite 119W`, `EB-L730U`), BenQ (`MW560`, `MH560`, `LK936ST`), Sony (`VPL-PHZ60`, `VPL-PHZ50`, `VPL-CWZ10`).
  - **Smartboards:** SMART Technologies (`SMART Board 7000R Pro`, `SMART Board MX065-V2`, `SMART Board GX065`, `SMART Board 6000S`), ViewSonic (`ViewBoard IFP6550`, `ViewBoard IFP7550`, `ViewBoard IFP8650`), BenQ (`BenQ Board Master RP6502`, `BenQ Board Pro RP7502`, `BenQ Board Essential RE6501`).
- **Audit & History:** Every device addition, relocation, status change, and repair is tracked in `device_history`.

---

## 5. Complete API Endpoints (`/api/v1`)

### Health
- `GET /health` (Public root health & database liveness)
- `GET /api/v1/health` (Public versioned health)

### Authentication
- `POST /api/v1/auth/google` (Public: Exchange Google ID token for application JWT)
- `GET /api/v1/auth/me` (Authenticated: Current active user profile and role)

### Administration (`require_admin`)
- `POST /api/v1/admin/users` (Provision new user account)
- `GET /api/v1/admin/users` (List provisioned users with role/status filters)
- `PATCH /api/v1/admin/users/{id}` (Update user name, role, or active status)
- `GET /api/v1/admin/reports/summary` (Dynamic DB metrics: rooms, devices, complaints, repairs)

### Classrooms
- `POST /api/v1/classrooms` (Admin/Technician: Register classroom with unique room number)
- `GET /api/v1/classrooms` (Authenticated: Paginated active classroom list with search)
- `GET /api/v1/classrooms/{id}` (Authenticated: Classroom details)
- `PATCH /api/v1/classrooms/{id}` (Admin: Update room metadata or active status)
- `GET /api/v1/classrooms/{id}/devices` (Authenticated: Real database devices in selected room)

### Devices
- `POST /api/v1/devices` (Admin/Technician: Register AV equipment with validated room)
- `GET /api/v1/devices/{id}` (Authenticated: Device details and operational status)
- `PATCH /api/v1/devices/{id}` (Admin/Technician: Update device status/location; logs `device_history`)

### Troubleshooting Sessions (Faculty/Admin)
- `POST /api/v1/troubleshooting/sessions` (Start guided session for classroom device with symptom text)
- `POST /api/v1/troubleshooting/sessions/{id}/steps/next` (Fetch pending or next rule-based step)
- `POST /api/v1/troubleshooting/sessions/{id}/steps/{step_id}/result` (Record step outcome: SUCCESS/FAILED/SKIPPED)
- `POST /api/v1/troubleshooting/sessions/{id}/complete` (Mark session RESOLVED)
- `POST /api/v1/troubleshooting/sessions/{id}/complaint` (Escalate unresolved session to technician complaint)

### Complaints & Repairs
- `POST /api/v1/complaints` (Authenticated: Submit direct equipment complaint)
- `GET /api/v1/complaints` (Role-aware: Faculty see own; Technicians see assigned/all; Admin sees all)
- `GET /api/v1/complaints/{id}` (Role-aware: Complaint details and repair record)
- `PATCH /api/v1/complaints/{id}/assignment` (Admin: Assign complaint to active technician)
- `PATCH /api/v1/complaints/{id}/status` (Assigned Technician/Admin: Update progress e.g. IN_PROGRESS)
- `POST /api/v1/complaints/{id}/resolution` (Assigned Technician/Admin: Record repair, restore device to OPERATIONAL)

### Knowledge Document Metadata
- `POST /api/v1/knowledge/documents` (Admin/Technician: Register manual/guide metadata)
- `GET /api/v1/knowledge/documents` (Authenticated: List equipment documentation)
- `GET /api/v1/knowledge/documents/{id}` (Authenticated: Retrieve document metadata)

---

## 6. Rule-Based Troubleshooting Workflow (No RAG Required)

The troubleshooting workflow operates completely without AI APIs or external RAG dependencies:
1. Faculty selects classroom (`GET /classrooms`) and fetches assigned devices (`GET /classrooms/{id}/devices`).
2. Faculty submits observed symptom (`POST /troubleshooting/sessions`).
3. Dedicated rule engine (`backend/app/services/troubleshooting_catalogue.py`) selects safe, non-invasive diagnostic steps (cable check, input source, lens shutter, battery, calibration).
4. Faculty submits result for each step (`POST /troubleshooting/sessions/{id}/steps/{step_id}/result`).
5. If resolved, session completes (`POST /troubleshooting/sessions/{id}/complete`).
6. If unresolved, faculty escalates to an official technician repair complaint (`POST /troubleshooting/sessions/{id}/complaint`), which sets device status to `FAULTY` and alerts the AV team.

---

## 7. Future RAG Integration Interface

A clean, typed interface has been defined in `backend/app/services/rag_interface.py` to allow future integration of RAG and vector retrieval without altering the database schema or frontend contracts:

- **Context Builder:** `build_rag_troubleshooting_context(db, session_id)` retrieves device specs, classroom metadata, previous steps and results, and past repair history into a strongly typed `RAGTroubleshootingContext` Pydantic model.
- **Pluggable Base:** `BaseRAGDiagnosticService` defines `generate_diagnostic_step(context)` and `retrieve_evidence(query, device_context)`.
- **Graceful Fallback:** `StubRAGDiagnosticService` operates when no external AI API is configured.

---

## 8. Frontend Integration Guide (React / Vite)

1. **API Base URL:** Configure `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
2. **CORS:** Ensure your React dev server origin (e.g. `http://localhost:5173`) is listed in `.env` under `CORS_ORIGINS`.
3. **Authentication:**
   - Sign in via Google Identity Services button on React frontend to obtain `id_token`.
   - Call `POST /api/v1/auth/google` with `{ "id_token": "<google_jwt>" }`.
   - Store returned `access_token` in memory or secure storage.
   - Attach header to all subsequent requests:
     ```http
     Authorization: Bearer <access_token>
     ```
4. **Device Selector:** Never hardcode classrooms or devices. Call `GET /api/v1/classrooms` to populate room dropdowns, then `GET /api/v1/classrooms/{id}/devices` to populate the device dropdown. Display labels using `${device.device_type} — ${device.brand} — ${device.model}`.
5. **Standard Envelopes:**
   - Single resource: `{ "data": { ... } }`
   - Paginated list: `{ "data": [ ... ], "meta": { "limit": 20, "offset": 0, "total": 1 } }`
   - Errors: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": { ... } } }`

---

## 9. Running Tests

Run the complete 41-test automated suite:
```powershell
pytest -v
```

All 41 tests run against an isolated in-memory test database with mocked Google OAuth tokens and foreign-key enforcement enabled.

---

## 10. Known Limitations & Scope Boundaries

1. **RAG / Vector Database:** RAG, semantic chunking, and PDF text extraction are intentionally omitted per specification for Phase 2/3 and will be integrated by the RAG team member using `rag_interface.py`.
2. **Google Identity Verification:** In local development without real Google Cloud credentials, token verification is tested via mocked tokens; live sign-in requires setting a real `GOOGLE_CLIENT_ID` in `.env`.
