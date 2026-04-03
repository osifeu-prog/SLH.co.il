# DB Change Workflow

Purpose
Safe, repeatable SQL workflow for SLH_PROJECT_V2.

Rules
1. Never run important SQL only from random terminal fragments.
2. Every DB change must exist as a file under ops/sql/.
3. Always run with psql -v ON_ERROR_STOP=1.
4. Always verify the exact rows after execution.
5. Never store DB passwords or full connection strings in repo files.
6. Use UTF-8 without BOM and LF.

Preflight
Before any SQL change:
1. Ensure DATABASE_URL exists in current shell.
2. Ensure PGCLIENTENCODING=UTF8.
3. Ensure psql is available.
4. Ensure the SQL file exists.
5. Prefer .\ops\db-run.ps1.

Execution
.\ops\db-run.ps1 .\ops\sql\<file>.sql

Verification
For user-facing text values:
1. SELECT key, value_text
2. SELECT length(value_text)
3. SELECT encode(convert_to(value_text, 'UTF8'), 'hex')
4. Validate in app runtime, not only in psql console output

Review gate before external testers
- Python compile passes
- worker starts cleanly
- store flow works
- order flow works
- admin payment review works
- no secret leaked to repo