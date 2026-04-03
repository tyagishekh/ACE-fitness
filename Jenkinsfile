pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh 'python -m venv .venv'
                sh '. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'
            }
        }

        stage('Build Validation') {
            steps {
                sh '. .venv/bin/activate && python -m py_compile app.py'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '. .venv/bin/activate && pytest -q'
            }
        }
    }
}
