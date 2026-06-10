class HealthService:
    def __init__(self, db):
        self.db = db

    # === 体重 ===

    def record_weight(self, weight, date, note=""):
        if weight <= 0:
            raise ValueError("体重必须大于0")
        cur = self.db.execute(
            "INSERT INTO health_weight (weight, date, note) VALUES (?,?,?)",
            (weight, date, note))
        self.db.commit()
        return {"id": cur.lastrowid, "weight": weight, "date": date, "note": note}

    def list_weight(self, date_from=None, date_to=None):
        sql = "SELECT * FROM health_weight WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND date <= ?"; params.append(date_to)
        sql += " ORDER BY date DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def get_weight_trend(self, days=30):
        rows = self.db.execute(
            "SELECT date, weight FROM health_weight ORDER BY date DESC LIMIT ?",
            (days,)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def delete_weight(self, record_id):
        self.db.execute("DELETE FROM health_weight WHERE id=?", (record_id,))
        self.db.commit()
        return True

    # === 运动 ===

    def record_exercise(self, type, duration, calories=0, date="", note=""):
        if duration <= 0:
            raise ValueError("运动时长必须大于0")
        if not type:
            raise ValueError("运动类型不能为空")
        cur = self.db.execute(
            "INSERT INTO health_exercise (type, duration, calories, date, note) VALUES (?,?,?,?,?)",
            (type, duration, calories, date, note))
        self.db.commit()
        return {"id": cur.lastrowid, "type": type, "duration": duration,
                "calories": calories, "date": date, "note": note}

    def list_exercise(self, date_from=None, date_to=None):
        sql = "SELECT * FROM health_exercise WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND date <= ?"; params.append(date_to)
        sql += " ORDER BY date DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def get_exercise_stats(self, days=30):
        row = self.db.execute(
            "SELECT COUNT(*) as total_count, COALESCE(SUM(duration),0) as total_duration, "
            "COALESCE(SUM(calories),0) as total_calories FROM health_exercise "
            "WHERE date >= date('now', ? || ' days')", (f"-{days}",)).fetchone()
        return dict(row)

    def delete_exercise(self, record_id):
        self.db.execute("DELETE FROM health_exercise WHERE id=?", (record_id,))
        self.db.commit()
        return True

    # === 饮水 ===

    def record_water(self, amount, date):
        if amount <= 0:
            raise ValueError("饮水量必须大于0")
        cur = self.db.execute(
            "INSERT INTO health_water (amount, date) VALUES (?,?)", (amount, date))
        self.db.commit()
        return {"id": cur.lastrowid, "amount": amount, "date": date}

    def list_water(self, date_from=None, date_to=None):
        sql = "SELECT * FROM health_water WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND date <= ?"; params.append(date_to)
        sql += " ORDER BY date DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def get_daily_water(self, date):
        row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM health_water WHERE date=?",
            (date,)).fetchone()
        return row["total"]

    def delete_water(self, record_id):
        self.db.execute("DELETE FROM health_water WHERE id=?", (record_id,))
        self.db.commit()
        return True

    # === 睡眠 ===

    def record_sleep(self, start_time, end_time, quality=3, date=""):
        if quality < 1 or quality > 5:
            raise ValueError("睡眠质量必须在1-5之间")
        if not self._is_valid_sleep_time(start_time, end_time):
            raise ValueError("起床时间必须晚于入睡时间")
        cur = self.db.execute(
            "INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES (?,?,?,?)",
            (start_time, end_time, quality, date))
        self.db.commit()
        return {"id": cur.lastrowid, "start_time": start_time, "end_time": end_time,
                "quality": quality, "date": date}

    def list_sleep(self, date_from=None, date_to=None):
        sql = "SELECT * FROM health_sleep WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND date <= ?"; params.append(date_to)
        sql += " ORDER BY date DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def get_sleep_stats(self, days=7):
        rows = self.db.execute(
            "SELECT quality, start_time, end_time FROM health_sleep ORDER BY date DESC LIMIT ?",
            (days,)).fetchall()
        if not rows:
            return {"avg_duration": 0, "avg_quality": 0, "trend": []}
        total_duration = 0
        total_quality = 0
        trend = []
        for r in rows:
            q = r["quality"]
            total_quality += q
            trend.append({"date": r["start_time"][:10], "quality": q})
        avg_quality = round(total_quality / len(rows), 1)
        return {"avg_duration": 0, "avg_quality": avg_quality, "trend": trend}

    def delete_sleep(self, record_id):
        self.db.execute("DELETE FROM health_sleep WHERE id=?", (record_id,))
        self.db.commit()
        return True

    @staticmethod
    def _is_valid_sleep_time(start_time, end_time):
        """Validate that start_time is before end_time, handling various formats.
        Supports: 'HH:MM', 'YYYY-MM-DD HH:MM', and ISO format.
        """
        from datetime import datetime
        # Try to parse as full datetime first
        formats = [
            "%Y-%m-%d %H:%M",     # 2026-06-11 23:00
            "%Y-%m-%dT%H:%M",     # 2026-06-11T23:00
            "%Y-%m-%d %H:%M:%S",  # 2026-06-11 23:00:00
            "%Y-%m-%dT%H:%M:%S",  # 2026-06-11T23:00:00
        ]
        for fmt in formats:
            try:
                st = datetime.strptime(start_time, fmt)
                et = datetime.strptime(end_time, fmt)
                return st < et
            except ValueError:
                continue
        # Fallback: treat as pure time strings (e.g., '23:00', '07:00')
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                st = datetime.strptime(start_time, fmt)
                et = datetime.strptime(end_time, fmt)
                if st < et:
                    return True  # Same-day sleep (e.g., 07:00 to 22:00)
                # start >= end: likely overnight sleep (e.g., 23:00 to 07:00 = 8h)
                # Calculate overnight duration in hours
                start_minutes = st.hour * 60 + st.minute
                end_minutes = et.hour * 60 + et.minute
                overnight_hours = ((24 * 60 - start_minutes) + end_minutes) / 60
                # Valid sleep range: 2-18 hours
                return 2 <= overnight_hours <= 18
            except ValueError:
                continue
        # Last resort: lexical comparison
        return start_time < end_time

    # === 看板 ===

    def get_dashboard(self):
        from datetime import date
        today = date.today().isoformat()
        weight_row = self.db.execute(
            "SELECT weight FROM health_weight WHERE date<=? ORDER BY date DESC LIMIT 1",
            (today,)).fetchone()
        water_total = self.get_daily_water(today)
        exercise_row = self.db.execute(
            "SELECT COALESCE(SUM(duration),0) as total FROM health_exercise WHERE date=?",
            (today,)).fetchone()
        sleep_row = self.db.execute(
            "SELECT * FROM health_sleep WHERE date<=? ORDER BY date DESC LIMIT 1",
            (today,)).fetchone()
        return {
            "weight": weight_row["weight"] if weight_row else None,
            "water_total": water_total,
            "exercise_today": exercise_row["total"] if exercise_row else 0,
            "sleep_last": dict(sleep_row) if sleep_row else None
        }
