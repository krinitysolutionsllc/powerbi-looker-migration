# MSTR-to-Looker Repo -- Architecture Reference

Compressed reference for the `strategy-to-looker-migration-tool` repository. Use this as context when building the Power BI-to-Looker migration tool.

---

## Core Philosophy

```
Source (MicroStrategy)  -->  Staging (MariaDB)  -->  Target (Looker)
     Extraction              Transformation           Deployment
     (mstrio-py)             (Python + AI)            (Looker SDK + Git)
```

MariaDB is the central staging layer. Every piece of metadata is extracted into MariaDB first, then transformed/analyzed, then deployed to Looker. This decouples source and target, allows restarts at any stage, and enables rationalization before migration.

---

## Directory Layout

```
lib/
  connectors/          # mstr_connector, looker_connector, mariadb_connection
  db_constants.py      # Tables/Columns classes -- single source of truth for DB names
  utils/               # datetime, enum, type helpers

schema_migration/
  extraction/          # MSTR schema objects -> MariaDB (modeling_* tables)
  lookml_generator/    # MariaDB -> LookML views, model, security filters
  looker_api_deployment/  # LookML -> GitHub -> Looker project

content_migration/
  extraction/          # Reports, dashboards, documents -> MariaDB (content_* tables)
  deployment/          # MariaDB -> Looker Looks, dashboards (scaffold)

user_access_migration/
  migrations/          # Users, groups, roles -> MariaDB (identity_*, access_* tables)
  scripts/             # MariaDB -> Looker users, groups, roles, folders

subscription_migration/
  extraction/          # Schedules, subscriptions -> MariaDB (distribution_* tables)
  deployment/          # MariaDB -> Looker scheduled plans

cube_to_explore/       # OLAP cubes -> PDT-backed Explores
  scripts/             # Extraction, PDT generation, model generation
  expression_matching/ # MSTR metric expression -> SQL column matching

rationalizer/
  extraction/          # Identify unused content + schema objects
  cleanup/             # Delete unused rows from staging tables

prism_bi_agents/       # Google ADK agent orchestration
  agent.py             # Orchestrator (root_agent)
  sub_agents/          # 8 specialist agents
  tools/               # script_tools, db_tools, connection_tools
```

---

## Database Conventions

### Table Prefixes

| Prefix | Domain |
|---|---|
| `identity_` | Users, groups, memberships |
| `access_` | Security roles, privileges, permission mappings |
| `data_` | Projects (top-level containers) |
| `modeling_` | Schema objects (attributes, facts, metrics, filters, tables) |
| `content_` | Reports, dashboards, documents, ACLs |
| `objects_` | OLAP cubes |
| `distribution_` | Subscriptions, schedules |
| `rationalizer_` | Unused object flags |

### Constants Pattern

All table and column names are centralized in `lib/db_constants.py` as `Tables.*` and `Columns.*`. No string literals for DB names in application code.

```python
from lib.db_constants import Tables, Columns

cursor = db.execute(
    f"SELECT {Columns.NAME} FROM {Tables.IDENTITY_USERS} WHERE {Columns.ID} = %s",
    (user_id,)
)
```

### Looker ID Tracking

Every staging table that creates a Looker resource has a `looker_*_id` column (e.g., `looker_user_id`, `looker_group_id`, `looker_folder_id`, `looker_role_id`). This enables idempotent re-runs and teardown.

### Migration Status Tracking

Content and subscription tables use `migration_status` (`pending` -> `deployed` / `skipped` / `failed`) and `migration_notes` columns.

---

## Extraction Pattern

### Structure

Each domain has a `run_all_extractions.py` that calls individual sync functions sequentially:

```python
extraction_steps = [
    ("Attributes", sync_attributes),
    ("Facts", sync_facts),
    ("Metrics", sync_metrics),
]
for name, func in extraction_steps:
    func(project_id=project_id)
```

### Database Write Pattern

- `MariaDBConnection.from_env()` reads `MARIADB_*` env vars.
- Context manager: `with MariaDBConnection.from_env() as db:`.
- Tables created with `CREATE TABLE IF NOT EXISTS`.
- Upserts via `INSERT ... ON DUPLICATE KEY UPDATE`.
- `execute(query, params, dictionary=False, auto_commit=False)` -- supports both tuple and dict cursors.

### Source Connector Pattern

`MicroStrategyConnector` is a context manager wrapping `mstrio-py`:

```python
with MicroStrategyConnector() as mstr:
    users = mstr.fetch_users()
    groups = mstr.fetch_groups()
    projects = mstr.fetch_projects()
```

Credentials from env: `MSTR_BASE_URL`, `MSTR_USERNAME`, `MSTR_PASSWORD`.

---

## LookML Generation Pattern

### Four Stages

1. **Base views** -- One `.view.lkml` per logical table. Attributes become dimensions, facts become measures, simple metrics get direct type mapping.
2. **AI post-processing** -- Gemini translates MSTR SQL functions to BigQuery SQL, converts date attributes to `dimension_group`, fixes count measures.
3. **Complex metrics** -- Batch AI translation via `ai_batch_process_metrics.py`. Results cached in `metrics_ai_cache.json`.
4. **Post-processing** -- Circular reference detection, validation, cleanup.

### Model Generation

- One explore per fact table.
- Auto-joins based on foreign key relationships between logical tables.
- Star schema pattern: fact table at center, dimension tables joined.

### Security Filter Generation

- MSTR security filters -> Looker `access_filter` blocks on explores.
- Uses AI for field matching (MSTR filter qualification -> LookML field reference).
- Generates user attributes for group-based access.

