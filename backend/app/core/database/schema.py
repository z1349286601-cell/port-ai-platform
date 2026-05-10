"""
Phase 1a database DDL for production / equipment / energy / sessions domains.
Chinese schema descriptions are used by NL2SQL schema_extractor.py.
"""

# ============================================================
# Domain-level schema descriptions (used in NL2SQL prompts)
# ============================================================

SCHEMA_DESCRIPTIONS = {
    "production": "生产运营数据库，包含船舶、集装箱、泊位、堆场、闸口、工班、作业等港口核心业务数据",
    "equipment": "设备运维数据库，包含设备台账、运行状态、IOT监控等数据",
    "energy": "能源环保数据库，包含电力消耗、新能源发电、碳排放等数据",
    "sessions": "系统会话库，存储用户会话和对话消息",
}

# ============================================================
# Table-level Chinese descriptions
# ============================================================

TABLE_DESCRIPTIONS = {
    "dim_berth": "泊位维度表，记录港口泊位的基本属性，如泊位编号、最大吃水深度、长度、是否可用",
    "dim_vessel": "船舶维度表，记录船舶基本信息，如船名、IMO编号、船型、总吨位、载重吨",
    "dim_yard_block": "堆场区块维度表，记录堆场区块编号、类型（集装箱/散货/滚装）、容量",
    "dim_gate_lane": "闸口车道维度表，记录闸口编号、车道类型（进口/出口）、是否启用",
    "dim_device_type": "设备类型维度表，记录设备类型编码和名称，如岸桥、场桥、叉车、传送带",
    "dim_device": "设备维度表，记录港口设备台账，如岸桥、门机、传送带的型号、厂家、安装日期",
    "dim_energy_type": "能源类型维度表，记录电力、燃油、天然气等能源分类",

    "fact_container": "集装箱当前状态快照表，记录每个集装箱的当前位置、箱型、状态、关联船舶、在场天数",
    "fact_vessel_schedule": "船舶计划事实表，记录船舶预计到港/靠泊/离泊时间，每条记录=一次靠泊计划",
    "fact_vessel_operation": "船舶作业事实表，记录每次吊具移动，每条记录=一次move",
    "fact_shift_progress": "工班进度事实表，记录各班次各泊位各船的作业进度",
    "fact_gate_transaction": "闸口通行事实表，记录每辆车的进出闸记录",
    "fact_device_operation": "设备运行事实表，记录设备每次启停、运行时长、故障信息",
    "fact_iot_monitor": "设备IOT监控快照表，记录设备温度、振动等传感器日快照数据",
    "fact_electricity_daily": "日电耗事实表，记录每日各部门、各区域的电力消耗",

    "agg_operation_volume_daily": "每日作业量汇总表，按日期+泊位+船型预聚合的吞吐量统计",
    "agg_yard_occupancy_daily": "每日堆场占用汇总表，按日期+区块预聚合的在场箱量",

    "sessions": "会话表，记录用户会话元数据",
    "messages": "消息表，记录会话中的对话消息",
}

# ============================================================
# production.db DDL
# ============================================================

