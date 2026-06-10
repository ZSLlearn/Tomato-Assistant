class ScheduleService:
    def __init__(self, db):
        self.db = db

    def create_event(self, title, start_time, end_time="", description="",
                     category="个人", priority=2):
        if not title:
            raise ValueError("标题不能为空")
        if start_time and end_time and start_time >= end_time:
            raise ValueError("开始时间必须早于结束时间")
        if category not in ('工作', '个人', '紧急'):
            raise ValueError("分类必须是 工作/个人/紧急")
        if priority not in (1, 2, 3):
            raise ValueError("优先级必须在1-3之间")
        cur = self.db.execute(
            "INSERT INTO schedule_events (title, description, start_time, end_time, category, priority) "
            "VALUES (?,?,?,?,?,?)",
            (title, description, start_time, end_time, category, priority))
        self.db.commit()
        return {"id": cur.lastrowid, "title": title, "description": description,
                "start_time": start_time, "end_time": end_time, "category": category,
                "priority": priority, "is_completed": 0}

    def list_events(self, date_from=None, date_to=None, category=None, is_completed=None):
        sql = "SELECT * FROM schedule_events WHERE is_deleted=0"
        params = []
        if date_from:
            sql += " AND date(start_time) >= ?"; params.append(date_from)
        if date_to:
            sql += " AND date(start_time) <= ?"; params.append(date_to)
        if category:
            sql += " AND category = ?"; params.append(category)
        if is_completed is not None:
            sql += " AND is_completed = ?"; params.append(int(is_completed))
        sql += " ORDER BY start_time ASC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def get_events_by_date(self, date):
        return self.list_events(date_from=date, date_to=date)

    def get_events_by_month(self, year, month):
        prefix = f"{year}-{month:02d}"
        return self.list_events(date_from=f"{prefix}-01", date_to=f"{prefix}-31")

    def update_event(self, event_id, **kwargs):
        row = self.db.execute(
            "SELECT * FROM schedule_events WHERE id=? AND is_deleted=0", (event_id,)).fetchone()
        if not row:
            raise ValueError("日程不存在")
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE schedule_events SET {sets} WHERE id=?",
            (*kwargs.values(), event_id))
        self.db.commit()
        return self._get(event_id)

    def mark_completed(self, event_id):
        row = self.db.execute(
            "SELECT * FROM schedule_events WHERE id=? AND is_deleted=0", (event_id,)).fetchone()
        if not row:
            raise ValueError("日程不存在")
        new_status = 0 if row["is_completed"] else 1
        self.db.execute("UPDATE schedule_events SET is_completed=? WHERE id=?", (new_status, event_id))
        self.db.commit()
        return self._get(event_id)

    def delete_event(self, event_id):
        self.db.execute("UPDATE schedule_events SET is_deleted=1 WHERE id=?", (event_id,))
        self.db.commit()
        return True

    def get_upcoming_events(self, hours=24):
        from datetime import datetime, timedelta
        now = datetime.now().isoformat()
        cutoff = (datetime.now() + timedelta(hours=hours)).isoformat()
        rows = self.db.execute(
            "SELECT * FROM schedule_events WHERE is_deleted=0 AND is_completed=0 "
            "AND start_time >= ? AND start_time <= ? ORDER BY start_time ASC",
            (now, cutoff)).fetchall()
        return [dict(r) for r in rows]

    def _get(self, eid):
        r = self.db.execute("SELECT * FROM schedule_events WHERE id=?", (eid,)).fetchone()
        return dict(r) if r else None
