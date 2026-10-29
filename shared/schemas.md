# CleanFix AI — Shared Schemas & Data Contracts

This document formalizes the data contracts and Pydantic schemas shared across **AI Developer 1** (RAG/Retrieval), **AI Developer 2** (Diagnostic Reasoning & LLM Orchestration), the **Backend Developer** (Persistence & API), and the **Frontend Developer** (Client UI).

---

## 1. Core Enumerations

### 1.1 Device Types
```json
["projector", "microphone", "smart_board"]
```

### 1.2 Decision Types
- `ask_question`: Engine requires clarifying information before recommending a physical action.
- `next_step`: Engine recommends an approved, safe troubleshooting action.
- `resolved`: The issue is confirmed fixed by faculty feedback or verification.
- `escalate`: The issue requires professional IT/AV technician intervention or safety halt.

### 1.3 Step Result Statuses
- `resolved`: The action resolved the problem.
- `not_resolved`: The action was performed, but the fault remains.
- `unknown`: Faculty is unsure whether the action succeeded or cannot tell.
- `unable_to_perform`: Faculty cannot perform the action safely or lacks access/tools.

### 1.4 Retrieval Statuses
- `found`: Relevant evidence chunks were retrieved from documentation.
- `no_match`: Query executed successfully, but no relevant documentation chunks met relevance thresholds.
- `failed`: Retrieval subsystem experienced an error or network/indexing failure.

### 1.5 Safety Levels
- `low`: Non-invasive, safe for any user (e.g., checking power switch, remote buttons, software settings).
- `medium`: Low-risk physical check (e.g., reseating user-accessible HDMI cable, checking external mic batteries).
- `high`: Hazardous (opening equipment, bare wires, electrical repairs) — **Strictly forbidden for faculty self-service; triggers immediate escalation**.

---

## 2. Retrieval Contracts (AI Developer 1 -> AI Developer 2)

### EvidenceItem
Represents a single retrieved chunk from verified equipment manuals.

| Field | Type | Description |
|---|---|---|
| `document_id` | `str` (UUID) | Unique identifier of the manual/document |
| `title` | `str` | Title of the manual/guide |
| `page_number` | `Optional[int]` | Page number within the source manual, if available |
| `chunk_id` | `str` | Specific chunk identifier |
| `text` | `str` | Text content of the manual excerpt |
| `relevance_score` | `float` | Cosine similarity or relevance score (0.0 to 1.0) |

### RetrievalResult
The response returned by AI Developer 1's `retrieve_evidence` function.

```json
{
  "query": "projector no signal blue screen",
  "device_context": {
    "device_type": "projector",
    "brand": "Epson",
    "model": "PowerLite 2250U"
  },
  "evidence": [
    {
      "document_id": "doc-epson-pl2250u",
      "title": "Epson PowerLite 2250U User's Guide",
      "page_number": 48,
      "chunk_id": "epson-ch-48-no-signal",
      "text": "If 'No Signal' appears, press the Source Search button on the remote or control panel to switch to HDMI 1 or Computer 1.",
      "relevance_score": 0.89
    }
  ],
  "retrieval_status": "found"
}
```

---

## 3. Session Context Contract (Backend -> AI Developer 2)

### StepHistoryItem
History of a diagnostic step previously recommended and executed.

| Field | Type | Description |
|---|---|---|
| `step_id` | `str` | Unique ID of the step instance |
| `action_id` | `Optional[str]` | Approved action ID from registry |
| `instruction` | `str` | Instruction given to the user |
| `result_status` | `StepResultStatus` | `resolved`, `not_resolved`, `unknown`, `unable_to_perform` |
| `user_feedback` | `Optional[str]` | Optional comment from faculty |
| `timestamp` | `Optional[str]` | ISO 8601 timestamp |

### QuestionHistoryItem
History of questions asked and answered.

| Field | Type | Description |
|---|---|---|
| `question_id` | `str` | Unique ID of the question |
| `question_text` | `str` | Question text |
| `answer` | `str` | User's response |

### SessionContext
Passed into `generate_diagnosis(session_context, evidence)`.

