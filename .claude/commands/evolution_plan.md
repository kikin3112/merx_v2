# SaaS Control Center 2026: Evolution Plan

**Date:** December 2025 (Simulated)
**Target:** Superadmin Control Center (SaaS)

## 1. Executive Summary
The current Control Center is functionally solid, handling core tenant lifecycle (CRUD, Plans, Basic States). To align with "State of the Art" standards for late 2025, we propose evolving it into a **Proactive Command Center**.

The key shift is from **"Management"** (reactive data entry) to **"Governance & Observability"** (proactive monitoring, security, and granular control).

## 2. Gap Analysis

| Feature Area | Current Status | 2025 Standard (Gap) |
| :--- | :--- | :--- |
| **Tenant Access** | Tenant CRUD, User Roles | **Impersonation** ("Ghost Mode") for support. |
| **Audit/Security** | Row-level (`updated_by`) | **Immutable Activity Logs** (Who did what, when). |
| **Feature Control** | Plan-based `config` (JSON) | **Granular Feature Flags** per tenant (Plan overrides). |
| **Observability** | Basic Stats (Count) | **Health Scoring** ("Pulse") & Usage trends. |
| **Lifecycle** | Status (Active/Suspended) | **Maintenance Mode**, Onboarding Checklists. |
| **Billing** | Payment History | **Invoice Management**, Dunning control. |

## 3. Proposed Evolution: The "2026 Standard"

### 3.1 Identity Surrogate ("Ghost Mode")
**Goal:** Allow Superadmins to log in *as* a specific tenant user to reproduce bugs or configure settings, without asking for passwords.

*   **Implementation:** 
    *   Backend: `POST /tenants/{id}/impersonate/{user_id}` returns a short-lived, high-privilege JWT.
    *   **Security Critical:** 
        *   Must require re-authentication (MFA preferred) to initiate.
        *   **Visual Indicator:** A persistent "You are impersonating X" banner on the frontend to prevent mistakes.
        *   **Audit:** The session must be strictly logged as `Actor: Superadmin`, `Target: User`, `Action: Impersonate`.

### 3.2 Sentinel: Centralized Audit Logs
**Goal:** A "Flight Recorder" for the SaaS. Essential for compliance (SOC2) and security.

*   **Implementation:**
    *   New Table: `audit_logs` (global).
    *   Fields: `actor_id`, `tenant_id` (optional), `action` (e.g., `tenant.update`, `user.impersonate`), `resource_id`, `changes` (JSON diff), `ip_address`, `user_agent`.
    *   **Features:**
        *   UI: Searchable history in Tenant Detail view.
        *   Export: CSV/JSON export for compliance.
        *   Immutability: Ensure logs cannot be deleted via standard UI.

### 3.3 Granular Feature Flags (Plan Overrides)
**Goal:** Decouple "Code Deployment" from "Feature Release" and allow custom deals.

*   **Implementation:**
    *   Enhance `tenants.configuracion` or add `tenant_features` table.
    *   Logic: `EffectiveFeatures = PlanFeatures + TenantOverrides`.
    *   **Use Case:** Enable "Beta Module" for just *one* tenant, or disable a specific feature for a tenant with payment issues without suspending the whole account.

### 3.4 Tenant "Pulse" (Health Scoring)
**Goal:** Predict churn before it happens.

*   **Implementation:**
    *   Aggregated score (0-100) based on:
        *   **Login Frequency**: Are they using the app?
        *   **Core Actions**: (e.g., Invoices created, Products added).
        *   **Support Tickets**: High volume?
        *   **Payment Status**: Late payments?
    *   **UI:** Color-coded badges (Healthy/At-Risk/Critical) in the main list.

### 3.5 Operational States
**Goal:** Better control during incidents or offboarding.

*   **Maintenance Mode:**
    *   Tenant state where users can *login* and *read* data, but **cannot write** (POST/PUT/DELETE blocked).
    *   Useful for: Data migrations, non-payment soft-blocks, offboarding.

### 3.6 Financial Operations Center
**Goal:** Full visibility into billing beyond just "Paid/Unpaid".

*   **Features:**
    *   View/Download generated Invoice PDFs.
    *   Manual "Credit Note" or "Refund" actions.
    *   **Dunning Management:** See email retry status for failed payments.

### 3.7 Total Control: User Governance ("God Mode")
**Goal:** Complete lifecycle management of *any* user, independent of tenants.

*   **Gap:** Currently, admins can only manage users *within* a tenant. Cannot create "orphan" users or edit global profiles (email/password).
*   **Implementation:**
    *   **Global User CRUD:** New view "All Users" to create/edit users directly.
    *   **Force Password Reset:** Trigger email or manually set password hash (emergency).
    *   **MFA Management:** Reset/Disable MFA for locked-out users.
    *   **Session Kill:** Force logout for specific users.

## 4. Implementation roadmap (Suggestions)

1.  **Phase 1 (Security Core):** Implement **Audit Logs** (middleware based) and **Impersonation** (with audit integration).
2.  **Phase 2 (Observability):** Implement **Health Pulse** calculation job and UI indicators.
3.  **Phase 3 (Control):** Implement **Maintenance Mode** and **Granular Feature Flags**.

This research aligns with the "Control Center" vision, transforming it from a list of tenants into a powerful governance tool.
