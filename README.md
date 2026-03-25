# Power BI → Looker migration

Goal: build tooling to automate as much of the migration as practical (extract → MariaDB staging → Looker).

## Directory structure

```
powerBI-looker-migration/
├── README.md
├── AGENTS.md                       # AI + human: migration lens & current environment (tenant/dev)
├── docs/
│   ├── migration-source-of-truth.md  # Project brain: scope, workflows, agents, decisions
│   ├── mstr-looker-repo-reference.md
│   └── runbook.md
├── data_samples/
│   └── AdventureWorksSales.json    # Sample semantic model (BIM-style JSON)
├── lib/
│   └── power_bi_client.py          # PowerBIAppClient / PowerBIUserClient (MSAL + httpx)
├── main.py                         # Minimal example: list workspaces (groups) via REST
├── .env.example                    # Env var names and placeholders (safe to commit)
├── .env                            # Local secrets (not committed; copy from .env.example)
└── .gitignore
```

## Architecture diagram

High-level flow and components: **[Lucidchart — migration architecture](https://lucid.app/lucidchart/a4f92d43-915f-4da9-a6f7-eb5ebf5e6890/edit?viewport_loc=4770%2C3989%2C959%2C2557%2C0_0&invitationId=inv_efa6f103-d06d-497c-87e3-54170df63f42)** (Lucidchart; sign-in may be required).

## Where to read

| Doc                                                                            | Purpose                                                                                                                                                   |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[AGENTS.md](./AGENTS.md)** | **Agent & environment brief:** PBI→Looker framing, editable **current tenant/dev** tables (admin, Fabric, Pro, XMLA, etc.). Cursor rules point here. |
| **[docs/migration-source-of-truth.md](./docs/migration-source-of-truth.md)** | **Single source of truth** (“project brain”): diagrams, **migration workflows**, content mapping, APIs, extraction, MariaDB schema, DAX→LookML, **pipeline** (Section 6), **agents** (Section 7), PPU, glossary. Start here for what is being built and why. |
| **[docs/mstr-looker-repo-reference.md](./docs/mstr-looker-repo-reference.md)** | **Implementation patterns** from the MicroStrategy sibling repo (directories, extraction scripts, deployment order). Use when coding; not a PBI tutorial. |
| [docs/runbook.md](./docs/runbook.md)                                           | Mac dev, **env vars**, Power BI REST clients, how to run `main.py`.                                                                                       |

## Local setup (current repo)

1. Install **[uv](https://github.com/astral-sh/uv)** (or use your own Python 3.13+ and `pip install -e .`).
2. Copy **`.env.example`** → **`.env`** and set at least **`AZURE_CLIENT_ID`** and **`AZURE_TENANT_ID`**. Add **`AZURE_SECRET_VALUE`** only if you use **`PowerBIAppClient`** (service principal).
3. Run **`uv run main.py`** — today this calls the Power BI REST API to list **workspaces** (`GET .../myorg/groups`) using the client wired in `main.py`.

See **[docs/runbook.md](./docs/runbook.md)** for **user vs app** auth (why `groups` can be empty for an app) and Entra app registration notes.

**Implementation note:** Core paths are **deterministic Python** (extract → stage → transform → deploy). The source-of-truth doc (Sections 6–7) defines callable pipeline steps and the eight agent roles; orchestration should wrap those entry points, not replace them with ad hoc LLM logic.
