#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "   EduPredict AI - Inicializacao Local                     "
echo "=========================================================="

if ! command -v python3 &> /dev/null; then
    echo "Erro: python3 nao encontrado no sistema. Instale o Python 3."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python detectado: $PYTHON_VERSION"

if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual 'venv'..."
    python3 -m venv venv
    echo "Ambiente virtual criado."
else
    echo "Ambiente virtual 'venv' existente."
fi

source venv/bin/activate

echo "Verificando dependencias..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "Dependencias prontas."

mkdir -p uploads models

export PORT=${PORT:-5001}

echo "--------------------------------------------------------"
echo "Servidor iniciando em: http://localhost:${PORT}"
echo "Pressione Ctrl+C para encerrar."
echo "--------------------------------------------------------"

exec python -m app.app
