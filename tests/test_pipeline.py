from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_query_structure_extracts_core_fields():
    resp = client.post('/query/structure', json={'user_input': '이번 주말에 부산에서 2명이서 10만원 이하로 낚시하고 싶어'})
    assert resp.status_code == 200
    body = resp.json()['structured_query']
    assert body['location'] == '부산'
    assert body['activity'] == '낚시'
    assert body['price_max'] == 100000
    assert body['people_count'] == 2


def test_pipeline_returns_constrained_recommendation():
    resp = client.post('/pipeline/run', json={'user_input': '이번 주말에 부산에서 2명이서 10만원 이하로 낚시하고 싶어'})
    assert resp.status_code == 200
    body = resp.json()

    candidates = body['filtered_candidates']
    assert len(candidates) >= 1
    selected_id = body['final_recommendation']['selected_id']
    candidate_ids = {c['id'] for c in candidates}
    assert selected_id in candidate_ids
