# 🎓 EduPredict AI • TCC Predição de Faltas Escolares

Sistema inteligente de suporte à decisão educacional para **predição de absenteísmo escolar**, integrando **Machine Learning**, **Dados Abertos (APIs Open-Meteo e BrasilAPI)**, **Dashboard de Pesos/Importâncias** e **Versionamento de Modelos**, totalmente conteinerizado com **Docker**.

---

## 🚀 Funcionalidades Principais

1. **🔮 Simulador de Predição de Faltas**:
   - Predição precisa da porcentagem (%) de ausências esperada para o turno escolar.
   - Classificação em faixas de risco (🟢 Baixo <10%, 🟡 Moderado 10-18%, 🔴 Crítico/Alto >18%).
   - Gauge gráfico dinâmico animado e projeções práticas de impacto (ex: quantas ausências em uma turma de 40 alunos e em uma escola de 500 alunos).
   - Histórico em tempo real das simulações da sessão com comparação de cenários.

2. **🌐 Preenchimento Automático via Dados Abertos (Open Data)**:
   - **Open-Meteo API**: Coleta em tempo real da previsão de tempo, clima (Ensolarado, Nublado, Chuvoso) e precipitação (chuva em mm) para a cidade de São Paulo sem necessidade de chave de API.
   - **BrasilAPI**: Consulta automática de feriados nacionais e detecção de pontes/emendas de feriado (vésperas e pós-feriado).
   - Botão **"Preencher com Dados Abertos"** para sincronizar as variáveis com 1 clique.

3. **📊 Dashboard de Pesos & Importâncias (Feature Importance)**:
   - Gráfico de barras horizontais com a contribuição percentual de cada variável (Turno, Clima, Trânsito, Feriados, Chuva, Jogos, etc.).
   - Gráfico donut interativo de distribuição de relevância.
   - Tabela analítica com o detalhamento das features dummificadas (One-Hot Encoded) e numéricas extraídas do Pipeline.
   - Indicadores de desempenho em produção: **MAE**, **RMSE** e **R²**.

4. **🚀 Treinamento Comparativo & Versionamento de Modelos**:
   - Upload de novos arquivos CSV (drag & drop) ou seleção de bases padrão existentes (`base_1500_linhas_sao_paulo.csv`, etc.).
   - Treinamento comparativo automatizado de 4 algoritmos:
     - 🌲 *Random Forest Regressor*
     - 🚀 *Gradient Boosting Regressor*
     - ⚡ *HistGradientBoosting Regressor*
     - 📐 *Ridge Regressor*
   - O algoritmo com menor MAE na partição de validação é selecionado e salvo com tag de versão (`v1.1`, `v2.0`, etc.).
   - Tabela de versionamento com métricas completas e botão para **ativar qualquer versão** instantaneamente em produção.

---

## 🚀 Executando Localmente (Sem Docker - Automático)

O projeto conta com um script automatizado que **cria o ambiente virtual (`venv`) automaticamente**, instala todas as dependências e inicializa o servidor:

### 1. Iniciar com 1 comando (Linux / macOS):
```bash
./run_local.sh
```
> *(Caso necessário, conceda permissão de execução com `chmod +x run_local.sh`)*

O script realiza automaticamente:
1. Verificação da versão do Python 3 no sistema.
2. Criação automática da pasta `venv` (se ainda não existir).
3. Ativação do ambiente virtual (`source venv/bin/activate`).
4. Instalação e verificação das dependências via `requirements.txt`.
5. Inicialização da aplicação Flask na porta `5001` (evitando conflito com o AirPlay do macOS na porta 5000).

---

### 2. Executando Passo a Passo Manualmente (Alternativa):

Se preferir executar cada comando manualmente no terminal:

```bash
# 1. Cria o ambiente virtual
python3 -m venv venv

# 2. Ativa o ambiente virtual
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instala as dependências
pip install -r requirements.txt

# 4. Inicia o servidor Flask
python -m app.app
```

---

### 3. Acessar a Aplicação:
Abra seu navegador em:
👉 **[http://localhost:5001](http://localhost:5001)**

---

## 🐳 Executando com Docker (Opcional)

Se preferir rodar em containers Docker:

### 1. Construir e Iniciar os Containers:
```bash
docker compose up --build
```

### 2. Acessar a Aplicação:
Abra seu navegador em:
👉 **[http://localhost:5001](http://localhost:5001)**

Para parar a execução:
```bash
docker compose down
```

> **Nota de Persistência:** O volume `./models` mantém todos os modelos treinados e o registro de versões preservados mesmo após reiniciar o container.

---

## 🔌 Documentação da API REST

A aplicação disponibiliza endpoints JSON para integração externa:

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/predict` | Realiza a predição da porcentagem de faltas recebendo o JSON dos parâmetros. |
| `GET` | `/api/weights` | Retorna as importâncias e pesos relativos das variáveis do modelo ativo. |
| `GET` | `/api/models` | Lista todos os modelos versionados e qual está ativo em produção. |
| `POST` | `/api/models/activate` | Define uma versão específica de modelo como o modelo ativo. |
| `POST` | `/api/train` | Recebe arquivo CSV via formulário multipart e retreina/versiona novo modelo. |
| `GET` | `/api/download-template` | Faz o download da planilha modelo CSV com cabeçalhos e exemplos para treino. |
| `GET` | `/api/open-data` | Consulta clima e feriados nas APIs abertas para a data informada. |
| `GET` | `/api/health` | Health check da aplicação para orquestradores e monitoramento. |

---

## 📁 Estrutura do Projeto

```text
tcc-predicao-faltas/
├── app/
│   ├── app.py                  # Rotas e endpoints REST da aplicação Flask
│   ├── model_service.py        # Gestão, inferência e versionamento de modelos
│   ├── trainer.py              # Pipeline Scikit-learn, split, fit e cálculo de métricas
│   ├── open_data_service.py    # Integração com APIs abertas (Open-Meteo & BrasilAPI)
│   ├── static/
│   │   ├── css/style.css       # Estilização moderna e responsiva (Dark Theme)
│   │   ├── js/app.js           # Lógica do front-end, gráficos Chart.js e AJAX
│   │   └── template_treinamento_modelo.csv # Planilha modelo para novos treinos
│   └── templates/
│       └── index.html          # Interface web unificada com abas
├── models/
│   ├── registry.json           # Catálogo versionado de modelos com histórico e métricas
│   └── modelo_falta_escola_1500.joblib
├── run_local.sh                # Script de inicialização local com criação automática de venv
├── Dockerfile                  # Especificação do container Python 3.11 com Gunicorn
├── docker-compose.yml          # Configuração de orquestração e volumes
├── requirements.txt            # Dependências Python (Flask, Scikit-learn, Pandas, etc.)
└── README.md
```