PRODUCTION_DDL = """

PRAGMA foreign_keys = ON;

-- dim_berth: 泊位维度表
CREATE TABLE IF NOT EXISTS dim_berth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berth_code TEXT NOT NULL UNIQUE,
    berth_name TEXT NOT NULL,
    max_draft REAL NOT NULL COMMENT '最大吃水深度（米）',
    length REAL NOT NULL COMMENT '泊位长度（米）',
    berth_type TEXT NOT NULL CHECK(berth_type IN ('CONTAINER','BULK','RO_RO','GENERAL')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- dim_vessel: 船舶维度表
CREATE TABLE IF NOT EXISTS dim_vessel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vessel_code TEXT NOT NULL UNIQUE,
    vessel_name_cn TEXT NOT NULL,
    vessel_name_en TEXT,
    imo_no TEXT,
    vessel_type TEXT NOT NULL CHECK(vessel_type IN ('CONTAINER','BULK','RO_RO','TANKER','GENERAL')),
    gross_tonnage REAL COMMENT '总吨位',
    deadweight_ton REAL COMMENT '载重吨（吨）',
    teu_capacity INTEGER COMMENT '标箱容量（TEU）',
    ship_company TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- dim_yard_block: 堆场区块维度表
CREATE TABLE IF NOT EXISTS dim_yard_block (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_code TEXT NOT NULL UNIQUE,
    block_name TEXT NOT NULL,
    block_type TEXT NOT NULL CHECK(block_type IN ('CONTAINER','BULK','RO_RO','DANGEROUS','REEFER')),
    capacity_teu INTEGER COMMENT '容量（TEU）',
    max_tier INTEGER DEFAULT 5 COMMENT '最大堆存层数',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- dim_gate_lane: 闸口车道维度表
CREATE TABLE IF NOT EXISTS dim_gate_lane (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lane_code TEXT NOT NULL UNIQUE,
    lane_name TEXT NOT NULL,
    lane_type TEXT NOT NULL CHECK(lane_type IN ('INBOUND','OUTBOUND')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_container: 集装箱当前状态快照（缓变快照，UPSERT模式）
CREATE TABLE IF NOT EXISTS fact_container (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_code TEXT NOT NULL UNIQUE,
    container_type TEXT NOT NULL CHECK(container_type IN ('DRY_20','DRY_40','DRY_45','REEFER_20','REEFER_40','DANGEROUS','FLAT_RACK','OPEN_TOP','TANK')),
    container_status TEXT NOT NULL CHECK(container_status IN ('ON_SITE','DISCHARGED','LOADED')),
    current_bay TEXT COMMENT '当前贝位',
    yard_block_code TEXT REFERENCES dim_yard_block(block_code),
    vessel_code TEXT COMMENT '关联船舶',
    entry_time TEXT COMMENT '进港时间',
    on_site_days INTEGER DEFAULT 0 COMMENT '在场天数',
    is_dangerous INTEGER NOT NULL DEFAULT 0,
    dangerous_class TEXT,
    customs_status TEXT CHECK(customs_status IN ('CLEARED','PENDING','INSPECTION')),
    container_owner TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_vessel_schedule: 船舶计划事实表
CREATE TABLE IF NOT EXISTS fact_vessel_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id TEXT NOT NULL UNIQUE,
    vessel_code TEXT NOT NULL REFERENCES dim_vessel(vessel_code),
    berth_code TEXT NOT NULL REFERENCES dim_berth(berth_code),
    eta TEXT NOT NULL COMMENT '预计到港时间',
    etb TEXT COMMENT '预计靠泊时间',
    etd TEXT COMMENT '预计离泊时间',
    voyage_in TEXT COMMENT '进口航次',
    voyage_out TEXT COMMENT '出口航次',
    status TEXT NOT NULL CHECK(status IN ('SCHEDULED','BERTHED','DEPARTED','CANCELLED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_vessel_operation: 船舶作业事实表（每次move一条记录）
CREATE TABLE IF NOT EXISTS fact_vessel_operation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL UNIQUE,
    vessel_code TEXT NOT NULL REFERENCES dim_vessel(vessel_code),
    berth_code TEXT NOT NULL REFERENCES dim_berth(berth_code),
    container_code TEXT,
    move_type TEXT NOT NULL CHECK(move_type IN ('DISCHARGE','LOAD','RESTACK')),
    move_time TEXT NOT NULL COMMENT '作业时间',
    crane_id TEXT COMMENT '岸桥编号',
    shift TEXT COMMENT '班次（DAY/NIGHT）',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_shift_progress: 工班进度事实表
CREATE TABLE IF NOT EXISTS fact_shift_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_date TEXT NOT NULL,
    shift TEXT NOT NULL CHECK(shift IN ('DAY','NIGHT')),
    vessel_code TEXT NOT NULL REFERENCES dim_vessel(vessel_code),
    berth_code TEXT NOT NULL REFERENCES dim_berth(berth_code),
    planned_moves INTEGER NOT NULL DEFAULT 0,
    completed_moves INTEGER NOT NULL DEFAULT 0,
    progress_pct REAL DEFAULT 0 COMMENT '进度百分比',
    crane_cnt INTEGER DEFAULT 1 COMMENT '作业岸桥数',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_gate_transaction: 闸口通行事实表
CREATE TABLE IF NOT EXISTS fact_gate_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL UNIQUE,
    lane_code TEXT NOT NULL REFERENCES dim_gate_lane(lane_code),
    container_code TEXT,
    truck_plate TEXT NOT NULL,
    gate_time TEXT NOT NULL COMMENT '过闸时间',
    direction TEXT NOT NULL CHECK(direction IN ('IN','OUT')),
    vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('CONTAINER_TRUCK','BULK_TRUCK','FLATBED','SERVICE')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- agg_operation_volume_daily: 每日作业量汇总
CREATE TABLE IF NOT EXISTS agg_operation_volume_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,
    berth_code TEXT NOT NULL REFERENCES dim_berth(berth_code),
    vessel_type TEXT NOT NULL,
    discharge_cnt INTEGER DEFAULT 0 COMMENT '卸船箱量',
    load_cnt INTEGER DEFAULT 0 COMMENT '装船箱量',
    total_moves INTEGER DEFAULT 0 COMMENT '总move数',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- agg_yard_occupancy_daily: 每日堆场占用汇总
CREATE TABLE IF NOT EXISTS agg_yard_occupancy_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,
    block_code TEXT NOT NULL REFERENCES dim_yard_block(block_code),
    container_cnt INTEGER DEFAULT 0 COMMENT '在场箱量',
    occupancy_pct REAL DEFAULT 0 COMMENT '占用率百分比',
    dangerous_cnt INTEGER DEFAULT 0 COMMENT '危险品箱数量',
    reefr_cnt INTEGER DEFAULT 0 COMMENT '冷藏箱数量',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fact_container_code ON fact_container(container_code);
CREATE INDEX IF NOT EXISTS idx_fact_container_block ON fact_container(yard_block_code);
CREATE INDEX IF NOT EXISTS idx_fact_container_vessel ON fact_container(vessel_code);
CREATE INDEX IF NOT EXISTS idx_fact_container_status ON fact_container(container_status);
CREATE INDEX IF NOT EXISTS idx_fact_schedule_vessel ON fact_vessel_schedule(vessel_code);
CREATE INDEX IF NOT EXISTS idx_fact_schedule_berth ON fact_vessel_schedule(berth_code);
CREATE INDEX IF NOT EXISTS idx_fact_schedule_eta ON fact_vessel_schedule(eta);
CREATE INDEX IF NOT EXISTS idx_fact_operation_vessel ON fact_vessel_operation(vessel_code);
CREATE INDEX IF NOT EXISTS idx_fact_shift_progress_date ON fact_shift_progress(shift_date);
CREATE INDEX IF NOT EXISTS idx_fact_gate_time ON fact_gate_transaction(gate_time);
"""