```json
{
  "session_id": "sess-20261029-001",
  "device_id": "dev-proj-hall-a",
  "device_type": "projector",
  "brand": "Epson",
  "model": "PowerLite 2250U",
  "device_configuration": {
    "primary_input": "HDMI 1",
    "wall_plate": "Front Wall Plate 1"
  },
  "original_symptom": "The projector turns on and has a blue light, but shows No Signal when I connect my laptop.",
  "previous_steps": [
    {
      "step_id": "step-1",
      "action_id": "PROJ_CHECK_POWER_LED",
      "instruction": "Check that the projector power LED is solid blue or green.",
      "result_status": "resolved",
      "user_feedback": "Yes, it is solid blue.",
      "timestamp": "2026-10-29T14:10:00Z"
    }
  ],
  "previous_questions": [
    {
      "question_id": "q-laptop-os",
      "question_text": "Is your laptop running Windows or macOS?",
      "answer": "Windows"
    }
  ],
  "current_diagnostic_state": "verifying_input_source",
  "available_retrieved_evidence": [],
  "permitted_action_categories": [
    "user_interface_checks",
    "cable_reseat",
    "power_cycle_soft",
    "source_selection"
  ],
  "applicable_safety_constraints": [
    "no_opening_enclosures",
    "no_ladder_climbing",
    "no_exposed_wiring",
    "max_step_limit_5"
  ]
}
```

---

## 4. Diagnostic Output Contract (AI Developer 2 -> Backend)

### NextStep
Recommends a safe, approved diagnostic step.

| Field | Type | Description |
|---|---|---|
| `action_id` | `Optional[str]` | Identifier matching the approved Action Registry |
| `instruction` | `str` | Clear step-by-step instruction for faculty |
| `reason` | `str` | Non-technical rationale explaining why this step matters |
| `expected_observation` | `str` | What the user should observe if this step works |
| `safety_level` | `str` | `"low"` or `"medium"` (high-risk steps are rejected) |
| `requires_confirmation` | `bool` | True if user must confirm outcome before advancing |

### DiagnosticQuestion
Clarifying question to reduce uncertainty.

| Field | Type | Description |
|---|---|---|
| `question_id` | `str` | Stable question identifier |
| `text` | `str` | Concise, non-technical question |
| `input_type` | `str` | `"single_choice"` \| `"boolean"` \| `"text"` |
| `options` | `Optional[List[str]]` | e.g. `["Yes", "No", "Not sure", "Unable to perform"]` |

### SourceReference
Grounded citation pointing to retrieved evidence.

| Field | Type | Description |
|---|---|---|
| `document_id` | `str` | ID matching a retrieved evidence document |
| `page_number` | `Optional[int]` | Page number from retrieved chunk |
| `title` | `Optional[str]` | Document title |
| `chunk_id` | `Optional[str]` | Chunk identifier from retrieved evidence |
| `relevance_score` | `Optional[float]` | Normalized relevance score of the chunk |

### NormalizedSymptom
Structured candidate interpretation of user description.

| Field | Type | Description |
|---|---|---|
| `device_type` | `str` | Verified or inferred device type |
| `symptom_category` | `str` | Normalized category (e.g. `no_signal`, `no_audio`, `touch_unresponsive`) |
| `observed_status` | `str` | Current device state observed by user |
| `probable_causes` | `List[str]` | Plausible hypotheses (unconfirmed until verified) |
| `missing_information` | `List[str]` | Variables needed to narrow down cause |
| `original_symptom` | `str` | Preserved original user input |

### DiagnosisResult
The top-level validated Pydantic model.

```json
{
  "decision": "next_step",
  "reasoning_summary": "The projector is powered on, but the input source has not yet been verified against the active laptop connection.",
  "next_step": {
    "action_id": "PROJ_SOURCE_SEARCH",
    "instruction": "Press the 'Source Search' button on the projector remote control or wall panel to select HDMI 1.",
    "reason": "When a laptop is newly plugged in, the projector may still be listening to an inactive input port.",
    "expected_observation": "The projector screen displays your laptop desktop or presentation.",
    "safety_level": "low",
    "requires_confirmation": true
  },
  "question": null,
  "resolution_summary": null,
  "escalation_reason": null,
  "sources": [
    {
      "document_id": "doc-epson-pl2250u",
      "page_number": 48,
      "title": "Epson PowerLite 2250U User's Guide"
    }
  ],
  "uncertainty": "The laptop display output setting (Win+P duplicate) is unconfirmed.",
  "normalized_symptom": {
    "device_type": "projector",
    "symptom_category": "no_signal",
    "observed_status": "Projector powered on with blue LED, displaying 'No Signal'.",
    "probable_causes": [
      "Projector source not set to laptop input port",
      "Laptop display output not enabled (Win+P)",
      "HDMI cable loose at wall plate or laptop"
    ],
    "missing_information": [
      "Active input source selected on projector",
      "Laptop display projection mode"
    ],
    "original_symptom": "The projector turns on and has a blue light, but shows No Signal when I connect my laptop."
  }
}
```

