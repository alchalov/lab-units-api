"""LabUnits API — перевод результатов лабораторных анализов между единицами измерения."""

from fastapi import FastAPI

APP_NAME = "LabUnits API"
APP_VERSION = "0.1.0"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Cервис перевода результатов лабораторных анализов "
    "между единицами СИ и традиционными единицами.",
)


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
