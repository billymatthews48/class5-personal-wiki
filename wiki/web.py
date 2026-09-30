"""OPTIONAL local web interface: `wiki serve`. Same Harness as the CLI, standard library only.

Binds to 127.0.0.1 only. Three tabs map 1:1 to the CLI modes; every request goes through
Harness.search / Harness.ask / ChatSession.turn, so saved runs and citation checks are identical.
"""
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Academic Wiki</title>
<style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e2dfd8;--acc:#2f5d50;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe7;--mut:#a3a19b;--line:#33322f;--acc:#8cc2b0;--card:#1f1f1d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,sans-serif}
main{max-width:820px;margin:0 auto;padding:24px 16px}
h1{font-size:1.3rem;margin:0 0 4px} .sub{color:var(--mut);font-size:.9rem;margin-bottom:18px}
nav button{background:none;border:1px solid var(--line);color:var(--fg);padding:6px 14px;border-radius:6px;cursor:pointer;margin-right:6px}
nav button.on{background:var(--acc);border-color:var(--acc);color:var(--bg)}
form{display:flex;gap:8px;margin:16px 0} input{flex:1;padding:9px 12px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);font:inherit}
form button{padding:9px 16px;border:0;border-radius:6px;background:var(--acc);color:var(--bg);font:inherit;cursor:pointer}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0;white-space:pre-wrap}
.meta{color:var(--mut);font-size:.82rem} .you{border-left:3px solid var(--acc)}
</style></head><body><main>
<h1>Academic Wiki</h1><div class="sub">model __MODEL__ &middot; execution: local &middot; same harness as the CLI</div>
<nav><button data-m="chat" class="on">Chat</button><button data-m="ask">Ask</button><button data-m="search">Search</button></nav>
<form id="f"><input id="q" autocomplete="off" placeholder="Talk to Quill..."><button>Send</button></form>
<div id="out"></div></main>
<script>
let mode='chat';const ph={chat:'Talk to Quill...',ask:'Ask a factual question (standalone, cited)',search:'Search original passages (no answer generated)'};
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));b.classList.add('on');mode=b.dataset.m;q.placeholder=ph[mode];out.innerHTML=''});
function card(t,m,cls){const d=document.createElement('div');d.className='card '+(cls||'');d.textContent=t;if(m){const s=document.createElement('div');s.className='meta';s.textContent=m;d.appendChild(s)}out.appendChild(d);return d}
f.onsubmit=async e=>{e.preventDefault();const text=q.value.trim();if(!text)return;q.value='';
 if(mode!=='search')card(text,'','you');const wait=card('working... (local CPU, this can take a minute)');
 const r=await fetch('/api/'+mode,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
 const j=await r.json();wait.remove();if(j.error){card('Error: '+j.error);return}
 if(mode==='search'){j.passages.forEach(p=>card(p.text,`[${p.rank}] ${p.raw_path} (${p.locator}) · note: ${p.note_path||'-'} · ${p.method}`));return}
 if(mode==='ask'){card(j.answer,`status: ${j.status}\\n`+(j.sources.join('\\n')||'no citations'));return}
 card(j.reply,(j.retrieved?`searched notes: "${j.search_query}"\\n`+j.sources.join('\\n'):'no notes search'))};
</script></body></html>"""


def serve(harness, port=8765):
    session = harness.chat_session()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE.replace("__MODEL__", config.CHAT_MODEL), "text/html")
            else:
                self._send(404, json.dumps({"error": "not found"}))

        def do_POST(self):
            try:
                text = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))["text"]
                if self.path == "/api/search":
                    passages, _ = harness.search(text)
                    out = {"passages": [asdict(p) for p in passages]}
                elif self.path == "/api/ask":
                    rec = harness.ask(text)
                    out = {k: rec[k] for k in ("answer", "status", "sources")}
                elif self.path == "/api/chat":
                    e = session.turn(text)
                    out = {k: e[k] for k in ("reply", "retrieved", "search_query", "sources")}
                else:
                    return self._send(404, json.dumps({"error": "not found"}))
                self._send(200, json.dumps(out, default=str))
            except Exception as err:   # surface harness errors (Ollama down, empty index) in the UI
                self._send(500, json.dumps({"error": str(err)}))

        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"serving on http://127.0.0.1:{port} (local only; Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if session.log:
            print(f"chat transcript saved: {session.save()}")
