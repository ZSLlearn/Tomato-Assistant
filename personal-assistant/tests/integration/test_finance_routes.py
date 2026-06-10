def test_create_category_api(client):
    resp = client.post('/finance/api/categories',
                       json={"name": "餐饮", "type": "expense"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "餐饮"


def test_create_category_no_name(client):
    resp = client.post('/finance/api/categories',
                       json={"name": "", "type": "expense"})
    assert resp.status_code == 400


def test_create_category_invalid_type(client):
    resp = client.post('/finance/api/categories',
                       json={"name": "test", "type": "invalid"})
    assert resp.status_code == 400


def test_list_categories_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/categories',
                json={"name": "工资", "type": "income"})
    resp = client.get('/finance/api/categories')
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 2


def test_delete_category_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    resp = client.delete('/finance/api/categories/1')
    assert resp.status_code == 200
    cats = client.get('/finance/api/categories').get_json()["data"]
    assert len(cats) == 0


def test_add_record_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    resp = client.post('/finance/api/records',
                       json={"category_id": 1, "type": "expense",
                             "amount": 30, "date": "2026-06-10"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["amount"] == 30


def test_add_record_invalid_amount(client):
    resp = client.post('/finance/api/records',
                       json={"category_id": 1, "type": "expense",
                             "amount": -5, "date": "2026-06-10"})
    assert resp.status_code == 400


def test_add_record_zero_amount(client):
    resp = client.post('/finance/api/records',
                       json={"category_id": 1, "type": "expense",
                             "amount": 0, "date": "2026-06-10"})
    assert resp.status_code == 400


def test_add_record_no_date(client):
    resp = client.post('/finance/api/records',
                       json={"category_id": 1, "type": "expense",
                             "amount": 30})
    assert resp.status_code == 400


def test_list_records_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/records',
                json={"category_id": 1, "type": "expense",
                      "amount": 30, "date": "2026-06-10"})
    resp = client.get('/finance/api/records')
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_update_record_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/records',
                json={"category_id": 1, "type": "expense",
                      "amount": 30, "date": "2026-06-10"})
    resp = client.put('/finance/api/records/1',
                      json={"amount": 50, "note": "晚餐"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["amount"] == 50
    assert resp.get_json()["data"]["note"] == "晚餐"


def test_update_nonexistent_record(client):
    resp = client.put('/finance/api/records/999',
                      json={"amount": 50})
    assert resp.status_code == 404


def test_delete_record_api(client):
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/records',
                json={"category_id": 1, "type": "expense",
                      "amount": 30, "date": "2026-06-10"})
    resp = client.delete('/finance/api/records/1')
    assert resp.status_code == 200
    recs = client.get('/finance/api/records').get_json()["data"]
    assert len(recs) == 0


def test_monthly_summary_api(client):
    client.post('/finance/api/categories',
                json={"name": "工资", "type": "income"})
    client.post('/finance/api/categories',
                json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/records',
                json={"category_id": 1, "type": "income",
                      "amount": 5000, "date": "2026-06-10"})
    client.post('/finance/api/records',
                json={"category_id": 2, "type": "expense",
                      "amount": 200, "date": "2026-06-10"})
    resp = client.get('/finance/api/summary?year=2026&month=6')
    data = resp.get_json()["data"]
    assert data["balance"] == 4800
    assert data["total_income"] == 5000


def test_trend_api(client):
    client.post('/finance/api/categories',
                json={"name": "工资", "type": "income"})
    client.post('/finance/api/records',
                json={"category_id": 1, "type": "income",
                      "amount": 5000, "date": "2026-06-10"})
    resp = client.get('/finance/api/trend?year=2026&month=6')
    data = resp.get_json()["data"]
    assert len(data) >= 1


def test_page_renders(client):
    resp = client.get('/finance/')
    assert resp.status_code == 200
