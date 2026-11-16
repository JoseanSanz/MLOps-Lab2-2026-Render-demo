"""
Gradio GUI of the calculator (frontend).

It is a microservice of its own: it does not import the logic of the project, it
only calls the /calculate endpoint of the REST API (backend) through HTTP. The URL
of the API is read from the API_URL environment variable, so it does not need to
be hard-coded. It is hosted on Render as a web service of its own (see README.md).
"""

import os

import gradio as gr
import requests

# URL of the API created with FastAPI (environment variable of the GUI service)
API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")

# Render's free services sleep after ~15 min of inactivity and need up to a minute to
# wake up; the first request may have to wake up the API too, so the timeout is generous
TIMEOUT = float(os.environ.get("API_TIMEOUT", "90"))

OPERATIONS = ["add", "subtract", "multiply", "divide", "power"]


def calculate(a, b, operation):
    """Calls the API and returns the result or a readable error message."""
    if a is None or b is None:
        return "Error: both numbers are required"

    payload = {"op": operation, "a": a, "b": b}
    try:
        response = requests.post(f"{API_URL}/calculate", data=payload, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return "Error: the API did not answer in time (it may be starting, try again)"
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
        "The first request may take a while if the API is starting."
    ),
)

# Launch the GUI: listening on all the interfaces (0.0.0.0) and on the port given by
# the hosting platform in the PORT variable (7860, Gradio's default, locally)
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
