# CleanFix AI — API Contract & System Integration

This document defines the integration boundary between the **Frontend Client**, the **FastAPI Backend Server**, and the internal **AI Subsystems** (AI Developer 1: Retrieval, AI Developer 2: Diagnostic Reasoning).

---

## 1. System Architecture & Boundaries

```
┌─────────────────────────────────┐
│     Frontend Client (Web/UI)    │
└────────────────┬────────────────┘
                 │ HTTP / REST
                 ▼
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend Server                 │
│  - Authentication & Role RBAC                            │
│  - Session & State Management (PostgreSQL/SQLite)        │
│  - Complaint Ticketing / Escalation Persistence          │
│  - Rate Limiting & Input Validation                      │
└───────────────┬──────────────────────────┬───────────────┘
                │                          │
                │ Python Service Call      │ Python Service Call
                ▼                          ▼
  ┌─────────────────────────┐   ┌──────────────────────────┐
  │  AI Dev 1 (Retrieval)   │   │  AI Dev 2 (Diagnosis)    │
  │  retrieve_evidence()    │   │  generate_diagnosis()    │
  │  - PDF Ingestion        │   │  - Symptom Normalizer    │
  │  - Manual Chunking/FAISS│   │  - Safety Rule Engine    │
  │  - RAG Evidence Store   │   │  - Action Registry       │
  └─────────────────────────┘   │  - LLM Orchestrator      │
                                └──────────────────────────┘
```

> **Important Boundary Rule**: The AI engine (`server/ai`) operates as an internal Python module embedded in the backend process. It does **not** expose public HTTP endpoints directly to clients and does **not** write to the database. All persistence, authorization, and audit logs are managed by the FastAPI Backend.

---

## 2. Python Service Interface Contract

The AI subsystem exports both the end-to-end integration pipeline and the granular diagnosis engine entry point:

### 2.1 End-to-End RAG + Diagnosis Integration Service
```python
from server.ai.service import diagnose_session
from server.ai.diagnosis.models import SessionContext, DiagnosisResult

# Automates query construction, BM25 retrieval, and diagnosis generation
diagnosis_result: DiagnosisResult = diagnose_session(
    session_context=session_context,
    index_path="data/knowledge/chunks.jsonl", # optional, defaults to standard index
    top_k=5,                                  # optional
)
```

### 2.2 Direct Diagnosis Engine Entry Point
```python
from server.ai.diagnosis.service import generate_diagnosis
from server.ai.diagnosis.models import SessionContext, RetrievalResult, DiagnosisResult

# Invoked synchronously or via worker when retrieval is managed independently
diagnosis_result: DiagnosisResult = generate_diagnosis(
    session_context=session_context,
    evidence=retrieval_result
)
```

---

## 3. Backend HTTP REST Endpoints (FastAPI)

### 3.1 Start Diagnostic Session
- **POST** `/api/v1/sessions`
- **Description**: Initiates a new troubleshooting session when a faculty member reports an issue on a registered classroom device.

#### Request Payload:
```json
{
  "device_id": "dev-proj-hall-a",
  "symptom_description": "The projector turns on and has a blue light, but shows No Signal when I connect my laptop."
}
```

#### Response (201 Created):
```json
{
  "session_id": "sess-9a7f3b8c",
  "status": "in_progress",
  "diagnosis": {
    "decision": "ask_question",
    "reasoning_summary": "Initial symptom indicates power is functioning but video stream is not received.",
    "question": {
      "question_id": "q-cable-type",
      "text": "Are you connecting via HDMI cable or wireless display adapter?",
      "input_type": "single_choice",
      "options": ["HDMI cable", "Wireless display", "VGA / Other", "Not sure"]
    },
    "next_step": null,
    "sources": [],
    "uncertainty": "Connection medium is unspecified."
  }
}
```

---

### 3.2 Submit Step Outcome or Answer
- **POST** `/api/v1/sessions/{session_id}/steps`
- **Description**: Submits the result of the previous step or the answer to a question. The backend updates session history, calls `retrieve_evidence` (if needed for updated query), and calls `generate_diagnosis`.

#### Request Payload (for step outcome):
```json
{
  "step_id": "step-1",
  "action_id": "PROJ_SOURCE_SEARCH",
  "result_status": "not_resolved",
  "user_feedback": "I pressed Source Search, it cycled through inputs, but still says No Signal."
}
```

#### Request Payload (for question response):
```json
{
  "question_id": "q-cable-type",
  "answer": "HDMI cable"
}
```

#### Response (200 OK):
```json
{
  "session_id": "sess-9a7f3b8c",
  "status": "in_progress",
  "diagnosis": {
    "decision": "next_step",
    "reasoning_summary": "HDMI connection confirmed, but laptop video output mode (mirror/extend) has not been triggered.",
    "next_step": {
      "action_id": "PROJ_LAPTOP_DUPLICATE_DISPLAY",
      "instruction": "Press Windows Key + P on your laptop and click 'Duplicate'.",
      "reason": "Laptops often default to turning off external video projection.",
      "expected_observation": "The laptop desktop immediately mirrors onto the projector screen.",
      "safety_level": "low",
      "requires_confirmation": true
    },
    "question": null,
    "sources": [
      {
        "document_id": "doc-epson-pl2250u",
        "page_number": 49,
        "title": "Epson PowerLite 2250U User's Guide"
      }
    ],
    "uncertainty": "Operating system display output status"
  }
}
```

---

### 3.3 Session Resolution
When `diagnosis.decision == "resolved"`:
- Backend updates session status to `"resolved"`.
- Backend logs resolution metrics for equipment reliability reporting.
- Frontend displays resolution banner and optional feedback survey.

---

### 3.4 Session Escalation
When `diagnosis.decision == "escalate"`:
- Backend transitions session to `"escalated"`.
- Backend automatically generates a formal IT/AV Support Ticket with:
  - Device ID, room, brand, model
  - Full transcript of attempted steps and results
  - Symptom category and escalation reason
  - Safety hazard flags (if detected)
- Frontend displays technician dispatch notification and ticket reference number.

---

## 4. Safety & Security Guardrails

1. **Safety Enforcement**:
   - Any physical step returned by the AI module MUST belong to the `ActionRegistry`.
   - Any symptom indicating electrical hazards (smoke, sparks, burning odor, exposed wires) causes immediate escalation without attempting self-service steps.
2. **Untrusted Content Sanitization**:
   - User inputs and technician notes are treated as untrusted text.
   - Retrieved manual text is isolated in strict delimiters to prevent prompt injection.
3. **No Fabricated Citations**:
   - Citations are strictly matched against `evidence` chunks supplied by `retrieve_evidence`.
   - If `retrieval_status == "no_match"`, `sources` is guaranteed to be empty `[]`.
4. **Mock Mode Guarantee**:
   - If `LLM_PROVIDER=mock`, the system runs 100% deterministically without network calls or API keys, enabling frontend/backend integration testing out of the box.

