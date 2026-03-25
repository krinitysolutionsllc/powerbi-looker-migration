# Runbook — Power BI to Looker Migration Tool

**Jira:** [BIP-1074](https://66degrees.atlassian.net/browse/BIP-1074).

Scope, workflows, and agents: **[migration-source-of-truth.md](./migration-source-of-truth.md)**.

**Environment (admin, Fabric, Pro, etc.):** maintain **[AGENTS.md](../AGENTS.md)** (section *Current environment*) so tooling and AI guidance stay accurate.

---

## What works today

| Piece | Role |
|-------|------|
| **`lib/power_bi_client.py`** | **`PowerBIAppClient`**: client-credentials (app id + tenant + **client secret**) → bearer token for `https://analysis.windows.net/powerbi/api/.default`. **`PowerBIUserClient`**: interactive delegated sign-in (browser), same scope; optional cache file **`.msal_token_cache.json`** (gitignored). |
| **`main.py`** | Example script: loads **`.env`**, opens one of the clients, calls **`GET https://api.powerbi.com/v1.0/myorg/groups`** (list workspaces), prints JSON. Switch between clients by commenting/uncommenting the `with` blocks in `main.py`. |
| **`extraction/*.py`** | Service-principal REST extractors → MariaDB: workspaces, reports (+ pages), datasets (+ refresh schedule, datasources, refresh history), dashboards (+ tiles), dataflows, workspace users. **`extraction/run_all.py`** runs them in order. |
| **`sql/schema.sql`** | Creates staging tables (apply once to your MariaDB database). |
| **`lib/mariadb_client.py`** | **`MariaDBClient.from_env()`** context manager: **`.cursor()`**, **`.execute(sql, params)`**, **`.connection`** for the raw driver connection; commit/rollback on block exit. |
| **`lib/db_constants.py`** | Table and column name constants for SQL (no string literals in scripts). |
| **Dependencies** | **`httpx`**, **`msal`**, **`python-dotenv`**, **`mariadb`** (see **`pyproject.toml`**). Run with **`uv run main.py`** or **`uv run python extraction/run_all.py`** from the repo root. |

### Ruff (lint + format)

The repo uses **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting (dev dependency in **`pyproject.toml`** `[dependency-groups].dev`).

| Command | Purpose |
|--------|---------|
| `uv run ruff check .` | Lint the tree |
| `uv run ruff format .` | Apply formatter |

Settings live under **`[tool.ruff]`** in **`pyproject.toml`**: **`I`** (isort-style import order), **`UP`** (pyupgrade), **`E`/`F`/`B`**, **`known-first-party`** = `extraction`, `lib`, **`line-length`** = 100, **`E501`** ignored (long docstrings / strings are not forced to wrap).

**`extraction/*.py`:** each script prepends the repo root to **`sys.path`** so `from lib...` works when the file is run directly. Imports therefore come *after* that bootstrap, so **`E402`** (import not at top of file) is **ignored for `extraction/*.py`** via **`per-file-ignores`**. **`extraction/run_all.py`** imports local extractors in **alphabetical module order** (`extract_dashboards`, `extract_dataflows`, …) to match isort.

**Workspace list empty with `PowerBIAppClient`?** The token represents the **service principal**. `groups` only returns workspaces where that app is a **member or admin** (and tenant settings allow SP use). It does **not** see your personal **My workspace** as *you*. Use **`PowerBIUserClient`** to list workspaces as your user, or add the SP to each shared workspace (see **AGENTS.md** constraints).

### No Power BI admin APIs: workspace-scoped inventory

If you **cannot** use admin endpoints (Scanner, `admin/*`, tenant-wide catalog), the practical workaround is:

1. **Add the automation service principal to every shared workspace** you care about (Member or Admin, per org policy).
2. Call **`GET https://api.powerbi.com/v1.0/myorg/groups`** — the returned workspaces are your **entire migration “instance”** for that principal (not the full tenant).
3. For each `groupId`, call **group-scoped** APIs only, for example:
   - `GET .../myorg/groups/{groupId}/reports`
   - `GET .../myorg/groups/{groupId}/datasets`
   - `GET .../myorg/groups/{groupId}/dashboards`
   - `GET .../myorg/groups/{groupId}/dataflows`

**Why not `GET .../myorg/reports`?** That route lists **[My workspace](https://learn.microsoft.com/en-us/rest/api/power-bi/reports/get-reports)** for the **signed-in identity**. A **service account / service principal** does not have a normal user **My workspace** in that sense, so the unscoped call often returns **HTTP 403** (or is otherwise unusable) even when `GET .../groups/{groupId}/reports` works for workspaces where the SP is a member.

**Current environment:** see **AGENTS.md** — this repo assumes **no** admin APIs and **Fabric-backed shared workspaces** (sample content) reachable only via the SP + `groups` pattern above.

---

## Environment variables

Copy **`.env.example`** to **`.env`** (never commit **`.env`**).

| Variable | Required for | Purpose |
|----------|----------------|---------|
| `AZURE_CLIENT_ID` | Both clients | Entra application (client) ID |
| `AZURE_TENANT_ID` | Both clients | Entra directory (tenant) ID |
| `AZURE_SECRET_VALUE` | **`PowerBIAppClient` only** | Client secret **value** (not the secret ID) |
| `MARIADB_HOST` | Extraction scripts | MariaDB host (e.g. `127.0.0.1` or tunnel) |
| `MARIADB_PORT` | Optional (default `3306`) | Port |
| `MARIADB_USER` | Extraction scripts | Database user |
| `MARIADB_PASSWORD` | Extraction scripts | Database password |
| `MARIADB_DATABASE` | Extraction scripts | Database name (schema applied via **`sql/schema.sql`**) |

**Staging load:** apply **`sql/schema.sql`** once, set **`MARIADB_*`** and Azure vars in **`.env`**, then run **`uv run python extraction/run_all.py`** (or run individual scripts under **`extraction/`**). Rows are **upserted** (`ON DUPLICATE KEY UPDATE`); **`synced_at`** is set each run; API **`modifiedDate`** / **`modifiedDateTime`** (where returned) are stored in **`modified_date`** / **`created_date`** columns on the relevant tables.

For **`PowerBIUserClient`**, register a **public client** redirect URI (e.g. **Mobile and desktop** → `http://localhost`) in Entra and grant **delegated** Power BI API permissions as needed for the calls you make.

---

## Developing on Mac (without Power BI Desktop)

You **do not need Power BI Desktop** to build or run the agents. All access is via cloud APIs:

| Need | How on Mac |
|------|------------|
| **REST API** (workspaces, reports, datasets, export) | HTTP; use a **service principal** (Azure Entra app) with Power BI permissions. Works from any OS. |
| **Scanner API** (tenant metadata) | Same auth as REST; admin scope. Chunk workspaces (≤100), poll for scan result. |
| **XMLA** (relationships, RLS, DMVs) | Connect to `powerbi://api.powerbi.com/...` from Python with **pytabular**. On PPU use a PPU-licensed service account; on Fabric/Premium a service principal can be used. |
| **pbi-tools** (PBIX/PBIR extraction) | **Core edition** is cross-platform; requires **.NET 8** on Mac. Operates on local files only (e.g. PBIX obtained via REST export elsewhere). |

**To develop without live Power BI calls:** use local samples (e.g. **`data_samples/`**, extracted PBIX folders) and keep REST code behind the clients in **`lib/power_bi_client.py`**. Microsoft’s Power BI REST docs cover auth, permissions, and endpoints for each operation you add next.