/* =========================================================
   JAVASCRIPT CLEAN • EDUPREDICT AI
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const state = {
    activeVersion: null,
    models: [],
    history: [],
    chartGrouped: null,
    chartDonut: null
  };

  const elements = {
    tabs: document.querySelectorAll(".nav-tab"),
    tabPanels: document.querySelectorAll(".tab-panel"),
    activeModelLabel: document.getElementById("activeModelLabel"),
    
    // Formulário de Predição
    formPrediction: document.getElementById("formPrediction"),
    inputDate: document.getElementById("inputDate"),
    inputTurno: document.getElementById("inputTurno"),
    inputClima: document.getElementById("inputClima"),
    inputDiaSemana: document.getElementById("inputDiaSemana"),
    inputTransito: document.getElementById("inputTransito"),
    transitoValLabel: document.getElementById("transitoValLabel"),
    inputChoveu: document.getElementById("inputChoveu"),
    inputFutebol: document.getElementById("inputFutebol"),
    inputFeriadoAntes: document.getElementById("inputFeriadoAntes"),
    inputFeriadoDepois: document.getElementById("inputFeriadoDepois"),
    selectModelVersion: document.getElementById("selectModelVersion"),
    btnAutoOpenData: document.getElementById("btnAutoOpenData"),
    btnCalculatePrediction: document.getElementById("btnCalculatePrediction"),

    // Painel de Resultados
    resultPercentage: document.getElementById("resultPercentage"),
    resultRiskBadge: document.getElementById("resultRiskBadge"),
    resultRiskMessage: document.getElementById("resultRiskMessage"),
    projTurma: document.getElementById("projTurma"),
    projEscola500: document.getElementById("projEscola500"),
    projDiffMean: document.getElementById("projDiffMean"),
    factorsList: document.getElementById("factorsList"),

    // Dashboard
    dashActiveAlgo: document.getElementById("dashActiveAlgo"),
    dashActiveMae: document.getElementById("dashActiveMae"),
    dashActiveR2: document.getElementById("dashActiveR2"),

    // Treinamento
    formTraining: document.getElementById("formTraining"),
    inputVersionName: document.getElementById("inputVersionName"),
    inputCsvFile: document.getElementById("inputCsvFile"),
    filePickerText: document.getElementById("filePickerText"),
    selectDefaultDataset: document.getElementById("selectDefaultDataset"),
    selectTrainSplit: document.getElementById("selectTrainSplit"),
    splitPreviewBar: document.getElementById("splitPreviewBar"),
    btnStartTraining: document.getElementById("btnStartTraining"),
    trainingLoading: document.getElementById("trainingLoading"),
    trainingResultBox: document.getElementById("trainingResultBox"),
    trainingSuccessMsg: document.getElementById("trainingSuccessMsg"),
    tableModelsBody: document.getElementById("tableModelsBody"),

    // Seletores de Modelo Corrente & Ações
    topbarSelectModel: document.getElementById("topbarSelectModel"),
    btnMakeCurrentPredict: document.getElementById("btnMakeCurrentPredict"),
    dashSelectModel: document.getElementById("dashSelectModel"),
    btnDashSetCurrent: document.getElementById("btnDashSetCurrent"),

    // Toasts
    toastContainer: document.getElementById("toastContainer")
  };

  // Inicializa data de hoje
  const todayIso = new Date().toISOString().split("T")[0];
  elements.inputDate.value = todayIso;

  // Notificação Toast
  function showToast(msg) {
    const t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    elements.toastContainer.appendChild(t);
    setTimeout(() => {
      t.style.opacity = "0";
      setTimeout(() => t.remove(), 300);
    }, 3500);
  }

  // Navegação de Abas
  elements.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      elements.tabs.forEach(t => t.classList.remove("active"));
      elements.tabPanels.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add("active");

      if (targetId === "tab-dashboard") {
        loadDashboard();
      }
    });
  });

  // Slider de Trânsito
  const transitoTextos = {
    1: "Nível 1 (Fluido)",
    2: "Nível 2 (Trânsito Leve)",
    3: "Nível 3 (Moderado)",
    4: "Nível 4 (Intenso)",
    5: "Nível 5 (Congestionado)"
  };
  elements.inputTransito.addEventListener("input", (e) => {
    elements.transitoValLabel.textContent = transitoTextos[e.target.value] || `Nível ${e.target.value}`;
  });

  // Consulta de Dados Abertos (8 APIs)
  async function fetchAllOpenData() {
    try {
      elements.btnAutoOpenData.disabled = true;
      elements.btnAutoOpenData.textContent = "⚡ Consultando 8 APIs...";

      const dateVal = elements.inputDate.value || todayIso;
      const turnoVal = elements.inputTurno.value || "Manhã";

      const res = await fetch(`/api/open-data?date=${encodeURIComponent(dateVal)}&turno=${encodeURIComponent(turnoVal)}`);
      const json = await res.json();

      elements.btnAutoOpenData.disabled = false;
      elements.btnAutoOpenData.textContent = "⚡ Preencher via Dados Abertos";

      if (!json.success || !json.data) {
        throw new Error(json.error || "Erro ao consultar APIs");
      }

      const d = json.data;

      // Preenche os campos
      if (d.clima) elements.inputClima.value = d.clima;
      if (d.dia_da_semana) elements.inputDiaSemana.value = d.dia_da_semana;
      elements.inputChoveu.checked = (d.choveu === 1);
      elements.inputFeriadoAntes.checked = (d.feriado_antes === 1);
      elements.inputFeriadoDepois.checked = (d.feriado_depois === 1);
      elements.inputFutebol.checked = (d.jogos_futebol === 1);

      if (d.transito) {
        elements.inputTransito.value = d.transito;
        elements.transitoValLabel.textContent = transitoTextos[d.transito] || `Nível ${d.transito}`;
      }

      showToast(`✓ ${d.total_apis} APIs abertas sincronizadas com sucesso!`);
    } catch (err) {
      elements.btnAutoOpenData.disabled = false;
      elements.btnAutoOpenData.textContent = "⚡ Preencher via Dados Abertos";
      console.error(err);
      showToast("Falha nas APIs abertas: " + err.message);
    }
  }

  elements.btnAutoOpenData.addEventListener("click", fetchAllOpenData);

  // Predição
  elements.formPrediction.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      version: elements.selectModelVersion.value || undefined,
      jogos_futebol: elements.inputFutebol.checked ? 1 : 0,
      clima: elements.inputClima.value,
      choveu: elements.inputChoveu.checked ? 1 : 0,
      dia_da_semana: elements.inputDiaSemana.value,
      feriado_antes: elements.inputFeriadoAntes.checked ? 1 : 0,
      feriado_depois: elements.inputFeriadoDepois.checked ? 1 : 0,
      transito: parseInt(elements.inputTransito.value, 10),
      turno: elements.inputTurno.value
    };

    try {
      elements.btnCalculatePrediction.disabled = true;
      elements.btnCalculatePrediction.textContent = "Calculando...";

      const resp = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const res = await resp.json();

      elements.btnCalculatePrediction.disabled = false;
      elements.btnCalculatePrediction.textContent = "Calcular Predição";

      if (!res.success) throw new Error(res.error);

      renderResult(res.data);
      addHistoryItem(res.data);
    } catch (err) {
      elements.btnCalculatePrediction.disabled = false;
      elements.btnCalculatePrediction.textContent = "Calcular Predição";
      showToast("Erro na predição: " + err.message);
    }
  });

  // Histórico de Predições da Sessão
  const tableHistoryBody = document.getElementById("tableHistoryBody");
  const btnClearHistory = document.getElementById("btnClearHistory");

  function addHistoryItem(data) {
    const timeStr = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const inp = data.inputs || {};

    const contexts = [];
    if (inp["Feriado (antes)"]) contexts.push("Véspera Feriado");
    if (inp["Feriado (depois)"]) contexts.push("Pós-Feriado");
    if (inp["Jogos Futebol"]) contexts.push("Futebol");
    const ctxText = contexts.length > 0 ? contexts.join(", ") : "Dia Típico";

    state.history.unshift({
      time: timeStr,
      turno: inp.TURNO || "Manhã",
      dia: inp["Dia da Semana"] || "--",
      clima: inp.Clima || "--",
      choveu: inp["Choveu?"] ? "Sim" : "Não",
      transito: `Nível ${inp["Trânsito"] || 3}`,
      context: ctxText,
      pct: `${data.prediction_pct}%`,
      badge: data.risk_badge || "success",
      level: data.risk_level || "Baixo"
    });

    if (state.history.length > 8) state.history.pop();
    renderHistoryTable();
  }

  function renderHistoryTable() {
    if (!tableHistoryBody) return;
    if (state.history.length === 0) {
      tableHistoryBody.innerHTML = `<tr><td colspan="9" class="empty-cell">Nenhuma predição realizada ainda. Faça uma simulação acima.</td></tr>`;
      return;
    }

    tableHistoryBody.innerHTML = state.history.map(item => `
      <tr>
        <td style="color:#94a3b8">${item.time}</td>
        <td><strong>${item.turno}</strong></td>
        <td>${item.dia}</td>
        <td>${item.clima}</td>
        <td>${item.choveu}</td>
        <td>${item.transito}</td>
        <td style="color:#94a3b8; font-size:0.75rem">${item.context}</td>
        <td><strong style="color:#60a5fa; font-size:0.95rem">${item.pct}</strong></td>
        <td><span class="risk-badge badge-${item.badge}">${item.level}</span></td>
      </tr>
    `).join("");
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener("click", () => {
      state.history = [];
      renderHistoryTable();
      showToast("Histórico limpo com sucesso.");
    });
  }

  function renderResult(data) {
    const pct = data.prediction_pct;
    elements.resultPercentage.textContent = pct.toFixed(1);

    elements.resultRiskBadge.className = `risk-badge badge-${data.risk_badge}`;
    elements.resultRiskBadge.textContent = `Risco ${data.risk_level}`;

    elements.resultRiskMessage.textContent = data.risk_message;

    elements.projTurma.textContent = `~${data.projections.turma_40_alunos} alunos`;
    elements.projEscola500.textContent = `~${data.projections.escola_500_alunos} alunos`;
    
    const diff = data.difference_from_mean >= 0 ? `+${data.difference_from_mean}%` : `${data.difference_from_mean}%`;
    elements.projDiffMean.textContent = diff;
    elements.projDiffMean.style.color = data.difference_from_mean > 0 ? "var(--risk-high)" : "var(--risk-low)";

    // Fatores
    if (data.key_factors && data.key_factors.length > 0) {
      elements.factorsList.innerHTML = data.key_factors.map(f => 
        `<span class="tag-factor">${f.name}</span>`
      ).join("");
    } else {
      elements.factorsList.innerHTML = `<span class="tag-empty">Sem fatores anormais</span>`;
    }
  }

  // Dashboard de Pesos
  async function loadDashboard(version) {
    try {
      const query = version ? `?version=${encodeURIComponent(version)}` : "";
      const resp = await fetch(`/api/weights${query}`);
      const res = await resp.json();
      if (!res.success) return;

      elements.dashActiveAlgo.textContent = res.algorithm || "RandomForest";
      elements.dashActiveMae.textContent = res.metrics?.MAE !== undefined ? `${res.metrics.MAE}%` : "--";
      elements.dashActiveR2.textContent = res.metrics?.R2 !== undefined ? res.metrics.R2 : "--";

      if (elements.dashSelectModel && res.version) {
        elements.dashSelectModel.value = res.version;
      }

      const grouped = res.weights?.grouped || [];

      // Gráfico de Barras
      const ctxBar = document.getElementById("chartWeightsGrouped");
      if (ctxBar) {
        if (state.chartGrouped) state.chartGrouped.destroy();
        state.chartGrouped = new Chart(ctxBar, {
          type: "bar",
          data: {
            labels: grouped.map(g => g.feature),
            datasets: [{
              data: grouped.map(g => g.weight_pct),
              backgroundColor: "rgba(59, 130, 246, 0.7)",
              borderRadius: 4
            }]
          },
          options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8" } },
              y: { grid: { display: false }, ticks: { color: "#f8fafc" } }
            }
          }
        });
      }

      // Gráfico de Donut
      const ctxDonut = document.getElementById("chartWeightsDonut");
      if (ctxDonut) {
        if (state.chartDonut) state.chartDonut.destroy();
        state.chartDonut = new Chart(ctxDonut, {
          type: "doughnut",
          data: {
            labels: grouped.map(g => g.feature),
            datasets: [{
              data: grouped.map(g => g.weight_pct),
              backgroundColor: ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#6366f1", "#14b8a6"],
              borderColor: "#131b2e",
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "right", labels: { color: "#94a3b8", font: { size: 11 }, boxWidth: 10 } }
            },
            cutout: "70%"
          }
        });
      }

    } catch (err) {
      console.error(err);
    }
  }

  // Trocar modelo corrente
  async function setActiveModel(versionTag) {
    if (!versionTag) return;
    try {
      const resp = await fetch("/api/models/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version: versionTag })
      });
      const res = await resp.json();
      if (!res.success) throw new Error(res.error);

      showToast(`✓ Modelo '${versionTag}' ativado como modelo corrente!`);
      await loadModels();
      await loadDashboard(versionTag);
    } catch (err) {
      showToast("Erro ao definir modelo corrente: " + err.message);
    }
  }

  // Apagar modelo criado
  async function deleteModel(versionTag) {
    if (!versionTag) return;
    const confirmDelete = window.confirm(`Deseja realmente apagar o modelo "${versionTag}"?\nEsta ação excluirá o arquivo treinado permanentemente.`);
    if (!confirmDelete) return;

    try {
      const resp = await fetch("/api/models/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version: versionTag })
      });
      const res = await resp.json();
      if (!res.success) throw new Error(res.error);

      showToast(`✓ Modelo '${versionTag}' excluído com sucesso!`);
      await loadModels();
      await loadDashboard();
    } catch (err) {
      showToast("Erro ao excluir modelo: " + err.message);
    }
  }

  // Modelos & Treinamento
  async function loadModels() {
    try {
      const resp = await fetch("/api/models");
      const res = await resp.json();
      if (!res.success) return;

      state.models = res.models || [];
      const active = state.models.find(m => m.is_active);
      state.activeVersion = active ? active.version : (state.models[0]?.version || null);

      // Topbar Select
      if (elements.topbarSelectModel) {
        elements.topbarSelectModel.innerHTML = state.models.map(m => `
          <option value="${m.version}" ${m.is_active ? 'selected' : ''}>
            ${m.version} (${m.best_algorithm})${m.is_active ? ' ★' : ''}
          </option>
        `).join("");
      }

      // Predição Select
      if (elements.selectModelVersion) {
        elements.selectModelVersion.innerHTML = state.models.map(m => `
          <option value="${m.version}" ${m.is_active ? 'selected' : ''}>
            ${m.version} ${m.is_active ? '(Corrente)' : ''}
          </option>
        `).join("");
      }

      // Dashboard Model Picker Select
      if (elements.dashSelectModel) {
        elements.dashSelectModel.innerHTML = state.models.map(m => `
          <option value="${m.version}" ${m.is_active ? 'selected' : ''}>
            ${m.version} ${m.is_active ? '(Corrente)' : ''}
          </option>
        `).join("");
      }

      const canDelete = state.models.length > 1;

      elements.tableModelsBody.innerHTML = state.models.map(m => {
        let splitText = "80% / 20%";
        if (m.train_ratio_pct && m.test_ratio_pct) {
          splitText = `${m.train_ratio_pct}% / ${m.test_ratio_pct}%`;
        } else if (m.train_samples && m.test_samples) {
          const total = m.train_samples + m.test_samples;
          const tr = Math.round((m.train_samples / total) * 100);
          const te = 100 - tr;
          splitText = `${tr}% / ${te}%`;
        }

        const isCurrent = m.is_active;

        return `
        <tr class="${isCurrent ? 'row-current-active' : ''}">
          <td><strong>${m.version}</strong></td>
          <td>${m.best_algorithm}</td>
          <td><span class="split-pill-sm">${splitText}</span></td>
          <td>${m.best_metrics?.MAE !== undefined ? m.best_metrics.MAE : '--'}%</td>
          <td>${isCurrent ? '<span class="tag-active-sm">★ Corrente</span>' : '<span style="color:#64748b">Inativo</span>'}</td>
          <td>
            <div class="actions-cell">
              ${isCurrent ? '' : `<button type="button" class="btn-activate-sm" data-v="${m.version}" title="Tornar este modelo o modelo corrente">⭐ Ativar</button>`}
              <button type="button" class="btn-delete-sm" data-v="${m.version}" title="${canDelete ? 'Excluir modelo permanentemente' : 'Não é possível excluir o único modelo existente'}" ${canDelete ? '' : 'disabled style="opacity:0.35;cursor:not-allowed;"'}>🗑️ Excluir</button>
            </div>
          </td>
        </tr>
      `;}).join("");

      document.querySelectorAll(".btn-activate-sm[data-v]").forEach(b => {
        b.addEventListener("click", () => {
          const v = b.getAttribute("data-v");
          setActiveModel(v);
        });
      });

      document.querySelectorAll(".btn-delete-sm[data-v]").forEach(b => {
        b.addEventListener("click", () => {
          const v = b.getAttribute("data-v");
          deleteModel(v);
        });
      });

    } catch (err) {
      console.error(err);
    }
  }

  // Datasets padrão no select
  async function loadDatasets() {
    try {
      const resp = await fetch("/api/default-datasets");
      const res = await resp.json();
      if (res.success && res.datasets) {
        elements.selectDefaultDataset.innerHTML = '<option value="">-- Escolha um dataset do projeto se não enviar CSV --</option>' +
          res.datasets.map(d => `<option value="${d.filename}">${d.filename} (${d.size_kb} KB)</option>`).join("");
      }
    } catch (err) {
      console.error(err);
    }
  }

  elements.inputCsvFile.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      elements.filePickerText.textContent = e.target.files[0].name;
    }
  });

  if (elements.selectTrainSplit && elements.splitPreviewBar) {
    elements.selectTrainSplit.addEventListener("change", (e) => {
      const testRatio = Math.round(parseFloat(e.target.value) * 100);
      const trainRatio = 100 - testRatio;
      elements.splitPreviewBar.innerHTML = `
        <div class="split-bar-train" style="width: ${trainRatio}%;">${trainRatio}% Treino</div>
        <div class="split-bar-test" style="width: ${testRatio}%;">${testRatio}% Teste</div>
      `;
    });
  }

  // Notificação amigável ao baixar template
  const btnDownloadTemplate = document.getElementById("btnDownloadTemplate");
  if (btnDownloadTemplate) {
    btnDownloadTemplate.addEventListener("click", () => {
      showToast("Download da planilha modelo CSV iniciado!");
    });
  }

  // Treinamento
  elements.formTraining.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    const vName = elements.inputVersionName.value.trim();
    if (vName) fd.append("version_name", vName);

    const dSet = elements.selectDefaultDataset.value;
    if (dSet) fd.append("default_dataset", dSet);

    const testSizeVal = elements.selectTrainSplit ? elements.selectTrainSplit.value : "0.2";
    fd.append("test_size", testSizeVal);

    if (elements.inputCsvFile.files.length > 0) {
      fd.append("file", elements.inputCsvFile.files[0]);
    }

    if (elements.inputCsvFile.files.length === 0 && !dSet) {
      showToast("Selecione um arquivo CSV ou escolha um dataset.");
      return;
    }

    try {
      elements.btnStartTraining.disabled = true;
      elements.trainingLoading.classList.remove("hidden");
      elements.trainingResultBox.classList.add("hidden");

      const resp = await fetch("/api/train", { method: "POST", body: fd });
      const res = await resp.json();

      elements.btnStartTraining.disabled = false;
      elements.trainingLoading.classList.add("hidden");

      if (!res.success) throw new Error(res.error);

      elements.trainingResultBox.classList.remove("hidden");
      const tr = res.summary.train_ratio_pct || Math.round((1 - (res.summary.test_size || 0.2)) * 100);
      const te = res.summary.test_ratio_pct || Math.round((res.summary.test_size || 0.2) * 100);
      elements.trainingSuccessMsg.textContent = `✓ Modelo '${res.summary.version}' treinado com sucesso! Divisão: ${tr}% treino (${res.summary.train_samples} amostras) / ${te}% teste (${res.summary.test_samples} amostras). Algoritmo vencedor: ${res.summary.best_algorithm} (MAE: ${res.summary.best_metrics.MAE}%).`;

      showToast("Modelo treinado com sucesso!");
      loadModels();
      loadDashboard();
    } catch (err) {
      elements.btnStartTraining.disabled = false;
      elements.trainingLoading.classList.add("hidden");
      showToast("Falha no treino: " + err.message);
    }
  });

  // Listeners para trocar modelo ativo a partir de diferentes pontos da tela
  if (elements.topbarSelectModel) {
    elements.topbarSelectModel.addEventListener("change", (e) => {
      setActiveModel(e.target.value);
    });
  }

  if (elements.btnMakeCurrentPredict) {
    elements.btnMakeCurrentPredict.addEventListener("click", () => {
      const v = elements.selectModelVersion ? elements.selectModelVersion.value : null;
      if (v) setActiveModel(v);
    });
  }

  if (elements.dashSelectModel) {
    elements.dashSelectModel.addEventListener("change", (e) => {
      loadDashboard(e.target.value);
    });
  }

  if (elements.btnDashSetCurrent) {
    elements.btnDashSetCurrent.addEventListener("click", () => {
      const v = elements.dashSelectModel ? elements.dashSelectModel.value : null;
      if (v) setActiveModel(v);
    });
  }

  // Inicialização
  loadModels();
  loadDatasets();
  fetchAllOpenData();
});