# ============================================================
# equipment.db DDL
# ============================================================

EQUIPMENT_DDL = """

PRAGMA foreign_keys = ON;

-- dim_device_type: 设备类型维度表
CREATE TABLE IF NOT EXISTS dim_device_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code TEXT NOT NULL UNIQUE,
    type_name TEXT NOT NULL,
    category TEXT COMMENT '设备大类',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- dim_device: 设备维度表
CREATE TABLE IF NOT EXISTS dim_device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT NOT NULL UNIQUE,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK(device_type IN ('CRANE','VEHICLE','CONVEYOR','VESSEL','OTHER')),
    model TEXT,
    manufacturer TEXT,
    install_date TEXT,
    design_life_year INTEGER COMMENT '设计寿命（年）',
    health_score REAL DEFAULT 100 COMMENT '健康评分（0-100）',
    status TEXT NOT NULL CHECK(status IN ('RUNNING','STANDBY','FAULT','MAINTENANCE')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_device_operation: 设备运行事实表
CREATE TABLE IF NOT EXISTS fact_device_operation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL UNIQUE,
    device_code TEXT NOT NULL REFERENCES dim_device(device_code),
    start_time TEXT NOT NULL,
    end_time TEXT,
    running_hours REAL DEFAULT 0 COMMENT '运行小时数',
    status TEXT NOT NULL CHECK(status IN ('RUNNING','STOPPED','FAULT','MAINTENANCE')),
    fault_code TEXT,
    fault_desc TEXT,
    operator_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_iot_monitor: 设备IOT监控日快照
CREATE TABLE IF NOT EXISTS fact_iot_monitor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_date TEXT NOT NULL,
    device_code TEXT NOT NULL REFERENCES dim_device(device_code),
    temperature REAL COMMENT '温度（℃）',
    vibration REAL COMMENT '振动值（mm/s）',
    current_a REAL COMMENT '电流（A）',
    power_kw REAL COMMENT '功率（kW）',
    is_abnormal INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fact_device_op_code ON fact_device_operation(device_code);
CREATE INDEX IF NOT EXISTS idx_fact_device_op_time ON fact_device_operation(start_time);
CREATE INDEX IF NOT EXISTS idx_fact_iot_device ON fact_iot_monitor(device_code);
CREATE INDEX IF NOT EXISTS idx_fact_iot_date ON fact_iot_monitor(monitor_date);
"""

