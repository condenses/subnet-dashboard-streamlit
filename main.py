import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import copy

st.set_page_config(page_title="Leaderboard - Neural Condense Subnet", layout="wide")

st.markdown(
    """
    <div align="center" style="color: black">

# Neural Condense Subnet <!-- omit in toc -->
[![](https://img.shields.io/badge/bittensor-discord-green?logo=discord)](https://discord.gg/bittensor)
[![](https://img.shields.io/badge/subnet-github-blue?logo=github)](https://github.com/condenses/neural-condense-subnet)

</div>
    """,
    unsafe_allow_html=True,
)

response = requests.get("https://report.condenses.ai/api/get-reports")
reports = response.json()
st.session_state.stats = response

hotkey_to_name = {
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator"
}

name_to_hotkey = {v: k for k, v in hotkey_to_name.items()}

selected_name = st.selectbox(
    "Select a validator", list(hotkey_to_name.values()), index=0
)

hotkey = name_to_hotkey[selected_name]

for report in reports["reports"]:
    if report["hotkey"] == hotkey:
        break
metadata = report["report"]["metadata"]
tier_distribution = {}
scores = {}
for uid, data in metadata.items():
    tier = data["tier"]
    scores[uid] = data["score"]
    if tier not in tier_distribution:
        tier_distribution[tier] = 0
    tier_distribution[tier] += 1

st.markdown(
    f"""
    <div align="center" style="color: black">
        <h1>Validator: {selected_name}</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

fig = go.Figure(
    data=[
        go.Pie(
            labels=list(tier_distribution.keys()),
            values=list(tier_distribution.values()),
            hole=0.3,
        )
    ]
)

fig.update_layout(
    title_text="Tier Distribution",
    title_x=0.5,
    title_font_size=20,
    title_font_family="Arial",
    title_font_color="black",
)

st.plotly_chart(fig)

# Plot each tier scores distribution as a histogram, x axis is UID, y axis is score

tiers = ["research", "inference_0", "inference_1"]

for tier in tiers:
    uids = [uid for uid, data in metadata.items() if data["tier"] == tier]
    if len(uids) == 0:
        continue
    scores_tier = [scores[uid] for uid in uids]
    print(uids, scores_tier)
    fig = go.Figure(
        data=[go.Bar(x=[str(uid) for uid in uids], y=scores_tier)],
    )
    fig.update_layout(
        title_text=f"{tier.capitalize()} tier",
        xaxis_title="UID",
        yaxis_title="Score",
        width=1200,
    )
    st.plotly_chart(fig)
