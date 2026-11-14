[![CICD](https://github.com/JoseanSanz/MLOps-Lab2-demo/actions/workflows/CICD.yml/badge.svg)](https://github.com/JoseanSanz/MLOps-Lab2-demo/actions/workflows/CICD.yml)

# MLOps-Lab2-demo

Demo for the second lab of the MLOps subject. A simple calculator is used as the
application, so that the focus is on the MLOps workflow. In this lab you will learn to:

* Organize a Python project with **uv** (dependencies pinned in `uv.lock`) and a **Makefile**.
* Test it with **pytest** (unit and integration tests) and check it with **black** and **pylint**.
* Expose the logic as a REST API with **FastAPI**.
* **Containerize** the API with **Docker**.
* Build a **CI/CD pipeline** with **GitHub Actions** that tests the code, builds and
  publishes the image, deploys the API on **Render** and the GUI on **Hugging Face Spaces**.
* Create a GUI with **Gradio** that uses the deployed API.

## Architecture

```
                 git push (main)
 Developer ───────────────────────► GitHub ──► GitHub Actions (CICD.yml)
                                                 │
                    1. build ── format, lint, tests
                    2. docker ── build image, smoke test, push to Docker Hub
                    3. deploy-render ── Render deploy hook ──► API (FastAPI) on Render
                    4. deploy-hf ── upload hf_space/ ──────► GUI (Gradio) on Hugging Face
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
├── hf_space/                  # Gradio GUI uploaded to the Hugging Face Space
│   ├── app.py
│   ├── requirements.txt
│   └── README.md              # Space configuration (sdk, sdk_version, app_file)
├── scripts/deploy_hf_space.py # uploads hf_space/ to the Space (used by the CI/CD)
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
make run-space                          # Gradio GUI against the local API (in another terminal)
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
| `deploy-render` | push to `main` | calls the Render deploy hook (Render pulls `:latest`) |
| `deploy-hf` | push to `main` | uploads `hf_space/` to the Space and sets its `API_URL` variable |

Pull requests run the tests and build the image but never deploy.

### Secrets (Settings → Secrets and variables → Actions)

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub user |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Account settings → Personal access tokens) |
| `RENDER_DEPLOY_HOOK_URL` | full deploy hook URL of the Render service (Settings → Deploy Hook) |
| `RENDER_API_URL` | public URL of the API on Render, e.g. `https://calculator-api-xxxx.onrender.com` |
| `HF_USERNAME` | Hugging Face user |
| `HF_TOKEN` | Hugging Face token with write permission |

### Setting up Render (once)

1. New → Web Service → *Existing image*: `docker.io/<DOCKERHUB_USERNAME>/calculator-api:latest`.
2. Free instance type. Render sets the `PORT` variable and the image listens on it.
3. Copy the Deploy Hook URL into the `RENDER_DEPLOY_HOOK_URL` secret and the service URL into `RENDER_API_URL`.

Free instances sleep after ~15 minutes of inactivity and take up to a minute to wake up:
the first request after a while is slow (the GUI waits up to 60 s).

### Hugging Face Space

The pipeline creates the Space `<HF_USERNAME>/MLOps-Lab2-demo` if it does not exist,
sets its `API_URL` variable and uploads the content of `hf_space/`. Do not edit the
files directly in the Space: change them in this repository.
