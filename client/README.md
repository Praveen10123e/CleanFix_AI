# ClassFix AI — Campus AV Operations Platform

> **AI-Powered Smart Classroom Audio-Visual Troubleshooting & Incident Management Platform**  
> Built for university faculty lectures, IT AV dispatch teams, and campus operations administrators.

---

## 1. System Architecture & Real Database Authentication

ClassFix AI is a complete frontend for smart classroom audio-visual troubleshooting and incident response. It integrates directly with the university backend API (`http://localhost:8000/api/v1`) and authenticates real users provisioned in the database.

### Key Architectural Standards
- **Real Database Authentication**: All user identities and role authorizations (`faculty`, `technician`, `admin`) are determined strictly by the backend response via `POST /auth/google` and `GET /auth/me`. No mock logins, hardcoded demo personas, or fake credential fallbacks exist.
- **Strict Role-Protected Routing**: Client routes are gated through the authenticated user's database role. Unauthorized users or unprovisioned Google accounts are blocked with an explicit Access Denied screen (`/unauthorized`). Roles stored in `localStorage` or URL query parameters are never trusted.
- **Direct Backend Integration**: All operational data (classrooms, registered hardware, active complaints, troubleshooting sessions, and SLA reports) is fetched live from the backend API. When the backend database is empty, the UI displays clear, informative empty states rather than placeholder records.
- **Centralized HTTP Client (`apiClient`)**: Dispatches standard JSON and multipart requests to `VITE_API_BASE_URL`. Automatically unwraps `{ "data": ... }` response envelopes, manages `Authorization: Bearer <token>` in `sessionStorage`, supports cookie-based sessions via `credentials: 'include'`, and normalizes HTTP errors (`401`, `403`, `404`, `422`, `500`).

---

## 2. Institutional Google Workspace Authentication Flow

1. **User Action**: The user clicks **Continue with Google** on the login page (`/login`).
2. **Token Acquisition**: Google Identity Services (GIS) prompts the user with the university Google Workspace sign-in popup.
3. **Backend Verification**: The frontend transmits the Google ID token to `POST /auth/google` with payload:
   ```json
   {
     "token": "<google_id_token>",
     "id_token": "<google_id_token>",
     "credential": "<google_id_token>"
   }
   ```
4. **Database Authorization**: The backend validates the Google token and checks whether the user is provisioned and active in the database.
5. **Session Resolution**: The backend returns the user session and token. The frontend verifies the user's role via the response or `GET /auth/me`.
6. **Role Dashboard Redirection**: The user is immediately routed to their designated console:
   - Faculty: `/faculty`
   - Field Technician: `/technician`
   - Campus Administrator: `/admin`

If an unprovisioned or inactive account attempts sign-in, access is denied with the exact error returned by the server.

---

## 3. Light UI Design System

Designed specifically for glare-free readability in classroom podiums and IT dispatch desks:

| Design Token | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Main Background** | `#F8FAF8` | Clean, glare-free canvas |
| **Cards & Surfaces** | `#FFFFFF` | Elevated surfaces with subtle borders |
| **Primary Green** | `#1B4D3E` | Authoritative institutional accent & active states |
| **Secondary Green** | `#E7F1EB` | Subtle pill badges, chips, and active highlights |
| **Soft Green** | `#F0F6F1` | Background for banners and diagnostic callouts |
| **Main Text** | `#202824` | Primary high-contrast typography (WCAG AAA) |
| **Secondary Text** | `#66736C` | Metadata, helper text, and timestamps |
| **Borders** | `#E3E9E4` | Crisp, modern border lines |
| **Warning** | `#B7791F` | Non-blocking alerts and medium priority tickets |
| **Error / Critical** | `#C2413B` | High/Critical priority issues & validation alerts |
| **Success** | `#27815B` | Resolved statuses & healthy device indicators |

### Viewport Calibration
Tested and verified for Google Chrome across standard resolutions without horizontal overflow:
- `1366 × 768` (Standard classroom podium laptops)
- `1440 × 900` (MacBook / ultrabook displays)
- `1920 × 1080` (IT dispatch control monitors at 100% zoom)

---

## 4. Role Portals & Application Pages

### Faculty Portal (`/faculty`)
- **Dashboard (`/faculty`)**: Active classroom selector, quick diagnostic symptom prompt, and active session resumption.
- **Classroom Directory (`/faculty/classrooms`)**: Campus building overview showing seating capacity and room status.
- **Classroom Equipment (`/faculty/classrooms/:classroomId`)**: Detailed inventory of registered AV equipment in the selected lecture hall.
- **Device Details (`/faculty/classrooms/:classroomId/devices/:deviceId`)**: Hardware specifications, serial number, IP address, and direct "Start AI Troubleshooting" action.
- **AI Troubleshooting (`/faculty/troubleshooting`)**:
  - Step-by-step diagnostic checks citing official OEM service manuals.
  - 4-way observation feedback: `Issue Resolved`, `Still Broken`, `Cannot Perform`, `Unsure / Unknown`.
  - Prominent **Request Technician** button that escalates unresolved sessions via `POST /troubleshooting/sessions/{id}/complaint`.
