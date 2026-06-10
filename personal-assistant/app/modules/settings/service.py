class SettingsService:
    def __init__(self, db):
        self.db = db

    def get(self, key, default=None):
        r = self.db.execute(
            "SELECT value FROM system_config WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set(self, key, value):
        self.db.execute(
            "INSERT OR REPLACE INTO system_config (key, value) VALUES (?,?)",
            (key, value))
        self.db.commit()

    def get_all(self):
        rows = self.db.execute("SELECT key, value FROM system_config").fetchall()
        return {r["key"]: r["value"] for r in rows}
