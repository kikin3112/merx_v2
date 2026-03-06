# chandelierp: CRM Module Master Plan (v1.0)

**Date:** 2026-02-13
**Objective:** Implement a **Manual CRM Module** within the existing chandelierp ERP. This module functions as a distinct extension for commercial management, leveraging existing data (Clients/Users) without altering core ERP logic.

> **Scope Note:** This roadmap explicitly excludes AI/LLM features. The focus is on operational efficiency, manual control, and reporting.

---

## 1. The Core Concept: "Deal Flow System"

We are not building a "Contacts DB" (that is `Terceros`). We are building a system to manage the **Sales Process**.

### Core Features (MVP)
1.  **Pipeline Management:** Configurable sales workflows (e.g., "New Sales", "Renewals").
2.  **Deal Tracking:** Visual management of opportunities (Kanban).
3.  **Unified Activity Feed:** A chronologically ordered history of Notes, Calls, Emails, and Tasks linked to a Deal.

---

## 2. Technical Architecture & Schema

### New Tables (`app.datos.modelos_crm`)

#### 1. `crm_pipelines` & `crm_stages`
Defines the process.
*   **Pipeline:** `id`, `nombre`, `is_default`
*   **Stage:** `pipeline_id`, `nombre` (e.g., "Qualified"), `probabilidad` (%), `orden`

#### 2. `crm_deals` (The core entity)
*   **Links:** `tercero_id` (Client), `usuario_id` (Owner), `stage_id` (Current Status).
*   **Data:** `nombre`, `valor_estimado` (Numeric), `fecha_cierre_estimada`.
*   **Status:** `estado_cierre` (OPEN, WON, LOST).

#### 3. `crm_activities` (The history)
*   **Links:** `deal_id`, `usuario_id`.
*   **Data:** `tipo` (CALL, EMAIL, NOTE, MEETING), `contenido` (Text), `fecha`.

---

## 3. Implementation Roadmap

### Phase 1: Database Foundation
*   [ ] Create `backend/app/datos/modelos_crm.py`.
*   [ ] Generate Alembic migration: `add_crm_module_tables`.
*   [ ] Apply migration to DB.
*   [ ] Verify Relationship integrity (Deals <-> Terceros).

### Phase 2: Backend Logic (API)
*   [ ] **Service Layer (`crm_service.py`):**
    *   `create_deal(data)`
    *   `move_deal(deal_id, new_stage_id)` -> Updates stage and log activity.
    *   `add_activity(deal_id, type, content)`
*   [ ] **API Routes (`rutas/crm.py`):**
    *   `GET /crm/pipelines`: Full tree of Pipelines -> Stages.
    *   `POST /crm/deals`: Create new opportunity.
    *   `GET /crm/deals`: List with filters (Pipeline, Owner).
    *   `PATCH /crm/deals/{id}/stage`: Drag & drop handler.
    *   `POST /crm/deals/{id}/activities`: Log interaction.

### Phase 3: Frontend Interface
*   [ ] **Kanban Board Component:**
    *   Columns = Stages.
    *   Cards = Deals (Show Name, Value, Client).
    *   Drag & Drop to move cards.
*   [ ] **Deal Detail View (Modal/Page):**
    *   **Header:** Status, Value, Close Date.
    *   **Left Panel:** Client Info (from `Terceros`).
    *   **Right Panel:** Activity Feed (List of events + "Add Note" form).
*   [ ] **Quick Actions:**
    *   "Convert to Quote" button (Future integration with `Cotizaciones`).

### Phase 4: Reporting & Automation (No AI)
*   [ ] **Funnel Analytics:**
    *   Conversion Rate (Lead -> Won).
    *   Drop-off analysis (Where do we lose deals?).
*   [ ] **Sales Velocity:** Average days to close.
*   [ ] **Basic Automation:**
    *   *Trigger:* Deal moves to "Won" -> *Action:* Email notification to Finance.
    *   *Trigger:* Deal moves to "Proposal" -> *Action:* Create "Follow-up" task.

---

## 4. Immediate Next Steps
1.  Execute **Phase 1** (Schema & Migrations).
2.  Review Database structure.
3.  Begin **Phase 2** (API Development).
