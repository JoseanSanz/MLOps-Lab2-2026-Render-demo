"""
REST API of the calculator built with FastAPI.

Endpoints:
    GET  /           home page with a link to the interactive documentation
    GET  /health     health check (Docker HEALTHCHECK, CI smoke test, Render)
    POST /calculate  arithmetical operation (form data: op, a, b)
"""

import math
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from mylib.calculator import add, divide, multiply, power, subtract

# Operations supported by the API and the function that implements each one
OPERATIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "power": power,
}

# Create an instance of FastAPI
app = FastAPI(
    title="API of the Calculator using FastAPI",
    description="API to perform arithmetical operations using mylib.calculator",
    version="1.1.0",
)

# The templates folder is located relative to this file, so the API works
# whatever the working directory is (locally, in Docker or in the tests)
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Home page with a link to the interactive documentation (/docs)."""
    return templates.TemplateResponse(request, "home.html")


@app.get("/health")
def health():
    """Health check: it answers while the API is running."""
    return {"status": "ok"}


@app.post("/calculate")
def calculate(op: str = Form(), a: float = Form(), b: float = Form()):
    """
    Performs an arithmetical operation according to the input parameters.

    - op: add, subtract, multiply, divide or power (case-insensitive)
    - a, b: operands
    """
    op = op.lower()
    operation = OPERATIONS.get(op)
    if operation is None:
        raise HTTPException(status_code=400, detail="Invalid operation")
    if op == "divide" and b == 0:
        raise HTTPException(status_code=400, detail="Zero division not allowed")

    try:
        result = operation(a, b)
    except OverflowError as exc:
        raise HTTPException(status_code=400, detail="Result too large") from exc

    # JSON cannot represent complex numbers, inf or nan
    if isinstance(result, complex) or not math.isfinite(result):
        raise HTTPException(
            status_code=400, detail="The result is not a finite real number"
        )

    return {"result": result}


# Entry point (for direct execution only: python -m api.api)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)
