"""LabUnits API — перевод результатов лабораторных анализов между единицами измерения."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

# --- Настройки из переменных окружения (значения по умолчанию — после запятой) ---
APP_NAME = os.getenv("APP_NAME", "LabUnits API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def read_precision() -> int:
    """Читает DEFAULT_PRECISION; при ошибке берёт 2, чтобы сервис не падал."""
    raw = os.getenv("DEFAULT_PRECISION", "2")
    try:
        precision = int(raw)
    except ValueError:
        precision = -1
    if not 0 <= precision <= 6:
        logging.getLogger("labunits").warning(
            "Некорректное DEFAULT_PRECISION=%r, используется 2", raw
        )
        return 2
    return precision


# --- Журнал событий ---
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("labunits")

DEFAULT_PRECISION = read_precision()

# Справочник показателей.
# factor — коэффициент пересчёта: значение в традиционных единицах = значение в СИ * factor.
# Источник коэффициентов: Labcorp, SI Unit Conversion Table
# https://www.labcorp.com/resource/si-unit-conversion-table
ANALYTES = {
    "glucose": {
        "name": "Глюкоза",
        "si_unit": "mmol/L",
        "conventional_unit": "mg/dL",
        "factor": 18.02,
    },
    "cholesterol": {
        "name": "Холестерин общий",
        "si_unit": "mmol/L",
        "conventional_unit": "mg/dL",
        "factor": 38.61,
    },
    "triglycerides": {
        "name": "Триглицериды",
        "si_unit": "mmol/L",
        "conventional_unit": "mg/dL",
        "factor": 88.5,
    },
    "creatinine": {
        "name": "Креатинин",
        "si_unit": "umol/L",
        "conventional_unit": "mg/dL",
        "factor": 0.0113,
    },
    "uric_acid": {
        "name": "Мочевая кислота",
        "si_unit": "umol/L",
        "conventional_unit": "mg/dL",
        "factor": 0.0169,
    },
    "bilirubin": {
        "name": "Билирубин общий",
        "si_unit": "umol/L",
        "conventional_unit": "mg/dL",
        "factor": 0.0585,
    },
    "calcium": {
        "name": "Кальций общий",
        "si_unit": "mmol/L",
        "conventional_unit": "mg/dL",
        "factor": 4.0,
    },
    "iron": {
        "name": "Железо сывороточное",
        "si_unit": "umol/L",
        "conventional_unit": "ug/dL",
        "factor": 5.587,
    },
    "hemoglobin": {
        "name": "Гемоглобин",
        "si_unit": "g/L",
        "conventional_unit": "g/dL",
        "factor": 0.1,
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Сервис запущен: %s %s, показателей: %d, знаков после запятой: %d",
        APP_NAME, APP_VERSION, len(ANALYTES), DEFAULT_PRECISION,
    )
    yield
    logger.info("Сервис остановлен")


app = FastAPI(
    lifespan=lifespan,
    title=APP_NAME,
    version=APP_VERSION,
    description="Сервис перевода результатов лабораторных анализов "
    "между единицами СИ и традиционными единицами.",
)


def find_analyte(code: str) -> dict:
    """Ищет показатель по коду без учёта регистра или возвращает 404."""
    analyte = ANALYTES.get(code.lower())
    if analyte is None:
        logger.warning("Запрошен неизвестный показатель: %s", code)
        raise HTTPException(
            status_code=404,
            detail=f"Показатель '{code}' не найден. Список кодов: /analytes",
        )
    return analyte


@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "message": "Сервис работает",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION}


@app.get("/analytes")
def list_analytes():
    """Список всех показателей, для которых доступен пересчёт."""
    return {
        "count": len(ANALYTES),
        "analytes": [{"code": code, **data} for code, data in ANALYTES.items()],
    }


@app.get("/analytes/{code}")
def get_analyte(code: str):
    """Карточка одного показателя по его коду, например /analytes/glucose."""
    return {"code": code.lower(), **find_analyte(code)}


@app.get("/convert/{code}")
def convert(
    code: str,
    value: float = Query(..., ge=0, description="Результат анализа, не меньше 0"),
    to: Literal["conventional", "si"] = Query(
        "conventional",
        description="Куда переводить: conventional — в традиционные единицы, si — в СИ",
    ),
):
    """Переводит результат анализа между единицами СИ и традиционными единицами."""
    analyte = find_analyte(code)
    factor = analyte["factor"]

    if to == "conventional":
        result = value * factor
        from_unit, to_unit = analyte["si_unit"], analyte["conventional_unit"]
    else:
        result = value / factor
        from_unit, to_unit = analyte["conventional_unit"], analyte["si_unit"]

    rounded = round(result, DEFAULT_PRECISION)
    logger.info(
        "Пересчёт %s: %s %s -> %s %s", code.lower(), value, from_unit, rounded, to_unit
    )
    return {
        "code": code.lower(),
        "name": analyte["name"],
        "input": {"value": value, "unit": from_unit},
        "result": {"value": rounded, "unit": to_unit},
        "factor": factor,
    }
