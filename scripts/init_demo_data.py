"""
Phase 1a demo data initialization.
Creates SQLite databases with seed data for production, equipment, energy domains.
Run: python scripts/init_demo_data.py
"""

import sqlite3
import os
import random
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sqlite")
os.makedirs(DATA_DIR, exist_ok=True)

random.seed(42)
NOW = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
DAYS_BACK = 60


def create_db(name):
    path = os.path.join(DATA_DIR, f"{name}.db")
    # Retry file removal in case of lock contention (Windows)
    for attempt in range(5):
        try:
            if os.path.exists(path):
                os.remove(path)
            break
        except PermissionError:
            if attempt < 4:
                time.sleep(0.5)
            else:
                raise
    # Also clean up WAL/SHM files
    for suffix in ("-wal", "-shm"):
        wal_path = path + suffix
        try:
            if os.path.exists(wal_path):
                os.remove(wal_path)
        except OSError:
            pass
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ============================================================
# production.db
# ============================================================
def init_production():
    conn = create_db("production")

    conn.executescript("""
    CREATE TABLE dim_berth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        berth_code TEXT NOT NULL UNIQUE,
        berth_name TEXT NOT NULL,
        max_draft REAL NOT NULL,
        length REAL NOT NULL,
        berth_type TEXT NOT NULL CHECK(berth_type IN ('CONTAINER','BULK','RO_RO','GENERAL')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE dim_vessel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vessel_code TEXT NOT NULL UNIQUE,
        vessel_name_cn TEXT NOT NULL,
        vessel_name_en TEXT,
        imo_no TEXT,
        vessel_type TEXT NOT NULL CHECK(vessel_type IN ('CONTAINER','BULK','RO_RO','TANKER','GENERAL')),
        gross_tonnage REAL,
        deadweight_ton REAL,
        teu_capacity INTEGER,
        ship_company TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE dim_yard_block (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_code TEXT NOT NULL UNIQUE,
        block_name TEXT NOT NULL,
        block_type TEXT NOT NULL CHECK(block_type IN ('CONTAINER','BULK','RO_RO','DANGEROUS','REEFER')),
        capacity_teu INTEGER,
        max_tier INTEGER DEFAULT 5,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE dim_gate_lane (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lane_code TEXT NOT NULL UNIQUE,
        lane_name TEXT NOT NULL,
        lane_type TEXT NOT NULL CHECK(lane_type IN ('INBOUND','OUTBOUND')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_container (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_code TEXT NOT NULL UNIQUE,
        container_type TEXT NOT NULL CHECK(container_type IN ('DRY_20','DRY_40','DRY_45','REEFER_20','REEFER_40','DANGEROUS','FLAT_RACK','OPEN_TOP','TANK')),
        container_status TEXT NOT NULL CHECK(container_status IN ('ON_SITE','DISCHARGED','LOADED')),
        current_bay TEXT,
        yard_block_code TEXT,
        vessel_code TEXT,
        entry_time TEXT,
        on_site_days INTEGER DEFAULT 0,
        is_dangerous INTEGER NOT NULL DEFAULT 0,
        dangerous_class TEXT,
        customs_status TEXT CHECK(customs_status IN ('CLEARED','PENDING','INSPECTION')),
        container_owner TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_vessel_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id TEXT NOT NULL UNIQUE,
        vessel_code TEXT NOT NULL,
        berth_code TEXT NOT NULL,
        eta TEXT NOT NULL,
        etb TEXT,
        etd TEXT,
        voyage_in TEXT,
        voyage_out TEXT,
        status TEXT NOT NULL CHECK(status IN ('SCHEDULED','BERTHED','DEPARTED','CANCELLED')),
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_vessel_operation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id TEXT NOT NULL UNIQUE,
        vessel_code TEXT NOT NULL,
        berth_code TEXT NOT NULL,
        container_code TEXT,
        move_type TEXT NOT NULL CHECK(move_type IN ('DISCHARGE','LOAD','RESTACK')),
        move_time TEXT NOT NULL,
        crane_id TEXT,
        shift TEXT CHECK(shift IN ('DAY','NIGHT')),
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_shift_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_date TEXT NOT NULL,
        shift TEXT NOT NULL CHECK(shift IN ('DAY','NIGHT')),
        vessel_code TEXT NOT NULL,
        berth_code TEXT NOT NULL,
        planned_moves INTEGER NOT NULL DEFAULT 0,
        completed_moves INTEGER NOT NULL DEFAULT 0,
        progress_pct REAL DEFAULT 0,
        crane_cnt INTEGER DEFAULT 1,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_gate_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL UNIQUE,
        lane_code TEXT NOT NULL,
        container_code TEXT,
        truck_plate TEXT NOT NULL,
        gate_time TEXT NOT NULL,
        direction TEXT NOT NULL CHECK(direction IN ('IN','OUT')),
        vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('CONTAINER_TRUCK','BULK_TRUCK','FLATBED','SERVICE')),
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE agg_operation_volume_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_date TEXT NOT NULL,
        berth_code TEXT NOT NULL,
        vessel_type TEXT NOT NULL,
        discharge_cnt INTEGER DEFAULT 0,
        load_cnt INTEGER DEFAULT 0,
        total_moves INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE agg_yard_occupancy_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_date TEXT NOT NULL,
        block_code TEXT NOT NULL,
        container_cnt INTEGER DEFAULT 0,
        occupancy_pct REAL DEFAULT 0,
        dangerous_cnt INTEGER DEFAULT 0,
        reefr_cnt INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # dim_berth
    berths = [
        ("B01", "1号泊位", 16.5, 350, "CONTAINER"),
        ("B02", "2号泊位", 16.5, 350, "CONTAINER"),
        ("B03", "3号泊位", 14.0, 300, "BULK"),
        ("B04", "4号泊位", 12.0, 280, "GENERAL"),
    ]
    conn.executemany(
        "INSERT INTO dim_berth (berth_code, berth_name, max_draft, length, berth_type) VALUES (?,?,?,?,?)",
        berths,
    )

    # dim_vessel
    vessels = [
        ("COSCO-STAR", "中远海运恒星", "COSCO STAR", "IMO9400123", "CONTAINER", 120000, 140000, 10000, "中远海运"),
        ("COSCO-MOON", "中远海运月亮", "COSCO MOON", "IMO9400456", "CONTAINER", 110000, 130000, 8500, "中远海运"),
        ("MSC-BEIJING", "地中海北京号", "MSC BEIJING", "IMO9500123", "CONTAINER", 150000, 180000, 14000, "MSC"),
        ("MAERSK-SHANGHAI", "马士基上海号", "MAERSK SHANGHAI", "IMO9600345", "CONTAINER", 140000, 170000, 13000, "马士基"),
        ("OOCL-TIANJIN", "东方海外天津号", "OOCL TIANJIN", "IMO9700678", "CONTAINER", 90000, 110000, 8000, "OOCL"),
        ("EVER-GREEN", "长荣绿洲", "EVER GREEN", "IMO9800901", "CONTAINER", 100000, 120000, 9000, "Evergreen"),
        ("PACIFIC-BULK", "太平洋散货", "PACIFIC BULK", "IMO9900234", "BULK", 80000, 100000, 0, "太平洋航运"),
        ("GOLDEN-GRAIN", "金色谷物号", "GOLDEN GRAIN", "IMO8500567", "BULK", 60000, 80000, 0, "中粮国际"),
        ("AUTO-EXPRESS", "汽车快线", "AUTO EXPRESS", "IMO9920890", "RO_RO", 50000, 30000, 0, "NYK Line"),
        ("SEA-CHEM", "海化号", "SEA CHEM", "IMO9800902", "TANKER", 70000, 90000, 0, "Stolt-Nielsen"),
    ]
    conn.executemany(
        "INSERT INTO dim_vessel (vessel_code, vessel_name_cn, vessel_name_en, imo_no, vessel_type, gross_tonnage, deadweight_ton, teu_capacity, ship_company) VALUES (?,?,?,?,?,?,?,?,?)",
        vessels,
    )

    # dim_yard_block
    yard_blocks = [
        ("A01", "A区01排", "CONTAINER", 300, 5),
        ("A02", "A区02排", "CONTAINER", 300, 5),
        ("A03", "A区03排", "CONTAINER", 300, 5),
        ("B01", "B区01排", "REEFER", 80, 4),
        ("B02", "B区02排", "CONTAINER", 250, 5),
        ("C01", "C区01排", "DANGEROUS", 100, 3),
        ("D01", "D区-散货堆场", "BULK", 0, 2),
        ("E01", "E区-滚装场地", "RO_RO", 200, 2),
        ("F01", "F区01排", "CONTAINER", 280, 5),
        ("F02", "F区02排", "CONTAINER", 280, 5),
    ]
    conn.executemany(
        "INSERT INTO dim_yard_block (block_code, block_name, block_type, capacity_teu, max_tier) VALUES (?,?,?,?,?)",
        yard_blocks,
    )

    # dim_gate_lane
    lanes = [
        ("IN-1", "进口1号道", "INBOUND"),
        ("IN-2", "进口2号道", "INBOUND"),
        ("OUT-1", "出口1号道", "OUTBOUND"),
        ("OUT-2", "出口2号道", "OUTBOUND"),
        ("OUT-3", "出口3号道", "OUTBOUND"),
    ]
    conn.executemany(
        "INSERT INTO dim_gate_lane (lane_code, lane_name, lane_type) VALUES (?,?,?)",
        lanes,
    )

    # fact_container (~200 rows)
    container_types = ["DRY_20", "DRY_40", "DRY_45", "REEFER_20", "REEFER_40", "DANGEROUS", "FLAT_RACK"]
    statuses = ["ON_SITE"] * 85 + ["DISCHARGED"] * 10 + ["LOADED"] * 5
    active_blocks = [b[0] for b in yard_blocks if b[0] not in ("D01", "E01")]
    bay_zones = [f"A-{r:02d}-{t:02d}" for r in range(1, 6) for t in range(1, 6)]
    owners = ["中远海运", "MSC", "马士基", "OOCL", "CMA CGM", "中粮", "Hapag-Lloyd", "ONE", "万海"]
    vessel_codes = [v[0] for v in vessels if v[4] == "CONTAINER"]

    containers = []
    for i in range(200):
        code = f"BC-{i+1:03d}"
        ctype = random.choice(container_types)
        status = random.choice(statuses)
        block = random.choice(active_blocks)
        bay = random.choice(bay_zones)
        vessel = random.choice(vessel_codes) if status != "ON_SITE" and random.random() > 0.3 else ""
        days_ago = random.randint(0, 30)
        entry = (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")
        on_site = days_ago if status == "ON_SITE" else random.randint(0, days_ago)
        is_dangerous = 1 if ctype == "DANGEROUS" or (random.random() < 0.05) else 0
        dclass = random.choice(["1.4G", "2.1", "3", "4.1", "5.1", "6.1", "8", "9"]) if is_dangerous else None
        containers.append((code, ctype, status, bay, block, vessel, entry, on_site, is_dangerous, dclass,
                           random.choice(["CLEARED", "PENDING", "INSPECTION"]), random.choice(owners)))
    conn.executemany(
        "INSERT INTO fact_container (container_code, container_type, container_status, current_bay, yard_block_code, vessel_code, entry_time, on_site_days, is_dangerous, dangerous_class, customs_status, container_owner) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        containers,
    )

    # fact_vessel_schedule (~30 rows)
    schedules = []
    for i in range(30):
        sid = f"SCH-{i+1:04d}"
        vessel = random.choice(vessel_codes[:6])
        berth = "B01" if vessel in ("COSCO-STAR", "MSC-BEIJING") else random.choice(["B01", "B02", "B03", "B04"])
        days_fwd = random.randint(-10, 14)
        eta = (NOW + timedelta(days=days_fwd) + timedelta(hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M")
        etb = (NOW + timedelta(days=days_fwd) + timedelta(hours=random.randint(1, 4))).strftime("%Y-%m-%d %H:%M") if days_fwd >= 0 else (NOW - timedelta(days=-days_fwd)).strftime("%Y-%m-%d %H:%M")
        etd = (NOW + timedelta(days=days_fwd) + timedelta(hours=random.randint(12, 36))).strftime("%Y-%m-%d %H:%M") if days_fwd >= 0 else (NOW + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d %H:%M")
        status = "SCHEDULED" if days_fwd > 0 else ("BERTHED" if days_fwd >= -3 else random.choice(["DEPARTED", "DEPARTED", "DEPARTED", "CANCELLED"]))
        schedules.append((sid, vessel, berth, eta, etb, etd, f"V{i+1:03d}N", f"V{i+1:03d}S", status))
    conn.executemany(
        "INSERT INTO fact_vessel_schedule (schedule_id, vessel_code, berth_code, eta, etb, etd, voyage_in, voyage_out, status) VALUES (?,?,?,?,?,?,?,?,?)",
        schedules,
    )

    # fact_vessel_operation (~500 rows)
    operations = []
    for i in range(500):
        oid = f"OP-{i+1:06d}"
        vessel = random.choice(vessel_codes[:6])
        berth = "B01" if vessel in ("COSCO-STAR", "MSC-BEIJING") else random.choice(["B01", "B02"])
        days_ago = random.randint(0, 14)
        move_time = (NOW - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
        move_type = random.choice(["DISCHARGE"] * 4 + ["LOAD"] * 4 + ["RESTACK"] * 2)
        container = f"BC-{random.randint(1,200):03d}"
        crane = random.choice(["QC-01", "QC-02", "QC-03"])
        shift = "DAY" if random.randint(8, 19) else "NIGHT"
        operations.append((oid, vessel, berth, container, move_type, move_time, crane, shift))
    conn.executemany(
        "INSERT INTO fact_vessel_operation (operation_id, vessel_code, berth_code, container_code, move_type, move_time, crane_id, shift) VALUES (?,?,?,?,?,?,?,?)",
        operations,
    )

    # fact_shift_progress (~40 rows)
    progress = []
    for d in range(14):
        date_str = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
        for shift in ("DAY", "NIGHT"):
            for vessel in random.sample(vessel_codes[:4], 2):
                planned = random.randint(80, 200)
                completed = random.randint(0, planned)
                pct = round(completed / planned * 100, 1)
                berth = random.choice(["B01", "B02"])
                progress.append((date_str, shift, vessel, berth, planned, completed, pct, random.randint(1, 3)))
    conn.executemany(
        "INSERT INTO fact_shift_progress (shift_date, shift, vessel_code, berth_code, planned_moves, completed_moves, progress_pct, crane_cnt) VALUES (?,?,?,?,?,?,?,?)",
        progress,
    )

    # fact_gate_transaction (~200 rows, ensure today has data)
    gates = []
    # Reserve ~40 transactions for today
    today_start = NOW.strftime("%Y-%m-%d")
    for i in range(40):
        tid = f"GT-TODAY-{i+1:04d}"
        lane = random.choice([l[0] for l in lanes])
        direction = "IN" if lane.startswith("IN") else "OUT"
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        gt = f"{today_start} {hour:02d}:{minute:02d}"
        truck = f"鲁B{random.randint(10000,99999)}"
        vtype = random.choice(["CONTAINER_TRUCK"] * 7 + ["BULK_TRUCK"] * 2 + ["FLATBED"])
        container = f"BC-{random.randint(1,200):03d}" if vtype == "CONTAINER_TRUCK" else None
        gates.append((tid, lane, container, truck, gt, direction, vtype))
    # Remaining ~160 distributed over past 30 days
    for i in range(160):
        tid = f"GT-{i+1:06d}"
        lane = random.choice([l[0] for l in lanes])
        direction = "IN" if lane.startswith("IN") else "OUT"
        days_ago = random.randint(1, 30)
        hour = random.randint(0, 23)
        gt = (NOW - timedelta(days=days_ago, hours=hour, minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
        truck = f"鲁B{random.randint(10000,99999)}"
        vtype = random.choice(["CONTAINER_TRUCK"] * 7 + ["BULK_TRUCK"] * 2 + ["FLATBED"])
        container = f"BC-{random.randint(1,200):03d}" if vtype == "CONTAINER_TRUCK" else None
        gates.append((tid, lane, container, truck, gt, direction, vtype))
    conn.executemany(
        "INSERT INTO fact_gate_transaction (transaction_id, lane_code, container_code, truck_plate, gate_time, direction, vehicle_type) VALUES (?,?,?,?,?,?,?)",
        gates,
    )

    # agg_operation_volume_daily (~60 rows)
    agg_ops = []
    for d in range(60):
        date_str = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
        for berth in ("B01", "B02"):
            discharge = random.randint(50, 200)
            load = random.randint(50, 200)
            agg_ops.append((date_str, berth, "CONTAINER", discharge, load, discharge + load))
    conn.executemany(
        "INSERT INTO agg_operation_volume_daily (stat_date, berth_code, vessel_type, discharge_cnt, load_cnt, total_moves) VALUES (?,?,?,?,?,?)",
        agg_ops,
    )

    # agg_yard_occupancy_daily (~240 rows)
    agg_yard = []
    container_blocks = [b[0] for b in yard_blocks if b[2] == "CONTAINER"]
    for d in range(30):
        date_str = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
        for block in container_blocks:
            cnt = random.randint(100, 280)
            cap = next((b[3] for b in yard_blocks if b[0] == block), 300)
            pct = round(cnt / cap * 100, 1)
            agg_yard.append((date_str, block, cnt, pct, random.randint(0, 10), random.randint(0, 5)))
    conn.executemany(
        "INSERT INTO agg_yard_occupancy_daily (stat_date, block_code, container_cnt, occupancy_pct, dangerous_cnt, reefr_cnt) VALUES (?,?,?,?,?,?)",
        agg_yard,
    )

    conn.commit()
    conn.close()
    print(f"  production.db: {len(berths)} berths, {len(vessels)} vessels, {len(containers)} containers, {len(schedules)} schedules, {len(operations)} ops, {len(gates)} gate txns")


# ============================================================
# equipment.db
# ============================================================
def init_equipment():
    conn = create_db("equipment")

    conn.executescript("""
    CREATE TABLE dim_device_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_code TEXT NOT NULL UNIQUE,
        type_name TEXT NOT NULL,
        category TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE dim_device (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_code TEXT NOT NULL UNIQUE,
        device_name TEXT NOT NULL,
        device_type TEXT NOT NULL CHECK(device_type IN ('CRANE','VEHICLE','CONVEYOR','VESSEL','OTHER')),
        model TEXT,
        manufacturer TEXT,
        install_date TEXT,
        design_life_year INTEGER,
        health_score REAL DEFAULT 100,
        status TEXT NOT NULL CHECK(status IN ('RUNNING','STANDBY','FAULT','MAINTENANCE')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_device_operation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id TEXT NOT NULL UNIQUE,
        device_code TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        running_hours REAL DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('RUNNING','STOPPED','FAULT','MAINTENANCE')),
        fault_code TEXT,
        fault_desc TEXT,
        operator_name TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_iot_monitor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_date TEXT NOT NULL,
        device_code TEXT NOT NULL,
        temperature REAL,
        vibration REAL,
        current_a REAL,
        power_kw REAL,
        is_abnormal INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # dim_device_type (5 rows for Phase 1a, plan specifies 8 for full coverage)
    device_types = [
        ("CRANE", "岸桥/场桥/门机", "起重设备"),
        ("VEHICLE", "叉车/正面吊/自卸车", "运输车辆"),
        ("CONVEYOR", "传送带", "输送设备"),
        ("VESSEL", "装船机/卸船机", "船舶设备"),
        ("OTHER", "其他", "其他设备"),
    ]
    conn.executemany(
        "INSERT INTO dim_device_type (type_code, type_name, category) VALUES (?,?,?)",
        device_types,
    )

    # dim_device (15 rows)
    devices = [
        ("QC-01", "1号岸桥", "CRANE", "ZPMC-65T", "振华重工", "2018-03-15", 25, 92.5, "RUNNING"),
        ("QC-02", "2号岸桥", "CRANE", "ZPMC-65T", "振华重工", "2018-03-15", 25, 88.0, "RUNNING"),
        ("QC-03", "3号岸桥", "CRANE", "ZPMC-50T", "振华重工", "2019-07-01", 25, 45.0, "FAULT"),
        ("RTG-01", "1号轮胎吊", "CRANE", "KALMAR-RTG", "卡尔玛", "2017-05-20", 20, 85.0, "RUNNING"),
        ("RTG-02", "2号轮胎吊", "CRANE", "KALMAR-RTG", "卡尔玛", "2017-05-20", 20, 95.0, "RUNNING"),
        ("RTG-03", "3号轮胎吊", "CRANE", "KALMAR-RTG", "卡尔玛", "2019-10-01", 20, 78.0, "MAINTENANCE"),
        ("RMG-01", "1号轨道吊", "CRANE", "ZPMC-RMG", "振华重工", "2020-01-15", 20, 90.0, "RUNNING"),
        ("YC-01", "1号叉车", "VEHICLE", "HELI-10T", "合力叉车", "2020-06-01", 10, 80.0, "RUNNING"),
        ("YC-02", "2号叉车", "VEHICLE", "HELI-5T", "合力叉车", "2021-03-15", 10, 91.0, "RUNNING"),
        ("TL-01", "1号拖车", "VEHICLE", "KALMAR-TT", "卡尔玛", "2019-01-10", 12, 75.0, "RUNNING"),
        ("TL-02", "2号拖车", "VEHICLE", "KALMAR-TT", "卡尔玛", "2019-01-10", 12, 82.0, "RUNNING"),
        ("TL-03", "3号拖车", "VEHICLE", "KALMAR-TT", "卡尔玛", "2020-08-15", 12, 100.0, "STANDBY"),
        ("CV-01", "1号传送带", "CONVEYOR", "SBM-BC", "Sandvik", "2018-06-01", 15, 88.0, "RUNNING"),
        ("CV-02", "2号传送带", "CONVEYOR", "SBM-BC", "Sandvik", "2018-06-01", 15, 87.0, "RUNNING"),
        ("PS-01", "1号卸船机", "OTHER", "BHS-SU", "BHS-Sonthofen", "2021-01-20", 15, 93.0, "RUNNING"),
    ]
    conn.executemany(
        "INSERT INTO dim_device (device_code, device_name, device_type, model, manufacturer, install_date, design_life_year, health_score, status) VALUES (?,?,?,?,?,?,?,?,?)",
        devices,
    )

    # fact_device_operation (~60 rows)
    device_ops = []
    for i in range(60):
        oid = f"DEV-OP-{i+1:04d}"
        dev = random.choice([d[0] for d in devices])
        days_ago = random.randint(0, 14)
        start = (NOW - timedelta(days=days_ago, hours=random.randint(0, 20))).strftime("%Y-%m-%d %H:%M")
        hours = random.uniform(0.5, 8.0)
        end = (datetime.strptime(start, "%Y-%m-%d %H:%M") + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        status = random.choice(["RUNNING"] * 8 + ["STOPPED"] + ["FAULT"])
        fault = None if status != "FAULT" else random.choice(["E01-过热", "E02-振动超标", "E03-电流异常"])
        device_ops.append((oid, dev, start, end, round(hours, 1), status, fault, fault, f"operator_{random.randint(1,5)}"))
    conn.executemany(
        "INSERT INTO fact_device_operation (operation_id, device_code, start_time, end_time, running_hours, status, fault_code, fault_desc, operator_name) VALUES (?,?,?,?,?,?,?,?,?)",
        device_ops,
    )

    # fact_iot_monitor (~450 rows: 15 devices × 30 days)
    iot_data = []
    for device in [d[0] for d in devices]:
        for d in range(30):
            date_str = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
            temp = round(random.uniform(25, 60), 1)
            vib = round(random.uniform(0.5, 8.0), 2)
            current = round(random.uniform(50, 200), 1)
            power = round(random.uniform(20, 80), 1)
            abnormal = 1 if (temp > 55 or vib > 6.0) else 0
            iot_data.append((date_str, device, temp, vib, current, power, abnormal))
    conn.executemany(
        "INSERT INTO fact_iot_monitor (monitor_date, device_code, temperature, vibration, current_a, power_kw, is_abnormal) VALUES (?,?,?,?,?,?,?)",
        iot_data,
    )

    conn.commit()
    conn.close()
    print(f"  equipment.db: {len(devices)} devices, {len(device_ops)} ops, {len(iot_data)} iot records")


# ============================================================
# energy.db
# ============================================================
def init_energy():
    conn = create_db("energy")

    conn.executescript("""
    CREATE TABLE dim_energy_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        energy_code TEXT NOT NULL UNIQUE,
        energy_name TEXT NOT NULL,
        energy_category TEXT NOT NULL CHECK(energy_category IN ('ELECTRICITY','FUEL','GAS','WATER','RENEWABLE')),
        unit TEXT NOT NULL,
        co2_factor REAL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE fact_electricity_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_date TEXT NOT NULL,
        dept_code TEXT NOT NULL,
        dept_name TEXT,
        consumption_kwh REAL NOT NULL DEFAULT 0,
        peak_kwh REAL DEFAULT 0,
        valley_kwh REAL DEFAULT 0,
        pv_generation_kwh REAL DEFAULT 0,
        wind_generation_kwh REAL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # dim_energy_type (8 rows)
    energy_types = [
        ("ELEC_GRID", "市电", "ELECTRICITY", "kWh", 0.581),
        ("ELEC_PV", "光伏发电", "RENEWABLE", "kWh", 0.0),
        ("ELEC_WIND", "风力发电", "RENEWABLE", "kWh", 0.0),
        ("DIESEL", "柴油", "FUEL", "吨", 3.16),
        ("GASOLINE", "汽油", "FUEL", "吨", 2.93),
        ("LNG", "液化天然气", "GAS", "立方米", 0.0022),
        ("WATER_FRESH", "淡水", "WATER", "吨", 0.0),
        ("SHORE_PWR", "岸电", "ELECTRICITY", "kWh", 0.581),
    ]
    conn.executemany(
        "INSERT INTO dim_energy_type (energy_code, energy_name, energy_category, unit, co2_factor) VALUES (?,?,?,?,?)",
        energy_types,
    )

    # fact_electricity_daily (~90 rows: 3 depts × 30 days)
    depts = [
        ("OPS", "作业调度中心"),
        ("EQUIP", "设备管理部"),
        ("ADMIN", "综合管理部"),
    ]
    elec_data = []
    for d in range(30):
        date_str = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
        for dept_code, dept_name in depts:
            base = {"OPS": 5000, "EQUIP": 2000, "ADMIN": 800}[dept_code]
            consumption = round(random.uniform(base * 0.8, base * 1.2), 0)
            peak = round(consumption * random.uniform(0.5, 0.7), 0)
            valley = round(consumption * random.uniform(0.3, 0.5), 0)
            pv = round(random.uniform(200, 500), 0)
            wind = round(random.uniform(50, 150), 0)
            elec_data.append((date_str, dept_code, dept_name, consumption, peak, valley, pv, wind))
    conn.executemany(
        "INSERT INTO fact_electricity_daily (stat_date, dept_code, dept_name, consumption_kwh, peak_kwh, valley_kwh, pv_generation_kwh, wind_generation_kwh) VALUES (?,?,?,?,?,?,?,?)",
        elec_data,
    )

    conn.commit()
    conn.close()
    print(f"  energy.db: {len(energy_types)} energy types, {len(elec_data)} daily records")


# ============================================================
# sessions.db (schema only, data via session_store.py)
# ============================================================
def init_sessions():
    conn = create_db("sessions")

    conn.executescript("""
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
        sources TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Pre-create 3 demo sessions
    INSERT INTO sessions (session_id, channel, user_id, title, message_count) VALUES
        ('demo-session-1', 'web', 'operator1', '船舶查询', 0),
        ('demo-session-2', 'web', 'safety_officer', '安全规程问答', 0),
        ('demo-session-3', 'web', 'equipment_mgr', '设备状态查询', 0);
    """)

    conn.commit()
    conn.close()
    print("  sessions.db: schema + 3 demo sessions")


if __name__ == "__main__":
    print("Initializing demo data...")
    init_production()
    init_equipment()
    init_energy()
    init_sessions()
    print("Done! All databases created in", DATA_DIR)
