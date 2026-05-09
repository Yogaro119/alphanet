import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import check_auth, load_dashboard_css, render_sidebar
import requests
import time
import datetime

st.set_page_config(page_title="AlphaNet — Bulk Downloader", page_icon="📥",
                   layout="wide", initial_sidebar_state="expanded")

check_auth()
load_dashboard_css()
render_sidebar("bulk")

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">📥 &nbsp;BULK DOWNLOADER</div>
        <div style="font-family:var(--mono);font-size:11px;color:rgba(255,255,255,0.3);
                    letter-spacing:2px;margin-top:4px;">
            MULTI-URL FILE DOWNLOADER
        </div>
    </div>
    <div class="page-badge">● &nbsp;DOWNLOADER READY</div>
</div>
""", unsafe_allow_html=True)

# ─── Input ────────────────────────────────────────────────────────────────────
st.markdown('<div class="panel-card"><div class="panel-title">🔗 DOWNLOAD URLS</div>',
            unsafe_allow_html=True)

url_input = st.text_area(
    "Enter file URLs (one per line)",
    placeholder="https://example.com/file1.pdf\nhttps://example.com/image.png",
    height=140, label_visibility="collapsed", key="dl_urls"
)
st.markdown("</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    dl_btn = st.button("⬇  START DOWNLOAD", key="run_dl", use_container_width=True)
with col2:
    st.markdown("""
    <div style="font-family:var(--mono);font-size:11px;
                color:rgba(255,255,255,0.3);padding:10px 0;letter-spacing:1px;">
        Files will be saved to the <code>downloads/</code> folder in the project directory.
    </div>
    """, unsafe_allow_html=True)

# ─── Download Logic ───────────────────────────────────────────────────────────
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def download_file(url: str) -> dict:
    url = url.strip()
    if not url:
        return {}
    fname = url.split("/")[-1].split("?")[0] or "file_" + str(int(time.time()))
    fpath = os.path.join(DOWNLOADS_DIR, fname)
    try:
        start = time.time()
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(fpath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        elapsed = round(time.time() - start, 2)
        size_kb = round(downloaded / 1024, 1)
        return {
            "URL": url, "Filename": fname,
            "Size": f"{size_kb} KB", "Time": f"{elapsed}s",
            "Status": "✅ Done", "Path": fpath
        }
    except Exception as e:
        return {
            "URL": url, "Filename": fname,
            "Size": "—", "Time": "—",
            "Status": f"❌ {str(e)[:50]}", "Path": "—"
        }


if dl_btn:
    urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
    if not urls:
        st.markdown('<div class="a-warn">⚠ &nbsp;Please enter at least one URL.</div>',
                    unsafe_allow_html=True)
    else:
        results = []
        prog = st.progress(0)
        log_box = st.empty()

        for i, url in enumerate(urls):
            log_box.markdown(f"""
            <div style="font-family:var(--mono);font-size:12px;
                        color:rgba(0,200,255,0.7);letter-spacing:1px;">
                › Downloading: {url[:80]}...
            </div>""", unsafe_allow_html=True)
            r = download_file(url)
            if r:
                results.append(r)
            prog.progress((i + 1) / len(urls))

        log_box.empty()
        prog.empty()

        if results:
            success = sum(1 for r in results if "Done" in r["Status"])
            failed  = len(results) - success

            s1, s2 = st.columns(2)
            with s1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="mc-label">COMPLETED</div>
                    <div class="mc-value" style="color:#00ff88;">{success}</div>
                </div>""", unsafe_allow_html=True)
            with s2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="mc-label">FAILED</div>
                    <div class="mc-value" style="color:#ff4d6a;">{failed}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📋 DOWNLOAD LOG</div>', unsafe_allow_html=True)

            for r in results:
                ok = "Done" in r["Status"]
                color = "#00ff88" if ok else "#ff4d6a"
                st.markdown(f"""
                <div style="background:var(--panel);border:1px solid {color}33;
                            border-left:3px solid {color};border-radius:10px;
                            padding:14px 20px;margin-bottom:8px;">
                    <div style="font-family:var(--mono);font-size:13px;
                                color:var(--white);margin-bottom:4px;">
                        {r['Filename']}
                    </div>
                    <div style="font-family:var(--mono);font-size:11px;
                                color:rgba(255,255,255,0.35);">
                        {r['Status']} &nbsp;·&nbsp; {r['Size']} &nbsp;·&nbsp; {r['Time']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Log activity
            if "logs" not in st.session_state:
                st.session_state["logs"] = []
            st.session_state["logs"].append({
                "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Module": "Bulk Downloader",
                "Action": f"Downloaded {len(results)} files",
                "Result": f"{success} success, {failed} failed"
            })

# ─── Downloads folder viewer ──────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="panel-title">📁 DOWNLOADS FOLDER</div>', unsafe_allow_html=True)

files = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))]
if files:
    for f in sorted(files)[:20]:
        fpath = os.path.join(DOWNLOADS_DIR, f)
        size  = os.path.getsize(fpath)
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:10px 16px;border-bottom:1px solid rgba(0,255,136,0.07);
                    font-family:var(--mono);font-size:12px;">
            <span style="color:rgba(255,255,255,0.7);">📄 {f}</span>
            <span style="color:rgba(0,255,136,0.5);">{round(size/1024,1)} KB</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="font-family:var(--mono);font-size:12px;
                color:rgba(255,255,255,0.25);text-align:center;padding:30px;">
        No files downloaded yet.
    </div>
    """, unsafe_allow_html=True)
