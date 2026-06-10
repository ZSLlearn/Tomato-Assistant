class ToolExecutor:
    def __init__(self, finance_svc, health_svc, schedule_svc, memo_svc, weather_svc):
        self.finance = finance_svc
        self.health = health_svc
        self.schedule = schedule_svc
        self.memo = memo_svc
        self.weather = weather_svc

    def execute(self, tool_name, params):
        if tool_name == "add_finance_record":
            return self.finance.add_record(
                params.get("category_id", 1), params.get("type", "expense"),
                params.get("amount", 0), params.get("date", ""), params.get("note", ""))

        if tool_name == "query_finance":
            qt = params.get("query_type", "recent")
            if qt == "monthly_summary":
                return self.finance.get_monthly_summary(
                    params.get("year", 2026), params.get("month", 6))
            if qt == "trend":
                return self.finance.get_trend(
                    params.get("year", 2026), params.get("month", 6))
            return self.finance.list_records()

        if tool_name == "record_health":
            ht = params.get("health_type", "")
            if ht == "weight":
                return self.health.record_weight(
                    params.get("value", 0), params.get("date", ""))
            if ht == "exercise":
                return self.health.record_exercise(
                    params.get("type", ""), params.get("duration", 0),
                    params.get("calories", 0), params.get("date", ""))
            if ht == "water":
                return self.health.record_water(
                    params.get("amount", 0), params.get("date", ""))
            if ht == "sleep":
                return self.health.record_sleep(
                    params.get("start_time", ""), params.get("end_time", ""),
                    params.get("quality", 3), params.get("date", ""))

        if tool_name == "query_health":
            qt = params.get("query_type", "dashboard")
            if qt == "dashboard":
                return self.health.get_dashboard()
            if qt == "weight_trend":
                return self.health.get_weight_trend(params.get("days", 30))
            if qt == "sleep_stats":
                return self.health.get_sleep_stats(params.get("days", 7))
            if qt == "exercise_stats":
                return self.health.get_exercise_stats(params.get("days", 30))

        if tool_name == "manage_schedule":
            action = params.get("action", "query")
            if action == "create":
                return self.schedule.create_event(
                    params.get("title", ""), params.get("start_time", ""),
                    params.get("end_time", ""), params.get("description", ""),
                    params.get("category", "个人"), params.get("priority", 2))
            if action == "query":
                return self.schedule.list_events(date_from=params.get("date"))
            if action == "complete":
                return self.schedule.mark_completed(params.get("event_id", 0))
            if action == "delete":
                return self.schedule.delete_event(params.get("event_id", 0))
            return self.schedule.list_events()

        if tool_name == "manage_memo":
            action = params.get("action", "query")
            if action == "create":
                return self.memo.create_note(
                    params.get("title", ""), params.get("content", ""),
                    params.get("category", ""), params.get("tags", ""))
            if action == "search":
                return self.memo.search(params.get("keyword", ""))
            if action == "query":
                return self.memo.list_notes()
            if action == "delete":
                return self.memo.delete_note(params.get("note_id", 0))
            return self.memo.list_notes()

        if tool_name == "query_weather":
            city = params.get("city", "北京")
            qt = params.get("type", "now")
            if qt == "forecast":
                return self.weather.get_forecast(city, params.get("days", 7))
            if qt == "life_index":
                return self.weather.get_life_index(city)
            return self.weather.get_real_time(city)

        return {"error": f"未知工具: {tool_name}"}
