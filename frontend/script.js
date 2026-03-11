const API = '';

// ── Tabs ──────────────────────────────────────────────────────────────────────
function trocarTab(nome) {
  document.querySelectorAll('.tab').forEach((t,i) => {
    const nomes = ['painel','membros','avisos','historico','stats','config'];
    t.classList.toggle('active', nomes[i] === nome);
  });
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + nome).classList.add('active');

  if (nome === 'painel') carregarPainel();
  if (nome === 'membros') carregarMembros();
  if (nome === 'historico') carregarHistorico();
  if (nome === 'stats') carregarEstatisticas();
  if (nome === 'config') carregarConfig();
}

// ── Painel ────────────────────────────────────────────────────────────────────
async function carregarPainel() {
  const data = await fetch('/api/painel').then(r => r.json());

  const d = new Date(data.data + 'T12:00:00');
  document.getElementById('header-data').textContent =
    d.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });

  document.getElementById('count-sim').textContent = data.confirmados.length;
  document.getElementById('count-nao').textContent = data.ausentes.length;
  document.getElementById('count-esp').textContent = data.aguardando.length;

  let html = '';

  if (data.confirmados.length) {
    html += '<div class="section-title">✅ Confirmados</div><div class="member-list">';
    data.confirmados.forEach(m => {
      html += `<div class="member-item">
        <div class="member-dot dot-verde"></div>
        <div><div class="member-nome">${m.nome}</div><div class="member-tel">${m.telefone}</div></div>
      </div>`;
    });
    html += '</div>';
  }

  if (data.ausentes.length) {
    html += '<div class="section-title">❌ Não vão hoje</div><div class="member-list">';
    data.ausentes.forEach(m => {
      html += `<div class="member-item">
        <div class="member-dot dot-vermelho"></div>
        <div><div class="member-nome">${m.nome}</div><div class="member-tel">${m.telefone}</div></div>
      </div>`;
    });
    html += '</div>';
  }

  if (data.aguardando.length) {
    html += '<div class="section-title">⏳ Aguardando resposta</div><div class="member-list">';
    data.aguardando.forEach(m => {
      html += `<div class="member-item">
        <div class="member-dot dot-cinza"></div>
        <div><div class="member-nome">${m.nome}</div><div class="member-tel">${m.telefone}</div></div>
      </div>`;
    });
    html += '</div>';
  }

  if (!html) html = '<div class="empty">Nenhuma resposta ainda. Dispare o pré-culto para começar!</div>';

  document.getElementById('listas-painel').innerHTML = html;
}

// ── Disparos ──────────────────────────────────────────────────────────────────
async function disparar(tipo) {
  if (!confirm(`Confirma o disparo ${tipo === 'pre' ? 'do pré-culto' : 'do fim do culto'}?`)) return;
  const r = await fetch(`/api/disparar/${tipo}`, { method: 'POST' }).then(r => r.json());
  toast(r.msg);
  setTimeout(carregarPainel, 3000);
}

// ── Membros ───────────────────────────────────────────────────────────────────
async function carregarMembros() {
  const membros = await fetch('/api/membros').then(r => r.json());
  const el = document.getElementById('lista-membros');

  window._membrosCache = membros; // guarda na memoria pra facilitar ediçao

  if (!membros.length) {
    el.innerHTML = '<div class="empty">Nenhum membro cadastrado ainda.</div>';
    return;
  }

  el.innerHTML = membros.map(m => `
    <div class="member-item">
      <div class="member-dot dot-verde"></div>
      <div style="flex: 1; min-width: 0;">
        <div class="member-nome">${m.nome}</div>
        <div class="member-tel">${m.telefone}${m.nascimento ? ' · ' + formatarData(m.nascimento) : ''}</div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn btn-outline" style="padding: 6px 10px; font-size: 12px; font-weight: 600;" onclick="abrirEdicao(${m.id})">Editar</button>
        <button class="btn btn-danger" style="padding: 6px 10px; font-size: 12px; font-weight: 600;" onclick="excluirMembro(${m.id}, '${m.nome}')">Excluir</button>
      </div>
    </div>
  `).join('');
}

