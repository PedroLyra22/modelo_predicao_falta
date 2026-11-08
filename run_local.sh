#!/usr/bin/env bash
# ==============================================================================
# EduPredict AI - Script de Inicialização Local Automática com venv
# ==============================================================================

set -e

# Navega para o diretório raiz do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🎓 ======================================================"
echo "🎓   EduPredict AI • Inicialização Local (Sem Docker)   "
echo "🎓 ======================================================"

# 1. Verifica se python3 está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: python3 não foi encontrado no sistema. Por favor, instale o Python 3."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "🔍 Detectado: $PYTHON_VERSION"

# 2. Cria o ambiente virtual venv se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual 'venv' automaticamente..."
    python3 -m venv venv
    echo "✅ Ambiente virtual criado com sucesso!"
else
    echo "✅ Ambiente virtual 'venv' já existente."
fi

# 3. Ativa o ambiente virtual
echo "⚡ Ativando venv..."
source venv/bin/activate

# 4. Verifica e instala/atualiza dependências
echo "📥 Verificando dependências do requirements.txt..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✅ Dependências verificadas e prontas!"

# 5. Garante diretórios necessários
mkdir -p uploads models

# 6. Define porta (padrão 5001 para evitar conflito com AirPlay na porta 5000 do macOS)
export PORT=${PORT:-5001}

echo "--------------------------------------------------------"
echo "🚀 Servidor iniciando em: http://localhost:${PORT}"
echo "👉 Pressione Ctrl+C para encerrar o servidor a qualquer momento."
echo "--------------------------------------------------------"

# 7. Inicia a aplicação Flask
exec python -m app.app