- **My Complaints (`/faculty/complaints`)**: History of incidents reported by the faculty member.

### Field Technician Portal (`/technician`)
- **Overview & Metrics (`/technician`)**: 3 compact operational metrics (Pending Tickets, Active Investigations, Resolved Today).
- **Incident Queue (`/technician/complaints`)**: Real-time searchable ticket list with status tabs (`ALL`, `PENDING`, `IN_PROGRESS`, `RESOLVED`, `ESCALATED`).
- **Slide-Over Complaint Detail Drawer**:
  - Full incident context: reporter, classroom, device parameters.
  - Complete AI diagnostic transcript from the faculty member's session.
  - One-click ticket claiming (`PATCH /complaints/{id}/assignment`).
  - Validated resolution submission form requiring `confirmed_cause`, `repair_action`, and optional `resolution_notes` before closing (`POST /complaints/{id}/resolution`).
- **Equipment Inventory (`/technician/equipment`)**: Campus hardware directory with status management and device registration modal (`POST /devices`).
- **Service Manuals (`/technician/manuals`)**: Technical PDF manuals library with multipart upload modal (`POST /knowledge/documents`).

### Campus Administrator Portal (`/admin`)
- **Operations Overview (`/admin`)**: Fleet health telemetry, total registered devices, system uptime, and average repair SLA.
- **Classroom Fleet Manager (`/admin/classrooms`)**: Room directory, building filters, operational room status updates (`PATCH /classrooms/{id}`), and Add Classroom modal (`POST /classrooms`).
- **User & Access Management (`/admin/users`)**: University personnel directory, role permissions modification (`PATCH /admin/users/{id}/role`), and Add User modal (`POST /admin/users`).
- **Device Inventory (`/admin/devices`)**: Hardware inventory management.
- **Operations Analytics & SLA Reports (`/admin/reports`)**: Incident trends, resolution velocity, and severity distribution (`GET /admin/reports/summary`).

---

## 5. Backend API Endpoints

The frontend communicates strictly with the agreed endpoints:

| Endpoint | Method | Role | Description |
| :--- | :---: | :---: | :--- |
| `/auth/google` | `POST` | Public | Verify Google OAuth ID token & authenticate user |
| `/auth/me` | `GET` | Authenticated | Retrieve current user profile and role |
| `/auth/logout` | `POST` | Authenticated | Conclude user session |
| `/classrooms` | `GET`, `POST` | All / Admin | List all classrooms or register a new room |
| `/classrooms/{id}` | `GET`, `PATCH` | All / Admin | Fetch room details or update status/capacity |
| `/classrooms/{id}/devices` | `GET` | All | Retrieve registered hardware in a classroom |
| `/devices` | `GET`, `POST` | All / Tech | List devices or register new classroom hardware |
| `/devices/{id}` | `GET`, `PATCH` | All / Tech | Hardware details or status updates |
| `/troubleshooting/sessions` | `POST` | Faculty | Initiate AI diagnostic session with symptom text |
| `/troubleshooting/sessions/{id}/steps/next` | `POST` | Faculty | Retrieve next recommended diagnostic step |
| `/troubleshooting/sessions/{id}/steps/{step_id}/result` | `POST` | Faculty | Submit observation result for a step |
| `/troubleshooting/sessions/{id}/complete` | `POST` | Faculty | Conclude session after successful resolution |
| `/troubleshooting/sessions/{id}/complaint` | `POST` | Faculty | Escalate diagnostic session to field technician queue |
| `/complaints` | `GET`, `POST` | All | Query complaint queue with status/priority filters |
| `/complaints/{id}` | `GET` | All | Retrieve full complaint record with diagnostic trace |
| `/complaints/{id}/assignment` | `PATCH` | Tech / Admin | Claim ticket or assign to field technician |
| `/complaints/{id}/status` | `PATCH` | Tech / Admin | Update complaint lifecycle status |
| `/complaints/{id}/resolution` | `POST` | Tech / Admin | Conclude ticket with confirmed cause & repair action |
| `/knowledge/documents` | `GET` | Tech / Admin | List indexed technical service manuals |
| `/knowledge/documents` | `POST` | Tech / Admin | Upload new OEM PDF manual (multipart/form-data) |
| `/admin/reports/summary` | `GET` | Admin | Fetch system SLA telemetry and incident distribution |
| `/admin/users` | `GET`, `POST` | Admin | List users or provision new staff |
| `/admin/users/{id}` | `PATCH` | Admin | Update user account details |
| `/admin/users/{id}/role` | `PATCH` | Admin | Update user role permissions |

---

## 6. Environment Setup & Execution

### Environment Variables
Configure `.env`:
```ini
# Backend API Base URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Application Environment
VITE_APP_ENV=development

# Google Workspace OAuth Client ID for institutional SSO
VITE_GOOGLE_CLIENT_ID=
```

### Run Locally
```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev
```

### Production Build
```bash
npm run build
```
Runs `tsc -b && vite build` ensuring 0 TypeScript errors and producing optimized production assets in `dist/`.
