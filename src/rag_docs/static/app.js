const question = document.querySelector('#question');
const queryButton = document.querySelector('#query-button');
const indexButton = document.querySelector('#index-button');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const generatorProfile = document.querySelector('#generator-profile');
const generatorModel = document.querySelector('#generator-model');
const generatorCheckButton = document.querySelector('#generator-check-button');
const generatorActivateButton = document.querySelector('#generator-activate-button');
let generatorState = null;

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
  return payload;
}

function setBusy(button, busy, message) {
  button.disabled = busy;
  status.textContent = message;
}

function selectedGenerator() {
  return generatorState?.profiles.find((profile) => profile.id === generatorProfile.value);
}

function renderSelectedGenerator() {
  const profile = selectedGenerator();
  if (!profile) return;
  document.querySelector('#generator-endpoint').textContent = profile.endpoint;
  generatorModel.replaceChildren();
  const option = document.createElement('option');
  option.value = profile.model;
  option.textContent = profile.model;
  generatorModel.append(option);
  generatorModel.disabled = true;
  const health = document.querySelector('#generator-health');
  health.textContent = 'Sin comprobar';
  health.className = '';
}

function renderGeneratorState(payload, preferredProfile = null) {
  generatorState = payload;
  const selection = preferredProfile || payload.active_profile;
  generatorProfile.replaceChildren();
  payload.profiles.forEach((profile) => {
    const option = document.createElement('option');
    option.value = profile.id;
    option.textContent = profile.label;
    option.selected = profile.id === selection;
    generatorProfile.append(option);
  });
  const active = payload.profiles.find((profile) => profile.id === payload.active_profile);
  document.querySelector('#generator-active').textContent = active
    ? `Activo: ${active.label} · ${active.model}`
    : 'Sin perfil activo';
  renderSelectedGenerator();
}

async function loadGeneratorState(preferredProfile = null) {
  const payload = await request('/api/generator');
  renderGeneratorState(payload, preferredProfile);
}

async function checkGenerator(profileId) {
  return request('/api/generator/check', {
    method: 'POST',
    body: JSON.stringify({ profile: profileId }),
  });
}

function renderAvailableModels(payload) {
  const availableModels = payload.available_models || [];
  generatorModel.replaceChildren();
  if (!availableModels.length) {
    const option = document.createElement('option');
    option.value = payload.model;
    option.textContent = payload.model;
    generatorModel.append(option);
    generatorModel.disabled = true;
    return;
  }
  availableModels.forEach((model) => {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    option.selected = model === payload.model;
    generatorModel.append(option);
  });
  if (!availableModels.includes(payload.model)) generatorModel.value = availableModels[0];
  generatorModel.disabled = false;
}

function renderGeneratorHealth(payload) {
  const health = document.querySelector('#generator-health');
  const count = payload.available_models?.length || 0;
  renderAvailableModels(payload);
  if (payload.ready) {
    health.textContent = `Disponible · ${count} modelo${count === 1 ? '' : 's'} detectado${count === 1 ? '' : 's'}`;
    health.className = 'ready';
  } else if (count) {
    health.textContent = `Se detectaron ${count} modelo${count === 1 ? '' : 's'}. Selecciona uno para activarlo.`;
    health.className = 'ready';
  } else {
    health.textContent = 'Endpoint disponible, pero no anuncia modelos instalados.';
    health.className = 'error';
  }
}

function locationText(citation) {
  const parts = Object.entries(citation.locator || {}).map(([key, value]) => `${key}: ${value}`);
  if (citation.section) parts.unshift(`sección: ${citation.section}`);
  return parts.join(' · ');
}

function renderCitations(citations) {
  const container = document.querySelector('#citations');
  container.replaceChildren();
  if (!citations.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No se recuperaron fuentes con evidencia suficiente.';
    container.append(empty);
    return;
  }
  citations.forEach((citation) => {
    const item = document.createElement('article');
    item.className = 'citation';
    const heading = document.createElement('div');
    heading.className = 'citation-title';
    const title = document.createElement('span');
    title.textContent = `[${citation.reference}] ${citation.file_name}`;
    const score = document.createElement('span');
    score.textContent = `${(citation.score * 100).toFixed(1)}%`;
    heading.append(title, score);
    const locator = document.createElement('p');
    locator.textContent = locationText(citation) || 'Documento completo';
    const snippet = document.createElement('p');
    snippet.textContent = citation.snippet;
    const path = document.createElement('p');
    path.className = 'path';
    path.textContent = citation.original_uri;
    const copy = document.createElement('button');
    copy.className = 'secondary';
    copy.textContent = 'Copiar ruta';
    copy.addEventListener('click', () => navigator.clipboard.writeText(citation.original_uri));
    item.append(heading, locator, snippet, path, copy);
    container.append(item);
  });
}

