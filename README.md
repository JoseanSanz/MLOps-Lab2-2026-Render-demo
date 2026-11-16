[![CICD](https://github.com/JoseanSanz/MLOps-Lab2-demo/actions/workflows/CICD.yml/badge.svg)](https://github.com/JoseanSanz/MLOps-Lab2-demo/actions/workflows/CICD.yml)

# MLOps-Lab2-demo

Demo for the second lab of the MLOps subject. A simple calculator is used as the
application, so that the focus is on the MLOps workflow. In this lab you will learn to:

* Organize a Python project with **uv** (dependencies pinned in `uv.lock`) and a **Makefile**.
* Test it with **pytest** (unit and integration tests) and check it with **black** and **pylint**.
* Expose the logic as a REST API with **FastAPI** (a microservice: the backend).
* **Containerize** the API with **Docker**.
* Build a **CI/CD pipeline** with **GitHub Actions** that tests the code, builds and
  publishes the image and deploys the API and the GUI on **Render**.
* Create a GUI with **Gradio** (the frontend, another service) that uses the deployed API.

There is another version of this demo that uses **Modal** instead of Render:
[MLOps-Lab2-2026-Modal-demo](https://github.com/JoseanSanz/MLOps-Lab2-2026-Modal-demo).

## Architecture

```
                 git push (main)
 Developer ───────────────────────► GitHub ──► GitHub Actions (CICD.yml)
                                                 │
                    1. build ── format, lint, tests
                    2. docker ── build image, smoke test, push to Docker Hub
                    3. deploy-backend ── deploy hook ──► API (FastAPI) on Render
                    4. deploy-gui ── deploy hook ──────► GUI (Gradio) on Render
                                                                      │
                                                  POST /calculate ◄───┘
```

## Project structure

```
├── mylib/calculator.py        # business logic (shared by the CLI and the API)
├── cli/cli.py                 # command-line interface (click)
├── api/api.py                 # REST API (FastAPI): /, /health, /calculate
├── templates/home.html        # home page of the API
├── tests/                     # unit tests (logic, GUI) and integration tests (CLI, API)
├── gui/                       # Gradio GUI (frontend): a separate web service on Render
│   ├── app.py
│   └── requirements.txt       # dependencies of the GUI service only
├── Dockerfile                 # image of the API (only runtime dependencies)
├── Makefile                   # common tasks
├── pyproject.toml / uv.lock   # dependencies (runtime and dev group)
└── .github/workflows/CICD.yml # CI/CD pipeline
```

## Run it locally

Requirements: [uv](https://docs.astral.sh/uv/) (installed by `make install` if missing) and Docker.

```bash
make install          # installs all the dependencies (runtime + dev)
make test             # tests with coverage (fails below 90 %)
make format lint      # formats the code and runs pylint

uv run python -m cli.cli add 1 2        # CLI
make run-api                            # API at http://localhost:8000/docs
make run-gui                            # Gradio GUI at http://localhost:7860 (in another terminal)
```

With Docker:

```bash
make docker-build     # docker build -t calculator-api .
make docker-run       # docker run --rm -p 8000:8000 calculator-api
curl http://localhost:8000/health
curl -X POST http://localhost:8000/calculate -d "op=add" -d "a=2" -d "b=3"
```

When you change the dependencies, use `uv add <package>` (or `uv add --dev <package>`)
and commit the updated `uv.lock`: the CI and the Docker image install exactly those versions.

## CI/CD pipeline

| Job | When | What it does |
|---|---|---|
| `build` | push and pull request to `main` | `make install`, `make format-check`, `make lint`, `make test` |
| `docker` | after `build` | builds the image and checks that the container answers `/health`; on `main` it pushes `:latest` and `:<commit SHA>` to Docker Hub |
| `deploy-backend` | push to `main` | calls the deploy hook of the API service (Render pulls `:latest`) |
| `deploy-gui` | push to `main` | calls the deploy hook of the GUI service (Render builds `gui/` from this commit) |

Pull requests run the tests and build the image but never deploy.

### Secrets (Settings → Secrets and variables → Actions)

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub user |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Account settings → Personal access tokens) |
| `RENDER_DEPLOY_HOOK_URL` | deploy hook URL of the API service (Settings → Deploy Hook) |
| `RENDER_GUI_DEPLOY_HOOK_URL` | deploy hook URL of the GUI service (Settings → Deploy Hook) |

### Setting up Render (once)

**API service (backend)**

1. New → Web Service → *Existing image*: `docker.io/<DOCKERHUB_USERNAME>/calculator-api:latest`.
2. Free instance type. Render sets the `PORT` variable and the image listens on it.
3. Copy the Deploy Hook URL into the `RENDER_DEPLOY_HOOK_URL` secret, and write down the
   URL of the service (e.g. `https://calculator-api-xxxx.onrender.com`).

**GUI service (frontend)**

1. New → Web Service → *Git provider*: this repository, branch `main`.
2. Root Directory: `gui` · Language: Python 3 · Build Command: `pip install -r requirements.txt`
   · Start Command: `python app.py` · Free instance type.
3. Environment variables: `API_URL` = URL of the API service (step 3 above), and
   `PYTHON_VERSION` = `3.13` if Render's default version is a different one.
4. Settings → Auto-Deploy: **Off**, so that the GUI is only deployed by the pipeline
   (after the tests pass). Copy its Deploy Hook URL into the `RENDER_GUI_DEPLOY_HOOK_URL` secret.

Free services sleep after ~15 minutes of inactivity and take up to a minute to wake up.
The first visit after a while may have to wake up both services, so it is slow (the GUI
waits up to 90 s for the API).
