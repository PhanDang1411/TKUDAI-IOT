<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lab 8 v3 - LLM Reasoning AIoT</title>
  <style>
    :root { --blue:#174a7c; --light:#f4f7fb; --green:#198754; --orange:#ff9800; --red:#dc3545; --gray:#5f6b7a; }
    body { margin:0; font-family: Arial, Helvetica, sans-serif; background:#eef3f8; color:#1f2937; }
    header { background:linear-gradient(135deg,#0d3b66,#1c77c3); color:white; padding:18px 28px; }
    header h1 { margin:0; font-size:24px; }
    header p { margin:6px 0 0; opacity:.9; }
    main { padding:18px; display:grid; grid-template-columns: 360px 1fr; gap:16px; }
    .card { background:white; border-radius:14px; box-shadow:0 4px 18px rgba(0,0,0,.08); padding:16px; margin-bottom:16px; }
    .card h2 { margin:0 0 12px; font-size:18px; color:var(--blue); }
    label { display:block; font-size:13px; font-weight:600; margin:10px 0 4px; color:#334155; }
    select, input[type=number], input[type=range] { width:100%; box-sizing:border-box; padding:8px; border:1px solid #cbd5e1; border-radius:8px; }
    button { border:0; border-radius:10px; padding:10px 12px; margin:4px 2px; cursor:pointer; background:#1c77c3; color:white; font-weight:600; }
    button.secondary { background:#64748b; } button.green { background:var(--green); } button.orange { background:var(--orange); } button.red { background:var(--red); }
    .grid3 { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:12px; }
    .result { border:1px solid #e2e8f0; border-radius:12px; padding:12px; min-height:260px; background:#fbfdff; }
    .result h3 { margin:0 0 8px; color:#0f172a; font-size:16px; }
    .risk { display:inline-block; padding:4px 8px; border-radius:999px; font-weight:bold; font-size:12px; background:#e2e8f0; }
    .LOW { background:#dcfce7; color:#166534; } .MEDIUM { background:#fef9c3; color:#854d0e; } .HIGH { background:#ffedd5; color:#9a3412; } .CRITICAL { background:#fee2e2; color:#991b1b; }
    pre { background:#0f172a; color:#d1e7ff; padding:12px; border-radius:10px; overflow:auto; max-height:340px; font-size:12px; }
    .sensor-row { border-bottom:1px solid #eef2f7; padding-bottom:8px; }
    .small { font-size:12px; color:#64748b; }
    .timeline { height:150px; border:1px solid #e2e8f0; border-radius:10px; background:linear-gradient(#fff,#f8fafc); display:flex; align-items:end; gap:4px; padding:8px; overflow:hidden; }
    .bar { width:12px; background:#1c77c3; border-radius:4px 4px 0 0; min-height:2px; }
    .notice { background:#fff7ed; border-left:4px solid #f97316; padding:10px; border-radius:8px; }
  </style>
</head>
<body>
<header>
  <h1>Lab 8 v3 - LLM Reasoning & Context-aware Decision for AIoT</h1>
  <p>So sánh trực tiếp: Chỉ cảm biến → Cảm biến + AI models → Cảm biến + AI models + LLM</p>
</header>
<main>
  <section>
    <div class="card">
      <h2>1. Chọn kịch bản</h2>
      <select id="scenario"></select>
      <p id="scenarioWhy" class="small"></p>
      <button onclick="resetScenario()">Reset</button>
      <button class="green" onclick="startTimeline()">Start timeline</button>
      <button class="red" onclick="stopTimeline()">Stop</button>
      <button class="orange" onclick="stepTimeline()">Next step</button>
    </div>
    <div class="card">
      <h2>2. Sensor Control Panel</h2>
      <p class="small">Có thể tự chỉnh cảm biến để tạo tình huống mới rồi bấm Apply sensors.</p>
      <div id="sensorControls"></div>
      <button class="green" onclick="applySensors()">Apply sensors</button>
    </div>
    <div class="card">
      <h2>3. LLM mode</h2>
      <select id="llmMode">
        <option value="mock">mock - luôn chạy được</option>
        <option value="local">local - Ollama</option>
        <option value="api">api - placeholder/fallback</option>
      </select>
      <button class="green" onclick="compare()">So sánh 3 tầng</button>
      <button class="secondary" onclick="refreshState()">Refresh state</button>
    </div>
  </section>
  <section>
    <div class="card">
      <h2>Live telemetry timeline</h2>
      <div id="currentState" class="notice">Đang tải...</div>
      <div id="timeline" class="timeline"></div>
    </div>
    <div class="card">
      <h2>Kết quả so sánh</h2>
      <div class="grid3">
        <div class="result"><h3>1) Chỉ cảm biến</h3><div id="sensorOnly"></div></div>
        <div class="result"><h3>2) Cảm biến + AI models</h3><div id="sensorAI"></div></div>
        <div class="result"><h3>3) Cảm biến + AI models + LLM</h3><div id="sensorAILLM"></div></div>
      </div>
    </div>
    <div class="card">
      <h2>Evidence từ các lab trước</h2>
      <div id="evidence"></div>
      <p class="small"><b>Câu chốt:</b> Lab 3/4/6/7 tạo bằng chứng. Lab 8 dùng LLM để reasoning trên bằng chứng đó; LLM không thay thế các model trước.</p>
    </div>
    <div class="card">
      <h2>Context / raw JSON</h2>
      <pre id="rawJson">{}</pre>
    </div>
  </section>
</main>
<script>
let scenarios = [];
let state = null;

async function api(path, opts={}) { const r = await fetch(path, opts); if(!r.ok) throw new Error(await r.text()); return await r.json(); }
function riskBadge(r) { return `<span class="risk ${r}">${r}</span>`; }
function pretty(obj) { return JSON.stringify(obj, null, 2); }

async function init() {
  scenarios = await api('/scenarios');
  const sel = document.getElementById('scenario');
  sel.innerHTML = scenarios.map(s => `<option value="${s.scenario_id}">${s.title}</option>`).join('');
  sel.onchange = resetScenario;
  await resetScenario();
  const es = new EventSource('/stream/events');
  es.onmessage = (ev) => { const data = JSON.parse(ev.data); state = data.state; renderState(); };
}
async function resetScenario() {
  const sid = document.getElementById('scenario').value;
  state = await api(`/live/reset?scenario_id=${sid}`, {method:'POST'});
  const s = scenarios.find(x=>x.scenario_id===sid);
  document.getElementById('scenarioWhy').textContent = s ? s.why : '';
  renderState();
  await compare();
}
async function startTimeline() { const sid = document.getElementById('scenario').value; state = await api(`/live/start?scenario_id=${sid}&interval_sec=2`, {method:'POST'}); renderState(); }
async function stopTimeline() { state = await api('/live/stop', {method:'POST'}); renderState(); }
async function stepTimeline() { state = await api('/live/step', {method:'POST'}); renderState(); await compare(); }
async function refreshState() { state = await api('/live/state'); renderState(); }
function renderState() {
  if(!state) return;
  document.getElementById('currentState').innerHTML = `<b>${state.scenario_title}</b><br>step=${state.step_index}, running=${state.running}, updated=${state.last_updated}<br><b>Sensors:</b> ${Object.entries(state.sensors).map(([k,v])=>`${k}=${v}`).join(', ')}`;
  renderControls(); renderTimeline();
}
function renderControls() {
  const box = document.getElementById('sensorControls');
  const schema = state.editable_sensors || {}; const sensors = state.sensors || {};
  let html = '';
  for (const [key, spec] of Object.entries(schema)) {
    const val = sensors[key];
    html += `<div class="sensor-row"><label>${key} ${spec.unit ? '('+spec.unit+')' : ''}</label>`;
    if (spec.type === 'number') {
      html += `<input id="input_${key}" type="range" min="${spec.min}" max="${spec.max}" step="${spec.step}" value="${val}" oninput="document.getElementById('val_${key}').textContent=this.value">`;
      html += `<span class="small">value: <b id="val_${key}">${val}</b></span>`;
    } else {
      html += `<select id="input_${key}">${spec.options.map(o=>`<option value="${o}" ${String(o)===String(val)?'selected':''}>${o}</option>`).join('')}</select>`;
    }
    html += `</div>`;
  }
  box.innerHTML = html;
}
async function applySensors() {
  const schema = state.editable_sensors || {}; const updates = {};
  for (const [key, spec] of Object.entries(schema)) { updates[key] = document.getElementById('input_'+key).value; }
  state = await api('/live/update-sensor', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({updates})});
  renderState(); await compare();
}
function renderTimeline() {
  const hist = state.history || [];
  const key = hist.some(x=>x.co2_ppm !== undefined) ? 'co2_ppm' : hist.some(x=>x.temperature_c !== undefined) ? 'temperature_c' : null;
  if (!key) { document.getElementById('timeline').innerHTML = '<span class="small">No numeric timeline yet.</span>'; return; }
  const values = hist.map(x=>Number(x[key]||0)); const max = Math.max(...values, 1);
  document.getElementById('timeline').innerHTML = values.map(v=>`<div class="bar" title="${key}: ${v}" style="height:${Math.max(3, v/max*130)}px"></div>`).join('');
}
async function compare() {
  if(!state) await refreshState();
  const sid = state.scenario_id; const mode = document.getElementById('llmMode').value;
  const data = await api(`/compare-three-levels/${sid}?mode=${mode}`);
  renderCompare(data);
}
function renderCompare(data) {
  document.getElementById('sensorOnly').innerHTML = `${riskBadge(data.sensor_only.risk_level)}<p>${data.sensor_only.summary}</p><p><b>Action:</b> ${data.sensor_only.recommended_action}</p><p class="small">${data.sensor_only.reason}</p><p class="small"><b>Hạn chế:</b> ${data.sensor_only.limitations.join('; ')}</p>`;
  document.getElementById('sensorAI').innerHTML = `${riskBadge(data.sensor_plus_ai_models.risk_level)}<p>${data.sensor_plus_ai_models.summary}</p><p><b>Action:</b> ${data.sensor_plus_ai_models.recommended_action}</p><p class="small">${data.sensor_plus_ai_models.reason}</p><p class="small"><b>Hạn chế:</b> ${data.sensor_plus_ai_models.limitations.join('; ')}</p>`;
  const llm = data.sensor_ai_llm.final_decision;
  document.getElementById('sensorAILLM').innerHTML = `${riskBadge(llm.risk_level)}<p>${llm.situation_summary}</p><p><b>Action:</b> ${llm.recommended_action}</p><p><b>Human review:</b> ${llm.need_human_review}</p><p><b>Control allowed:</b> ${llm.control_allowed}</p><p class="small"><b>Blocked:</b> ${llm.blocked_reason}</p>`;
  document.getElementById('evidence').innerHTML = `<pre>${pretty(data.sensor_plus_ai_models.ai_model_outputs)}</pre>`;
  document.getElementById('rawJson').textContent = pretty(data);
}
init().catch(err => { document.body.innerHTML = '<pre>'+err.stack+'</pre>'; });
</script>
</body>
</html>