# ============================================================
# energy.db DDL
# ============================================================

ENERGY_DDL = """

PRAGMA foreign_keys = ON;

-- dim_energy_type: 能源类型维度表
CREATE TABLE IF NOT EXISTS dim_energy_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    energy_code TEXT NOT NULL UNIQUE,
    energy_name TEXT NOT NULL,
    energy_category TEXT NOT NULL CHECK(energy_category IN ('ELECTRICITY','FUEL','GAS','WATER','RENEWABLE')),
    unit TEXT NOT NULL COMMENT '计量单位（kWh/吨/立方米）',
    co2_factor REAL COMMENT '碳排放因子',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- fact_electricity_daily: 日电耗事实表
CREATE TABLE IF NOT EXISTS fact_electricity_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,
    dept_code TEXT NOT NULL COMMENT '部门编码',
    dept_name TEXT COMMENT '部门名称',
    consumption_kwh REAL NOT NULL DEFAULT 0 COMMENT '用电量（kWh）',
    peak_kwh REAL DEFAULT 0 COMMENT '峰时用电',
    valley_kwh REAL DEFAULT 0 COMMENT '谷时用电',
    pv_generation_kwh REAL DEFAULT 0 COMMENT '光伏发电量',
    wind_generation_kwh REAL DEFAULT 0 COMMENT '风力发电量',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fact_elec_date ON fact_electricity_daily(stat_date);
CREATE INDEX IF NOT EXISTS idx_fact_elec_dept ON fact_electricity_daily(dept_code);
"""

# ============================================================
# sessions.db DDL
# ============================================================

SESSIONS_DDL = """

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    channel TEXT NOT NULL DEFAULT 'web',
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    title TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived','deleted')),
    message_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    intent TEXT,
    sources TEXT COMMENT 'JSON array of source citations',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
"""

# ============================================================
# Domain → DDL mapping
# ============================================================

DOMAIN_DDL_MAP = {
    "production": PRODUCTION_DDL,
    "equipment": EQUIPMENT_DDL,
    "energy": ENERGY_DDL,
    "sessions": SESSIONS_DDL,
}
