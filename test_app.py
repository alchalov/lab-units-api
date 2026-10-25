"""Автоматические тесты LabUnits API. Запуск: python -m pytest -v"""

import pytest
from fastapi.testclient import TestClient

import app_final
from app_final import app

client = TestClient(app)


# --- Служебные маршруты ---

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_matches_settings():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": app_final.APP_NAME,
        "version": app_final.APP_VERSION,
    }


def test_root_points_to_docs():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


# --- Справочник показателей ---

def test_list_analytes():
    response = client.get("/analytes")
    data = response.json()
    assert response.status_code == 200
    assert data["count"] == len(data["analytes"]) == 9
    codes = {item["code"] for item in data["analytes"]}
    assert {"glucose", "creatinine", "hemoglobin"} <= codes


def test_get_analyte_is_case_insensitive():
    response = client.get("/analytes/GLUCOSE")
    assert response.status_code == 200
    assert response.json()["code"] == "glucose"
    assert response.json()["factor"] == 18.02


def test_get_unknown_analyte_returns_404():
    response = client.get("/analytes/sodium")
    assert response.status_code == 404
    assert "sodium" in response.json()["detail"]


# --- Пересчёт единиц ---

@pytest.mark.parametrize(
    "code, si_value, expected",
    [
        ("glucose", 5.5, 99.11),
        ("cholesterol", 5.0, 193.05),
        ("bilirubin", 17.1, 1.0),
        ("calcium", 2.5, 10.0),
        ("hemoglobin", 140, 14.0),
    ],
)
def test_convert_si_to_conventional(code, si_value, expected):
    response = client.get(f"/convert/{code}", params={"value": si_value})
    assert response.status_code == 200
    assert response.json()["result"]["value"] == pytest.approx(expected, abs=0.01)


def test_convert_conventional_to_si():
    response = client.get("/convert/glucose", params={"value": 99, "to": "si"})
    data = response.json()
    assert response.status_code == 200
    assert data["input"]["unit"] == "mg/dL"
    assert data["result"]["unit"] == "mmol/L"
    assert data["result"]["value"] == pytest.approx(5.49, abs=0.01)


def test_convert_negative_value_returns_422():
    response = client.get("/convert/glucose", params={"value": -1})
    assert response.status_code == 422


def test_convert_invalid_direction_returns_422():
    response = client.get("/convert/glucose", params={"value": 5, "to": "xyz"})
    assert response.status_code == 422


def test_convert_without_value_returns_422():
    response = client.get("/convert/glucose")
    assert response.status_code == 422


def test_convert_unknown_analyte_returns_404():
    response = client.get("/convert/sodium", params={"value": 5})
    assert response.status_code == 404


# --- Настройки из окружения ---

def test_precision_is_read_from_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_PRECISION", "4")
    assert app_final.read_precision() == 4


@pytest.mark.parametrize("bad_value", ["abc", "-1", "10"])
def test_invalid_precision_falls_back_to_2(monkeypatch, bad_value):
    monkeypatch.setenv("DEFAULT_PRECISION", bad_value)
    assert app_final.read_precision() == 2
