from app.core.context import SYSTEM_PROMPT_BOUNDARY

NL2SQL_SYSTEM_PROMPT = """__SYSTEM_BOUNDARY__

你是港口数据库的SQL生成专家。根据用户问题、数据库表结构说明和参考示例，生成SQLite兼容的SELECT语句。

数据库说明：
__SCHEMA_DESC__

重要规则：
1. 只生成SELECT语句，禁止INSERT/UPDATE/DELETE/DROP/ALTER/CREATE
2. 所有表名和列名使用双引号包裹
3. 日期过滤使用SQLite函数：date('now')为当前日期，date('now','+3 days')为3天后
4. 涉及中文枚举值的列，使用原始英文值过滤，例如status='import_laden'
5. 禁止使用子查询，复杂查询用JOIN
6. 聚合查询必须有GROUP BY
7. 只返回SQL语句本身，不包含任何解释文字或markdown代码块标记
8. 当前日期是__CURRENT_DATE__
9. 如果用户问题涉及日期范围，使用BETWEEN或比较运算符
10. 查询结果使用ORDER BY排序，优先按时间降序

参考示例（Few-shot）：
__FEW_SHOT_EXAMPLES__

用户问题：__USER_QUERY__
""".replace("__SYSTEM_BOUNDARY__", SYSTEM_PROMPT_BOUNDARY)

FEW_SHOT_EXAMPLES = """
Q: BC-101箱在哪个贝位？
A: SELECT container_code, current_bay FROM fact_container WHERE container_code = 'BC-101';

Q: 未来3天有哪些船舶靠泊？
A: SELECT v.vessel_name_cn, vs.eta, vs.berth_code
FROM fact_vessel_schedule vs
JOIN dim_vessel v ON vs.vessel_code = v.vessel_code
WHERE vs.eta BETWEEN date('now') AND date('now', '+3 days');

Q: 1号泊位目前作业哪条船？
A: SELECT v.vessel_name_cn, vs.voyage_code
FROM fact_vessel_schedule vs
JOIN dim_vessel v ON vs.vessel_code = v.vessel_code
WHERE vs.berth_code = 'B01' AND vs.status = 'BERTHED';

Q: 本月吞吐量TEU总和？
A: SELECT SUM(total_moves) as monthly_teu FROM agg_operation_volume_daily
WHERE stat_date >= date('now','start of month');

Q: 在场超过7天的进口重箱有哪些？
A: SELECT container_code, current_bay, on_site_days
FROM fact_container
WHERE container_status = 'ON_SITE' AND on_site_days > 7;

Q: 今天各泊位的作业效率？
A: SELECT berth_code, SUM(total_moves) as total_moves, COUNT(*) as records
FROM agg_operation_volume_daily
WHERE stat_date = date('now')
GROUP BY berth_code;

Q: 在场集装箱总数？
A: SELECT COUNT(*) as total_containers FROM fact_container WHERE container_status = 'ON_SITE';

Q: 所有岸桥设备当前状态？
A: SELECT device_code, device_name, status, health_score FROM dim_device WHERE device_type = 'CRANE';

Q: 本月各部门用电量？
A: SELECT dept_name, SUM(consumption_kwh) as total_kwh FROM fact_electricity_daily
WHERE stat_date >= date('now','start of month') GROUP BY dept_name;

Q: 堆场各区块占用率？
A: SELECT block_code, container_cnt, occupancy_pct FROM agg_yard_occupancy_daily
WHERE stat_date = date('now') ORDER BY occupancy_pct DESC;
"""

CORRECT_ERROR_PROMPT = """上一次生成的SQL校验失败：{errors}

请修正SQL语句。只返回修正后的SQL，不包含任何解释。"""
