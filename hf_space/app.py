"""
Gradio GUI of the calculator, hosted in a Hugging Face Space.

It calls the /calculate endpoint of the API deployed on Render. The URL of the
API is read from the API_URL environment variable (a variable of the Space),
so it does not need to be hard-coded.
"""

import os

import gradio as gr
import requests

# ZeroGPU Spaces (the free option for Gradio Spaces) do not start without at least one
# function decorated with @spaces.GPU. This GUI does not need a GPU (it only calls the
# backend through HTTP), so the function is empty and never called: it does not use
# the GPU quota. The `spaces` package only exists in Hugging Face Spaces.
try:
    import spaces

    @spaces.GPU
    def zero_gpu_startup_check():
        """Required by ZeroGPU Spaces to start (never called)."""

except ImportError:  # locally and in the CI
    pass

# URL of the API created with FastAPI (set API_URL in the Space settings)
API_URL = os.environ.get(
    "API_URL", "https://calculator-api-latest-r081.onrender.com"
).rstrip("/")

# Render's free instances sleep after ~15 min of inactivity and need up to a
# minute to wake up, so the timeout must be generous
TIMEOUT = float(os.environ.get("API_TIMEOUT", "60"))

OPERATIONS = ["add", "subtract", "multiply", "divide", "power"]


def calculate(a, b, operation):
    """Calls the API and returns the result or a readable error message."""
    if a is None or b is None:
        return "Error: both numbers are required"

    payload = {"op": operation, "a": a, "b": b}
    try:
        response = requests.post(f"{API_URL}/calculate", data=payload, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return "Error: the API did not answer in time (it may be waking up, try again)"
    except requests.exceptions.RequestException as exc:
        return f"Error: could not connect to the API ({exc})"

    if response.ok:
        return str(response.json()["result"])

    try:
        detail = response.json().get("detail", response.text)
    except ValueError:  # the error body is not JSON
        detail = response.text
    return f"Error {response.status_code}: {detail}"


# GUI created using Gradio
demo = gr.Interface(
    fn=calculate,
    inputs=[
        gr.Number(label="Number X"),
        gr.Number(label="Number Y"),
        gr.Dropdown(choices=OPERATIONS, value="add", label="Arithmetical operation"),
    ],
    outputs=gr.Textbox(label="Result"),
    title="Calculator created with FastAPI and Gradio",
    description=(
        "Interactive calculator using the /calculate endpoint of the API. "
        "The first request may take up to a minute if the API is asleep."
    ),
)

# Launch the GUI
if __name__ == "__main__":
    demo.launch()
