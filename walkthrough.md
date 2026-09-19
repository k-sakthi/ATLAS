# ATLAS Stage 2 Monitor Implementation Report

## 1. Files Created
- `stage1/atlas.py` (Compatibility adapter)
- `stage2/crew.py` (Orchestrator and 6 nodes)
- `stage2/models.py` (Pydantic models for Stage 2)
- `stage2/memory.py` (Persistent memory layer)
- `stage2/api.py` (FastAPI router for Stage 2)
- `tests/test_stage2.py` (Pytest suite for Stage 2)
- `frontend/src/app/monitor/page.tsx` (Human Gate UI)
- `frontend/src/app/monitor/cycle/page.tsx` (Cycle Execution & Report UI)
- `frontend/src/app/monitor/queries/page.tsx` (Active Data Queries UI)
- `frontend/src/app/monitor/trace/page.tsx` (Trace Log UI)
- `frontend/patch_study.py` (Patch script used to safely inject events into the Study 360 profile)

## 2. Files Modified
- `app/main.py`: Mounted the `stage2.api` router under `/api/v1/stage2`.
- `frontend/src/components/Sidebar.tsx`: Added a new "Monitor (Stage 2)" navigation section.
- `frontend/src/app/study-360/[subjectId]/page.tsx`: Dynamically fetches and renders Stage 2 Escalations and Queries in the subject timeline.

## 3. Stage 1 Untouched
- All deterministic rules in `app/analysis.py` remain untouched.
- All CSV loading and correction logic in `app/repository.py` remains untouched.
- No modifications were made to the original clinical calculations.

## 4. Stage 2 Architecture
- **Adapter**: `stage1/atlas.py` cleanly maps the existing deterministic FastAPI outputs to simple python dicts.
- **Orchestration**: `stage2/crew.py` runs the 6 required nodes linearly.
- **Memory**: `stage2/memory.py` writes to a local `data/stage2_memory.json` file ensuring cycle state (queries, escalations, flags) persists between runs.
- **API**: Exposed through the existing FastAPI application, retaining a single cohesive backend process.

## 5. Six Node Implementation
1. **Detect**: Uses unchanged `atlas` adapter to fetch all deterministically calculated SAEs, Hy's Law, Dosing Errors, Protocol Deviations, and Exclusions for a given cut.
2. **Medical Review**: Implements specific logic to escalate miscoded SAEs (`AESHOSP=Y` but `AESER=N`) and ignores known-baseline Hy's Law candidates.
3. **Data Manager**: Maps genuine dosing issues to targeted queries.
4. **Compliance**: Audits remaining deviations and prohibited meds for the current cut and protocol version.
5. **Human Gate**: Allows manual review overrides on escalations (Approve, Reject, Clarify). Rejections downgrade to monitor permanently.
6. **Execute**: Compiles statistics across the run and outputs a trace of all decisions.

## 6. Memory Design
Memory persists between cycle invocations to prevent exact duplicate alerts:
- A data issue generates **1 query** ever, tracked across runs.
- A rejected escalation is **never blindly re-escalated** on subsequent runs.
- Tracks `cycle_count` sequentially, storing open queries, site flags, and past escalation decisions.

## 7. Human Gate Implementation
The `/monitor` UI reads all `PENDING` escalations. Users can click:
- **Approve Action**: Moves state to `APPROVED`, flagged as executed.
- **Downgrade to Monitor**: Moves state to `REJECTED`, preventing future re-escalation.
- **Clarify Evidence**: Opens a prompt to submit a question.

## 8. CLARIFY Implementation
When CLARIFY is requested via the Human Gate:
- State is set to `CLARIFY`.
- The `human_gate` node (in the next simulated pass) automatically reads the question, fetches deterministic data from the graph (no hallucination), answers it, and sets the escalation back to `PENDING` for final Approval/Rejection. 
- The clarification history is visibly retained in the UI.

## 9. API Endpoints Created
- `POST /api/v1/stage2/run`
- `GET /api/v1/stage2/report/{cycle}`
- `GET /api/v1/stage2/trace/{cycle}`
- `GET /api/v1/stage2/escalations`
- `GET /api/v1/stage2/queries`
- `POST /api/v1/stage2/escalations/{id}/decision`

## 10. Frontend Pages
- `/monitor`: Modern "Human Gate" review center with explicit evidence exposure.
- `/monitor/cycle`: The main command interface to launch a new ReviewCrew cycle by cut and protocol version, with live trace and statistics.
- `/monitor/queries`: Dedicated pane for all open Site Queries.
- `/monitor/trace`: Trace history browser.
- `/study-360/[subjectId]`: Expanded to inject Stage 2 review history alongside deterministic lab/AE events.

## 11. Playwright Results
- **Pass**: Navigated `/monitor/cycle`, clicked "Execute Cycle" successfully.
- **Pass**: Navigated to `/monitor` (Human Gate), verified UI renders smoothly.
- **Pass**: Navigated to `/study-360/042-S02-004`, verified subject timeline loads without errors.
- **Pass**: 0 hydration or NextJS compile errors detected.

## 12. Pytest Results
- 31 passing tests (24 existing Stage 1 tests + 7 new Stage 2 tests).
- Verified: SAE same-cycle escalation, AESHOSP/AESER miscoding, empty cycle traces, zero duplicate query logic, site-level recurrent flag logic, human gate approve/reject memory logic, and human gate clarify resubmission.

## 13. Screenshots Created
- `cycle_report` (Cycle Dashboard displaying findings and trace)
- `human_gate` (Pending escalations queue)
- `study_360` (Updated subject profile timeline)

## 14. Known Limitations
- Data queries are currently just saved in JSON memory; they aren't actively dispatched to external site servers.
- The `stage1/atlas.py` adapter runs everything dynamically; if dataset gets to terabytes, `detect` may take seconds rather than milliseconds.

## Running the Application
BACKEND:
`uvicorn app.main:app --reload`
(Running on http://127.0.0.1:8000)

FRONTEND:
`cd frontend && npm run dev`
(Running on http://localhost:3000)