async function addMembro() {
  const nome = document.getElementById('m-nome').value.trim();
  const telefone = document.getElementById('m-tel').value.trim();
  const nascimento = document.getElementById('m-nasc').value;

  if (!nome || !telefone) { toast('Preencha nome e telefone.'); return; }

  const r = await fetch('/api/membros', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nome, telefone, nascimento })
  }).then(r => r.json());

  toast(r.msg);
  if (r.ok) {
    document.getElementById('m-nome').value = '';
    document.getElementById('m-tel').value = '';
    document.getElementById('m-nasc').value = '';
    carregarMembros();
  }
}

// ── Edição e Exclusão ──
function abrirEdicao(id) {
  const membro = window._membrosCache.find(m => m.id === id);
  if (!membro) return;

  document.getElementById('edit-id').value = membro.id;
  document.getElementById('edit-nome').value = membro.nome;
  document.getElementById('edit-tel').value = membro.telefone;
  document.getElementById('edit-nasc').value = membro.nascimento || '';
  document.getElementById('edit-ativo').checked = membro.ativo === 1;

  document.getElementById('modal-edicao').style.display = 'flex';
}

function fecharModal() {
  document.getElementById('modal-edicao').style.display = 'none';
}

async function salvarEdicaoMembro() {
  const id = document.getElementById('edit-id').value;
  const payload = {
    nome: document.getElementById('edit-nome').value.trim(),
    telefone: document.getElementById('edit-tel').value.trim(),
    nascimento: document.getElementById('edit-nasc').value || null,
    ativo: document.getElementById('edit-ativo').checked
  };

  if (!payload.nome || !payload.telefone) { toast('Nome e telefone obrigatórios.'); return; }

  const r = await fetch(`/api/membros/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json());

  toast(r.msg);
  if (r.ok) {
    fecharModal();
    carregarMembros();
  }
}

async function excluirMembro(id, nome) {
  if (!confirm(`Tem certeza que deseja excluir permanentemente o membro "${nome}"?\n\nIsso também apagará todo o histórico de presenças dele.`)) return;
  
  const r = await fetch(`/api/membros/${id}`, { method: 'DELETE' }).then(r => r.json());
  
  toast(r.msg);
  if (r.ok) carregarMembros();
}

function exportarCSV() {
  window.location.href = '/api/membros/export';
}

async function importarCSV(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  toast('⏳ Importando...');
  
  try {
    const res = await fetch('/api/membros/import', {
      method: 'POST',
      body: formData
    }).then(r => r.json());

    toast(res.msg);
    if (res.ok) carregarMembros();
  } catch (error) {
    toast('❌ Falha na comunicação com o servidor');
  }
  
  e.target.value = ''; // reseta pro próximo
}

// ── Avisos ──
async function dispararAviso() {
  const texto = document.getElementById('aviso-texto').value.trim();
  const fileInput = document.getElementById('aviso-midia');
  
  if (!texto && (!fileInput.files || fileInput.files.length === 0)) {
    toast('Preencha um texto longo ou anexe uma imagem/pdf.');
    return;
  }

  if (!confirm(`Confirma o disparo deste Aviso Geral para TODOS os membros ATIVOS?`)) return;

  const btn = document.getElementById('btn-enviar-aviso');
  btn.disabled = true;
  btn.textContent = 'Enviando...';

  const payload = { texto: texto };

  if (fileInput.files && fileInput.files.length > 0) {
    const file = fileInput.files[0];
    
    // Converte o arquivo em Base64 para a API
    const reader = new FileReader();
    reader.onload = async function() {
      // FileReader vai me dar "data:image/png;base64,....." extrair só os dados base64
      payload.media_base64 = reader.result.split(',')[1]; 
      
      // se type = application/pdf -> mediatype=document
      // se image/jpeg -> mediatype=image
      let mType = 'image';
      if (file.type.includes('pdf')) mType = 'document';
      else if (file.type.includes('video')) mType = 'video';
      else if (file.type.includes('audio')) mType = 'audio';
      
      payload.media_type = mType;
      payload.file_name = file.name;
      
      await executarEnvioAviso(payload, btn);
    };
    reader.readAsDataURL(file);
  } else {
    await executarEnvioAviso(payload, btn);
  }
}

async function executarEnvioAviso(payload, btn) {
  try {
    const r = await fetch('/api/avisos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(r => r.json());

    toast(r.msg);
    
    if (r.ok) {
      document.getElementById('aviso-texto').value = '';
      document.getElementById('aviso-midia').value = '';
    }
  } catch (err) {
    toast('❌ Ocorreu um erro no servidor.');
  } finally {
    btn.disabled = false;
    btn.textContent = '🚀 Enviar Aviso para Todos';
  }
}

// ── Config ────────────────────────────────────────────────────────────────────
async function carregarConfig() {
  const cfg = await fetch('/api/config').then(r => r.json());

  document.getElementById('cfg-pre').value = cfg.horario_pre_culto || '19:00';
  document.getElementById('cfg-fim').value = cfg.horario_fim_culto || '21:00';
  document.getElementById('cfg-yt').value = cfg.youtube_channel || '';
  document.getElementById('cfg-msg-pre').value = cfg.msg_pre_culto || '';
  document.getElementById('cfg-msg-bv').value = cfg.msg_boas_vindas || '';
  document.getElementById('cfg-msg-aus-pre').value = cfg.msg_ausente_pre || '';
  document.getElementById('cfg-msg-ate').value = cfg.msg_ate_amanha || '';
  document.getElementById('cfg-msg-aus-fim').value = cfg.msg_ausente_fim || '';

  // Dias
  const dias = (cfg.dias_culto || '').split(',').map(d => d.trim());
  document.querySelectorAll('.dia-btn').forEach(btn => {
    btn.classList.toggle('ativo', dias.includes(btn.dataset.dia));
  });
}

function toggleDia(btn) {
  btn.classList.toggle('ativo');
}

async function salvarConfig() {
  const dias = [...document.querySelectorAll('.dia-btn.ativo')]
    .map(b => b.dataset.dia).join(',');

  const payload = {
    horario_pre_culto: document.getElementById('cfg-pre').value,
    horario_fim_culto: document.getElementById('cfg-fim').value,
    youtube_channel: document.getElementById('cfg-yt').value,
    dias_culto: dias,
    msg_pre_culto: document.getElementById('cfg-msg-pre').value,
    msg_boas_vindas: document.getElementById('cfg-msg-bv').value,
    msg_ausente_pre: document.getElementById('cfg-msg-aus-pre').value,
    msg_ate_amanha: document.getElementById('cfg-msg-ate').value,
    msg_ausente_fim: document.getElementById('cfg-msg-aus-fim').value,
  };

  const r = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json());

  toast(r.ok ? '✅ Configurações salvas!' : '❌ Erro ao salvar.');
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}

function formatarData(d) {
  if (!d) return '';
  const [y, m, day] = d.split('-');
  return `${day}/${m}/${y}`;
}

// ── Histórico ─────────────────────────────────────────────────────────────────
async function carregarHistorico() {
  const inicio = document.getElementById('hist-inicio').value;
  const fim = document.getElementById('hist-fim').value;

  let url = '/api/historico';
  if (inicio && fim) url += `?inicio=${inicio}&fim=${fim}`;

  const data = await fetch(url).then(r => r.json());
  const el = document.getElementById('lista-historico');
  const dias = data.dias;

  const datasOrdenadas = Object.keys(dias).sort().reverse();
  if (!datasOrdenadas.length) {
    el.innerHTML = '<div class="empty">Nenhum registro encontrado no período.</div>';
    return;
  }

  let html = '';
  datasOrdenadas.forEach(d => {
    const membros = dias[d];
    const presentes = membros.filter(m => m.resposta === 'sim').length;
    const ausentes = membros.filter(m => m.resposta === 'nao').length;
    const dt = new Date(d + 'T12:00:00');
    const label = dt.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' });

    html += `<div class="dia-historico">`;
    html += `<div class="dia-historico-header">
      <span>📅 ${label}</span>
      <span>
        <span class="badge badge-verde">✅ ${presentes}</span>
        <span class="badge badge-vermelho">❌ ${ausentes}</span>
      </span>
    </div>`;
    html += '<div class="member-list">';
    membros.forEach(m => {
      const dot = m.resposta === 'sim' ? 'dot-verde' : 'dot-vermelho';
      const icon = m.resposta === 'sim' ? '✅' : '❌';
      html += `<div class="member-item">
        <div class="member-dot ${dot}"></div>
        <div><div class="member-nome">${m.nome}</div><div class="member-tel">${m.telefone}</div></div>
      </div>`;
    });
    html += '</div></div>';
  });

  el.innerHTML = html;
}

// ── Estatísticas ──────────────────────────────────────────────────────────────
async function carregarEstatisticas() {
  const data = await fetch('/api/estatisticas').then(r => r.json());

  document.getElementById('st-cultos').textContent = data.total_cultos;
  document.getElementById('st-membros').textContent = data.total_membros;
  document.getElementById('st-media').textContent = data.media_presenca;

  // Ranking
  const rankEl = document.getElementById('lista-ranking');
  if (data.ranking.length) {
    const maxPresencas = Math.max(...data.ranking.map(r => r.presencas)) || 1;
    rankEl.innerHTML = data.ranking.map((r, i) => {
      const pct = Math.round((r.presencas / maxPresencas) * 100);
      const total = r.total_respostas || 1;
      const freqPct = Math.round((r.presencas / total) * 100);
      return `<div class="ranking-item">
        <div class="ranking-pos">${i + 1}º</div>
        <div class="ranking-info">
          <div class="member-nome">${r.nome}</div>
          <div class="ranking-bar"><div class="ranking-fill" style="width:${pct}%"></div></div>
        </div>
        <div class="ranking-count">${r.presencas} presenças (${freqPct}%)</div>
      </div>`;
    }).join('');
  } else {
    rankEl.innerHTML = '<div class="empty">Sem dados de presença ainda.</div>';
  }

  // Gráfico
  desenharGrafico(data.presenca_por_dia);
}

function desenharGrafico(dados) {
  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');

  // Ajustar resolução
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width - 40;
  canvas.height = 200;

  const w = canvas.width;
  const h = canvas.height;
  const pad = { top: 20, right: 20, bottom: 40, left: 40 };

  ctx.clearRect(0, 0, w, h);

  if (!dados.length) {
    ctx.fillStyle = '#888';
    ctx.font = '14px Segoe UI';
    ctx.textAlign = 'center';
    ctx.fillText('Sem dados para exibir', w / 2, h / 2);
    return;
  }

  // Ordenar cronologicamente
  dados = [...dados].reverse();

  const maxVal = Math.max(...dados.map(d => d.presentes + d.ausentes)) || 1;
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;
  const barW = Math.max(8, Math.min(30, chartW / dados.length - 4));

  // Grid lines
  ctx.strokeStyle = '#e8e8e8';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(w - pad.right, y);
    ctx.stroke();
    ctx.fillStyle = '#888';
    ctx.font = '11px Segoe UI';
    ctx.textAlign = 'right';
    ctx.fillText(Math.round(maxVal - (maxVal / 4) * i), pad.left - 6, y + 4);
  }

  dados.forEach((d, i) => {
    const x = pad.left + (chartW / dados.length) * i + (chartW / dados.length - barW) / 2;

    // Barra presentes (verde)
    const hP = (d.presentes / maxVal) * chartH;
    ctx.fillStyle = '#1a6b3a';
    ctx.beginPath();
    ctx.roundRect(x, pad.top + chartH - hP, barW, hP, [3, 3, 0, 0]);
    ctx.fill();

    // Barra ausentes (vermelho, empilhada)
    const hA = (d.ausentes / maxVal) * chartH;
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.roundRect(x, pad.top + chartH - hP - hA, barW, hA, [3, 3, 0, 0]);
    ctx.fill();

    // Label data
    if (dados.length <= 15 || i % Math.ceil(dados.length / 10) === 0) {
      const dt = new Date(d.data + 'T12:00:00');
      const label = `${dt.getDate()}/${dt.getMonth() + 1}`;
      ctx.fillStyle = '#888';
      ctx.font = '10px Segoe UI';
      ctx.textAlign = 'center';
      ctx.fillText(label, x + barW / 2, h - pad.bottom + 16);
    }
  });

  // Legenda
  ctx.font = '11px Segoe UI';
  ctx.fillStyle = '#1a6b3a';
  ctx.fillRect(w - 160, 6, 10, 10);
  ctx.fillText('Presentes', w - 145, 15);
  ctx.fillStyle = '#e74c3c';
  ctx.fillRect(w - 80, 6, 10, 10);
  ctx.fillText('Ausentes', w - 65, 15);
}

// ── Init ──────────────────────────────────────────────────────────────────────
// Preencher datas padrão do histórico
(function() {
  const hoje = new Date();
  const mes = new Date(hoje);
  mes.setDate(mes.getDate() - 30);
  document.getElementById('hist-fim').value = hoje.toISOString().split('T')[0];
  document.getElementById('hist-inicio').value = mes.toISOString().split('T')[0];
})();

carregarPainel();
setInterval(carregarPainel, 30000); // auto-refresh a cada 30s