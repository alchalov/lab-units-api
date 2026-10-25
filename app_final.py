"""LabUnits API — перевод результатов лабораторных анализов между единицами измерения."""

from fastapi import FastAPI, HTTPException

APP_NAME = "LabUnits API"
APP_VERSION = "0.1.0"

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

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Сервис перевода результатов лабораторных анализов "
    "между единицами СИ и традиционными единицами.",
)


def find_analyte(code: str) -> dict:
    """Ищет показатель по коду без учёта регистра или возвращает 404."""
    analyte = ANALYTES.get(code.lower())
    if analyte is None:
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
