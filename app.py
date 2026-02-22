import time
import requests
import streamlit as st

st.set_page_config(page_title="QazDx", page_icon="🖤", layout="wide")

st.markdown(
    """
<style>
:root{
  --bg:#07060b;
  --panel: rgba(255,255,255,.055);
  --stroke: rgba(255,255,255,.12);
  --stroke2: rgba(255,255,255,.18);
  --text: rgba(255,255,255,.92);
  --muted: rgba(255,255,255,.72);
  --muted2: rgba(255,255,255,.55);

  --wine:#8c1236;
  --plum:#3a155f;
  --gold:#d8b17b;
  --ok:#4ee8b4;
  --bad:#ff4d6d;

  --r:16px;
  --r2:20px;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace;
}

html, body, [data-testid="stAppViewContainer"]{
  background:
    radial-gradient(900px 650px at 12% 8%, rgba(140,18,54,.22), transparent 60%),
    radial-gradient(900px 650px at 88% 12%, rgba(58,21,95,.20), transparent 60%),
    radial-gradient(900px 650px at 50% 92%, rgba(216,177,123,.08), transparent 65%),
    var(--bg);
  color: var(--text);
}
.block-container{ max-width: 1200px; padding-top: .8rem !important; padding-bottom: 2rem; }
[data-testid="stAppViewContainer"] *{ color: var(--text); }
.small{ font-size: .88rem; color: var(--muted2) !important; }
.muted{ color: var(--muted) !important; }
.mono{ font-family: var(--mono); }

section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.02)) !important;
  border-right: 1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] *{ color: var(--text) !important; }

.card{
  border-radius: var(--r2);
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.03));
  box-shadow: 0 12px 45px rgba(0,0,0,.35);
}
.panel{
  border-radius: var(--r);
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,.03);
}
.pad{ padding: 14px 14px; }
.padlg{ padding: 18px 18px; }

.pill{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px;
  border: 1px solid var(--stroke2);
  background: rgba(255,255,255,.04);
  font-size:.86rem; margin-right:8px; margin-bottom:8px;
}
.dot{ width:8px;height:8px;border-radius:999px;background:var(--muted2); }
.dot-ok{ background: var(--ok); }
.dot-bad{ background: var(--bad); }
.p-wine{ border-color: rgba(140,18,54,.55); background: rgba(140,18,54,.16); }
.p-plum{ border-color: rgba(58,21,95,.55); background: rgba(58,21,95,.13); }
.p-gold{ border-color: rgba(216,177,123,.60); background: rgba(216,177,123,.10); }

.stButton>button{
  border-radius: 14px !important;
  border: 1px solid rgba(216,177,123,.35) !important;
  background: rgba(255,255,255,.06) !important;
  color: var(--text) !important;
}
.stButton>button:hover{
  border-color: rgba(216,177,123,.65) !important;
  background: rgba(255,255,255,.08) !important;
  transform: translateY(-1px);
}

/* widgets dark */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[role="combobox"]{
  background: rgba(0,0,0,.35) !important;
  border: 1px solid rgba(255,255,255,.14) !important;
  color: var(--text) !important;
  border-radius: 14px !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder{
  color: rgba(255,255,255,.45) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

def ping(base: str, timeout: int = 2):
    for u in (f"{base}/docs", f"{base}/"):
        try:
            r = requests.get(u, timeout=timeout)
            if r.status_code < 500:
                return True, f"{u} → {r.status_code}"
        except Exception as e:
            last = str(e)
    return False, last if "last" in locals() else "No response"

def post_json(url: str, payload: dict, timeout: int):
    t0 = time.time()
    r = requests.post(url, json=payload, timeout=timeout)
    return r, (time.time() - t0) * 1000

def normalize_analyze(data: dict):
    top = data.get("top_diagnoses") or []
    out = []
    for d in top[:3]:
        out.append({
            "name": d.get("name") or d.get("diagnosis") or "Unknown",
            "icd": d.get("icd10_code","") or "",
            "pid": d.get("protocol_id","") or "",
            "score": d.get("confidence", d.get("score", None)),
            "ev": d.get("evidence", []) or [],
            "qs": d.get("recommended_questions", []) or [],
        })
    return out, data.get("latency_ms", None)

def normalize_diagnose(data: dict):
    diags = sorted((data.get("diagnoses") or []), key=lambda x: x.get("rank", 999))
    out = []
    for d in diags[:3]:
        out.append({"name":"(ICD only)", "icd": d.get("icd10_code","") or "", "pid":"", "score":None, "ev":[], "qs":[]})
    return out

# state
if "history" not in st.session_state:
    st.session_state["history"] = []

# sidebar
st.sidebar.markdown("## Settings")
api_url = st.sidebar.text_input("API base URL", st.session_state.get("api_url","http://127.0.0.1:8000")).rstrip("/")
st.session_state["api_url"] = api_url

mode = st.sidebar.radio("Mode", ["Smart (analyze)", "Fast (diagnose)"], index=0)
timeout_s = st.sidebar.slider("Timeout (seconds)", 5, 180, 60)
keep_history = st.sidebar.checkbox("Keep history", value=True)

st.sidebar.markdown("---")
preset = st.sidebar.selectbox("Presets", ["—",
    "Травма: упал на вытянутую руку, деформация предплечья, хруст",
    "Мочеиспускание: частые позывы, резь, боль в пояснице, мутная моча",
    "Герпес: зуд/жжение, пузырьки, язвочки, боль при мочеиспускании, рецидив",
    "Кашель/температура: кашель, одышка, температура 38.5, слабость",
], index=0)

if preset != "—":
    st.session_state["q"] = preset

# header
L, R = st.columns([1.5, 1.0])
with L:
    st.markdown(
        """
<div class="card padlg">
  <div style="font-size:1.6rem;font-weight:900;">QazDx</div>
  <div class="muted">Clinical decision support MVP • RU/KZ/EN</div>
</div>
""",
        unsafe_allow_html=True,
    )
with R:
    ok, msg = ping(api_url, timeout=2)
    st.markdown('<div class="panel pad">', unsafe_allow_html=True)
    st.markdown('<div class="small">Server</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:6px;">
  <div style="font-size:1.1rem;font-weight:900;">{"Online" if ok else "Offline"}</div>
  <div class="mono small">{api_url}</div>
</div>
<div style="margin-top:10px;">
  <span class="pill p-gold"><span class="dot {"dot-ok" if ok else "dot-bad"}"></span>{msg}</span>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

query = st.text_area(
    "Patient symptoms / complaint",
    value=st.session_state.get("q",""),
    height=180,
    placeholder="Например: боль, температура, тошнота…",
)
st.session_state["q"] = query

b1, b2, b3, b4 = st.columns([1,1,1,2])
run_btn = b1.button("Run", use_container_width=True)
ping_btn = b2.button("Ping", use_container_width=True)
clear_btn = b3.button("Clear", use_container_width=True)
with b4:
    st.caption("Smart uses /analyze (may be slow). Fast uses /diagnose (always returns).")

if clear_btn:
    st.session_state["q"] = ""
    st.rerun()

if ping_btn:
    ok2, msg2 = ping(api_url, timeout=2)
    st.success(f"OK: {msg2}") if ok2 else st.error(f"OFF: {msg2}")

if run_btn and query.strip():
    try:
        used = ""
        results = []
        engine_ms = None

        if mode.startswith("Smart"):
            try:
                r, dt = post_json(f"{api_url}/analyze", {"query": query}, timeout_s)
                if r.status_code == 200:
                    results, engine_ms = normalize_analyze(r.json())
                    used = f"/analyze • {dt:.0f} ms"
                else:
                    raise RuntimeError(r.text)
            except Exception:
                r2, dt2 = post_json(f"{api_url}/diagnose", {"query": query}, timeout_s)
                if r2.status_code == 200:
                    results = normalize_diagnose(r2.json())
                    used = f"/diagnose (fallback) • {dt2:.0f} ms"
                else:
                    st.error(f"API error: {r2.status_code}")
                    st.code(r2.text)
        else:
            r, dt = post_json(f"{api_url}/diagnose", {"query": query}, timeout_s)
            if r.status_code == 200:
                results = normalize_diagnose(r.json())
                used = f"/diagnose • {dt:.0f} ms"
            else:
                st.error(f"API error: {r.status_code}")
                st.code(r.text)

        if results:
            if keep_history:
                st.session_state["history"].insert(0, {"mode": mode, "query": query, "used": used, "resp": results})

            st.markdown("### Results")
            st.markdown(
                f'<span class="pill p-gold">{used}</span>' +
                (f'<span class="pill p-plum">engine: {engine_ms} ms</span>' if engine_ms else ""),
                unsafe_allow_html=True
            )

            cols = st.columns(3)
            for i in range(3):
                with cols[i]:
                    if i >= len(results):
                        st.markdown('<div class="panel pad"><div class="small">—</div></div>', unsafe_allow_html=True)
                        continue
                    d = results[i]
                    st.markdown('<div class="panel pad">', unsafe_allow_html=True)
                    st.markdown(f"**{i+1}. {d['name']}**")
                    chips = ""
                    if d["icd"]:
                        chips += f'<span class="pill p-wine">ICD-10: <b>{d["icd"]}</b></span>'
                    if d["pid"]:
                        chips += f'<span class="pill p-plum">protocol: <span class="mono">{d["pid"]}</span></span>'
                    if d["score"] is not None:
                        try:
                            chips += f'<span class="pill p-gold">score: <b>{float(d["score"]):.3f}</b></span>'
                        except Exception:
                            chips += f'<span class="pill p-gold">score: <b>{d["score"]}</b></span>'
                    st.markdown(chips, unsafe_allow_html=True)

                    if d["ev"] or d["qs"]:
                        with st.expander("Details", expanded=False):
                            if d["ev"]:
                                st.markdown("**Evidence**")
                                for e in d["ev"][:8]:
                                    st.write("•", e)
                            if d["qs"]:
                                st.markdown("**Follow-ups**")
                                for q in d["qs"][:8]:
                                    st.write("•", q)
                    st.markdown("</div>", unsafe_allow_html=True)

    except requests.exceptions.RequestException as e:
        st.error("Request failed (timeout / server down). Increase timeout or use Fast mode.")
        st.code(str(e))

if keep_history:
    st.markdown("---")
    st.markdown("### History")
    for idx, item in enumerate(st.session_state["history"][:8]):
        title = f"{idx+1}) {item['mode']} • {item['used']} • {item['query'][:60]}{'...' if len(item['query'])>60 else ''}"
        with st.expander(title):
            st.code(item["query"])
            st.json(item["resp"])