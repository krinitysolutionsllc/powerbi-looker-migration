-- Power BI REST staging (workspace-scoped). Apply once: mariadb ... < sql/schema.sql
-- Charset for JSON and names
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS data_workspaces (
    id CHAR(36) NOT NULL,
    name VARCHAR(512) NULL,
    is_read_only TINYINT(1) NULL,
    is_on_dedicated_capacity TINYINT(1) NULL,
    capacity_id CHAR(36) NULL,
    `type` VARCHAR(64) NULL,
    state VARCHAR(64) NULL,
    payload_json LONGTEXT NOT NULL,
    api_created_at DATETIME(6) NULL,
    api_modified_at DATETIME(6) NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_data_workspaces_synced (synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_reports (
    id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    name VARCHAR(512) NULL,
    web_url VARCHAR(2048) NULL,
    embed_url VARCHAR(2048) NULL,
    dataset_id CHAR(36) NULL,
    report_type VARCHAR(64) NULL,
    is_from_pbix TINYINT(1) NULL,
    description TEXT NULL,
    dataset_workspace_id CHAR(36) NULL,
    app_id CHAR(36) NULL,
    original_report_id CHAR(36) NULL,
    created_date DATETIME(6) NULL,
    modified_date DATETIME(6) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_content_reports_workspace (workspace_id),
    KEY idx_content_reports_dataset (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_report_pages (
    report_id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    page_name VARCHAR(512) NOT NULL,
    display_name VARCHAR(512) NULL,
    page_order INT NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (report_id, page_name),
    KEY idx_report_pages_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS semantic_datasets (
    id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    name VARCHAR(512) NULL,
    add_rows_api_enabled TINYINT(1) NULL,
    configured_by VARCHAR(512) NULL,
    is_refreshable TINYINT(1) NULL,
    is_effective_identity_required TINYINT(1) NULL,
    is_effective_identity_roles_required TINYINT(1) NULL,
    target_storage_mode VARCHAR(64) NULL,
    content_provider_type VARCHAR(128) NULL,
    created_date DATETIME(6) NULL,
    modified_date DATETIME(6) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_semantic_datasets_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dataset_refresh_schedules (
    dataset_id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    enabled TINYINT(1) NULL,
    days VARCHAR(512) NULL,
    times VARCHAR(1024) NULL,
    local_time_zone_id VARCHAR(256) NULL,
    notify_option VARCHAR(128) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (dataset_id),
    KEY idx_dataset_refresh_sched_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dataset_datasources (
    dataset_id CHAR(36) NOT NULL,
    datasource_id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    gateway_id CHAR(36) NULL,
    datasource_type VARCHAR(256) NULL,
    connection_details_json LONGTEXT NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (dataset_id, datasource_id),
    KEY idx_dataset_datasources_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dataset_refreshes (
    dataset_id CHAR(36) NOT NULL,
    refresh_request_id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    refresh_type VARCHAR(64) NULL,
    status VARCHAR(64) NULL,
    start_time DATETIME(6) NULL,
    end_time DATETIME(6) NULL,
    service_exception_json LONGTEXT NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (dataset_id, refresh_request_id),
    KEY idx_dataset_refreshes_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_dashboards (
    id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    display_name VARCHAR(512) NULL,
    embed_url VARCHAR(2048) NULL,
    is_read_only TINYINT(1) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_content_dashboards_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_dashboard_tiles (
    id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    dashboard_id CHAR(36) NOT NULL,
    report_id CHAR(36) NULL,
    dataset_id CHAR(36) NULL,
    title VARCHAR(1024) NULL,
    sub_title VARCHAR(1024) NULL,
    embed_url VARCHAR(2048) NULL,
    tile_row INT NULL,
    tile_col INT NULL,
    tile_width INT NULL,
    tile_height INT NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_dashboard_tiles_dashboard (dashboard_id),
    KEY idx_dashboard_tiles_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_dataflows (
    object_id CHAR(36) NOT NULL,
    workspace_id CHAR(36) NOT NULL,
    name VARCHAR(512) NULL,
    description TEXT NULL,
    configured_by VARCHAR(512) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (object_id),
    KEY idx_content_dataflows_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS identity_workspace_access (
    workspace_id CHAR(36) NOT NULL,
    identifier VARCHAR(256) NOT NULL,
    principal_type VARCHAR(32) NULL,
    display_name VARCHAR(512) NULL,
    email_address VARCHAR(512) NULL,
    graph_id VARCHAR(128) NULL,
    access_right VARCHAR(64) NULL,
    user_type VARCHAR(64) NULL,
    payload_json LONGTEXT NOT NULL,
    synced_at DATETIME(6) NOT NULL,
    PRIMARY KEY (workspace_id, identifier),
    KEY idx_identity_ws_access_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
