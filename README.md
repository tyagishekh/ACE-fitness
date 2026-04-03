# ACEest Fitness & Gym CI/CD Project

This repository contains a Flask-based fitness and gym management API for the ACEest Fitness & Gym DevOps assignment. The project demonstrates a full delivery workflow with unit testing, Docker containerization, GitHub Actions CI, and a Jenkins build pipeline.

## Project Structure

```text
.
|-- .github/workflows/main.yml
|-- app.py
|-- Dockerfile
|-- Jenkinsfile
|-- requirements.txt
|-- tests/test_app.py
`-- README.md
```

## Application Overview

The Flask application provides endpoints to:

- Check service health.
- View available training programs.
- List gym members.
- Add a new member with input validation.
- View a member by ID.
- Retrieve dashboard statistics for the gym.

The project keeps business rules in reusable Python functions and classes so that both API behaviour and internal logic can be validated with Pytest.

## Local Setup

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the Flask application

```bash
python app.py
```

The API starts on `http://localhost:5000`.

## Manual Test Execution

Run the Pytest suite with:

```bash
pytest -q
```

You can also validate the Python build step used in CI:

```bash
python -m py_compile app.py
```

## Docker Usage

### Build the image

```bash
docker build -t aceest-fitness-app .
```

### Run the container

```bash
docker run --rm -p 5000:5000 aceest-fitness-app
```

### Run tests in the container

```bash
docker run --rm aceest-fitness-app pytest -q
```

## GitHub Actions Pipeline

The workflow file is located at `.github/workflows/main.yml` and runs on every `push` and `pull_request`.

Pipeline stages:

1. Check out the latest source from GitHub.
2. Install Python dependencies.
3. Perform a build validation using `python -m py_compile app.py`.
4. Build the Docker image.
5. Run the Pytest suite on the GitHub Actions runner.
6. Run the same Pytest suite inside the Docker container for environment parity.

This ensures that the application code is valid, the container builds successfully, and the tests pass in both the host runner and the containerized environment.

## Jenkins Build Integration

The repository includes a `Jenkinsfile` for a declarative Jenkins pipeline. A Jenkins job can be configured to:

1. Pull the latest repository state from GitHub.
2. Create a fresh Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Run a clean build validation using `python -m py_compile app.py`.
5. Execute `pytest -q` as a secondary quality gate.

Recommended Jenkins setup:

- Create a Pipeline job in Jenkins.
- Point the job to this GitHub repository.
- Use the repository `Jenkinsfile`.
- Optionally add a GitHub webhook so every push can trigger a Jenkins build.

## Version Control Guidance

Branches:

- `master` for stable code
- `Dev` for feature development
- `IaC` for CI/CD

## Deliverables Checklist

- Flask source code in `app.py`
- Dependency list in `requirements.txt`
- Pytest suite in `tests/test_app.py`
- Dockerfile for containerized execution
- GitHub Actions workflow in `.github/workflows/main.yml`
- Jenkins pipeline in `Jenkinsfile`
- Professional setup and CI/CD documentation in `README.md`
