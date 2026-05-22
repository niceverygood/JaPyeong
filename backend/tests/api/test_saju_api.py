"""/v1/saju API 통합 테스트 (FastAPI TestClient)."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

BIRTH = {
    "name": "예시",
    "gender": "M",
    "calendar": "solar",
    "year": 1985,
    "month": 6,
    "day": 23,
    "hour": 14,
    "minute": 30,
    "longitude": 126.9784,
    "latitude": 37.5665,
    "timezone": "Asia/Seoul",
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_full():
    r = client.post("/v1/saju/analyze", json=BIRTH)
    assert r.status_code == 200, r.text
    d = r.json()
    # 8자
    assert d["pillars"]["year"] == {"gan": "乙", "ji": "丑"}
    assert d["pillars"]["day"] == {"gan": "癸", "ji": "巳"}
    assert d["pillars"]["hour"] == {"gan": "己", "ji": "未"}
    assert d["day_master"] == "癸"
    assert d["day_master_element"] == "水"
    # 대운
    assert d["daewoon"]["direction"] == "backward"
    assert d["daewoon"]["start_age"] == 6
    assert d["daewoon"]["periods"][0] == {"sequence": 1, "start_age": 6, "gan": "辛", "ji": "巳"}
    # 오행
    assert d["five_elements"]["dominant"] == "土"
    assert 0 <= d["five_elements"]["balance"] <= 1
    # 십성·관계 존재
    assert sum(d["ten_gods"].values()) > 0
    assert any(rel["type"] == "충" for rel in d["relations"])


def test_analyze_hour_unknown():
    body = {k: v for k, v in BIRTH.items() if k not in ("hour", "minute")}
    r = client.post("/v1/saju/analyze", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["pillars"]["hour"] is None


def test_analyze_validation_error():
    bad = {**BIRTH, "month": 13}
    r = client.post("/v1/saju/analyze", json=bad)
    assert r.status_code == 422  # pydantic 검증 실패


def test_luck_specific_date():
    r = client.get("/v1/saju/luck", params={"on": "2000-01-07"})
    assert r.status_code == 200, r.text
    il = r.json()["il_un"]
    assert il["gan"] + il["ji"] == "甲子"


def test_luck_default_today():
    r = client.get("/v1/saju/luck")
    assert r.status_code == 200
    body = r.json()
    assert {"date", "se_un", "wol_un", "il_un"} <= body.keys()


def test_openapi_lists_saju_routes():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/v1/saju/analyze" in paths
    assert "/v1/saju/luck" in paths
