// CSRF helper
function getCookie(name){
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
const csrftoken = getCookie('csrftoken');

const el = (sel)=>document.querySelector(sel);
const chat = el('#chat');
const historyBox = el('#history');
let collapseBtn = null;
let expandBtn = null;
const hero = el('#hero');

function addMsg(role, text){
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const safe = String(text).replace(/</g,'&lt;');
  wrap.innerHTML = `<div class="bubble">${safe}</div>`;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  if(hero){ hero.style.display='none'; }
  updateEmptyState();
}

// WebSocket chat
let ws;
function connectWS(){
  const sid = (window.OPTI && window.OPTI.CHAT_SESSION_ID) ? window.OPTI.CHAT_SESSION_ID : '';
  if(!sid) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/chat/${sid}/`);
  ws.onmessage = (e)=>{
    try { const msg = JSON.parse(e.data); if(msg.type==='assistant_message'){ addMsg('assistant', msg.text);} } catch{}
  };
}

document.addEventListener('DOMContentLoaded', ()=>{
  // Theme init
  const saved = localStorage.getItem('theme')||'dark';
  document.body.classList.toggle('theme-dark', saved==='dark');
  document.body.classList.toggle('theme-light', saved==='light');
  const t = el('#themeToggle');
  if(t){
    t.checked = (saved==='dark');
    t.addEventListener('change', ()=>{
      const dark = t.checked;
      document.body.classList.add('theme-transition');
      document.body.classList.toggle('theme-dark', dark);
      document.body.classList.toggle('theme-light', !dark);
      localStorage.setItem('theme', dark ? 'dark' : 'light');
      setTimeout(()=> document.body.classList.remove('theme-transition'), 450);
    });
  }

  // Query buttons now that DOM is ready
  collapseBtn = el('#collapseBtn');
  expandBtn = el('#expandBtn');

  // Sidebar collapse state
  const savedSidebar = localStorage.getItem('sidebar')||'shown';
  if(savedSidebar==='hidden') document.body.classList.add('sidebar-hidden');
  if(collapseBtn){ collapseBtn.addEventListener('click', ()=>{
    document.body.classList.toggle('sidebar-hidden');
    localStorage.setItem('sidebar', document.body.classList.contains('sidebar-hidden') ? 'hidden' : 'shown');
  }); }
  if(expandBtn){ expandBtn.addEventListener('click', ()=>{
    document.body.classList.remove('sidebar-hidden');
    localStorage.setItem('sidebar','shown');
  }); }

  // Connect WS and send messages
  connectWS();
  const sendBtn = el('#sendBtn');
  if(sendBtn){
    sendBtn.addEventListener('click', ()=>{
      const txtEl = el('#chatInput');
      const t = txtEl.value.trim(); if(!t || !ws) return;
      addMsg('user', t);
      ws.send(JSON.stringify({type:'user_message', text: t}));
      txtEl.value='';
    });
    const input = el('#chatInput');
    if(input){
      input.addEventListener('keydown', (ev)=>{
        if(ev.key === 'Enter' && !ev.shiftKey){ ev.preventDefault(); sendBtn.click(); }
      });
    }
  }

  try{ if(historyBox) renderHistory(JSON.parse(localStorage.getItem('opti_hist')||'[]')); }catch{}
  updateEmptyState();
});

function renderHistory(items){
  if(!historyBox) return;
  historyBox.innerHTML = items.map(i=>`<div class="small">#${i.id.slice(0,8)} • f*=${i.f}</div>`).join('');
}

function updateEmptyState(){
  if(!chat) return;
  const hasMessages = chat.querySelector('.msg') !== null;
  if(hasMessages){
    document.body.classList.remove('is-empty');
  } else {
    if(hero){ hero.style.display='block'; }
    document.body.classList.add('is-empty');
  }
}
