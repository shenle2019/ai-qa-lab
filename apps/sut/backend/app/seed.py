from .db import SessionLocal
from .models import Ticket

SAMPLE_TICKETS = [
    {
        "title": "登录验证码不显示",
        "description": "Chrome 下点击获取验证码无反应",
        "status": "open",
        "priority": "high",
    },
    {
        "title": "工单列表分页错乱",
        "description": "第二页重复展示第一页数据",
        "status": "open",
        "priority": "medium",
    },
    {
        "title": "知识库回答超时",
        "description": "RAG 接口 30 秒未返回",
        "status": "in_progress",
        "priority": "high",
    },
    {
        "title": "导出报表字段缺失",
        "description": "导出的 CSV 缺少创建时间列",
        "status": "in_progress",
        "priority": "low",
    },
    {
        "title": "移动端布局横向滚动",
        "description": "iPhone 13 下页面溢出",
        "status": "open",
        "priority": "medium",
    },
    {
        "title": "权限校验绕过",
        "description": "普通用户可访问管理员接口",
        "status": "closed",
        "priority": "high",
    },
    {
        "title": "搜索大小写不敏感",
        "description": "搜索 Ticket 找不到 ticket",
        "status": "closed",
        "priority": "low",
    },
]


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(Ticket).count() > 0:
            return
        for item in SAMPLE_TICKETS:
            db.add(Ticket(**item))
        db.commit()
    finally:
        db.close()
