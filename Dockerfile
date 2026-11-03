FROM python:3.11-slim

# Evita geração de bytecode .pyc e buffer de saída do stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.app:app

WORKDIR /app

# Instala ferramentas básicas de compilação para certas bibliotecas C se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Cria diretórios para persistência
RUN mkdir -p /app/models /app/uploads

EXPOSE 5000

# Executa o servidor Gunicorn com 2 workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app.app:app"]
