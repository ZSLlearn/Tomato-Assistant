from datetime import datetime


class FinanceService:
    def __init__(self, db):
        self.db = db

    # === 分类管理 ===

    def create_category(self, name, type, icon=""):
        existing = self.db.execute(
            "SELECT id FROM finance_categories WHERE name=? AND is_deleted=0",
            (name,)
        ).fetchone()
        if existing:
            raise ValueError(f"分类 '{name}' 已存在")
        cur = self.db.execute(
            "INSERT INTO finance_categories (name, type, icon) VALUES (?, ?, ?)",
            (name, type, icon)
        )
        self.db.commit()
        return {"id": cur.lastrowid, "name": name, "type": type, "icon": icon}

    def list_categories(self, type=None):
        if type:
            rows = self.db.execute(
                "SELECT * FROM finance_categories WHERE type=? AND is_deleted=0", (type,)
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM finance_categories WHERE is_deleted=0"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_category(self, category_id, **kwargs):
        row = self.db.execute(
            "SELECT * FROM finance_categories WHERE id=? AND is_deleted=0",
            (category_id,)
        ).fetchone()
        if not row:
            raise ValueError("分类不存在")
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE finance_categories SET {sets} WHERE id=?",
            (*kwargs.values(), category_id)
        )
        self.db.commit()
        return self._get_category(category_id)

    def delete_category(self, category_id):
        self.db.execute(
            "UPDATE finance_categories SET is_deleted=1 WHERE id=?", (category_id,)
        )
        self.db.commit()
        return True

    # === 账单 CRUD ===

    def add_record(self, category_id, type, amount, date, note=""):
        if amount <= 0:
            raise ValueError("金额必须大于0")
        if type not in ("income", "expense"):
            raise ValueError("类型必须是 income 或 expense")
        cat = self.db.execute(
            "SELECT * FROM finance_categories WHERE id=? AND is_deleted=0",
            (category_id,)
        ).fetchone()
        if not cat:
            raise ValueError("分类不存在")
        if cat["type"] != type:
            raise ValueError(f"分类'{cat['name']}'的类型为{cat['type']}，与记录类型{type}不匹配")
        created_at = datetime.now().isoformat()
        cur = self.db.execute(
            "INSERT INTO finance_records (category_id, type, amount, date, note, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (category_id, type, amount, date, note, created_at)
        )
        self.db.commit()
        return {
            "id": cur.lastrowid, "category_id": category_id, "type": type,
            "amount": amount, "date": date, "note": note, "created_at": created_at
        }

    def list_records(self, date_from=None, date_to=None, category_id=None, type=None):
        sql = ("SELECT r.*, c.name as category_name FROM finance_records r "
               "LEFT JOIN finance_categories c ON r.category_id=c.id WHERE r.is_deleted=0")
        params = []
        if date_from:
            sql += " AND r.date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND r.date <= ?"; params.append(date_to)
        if category_id:
            sql += " AND r.category_id = ?"; params.append(category_id)
        if type:
            sql += " AND r.type = ?"; params.append(type)
        sql += " ORDER BY r.date DESC, r.created_at DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def update_record(self, record_id, **kwargs):
        row = self.db.execute(
            "SELECT * FROM finance_records WHERE id=? AND is_deleted=0", (record_id,)
        ).fetchone()
        if not row:
            raise ValueError("记录不存在")
        if "amount" in kwargs and kwargs["amount"] <= 0:
            raise ValueError("金额必须大于0")
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE finance_records SET {sets} WHERE id=?",
            (*kwargs.values(), record_id)
        )
        self.db.commit()
        return self._get_record(record_id)

    def delete_record(self, record_id):
        self.db.execute(
            "UPDATE finance_records SET is_deleted=1 WHERE id=?", (record_id,)
        )
        self.db.commit()
        return True

    # === 统计 ===

    def get_monthly_summary(self, year, month):
        prefix = f"{year}-{month:02d}"
        income_row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM finance_records "
            "WHERE type='income' AND is_deleted=0 AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()
        expense_row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM finance_records "
            "WHERE type='expense' AND is_deleted=0 AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()
        cats = self.db.execute(
            "SELECT c.name, COALESCE(SUM(r.amount), 0) as amount "
            "FROM finance_categories c "
            "LEFT JOIN finance_records r ON c.id=r.category_id AND r.is_deleted=0 AND r.date LIKE ? "
            "WHERE c.is_deleted=0 AND c.type='expense' GROUP BY c.id",
            (f"{prefix}%",)
        ).fetchall()
        total_income = income_row["total"]
        total_expense = expense_row["total"]
        by_category = []
        for c in cats:
            pct = round(c["amount"] / total_expense * 100, 1) if total_expense > 0 else 0
            by_category.append({
                "name": c["name"], "amount": c["amount"], "percent": pct
            })
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "by_category": by_category
        }

    def get_trend(self, year, month):
        prefix = f"{year}-{month:02d}"
        rows = self.db.execute(
            "SELECT date, type, SUM(amount) as total FROM finance_records "
            "WHERE is_deleted=0 AND date LIKE ? GROUP BY date, type ORDER BY date",
            (f"{prefix}%",)
        ).fetchall()
        result = {}
        for r in rows:
            if r["date"] not in result:
                result[r["date"]] = {"date": r["date"], "income": 0, "expense": 0}
            result[r["date"]][r["type"]] = r["total"]
        return list(result.values())

    # === 内部辅助 ===

    def _get_category(self, cid):
        r = self.db.execute(
            "SELECT * FROM finance_categories WHERE id=?", (cid,)
        ).fetchone()
        return dict(r) if r else None

    def _get_record(self, rid):
        r = self.db.execute(
            "SELECT r.*, c.name as category_name FROM finance_records r "
            "LEFT JOIN finance_categories c ON r.category_id=c.id WHERE r.id=?", (rid,)
        ).fetchone()
        return dict(r) if r else None
