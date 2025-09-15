let patients = [];
window.__state = {};
window.__tags = [];

function setStatus(s){ document.getElementById('status').textContent = s; }
function el(id){ return document.getElementById(id); }
function clearTranscript(){ el('transcript').innerHTML=''; }

function addMsg(text, who, merge=false){
  const t = el('transcript');
  let bubble;
  if(merge){
    const last = t.lastElementChild;
    if(last && last.classList.contains('msg') && last.classList.contains(who)){
      bubble = last;
      bubble.textContent += text;
    } else {
      bubble = document.createElement('div');
      bubble.className = `msg ${who}`;
      bubble.textContent = text;
      t.appendChild(bubble);
    }
  } else {
    bubble = document.createElement('div');
    bubble.className = `msg ${who}`;
    bubble.textContent = text;
    t.appendChild(bubble);
  }
  t.scrollTop = t.scrollHeight;
  return bubble;
}

async function loadPatients(){
  const r = await fetch('/patients');
  const j = await r.json();
  patients = j.patients || [];
  const sel = el('patient'); sel.innerHTML='';
  patients.forEach(p=>{
    const o = document.createElement('option');
    o.value = p.patient_id;
    const label = `${p.patient_id} — ${p.preferred_name || ''} (${p.condition || ''})`;
    o.textContent = label;
    sel.appendChild(o);
  });
  if(patients.length){ sel.value = patients[0].patient_id; updatePreview(); }
}

function updatePreview(){
  const pid = el('patient').value;
  const p = patients.find(x=>x.patient_id===pid);
  el('p_name').textContent = (p?.preferred_name || '—');
  el('p_age').textContent = (p?.age || '—');
  el('p_cond').textContent = (p?.condition || '—');
  el('p_cc').textContent = (p?.chief_complaint || '—');
  el('p_lang').textContent = (p?.language || '—');
  el('p_interp').textContent = (String(p?.interpreter_needed)==='true'?'Yes':'No');
}

async function sendSync(pid, text){
  const r = await fetch('/chat_llm', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({patient_id: pid, user_text: text, state: window.__state || {}})
  });
  const j = await r.json();
  window.__state = j.state; window.__tags = (window.__tags||[]).concat(j.tags||[]);
  addMsg(j.reply, 'bot');
  setStatus('Done');
}

async function sendStream(pid, text){
  // Streaming via fetch ReadableStream, parse SSE lines and append to a single bubble
  const r = await fetch('/chat_llm_stream', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({patient_id: pid, user_text: text, state: window.__state || {}})
  });
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf='';
  let botBubble = addMsg('', 'bot', false); // start empty bubble
  botBubble.classList.add('typing');
  while(true){
    const {value, done} = await reader.read();
    if(done) break;
    buf += decoder.decode(value, {stream:true});
    let idx;
    while((idx = buf.indexOf('\n\n')) >= 0){
      const raw = buf.slice(0, idx); buf = buf.slice(idx+2);
      if(!raw.trim()) continue;
      const lines = raw.split('\n');
      let event='message', data='';
      for(const line of lines){
        if(line.startsWith('event:')) event = line.slice(6).trim();
        else if(line.startsWith('data:')) data += line.slice(5).trim();
      }
      if(event==='token'){
        botBubble.textContent += data;
      } else if(event==='meta'){
        try{
          const meta = JSON.parse(data);
          window.__state = meta.state;
          window.__tags = (window.__tags||[]).concat(meta.tags||[]);
        }catch{}
      } else if(event==='done'){
        // finalize bubble
        botBubble.classList.remove('typing');
        setStatus('Done');
      }
    }
  }
}

async function onSend(){
  const pid = el('patient').value;
  const text = el('user').value.trim();
  if(!pid || !text) return;
  addMsg(text, 'user');
  el('user').value='';
  setStatus('Sending...');
  const mode = el('mode').value;
  if(mode==='stream') await sendStream(pid, text); else await sendSync(pid, text);
}

async function onInterpreter(){
  // Convenience: inform the model that interpreter is present
  el('user').value = "An interpreter is present now.";
  await onSend();
}

function renderScoreDetails(details){
  const box = el('score-details'); box.innerHTML='';
  details.forEach(it=>{
    const div = document.createElement('div');
    div.className = 'detail';
    const label = document.createElement('div'); label.textContent = it.label;
    const badge = document.createElement('div'); badge.className = 'badge ' + (it.hit?'hit':'miss');
    badge.textContent = it.hit ? `+${it.points}/${it.max}` : `0/${it.max}`;
    div.appendChild(label); div.appendChild(badge);
    box.appendChild(div);
  });
}

function setScoreVis(score){
  el('score-num').textContent = `${score.percent}%`;
  el('score-bar-fill').style.width = `${score.percent}%`;
  renderScoreDetails(score.details || []);
}

async function onScore(){
  const tags = window.__tags || [];
  const r = await fetch('/score', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({tags})});
  const j = await r.json();
  setScoreVis(j);
}

function onScoreClear(){
  el('score-num').textContent = '—';
  el('score-bar-fill').style.width = '0%';
  el('score-details').innerHTML='';
}

function onReset(){
  window.__state = {}; window.__tags = [];
  clearTranscript(); onScoreClear();
  setStatus('Session reset');
}

el('send').addEventListener('click', onSend);
el('user').addEventListener('keydown', e=>{ if(e.key==='Enter'){ onSend(); }});
el('patient').addEventListener('change', updatePreview);
el('btn-interpreter').addEventListener('click', onInterpreter);
el('clear').addEventListener('click', onReset);
el('btn-score').addEventListener('click', onScore);
el('btn-score-clear').addEventListener('click', onScoreClear);

loadPatients().then(()=> setStatus('Ready'));
