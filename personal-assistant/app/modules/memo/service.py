from datetime import datetime


class MemoService:
    def __init__(self, db):
        self.db = db

    def create_note(self, title, content="", category="", tags=""):
        if not title:
            raise ValueError("标题不能为空")
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "INSERT INTO memo_notes (title, content, category, tags, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (title, content, category, tags, now, now))
        self.db.commit()
        return {"id": cur.lastrowid, "title": title, "content": content,
                "category": category, "tags": tags, "is_pinned": 0,
                "created_at": now, "updated_at": now}

    def get_note(self, note_id):
        r = self.db.execute("SELECT * FROM memo_notes WHERE id=?", (note_id,)).fetchone()
        if not r:
            raise ValueError("笔记不存在")
        return dict(r)

    def list_notes(self, category=None, tag=None, keyword=None, is_pinned=None):
        sql = "SELECT * FROM memo_notes WHERE 1=1"
        params = []
        if category:
            sql += " AND category = ?"; params.append(category)
        if tag:
            sql += " AND tags LIKE ?"; params.append(f"%{tag}%")
        if keyword:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if is_pinned is not None:
            sql += " AND is_pinned = ?"; params.append(int(is_pinned))
        sql += " ORDER BY is_pinned DESC, updated_at DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def update_note(self, note_id, **kwargs):
        r = self.db.execute("SELECT * FROM memo_notes WHERE id=?", (note_id,)).fetchone()
        if not r:
            raise ValueError("笔记不存在")
        kwargs["updated_at"] = datetime.now().isoformat()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE memo_notes SET {sets} WHERE id=?",
            (*kwargs.values(), note_id))
        self.db.commit()
        return self.get_note(note_id)

    def toggle_pin(self, note_id):
        r = self.db.execute("SELECT * FROM memo_notes WHERE id=?", (note_id,)).fetchone()
        if not r:
            raise ValueError("笔记不存在")
        new_pin = 0 if r["is_pinned"] else 1
        return self.update_note(note_id, is_pinned=new_pin)

    def delete_note(self, note_id):
        self.db.execute("DELETE FROM memo_notes WHERE id=?", (note_id,))
        self.db.commit()
        return True

    def search(self, keyword):
        return self.list_notes(keyword=keyword)