queryButton.addEventListener('click', async () => {
  const value = question.value.trim();
  if (!value) { status.textContent = 'Escribe una pregunta.'; question.focus(); return; }
  const active = generatorState?.profiles.find(
    (profile) => profile.id === generatorState.active_profile,
  );
  setBusy(queryButton, true, `Consultando índice y modelo ${active?.label || 'configurado'}…`);
  try {
    const payload = await request('/api/query', { method: 'POST', body: JSON.stringify({ question: value }) });
    result.hidden = false;
    document.querySelector('#answer').textContent = payload.answer;
    const badge = document.querySelector('#answer-status');
    badge.textContent = payload.answer_status;
    badge.className = `badge ${payload.answer_status === 'grounded' ? '' : 'insufficient'}`;
    renderCitations(payload.citations);
    status.textContent = 'Consulta completada.';
  } catch (error) { status.textContent = error.message; }
  finally { queryButton.disabled = false; }
});

generatorProfile.addEventListener('change', renderSelectedGenerator);

generatorCheckButton.addEventListener('click', async () => {
  const profileId = generatorProfile.value;
  const health = document.querySelector('#generator-health');
  generatorCheckButton.disabled = true;
  health.textContent = 'Comprobando…';
  health.className = '';
  try {
    const payload = await checkGenerator(profileId);
    renderGeneratorHealth(payload);
  } catch (error) {
    health.textContent = error.message;
    health.className = 'error';
  } finally {
    generatorCheckButton.disabled = false;
  }
});

generatorActivateButton.addEventListener('click', async () => {
  const profileId = generatorProfile.value;
  const profileLabel = selectedGenerator()?.label || profileId;
  generatorActivateButton.disabled = true;
  try {
    await request('/api/generator/activate', {
      method: 'POST',
      body: JSON.stringify({ profile: profileId, model: generatorModel.value }),
    });
    await loadGeneratorState(profileId);
    const checked = await checkGenerator(profileId);
    renderGeneratorHealth(checked);
    status.textContent = `Generador ${profileLabel} activado para las consultas siguientes.`;
  } catch (error) {
    status.textContent = error.message;
    document.querySelector('#generator-health').textContent = error.message;
    document.querySelector('#generator-health').className = 'error';
  } finally {
    generatorActivateButton.disabled = false;
  }
});

generatorModel.addEventListener('change', () => {
  const health = document.querySelector('#generator-health');
  health.textContent = `Listo para activar ${generatorModel.value}`;
  health.className = 'ready';
});

indexButton.addEventListener('click', async () => {
  setBusy(indexButton, true, 'Indexando fuentes…');
  try {
    const payload = await request('/api/index', { method: 'POST', body: '{}' });
    status.textContent = `Índice actualizado: ${payload.added} altas, ${payload.updated} cambios, ${payload.deleted} bajas, ${payload.unchanged} sin cambios.`;
  } catch (error) { status.textContent = error.message; }
  finally { indexButton.disabled = false; }
});

async function loadSources() {
  try {
    const payload = await request('/api/sources');
    const container = document.querySelector('#sources');
    container.replaceChildren();
    payload.sources.forEach((source) => {
      const item = document.createElement('div');
      item.className = 'source';
      const dot = document.createElement('span');
      dot.className = `dot ${source.available ? 'available' : ''}`;
      const text = document.createElement('div');
      const name = document.createElement('strong');
      name.textContent = source.id;
      const path = document.createElement('div');
      path.className = 'path';
      path.textContent = source.root;
      text.append(name, path);
      item.append(dot, text);
      container.append(item);
    });
  } catch (error) { status.textContent = error.message; }
}

Promise.all([loadSources(), loadGeneratorState()]).catch((error) => {
  status.textContent = error.message;
});
