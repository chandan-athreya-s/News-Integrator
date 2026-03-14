# streamlit_app/app.py
import os
import time
import json
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Latest News Integrator", page_icon="📰", layout="wide")
st.title("📰 Latest News Integrator")

with st.sidebar:
    st.header("Settings")
    backend = st.text_input("Backend URL", value=BACKEND_URL, help="FastAPI base URL")
    st.caption("Example: http://localhost:8000")

topic = st.text_input("Enter a topic or query", placeholder="e.g., generative AI regulation")
cols = st.columns(3)
with cols[0]:
    max_results = st.slider("Number of articles", min_value=3, max_value=20, value=10, step=1)
with cols[1]:
    time_range = st.selectbox("Time range", options=["24h", "7d", "30d"], index=1)
with cols[2]:
    language = st.text_input("Language (ISO code)", value="en")

submit = st.button("Fetch & Summarize", type="primary", use_container_width=True)

if submit:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    payload = {
        "topic": topic.strip(),
        "max_results": max_results,
        "time_range": time_range,
        "language": language.strip() or "en",
    }

    st.info(f"Querying backend at {backend} ...")
    start = time.time()
    with st.spinner("Fetching latest news and generating summary..."):
        try:
            resp = requests.post(f"{backend}/api/news/summary", json=payload, timeout=60)
            elapsed = time.time() - start
            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                st.success(f"Done in {elapsed:.2f}s")

                # Summary
                st.subheader("Summary")
                st.write(data["summary"])

                # Bullets
                if data.get("bullets"):
                    st.subheader("Key Highlights")
                    for b in data["bullets"]:
                        st.markdown(f"- {b}")

                # Follow-up questions
                if data.get("follow_ups"):
                    st.subheader("Suggested Follow-up Questions / Angles")
                    for q in data["follow_ups"]:
                        st.markdown(f"- {q}")

                # Articles
                st.subheader(f"Articles ({len(data.get('articles', []))})")
                for idx, a in enumerate(data.get("articles", []), start=1):
                    with st.expander(f"{idx}. {a.get('title')}", expanded=False):
                        st.markdown(f"**Source:** {a.get('source') or 'Unknown'}")
                        st.markdown(f"**Published:** {a.get('published_at') or 'Unknown'}")
                        st.markdown(f"**URL:** {a.get('url')}")
                        if a.get("snippet"):
                            st.write(a["snippet"])

                # Debug
                with st.expander("Debug / Raw JSON"):
                    st.code(json.dumps(data, indent=2))
        except requests.RequestException as e:
            st.error(f"Request failed: {e}")