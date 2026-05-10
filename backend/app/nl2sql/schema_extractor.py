import asyncio
from pathlib import Path
from app.core.database.schema import SCHEMA_DESCRIPTIONS, TABLE_DESCRIPTIONS
from app.core.database.sqlite_client import SQLiteClient


class SchemaDescription:
    def __init__(self, domain: str, tables: list[dict]):
        self.domain = domain
        self.domain_desc = SCHEMA_DESCRIPTIONS.get(domain, "")
        self.tables = tables

    def to_prompt_text(self) -> str:
        lines = [f"数据库: {self.domain_desc}"]
        for t in self.tables:
            lines.append(f"\n表: {t['table_name']}")
            lines.append(f"  说明: {t['table_desc']}")
            lines.append(f"  列:")
            for c in t["columns"]:
                extras = []
                if c.get("is_pk"):
                    extras.append("主键")
                if c.get("fk_to"):
                    extras.append(f"外键→{c['fk_to']}")
                if c.get("enum_values"):
                    extras.append(f"可选值: {', '.join(c['enum_values'])}")
                extra_str = f" ({', '.join(extras)})" if extras else ""
                lines.append(f"    - {c['name']} ({c['type']}): {c['desc']}{extra_str}")
        return "\n".join(lines)


class SchemaExtractor:
    ENUM_MAP = {
        "container_type": ["DRY_20", "DRY_40", "DRY_45", "REEFER_20", "REEFER_40",
                           "DANGEROUS", "FLAT_RACK", "OPEN_TOP", "TANK"],
        "container_status": ["ON_SITE", "DISCHARGED", "LOADED"],
        "vessel_type": ["CONTAINER", "BULK", "RO_RO", "TANKER", "GENERAL"],
        "berth_type": ["CONTAINER", "BULK", "RO_RO", "GENERAL"],
        "block_type": ["CONTAINER", "BULK", "RO_RO", "DANGEROUS", "REEFER"],
        "lane_type": ["INBOUND", "OUTBOUND"],
        "schedule_status": ["SCHEDULED", "BERTHED", "DEPARTED", "CANCELLED"],
        "move_type": ["DISCHARGE", "LOAD", "RESTACK"],
        "shift": ["DAY", "NIGHT"],
        "direction": ["IN", "OUT"],
        "vehicle_type": ["CONTAINER_TRUCK", "BULK_TRUCK", "FLATBED", "SERVICE"],
        "device_type": ["CRANE", "VEHICLE", "CONVEYOR", "VESSEL", "OTHER"],
        "device_status": ["RUNNING", "STANDBY", "FAULT", "MAINTENANCE"],
        "operation_status": ["RUNNING", "STOPPED", "FAULT", "MAINTENANCE"],
        "energy_category": ["ELECTRICITY", "FUEL", "GAS", "WATER", "RENEWABLE"],
        "customs_status": ["CLEARED", "PENDING", "INSPECTION"],
    }

    COLUMN_DESC_OVERRIDES = {
        "type_code": "设备类型编码",
        "type_name": "设备类型名称",
        "category": "设备大类",
        "berth_code": "泊位编号",
        "berth_name": "泊位名称",
        "max_draft": "最大吃水深度（米）",
        "length": "长度（米）",
        "vessel_code": "船舶编码",
        "vessel_name_cn": "船舶中文名",
        "vessel_name_en": "船舶英文名",
        "imo_no": "IMO编号",
        "gross_tonnage": "总吨位",
        "deadweight_ton": "载重吨（吨）",
        "teu_capacity": "标箱容量（TEU）",
        "ship_company": "船公司",
        "block_code": "堆场区块编码",
        "block_name": "堆场区块名称",
        "capacity_teu": "容量（TEU）",
        "max_tier": "最大堆存层数",
        "lane_code": "闸口车道编号",
        "lane_name": "车道名称",
        "container_code": "箱号",
        "current_bay": "当前贝位",
        "yard_block_code": "堆场区块编码",
        "entry_time": "进港时间",
        "on_site_days": "在场天数",
        "is_dangerous": "是否危险品",
        "dangerous_class": "危险品类别",
        "container_owner": "箱主",
        "schedule_id": "计划编号",
        "eta": "预计到港时间",
        "etb": "预计靠泊时间",
        "etd": "预计离泊时间",
        "voyage_in": "进口航次",
        "voyage_out": "出口航次",
        "operation_id": "作业编号",
        "move_time": "作业时间",
        "crane_id": "岸桥编号",
        "planned_moves": "计划作业量",
        "completed_moves": "已完成作业量",
        "progress_pct": "进度百分比",
        "crane_cnt": "作业岸桥数",
        "transaction_id": "通行记录编号",
        "truck_plate": "车牌号",
        "gate_time": "过闸时间",
        "stat_date": "统计日期",
        "discharge_cnt": "卸船箱量",
        "load_cnt": "装船箱量",
        "total_moves": "总作业量（moves）",
        "container_cnt": "在场箱量",
        "occupancy_pct": "占用率百分比",
        "dangerous_cnt": "危险品箱数量",
        "reefr_cnt": "冷藏箱数量",
        "device_code": "设备编码",
        "device_name": "设备名称",
        "model": "型号",
        "manufacturer": "厂家",
        "install_date": "安装日期",
        "design_life_year": "设计寿命（年）",
        "health_score": "健康评分（0-100）",
        "start_time": "开始时间",
        "end_time": "结束时间",
        "running_hours": "运行小时数",
        "fault_code": "故障代码",
        "fault_desc": "故障描述",
        "operator_name": "操作员姓名",
        "monitor_date": "监测日期",
        "temperature": "温度（℃）",
        "vibration": "振动值（mm/s）",
        "current_a": "电流（A）",
        "power_kw": "功率（kW）",
        "is_abnormal": "是否异常",
        "energy_code": "能源编码",
        "energy_name": "能源名称",
        "unit": "计量单位",
        "co2_factor": "碳排放因子",
        "dept_code": "部门编码",
        "dept_name": "部门名称",
        "consumption_kwh": "用电量（kWh）",
        "peak_kwh": "峰时用电",
        "valley_kwh": "谷时用电",
        "pv_generation_kwh": "光伏发电量",
        "wind_generation_kwh": "风力发电量",
        "berth_type": "泊位类型",
        "is_active": "是否启用",
        "status": "状态",
        "vessel_type_col": "船舶类型",
    }

    async def extract(self, db_path: str, domain: str) -> SchemaDescription:
        conn = SQLiteClient(db_path)
        await conn.connect()

        tables = []
        try:
            cursor = await conn.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            table_names = [row[0] for row in await cursor.fetchall()]

            for tname in table_names:
                table_info = await self._extract_table(conn, tname)
                tables.append(table_info)
        finally:
            await conn.close()

        return SchemaDescription(domain=domain, tables=tables)

    async def _extract_table(self, conn: SQLiteClient, table_name: str) -> dict:
        cursor = await conn.conn.execute(f"PRAGMA table_info(\"{table_name}\")")
        cols = await cursor.fetchall()

        fk_cursor = await conn.conn.execute(f"PRAGMA foreign_key_list(\"{table_name}\")")
        fks = await fk_cursor.fetchall()

        fk_map: dict[str, str] = {}
        for fk in fks:
            fk_map[fk[3]] = f"{fk[2]}.{fk[4]}"

        columns = []
        for col in cols:
            col_name = col[1]
            col_type = col[2]
            is_pk = bool(col[5])
            columns.append({
                "name": col_name,
                "type": col_type or "TEXT",
                "desc": self._get_col_desc(col_name),
                "is_pk": is_pk,
                "fk_to": fk_map.get(col_name),
                "enum_values": self.ENUM_MAP.get(col_name),
            })

        return {
            "table_name": table_name,
            "table_desc": TABLE_DESCRIPTIONS.get(table_name, table_name),
            "columns": columns,
        }

    def _get_col_desc(self, col_name: str) -> str:
        if col_name in self.COLUMN_DESC_OVERRIDES:
            return self.COLUMN_DESC_OVERRIDES[col_name]
        return col_name
