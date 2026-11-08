# EduPredict AI - TCC Predicao de Faltas Escolares

Sistema inteligente de suporte a decisao educacional para **predicao de absenteismo escolar**, integrando **Machine Learning**, **Dados Abertos (APIs Open-Meteo e BrasilAPI)**, **Dashboard de Pesos/Importancias** e **Versionamento de Modelos**.

---

## Funcionalidades Principais

1. **Simulador de Predicao de Faltas**:
   - Predicao da porcentagem (%) de ausencias esperada para o turno escolar.
   - Classificacao em faixas de risco (Baixo <10%, Moderado 10-18%, Critico/Alto >18%).
   - Projeções de impacto pratico (estimativa de ausencias em turma de 40 alunos e escola de 500 alunos).
   - Historico de simulacoes da sessao para comparacao de cenarios.

2. **Preenchimento Automatico via Dados Abertos (Open Data)**:
   - **Open-Meteo API**: Previsao de tempo, clima e precipitacao para Sao Paulo em tempo real sem necessidade de chave de API.
   - **BrasilAPI**: Consulta automatica de feriados nacionais e deteccao de emendas e pontes de feriado.
   - Botao para sincronizar as variaveis com um clique.

3. **Dashboard de Pesos e Importancias (Feature Importance)**:
   - Grafico de barras horizontais com a contribuicao percentual de cada variavel (Turno, Clima, Transito, Feriados, Chuva, Jogos, etc.).
   - Grafico donut de distribuicao de relevância.
   - Detalhamento analitico das features categoricas dummificadas (One-Hot Encoded) e numericas.
   - Indicadores de desempenho: **MAE**, **RMSE** e **R2**.

4. **Treinamento Comparativo e Versionamento de Modelos**:
   - Upload de novos arquivos CSV ou selecao de bases padrao existentes.
   - Download de planilha template em CSV com estrutura correta e exemplos.
   - Treinamento comparativo automatizado de 4 algoritmos:
     - Random Forest Regressor
     - Gradient Boosting Regressor
     - HistGradientBoosting Regressor
     - Ridge Regressor
   - Selecao automatica do modelo com menor MAE na particao de teste.
   - Historico de versoes com ativacao imediata de qualquer modelo em producao.

---

## Execucao Local

O projeto conta com um script automatizado que gerencia o ambiente virtual (`venv`), instala as dependencias e inicializa o servidor.

### Execucao Rapida (Recomendado)

```bash
./run_local.sh
```

O script executa automaticamente:
1. Verificacao do Python 3.
2. Criacao da pasta `venv` (caso nao exista).
3. Ativacao do ambiente virtual.
4. Instalacao e checagem de dependencias via `requirements.txt`.
5. Inicializacao do servidor Flask na porta `5001`.

### Execucao Manual (Passo a Passo)

```bash
# 1. Cria o ambiente virtual
python3 -m venv venv

# 2. Ativa o ambiente virtual
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instala as dependencias
pip install -r requirements.txt

# 4. Inicia o servidor Flask
python -m app.app
```

Acesse a aplicacao no navegador:
**http://localhost:5001**

---

## Documentacao da API REST

A aplicacao disponibiliza endpoints JSON para integracao externa:

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/api/predict` | Realiza a predicao da porcentagem de faltas recebendo o JSON dos parametros. |
| `GET` | `/api/weights` | Retorna as importancias e pesos relativos das variaveis do modelo ativo. |
| `GET` | `/api/models` | Lista todos os modelos versionados e indica o modelo ativo. |
| `POST` | `/api/models/activate` | Define uma versao especifica como o modelo ativo. |
| `POST` | `/api/train` | Recebe arquivo CSV via multipart/form-data, retreina e versiona um novo modelo. |
| `GET` | `/api/download-template` | Download da planilha modelo CSV com cabecalhos e exemplos. |
| `GET` | `/api/open-data` | Consulta clima, feriados e variaveis contextuais nas APIs abertas. |
| `GET` | `/api/health` | Health check da aplicacao. |

---

## Documentacao Tecnica e Artigos

Para aprofundamento teorico e metodologico:

- [Teoria Matematica, Engenharia de Features e Treinamento](docs/TEORIA_E_TREINAMENTO_DO_MODELO.md):
  - Formulacao matematica da tarefa de regressao supervisionada.
  - Pre-processamento matricial, imputacao e codificacao categorica (One-Hot Encoding).
  - Torneio comparativo de algoritmos (Random Forest, Gradient Boosting, HistGradientBoosting e Ridge).
  - Metricas de avaliacao (MAE, RMSE, R2) e extracao de feature importances (MDI e coeficientes regularizados).
  - Versionamento e governanca de artefatos.

- [Pipeline de Inferencia em Producao e Dados Abertos](docs/INFERENCIA_E_DADOS_ABERTOS.md):
  - Ciclo de vida da inferencia.
  - Integracao das APIs publicas (Open-Meteo, BrasilAPI, ESPN, CPTEC/INPE, IBGE).
  - Algoritmo de fusao sensorial para estimativa de transito urbano.
  - Dicionario de dados das 11 colunas e script para enriquecimento de bases legadas.
  - Faixas de risco operacional e suporte a tomada de decisao.

---

## Estrutura do Projeto

```text
modelo_predicao_faltas/
├── app/
│   ├── app.py                  # Rotas e endpoints REST da aplicacao Flask
│   ├── model_service.py        # Gestao, inferencia e versionamento de modelos
│   ├── trainer.py              # Pipeline Scikit-learn, split, fit e metricas
│   ├── open_data_service.py    # Integracao com APIs abertas
│   ├── static/
│   │   ├── css/style.css       # Estilizacao da interface
│   │   ├── js/app.js           # Logica do front-end e graficos Chart.js
│   │   └── template_treinamento_modelo.csv # Planilha modelo CSV
│   └── templates/
│       └── index.html          # Interface web
├── models/
│   ├── registry.json           # Catalogo versionado de modelos
│   └── modelo_falta_escola_1500.joblib
├── docs/
│   ├── TEORIA_E_TREINAMENTO_DO_MODELO.md
│   └── INFERENCIA_E_DADOS_ABERTOS.md
├── run_local.sh                # Script de inicializacao com venv
├── requirements.txt            # Dependencias Python
└── README.md
```