# Pensioner Portal (pension_mgmt) -- context for future work

Part of the IFMS prototype suite (4 independent apps under `E:\IFMS`): Employee Portal, Pensioner
Portal, Vendor Portal, and a back-office Admin Portal that talks to all three over their APIs.
Modeled on a GNCTD-style pensioner self-service SRS (bank-account change requests, benefit claims,
life certificate submission, arrears/grievances, tax declarations).

## Stack & ports
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL. Runs on **:9002**.
- Frontend: React (Vite) + Tailwind CSS (strictly Tailwind, no inline CSS). Runs on **:7002**.
- DB: `postgresql+psycopg2://pension_portal:pension_portal@localhost:5432/pension_portal` (see
  `backend/.env`).
- No migrations tool -- `Base.metadata.create_all()` on startup creates missing tables only.

## Non-negotiable project conventions (apply to every portal, not just this one)
- Keep code simple enough for a junior dev to follow -- no premature abstraction.
- Tailwind CSS only, never inline `style=` CSS.
- Every table has `AuditMixin`: `is_active`, `is_deleted`, `server_date`, `operation_date`.
- Boolean DB columns stay native SQLAlchemy `Boolean` -- **do not** convert to `VARCHAR(1)` Y/N.
  Explicitly proposed and explicitly rejected project-wide; see `emp_mgmt_pro/CONTEXT.md` for the
  full reasoning if this comes up again.
- Hand-drawn SVG icons only, no icon library, no emoji.
- Never run git/GitHub commands yourself -- always give the user the exact command to run.

## Auth pattern (same shape in every portal, including admin_portal)
Two-step JWT login: `POST /auth/login` (field is `ppo_number`, not email/username -- pensioners log
in by PPO number + password) returns a `pending_token` -> `POST /auth/verify-otp` (any 6 digits
accepted) returns the `access_token`. bcrypt used directly.

## Key backend modules
- `app/models.py` -- `Pensioner`, `BankChangeRequest`, `BenefitClaimRequest`, `Grievance`,
  `LifeCertificate`, arrears/tax records, `AuditLog`.
- `app/events.py` / `app/routers/audit.py` / `app/routers/reports.py` -- same pattern as
  emp_mgmt_pro: `log_action()` writes an audit row, reports router has `_status_counts()` +
  approver-only pipeline reports + a `my-summary` for any pensioner.
- `app/routers/approver.py` -- `GET /approver/queue` returns items tagged with `item_type`
  (`"bank_request"` or `"benefit_claim"`), reviewed via **separate** endpoints:
  `POST /approver/bank-requests/{id}/review` and `POST /approver/benefit-claims/{id}/review` (unlike
  emp_mgmt_pro's single generic `/approver/{kind}/{id}/review`). **admin_portal's
  `integrations.py` depends on this exact shape** -- don't change it without updating that file too.

## Frontend notes
- Custom bilingual i18n, no library, but a **different** pattern from emp_mgmt_pro: `src/i18n/hi.js`
  uses the English text itself as the dictionary key, with fallback-to-key on a miss (rather than
  emp's short symbolic keys). Don't assume the two i18n systems are interchangeable.
- `src/pages/ApplicationDateField.jsx` -- same shared component concept as emp_mgmt_pro, styled to
  match this app's own English-text-as-key `t()` calls. Present on every request/claim/register form.
- Approver grievance-queue cards show both a "Lodged" and a "Due" date -- Lodged was added later to
  match the "application date must be visible" requirement.

## Reviewer / approver accounts
No auto-seeded demo pensioner accounts -- register via the Register form. A HOD/approver-role test
account (`ppo_number=PPO/2026/OFFICER1`, password `test123`) was created manually during testing and
is now also used as **admin_portal's service account credential** (see
`admin_portal/backend/.env`, `PENSION_SERVICE_*`). Keep them in sync if this account changes.

## Status (as of 2026-09-03)
Reports/MIS and Audit Log implemented and tested (mirrored from vendor_mgmt). Application Date is on
every form and result table. ~85% of SRS-derived functional coverage by the project owner's informal
estimate; remaining gaps are mostly real-integration items intentionally out of scope for a
prototype (real bank-account/PPO verification is mocked, not a live API call).

## Related
See `E:\IFMS\admin_portal\CONTEXT.md` for how the back-office Admin Portal calls into this app's
`/approver/*` endpoints via a service account, and `E:\IFMS\TESTING_GUIDE.md` for cross-portal
end-to-end test steps.