### Source Tracking

Generated LookML includes `# mstr_source: <object_type>:<object_id>` comments. A mapping script parses these into `modeling_schema_lookml_mapping` for field-level lineage.

---

## Deployment Pattern

### Order

1. **Folders** -- One Looker folder per MSTR project.
2. **Users** -- Create in Looker, store `looker_user_id` back to MariaDB.
3. **Groups** -- Create in Looker, store `looker_group_id`.
4. **Roles** -- Permission sets + model sets + roles. Assign roles to groups.
5. **Folder access** -- Set content access (view/edit) per group per folder.
6. **LookML** -- Push to GitHub repo -> Looker project.
7. **Content** -- Create Looks (from reports) and scaffold dashboards. Field mapping via `modeling_schema_lookml_mapping`.
8. **Subscriptions** -- Create Looker scheduled plans from MSTR subscriptions. Resolve users, expand groups, convert schedules to cron.

### Looker Connector Pattern

```python
connector = LookerConnector(config_file="config/looker.ini", section="target")
connector.create_user(user_data)
connector.create_group(group_data)
connector.create_roles(roles_data)
connector.set_folder_access_permissions(folder_access_data)
```

Uses `looker_sdk.init40()`. Config in `config/looker.ini`.

### Idempotency

- Check existence before creation (by title, name, or external ID).
- Only process rows where `migration_status = 'pending'`.
- Store Looker IDs back to MariaDB on success.

### Teardown

Each deployment module has a teardown/cleanup script that reads Looker IDs from MariaDB and deletes created resources.

---

## Rationalization Pattern

### Purpose

Reduce migration scope by identifying unused "zombie" objects.

### Criteria

Object is unused if created > N months ago AND not executed in last N months (default: 13 months).

### Two-Phase

1. **Content rationalization** -- Flag unused reports, dashboards, documents, cubes based on execution history. Store in `rationalizer_unused_objects`.
2. **Schema rationalization** -- Flag metrics/attributes/facts/filters where ALL dependent content is unused. Store in `rationalizer_unused_schema_objects`.

### Cleanup

Destructive delete from staging tables. Content cleanup must run before schema cleanup.

---

## Agent Architecture

### Pattern

Google ADK, hub-and-spoke. All agents use `gemini-2.0-flash`.

### Orchestrator

- Root agent with `runbook_condensed.md` as instruction context.
- Tools: `check_all_connections`, `list_db_tables`, `query_mariadb`.
- Routes to sub-agents based on workflow phase.

### Sub-Agent Definition

```python
agent = Agent(
    name="MetadataExtractionAgent",
    model="gemini-2.0-flash",
    description="...",
    instruction="...",  # Detailed prompt with extraction order, rules, queries
    tools=[run_identity_extraction, run_schema_extraction, ...],
)
```

### Tool Pattern

Tools are Python functions that call migration scripts:

```python
def run_schema_extraction() -> dict:
    return run_migration_script("schema_migration/extraction/run_all_extractions.py")

# run_migration_script executes: uv run python <script_path> [args]
# Returns: {status, exit_code, stdout_tail, stderr_tail}
```

### Handoff Rules

- Sub-agents ONLY return to `prism_bi_orchestrator`.
- No direct agent-to-agent transfers.
- On completion, agents proactively hand back without waiting for user prompt.
- Agents never suggest next workflow phases (orchestrator decides).

### Workflow Order

```
1. Assessment          -- Scope/complexity analysis
2. Parity Gap          -- Platform capability gaps
3. Metadata Extraction -- MSTR -> MariaDB (identity, schema, content, subscriptions, cubes)
4. Rationalization     -- Flag + remove unused objects
5. Configuration       -- Looker users, groups, roles, folders
6. LookML Generation   -- Views, model, security filters -> GitHub
7. Content Deployment  -- Looks, dashboards -> Looker
8. Subscriptions       -- Scheduled plans -> Looker
```

---

## Environment Variables

```
# Source platform
MSTR_BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, MSTR_PROJECT_NAME

# Staging database
MARIADB_HOST, MARIADB_PORT, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE

# Target platform
LOOKER_API_BASE_URL (must end with /), LOOKER_API_CLIENT_ID, LOOKER_API_CLIENT_SECRET
LOOKER_NEW_PROJECT_NAME (optional override)

# Deployment
GITHUB_API_TOKEN, GITHUB_ORG_NAME

# AI
GEMINI_API_KEY
```

All loaded via `python-dotenv` (`load_dotenv()` at module level).

---

## Key Dependencies

```
mstrio-py        # MicroStrategy REST API wrapper
looker-sdk        # Looker API SDK (v4.0)
pymysql           # MariaDB client
python-dotenv     # .env loading
sqlglot           # SQL dialect translation
scipy             # Hungarian algorithm for metric matching
google-adk        # Agent framework
```

Package manager: `uv`. Run scripts with `uv run python <script>`.

---

## Cube-to-Explore Pattern

Specific to MSTR OLAP cubes, but the pattern of SQL-backed PDTs is transferable.

1. **Extract** cube definition + SQL from MSTR.
2. **Convert SQL** from MSTR multi-pass/temp-table pattern to BigQuery CTE pattern.
3. **Match metrics** -- Build expression trees from both MSTR metric definitions and SQL columns, then match using tree comparison + Hungarian algorithm. Confidence scoring: High (>=80%), Review (60-79%), Low (<60%).
4. **Generate PDT view** -- One `.view.lkml` per cube with `derived_table: { sql: ... }`.
5. **Generate model** -- One explore per cube.
