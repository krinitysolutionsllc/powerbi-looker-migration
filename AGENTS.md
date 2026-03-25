# Agent instructions

Humans: keep the **Current environment** section accurate so tooling and AI answers match reality.

## Project purpose

This repo is a **Power BI → Looker migration** tool: extract and understand PBI semantic/reporting intent, then hand off to Looker (LookML, explores, etc.).

When answering questions:

- Frame as: *What do we need from PBI to represent this in Looker?*
- **PBI:** Prefer REST inventory, optional DAX execute, PBIX/file paths where allowed. Respect limits in **Current environment** (no Premium/XMLA/admin assumptions unless stated there).
- **Looker:** Assume LookML/product work is handled elsewhere unless the user scopes it here.

## Current environment (edit me)

### Identity & admin

| | |
|--|--|
| **Power BI tenant / Entra admin** | No |
| **Power BI admin REST (Scanner, `admin/*`, tenant-wide inventory)** | No |
| **Can grant admin consent for apps** | No (depends on IT) |
| **Day-to-day auth for tooling** | User account (delegated / interactive) where needed; **automation uses a service principal** on specific workspaces |

### Licensing & platform (Power BI)

| | |
|--|--|
| **Fabric** | Yes — **two** shared workspaces the service account can access (sample models/reports live there); not tenant-wide |
| **Premium / PPU (workspace on Premium)** | No (except as implied by those Fabric workspaces) |
| **Pro** | Yes |
| **XMLA read/write (typical)** | Workspace-dependent; assume **off** unless confirmed for those workspaces |

### Automation

| | |
|--|--|
| **Service principal (app + secret) for REST** | Yes — SP is **added as member/admin to each shared workspace** to migrate. **`GET /groups`** lists only those workspaces; treat that list as the whole **instance scope** (workaround for no admin APIs). |
| **Scanner API / admin inventory** | No — requires Power BI admin |

### Development

| | |
|--|--|
| **OS** | macOS |
| **Lint / format** | **Ruff** — `uv run ruff check .` / `uv run ruff format .`; see **`pyproject.toml`** and **`docs/runbook.md`** (*Ruff*) |
| **Looker side** | Handled separately (this repo focuses on PBI extract + migration inputs) |

### Notes

- **REST pattern:** After `GET /groups`, call resource APIs with a **group id**: e.g. `GET /groups/{groupId}/reports`, `.../datasets`, etc. Do **not** rely on **`GET /reports`** (and similar **unscoped** “my org” content routes): those target **[My workspace](https://learn.microsoft.com/en-us/rest/api/power-bi/reports/get-reports)** for a **user** identity; a service account typically has **no** usable My workspace there, so unscoped calls often return **403** or misleading empties.
- _Add bullets here: app registration name, consent status, workspace names/ids you can access (no secrets)._

## Other docs

| Doc | Use |
|-----|-----|
| `docs/migration-source-of-truth.md` | Scope, workflows, agents |
| `docs/runbook.md` | Mac dev, API surfaces, pbi-tools, MariaDB extraction |
| `lib/power_bi_client.py` | `PowerBIAppClient` / `PowerBIUserClient` |
| `lib/mariadb_client.py` | `MariaDBClient.from_env()` |
| `lib/db_constants.py` | Staging table/column names |
| `sql/schema.sql` | MariaDB staging DDL |
| `extraction/` | REST → MariaDB scripts (`run_all.py`) |

If **Current environment** is missing a fact, state assumptions explicitly in answers.
