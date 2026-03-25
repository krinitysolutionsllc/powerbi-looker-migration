"""Central table and column names for MariaDB staging — use in SQL, no ad hoc literals."""


class Tables:
    DATA_WORKSPACES = "data_workspaces"
    CONTENT_REPORTS = "content_reports"
    CONTENT_REPORT_PAGES = "content_report_pages"
    SEMANTIC_DATASETS = "semantic_datasets"
    DATASET_REFRESH_SCHEDULES = "dataset_refresh_schedules"
    DATASET_DATASOURCES = "dataset_datasources"
    DATASET_REFRESHES = "dataset_refreshes"
    CONTENT_DASHBOARDS = "content_dashboards"
    CONTENT_DASHBOARD_TILES = "content_dashboard_tiles"
    CONTENT_DATAFLOWS = "content_dataflows"
    IDENTITY_WORKSPACE_ACCESS = "identity_workspace_access"


class Cols:
    # shared
    ID = "id"
    WORKSPACE_ID = "workspace_id"
    PAYLOAD_JSON = "payload_json"
    SYNCED_AT = "synced_at"
    API_CREATED_AT = "api_created_at"
    API_MODIFIED_AT = "api_modified_at"
    NAME = "name"
    DESCRIPTION = "description"
    DISPLAY_NAME = "display_name"

    # data_workspaces
    IS_READ_ONLY = "is_read_only"
    IS_ON_DEDICATED_CAPACITY = "is_on_dedicated_capacity"
    CAPACITY_ID = "capacity_id"
    TYPE = "type"
    STATE = "state"

    # content_reports
    WEB_URL = "web_url"
    EMBED_URL = "embed_url"
    DATASET_ID = "dataset_id"
    REPORT_TYPE = "report_type"
    IS_FROM_PBIX = "is_from_pbix"
    DATASET_WORKSPACE_ID = "dataset_workspace_id"
    APP_ID = "app_id"
    ORIGINAL_REPORT_ID = "original_report_id"
    CREATED_DATE = "created_date"
    MODIFIED_DATE = "modified_date"

    # content_report_pages
    REPORT_ID = "report_id"
    PAGE_NAME = "page_name"
    PAGE_ORDER = "page_order"

    # semantic_datasets
    ADD_ROWS_API_ENABLED = "add_rows_api_enabled"
    CONFIGURED_BY = "configured_by"
    IS_REFRESHABLE = "is_refreshable"
    IS_EFFECTIVE_IDENTITY_REQUIRED = "is_effective_identity_required"
    IS_EFFECTIVE_IDENTITY_ROLES_REQUIRED = "is_effective_identity_roles_required"
    TARGET_STORAGE_MODE = "target_storage_mode"
    CONTENT_PROVIDER_TYPE = "content_provider_type"

    # dataset_refresh_schedules
    ENABLED = "enabled"
    DAYS = "days"
    TIMES = "times"
    LOCAL_TIME_ZONE_ID = "local_time_zone_id"
    NOTIFY_OPTION = "notify_option"

    # dataset_datasources
    DATASOURCE_ID = "datasource_id"
    GATEWAY_ID = "gateway_id"
    DATASOURCE_TYPE = "datasource_type"
    CONNECTION_DETAILS_JSON = "connection_details_json"

    # dataset_refreshes
    REFRESH_REQUEST_ID = "refresh_request_id"
    REFRESH_TYPE = "refresh_type"
    STATUS = "status"
    START_TIME = "start_time"
    END_TIME = "end_time"
    SERVICE_EXCEPTION_JSON = "service_exception_json"

    # content_dashboards

    # content_dashboard_tiles
    DASHBOARD_ID = "dashboard_id"
    TITLE = "title"
    SUB_TITLE = "sub_title"
    TILE_ROW = "tile_row"
    TILE_COL = "tile_col"
    TILE_WIDTH = "tile_width"
    TILE_HEIGHT = "tile_height"

    # content_dataflows
    OBJECT_ID = "object_id"

    # identity_workspace_access
    IDENTIFIER = "identifier"
    PRINCIPAL_TYPE = "principal_type"
    EMAIL_ADDRESS = "email_address"
    GRAPH_ID = "graph_id"
    ACCESS_RIGHT = "access_right"
    USER_TYPE = "user_type"
