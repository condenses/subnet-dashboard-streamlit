import streamlit as st
import requests
import plotly.graph_objects as go

# Set up page configuration with a custom layout and favicon
st.set_page_config(page_title="Leaderboard - Neural Condense Subnet", layout="wide")

# Centered page title and navigation links
st.markdown(
    """
    <style>
        .centered { text-align: center; }
        .header { font-size: 36px; font-weight: 600; color: #333; }
        .subheader { color: #555; font-size: 16px; }
        .divider { margin: 20px 0; border-top: 1px solid #ddd; }
    </style>
    <div class="centered">
        <h1 class="header">Neural Condense Subnet</h1>
        <p class="subheader">
            <a href="https://discord.gg/bittensor" style="margin-right: 20px;">
                <img src="https://img.shields.io/badge/bittensor-discord-green?logo=discord">
            </a>
            <a href="https://github.com/condenses/neural-condense-subnet">
                <img src="https://img.shields.io/badge/subnet-github-blue?logo=github">
            </a>
        </p>
    </div>
    <div class="divider"></div>
    """,
    unsafe_allow_html=True,
)

# Fetch reports from API
response = requests.get("https://report.condenses.ai/api/get-reports")
reports = response.json()
st.session_state.stats = response

# Mapping hotkeys to validator names
hotkey_to_name = {
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator"
}
name_to_hotkey = {v: k for k, v in hotkey_to_name.items()}

# Columns layout
col1, col2 = st.columns([1, 2])

# User selection for validators in the left column
with col1:
    selected_name = st.selectbox(
        "Select a validator", list(hotkey_to_name.values()), index=0
    )
    hotkey = name_to_hotkey[selected_name]

# Find report for the selected hotkey
for report in reports["reports"]:
    if report["hotkey"] == hotkey:
        break

# Extract metadata and calculate tier distribution
metadata = report["report"]["metadata"]
tier_distribution = {}
scores = {}
for uid, data in metadata.items():
    tier = data["tier"]
    scores[uid] = data["score"]
    tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

# Display the selected validator's title in the left column
with col1:
    st.markdown(
        f"""
        <div class="centered">
            <h3 class="header">{selected_name}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Pie chart for tier distribution in the right column
with col2:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(tier_distribution.keys()),
                values=list(tier_distribution.values()),
                hole=0.3,
                marker=dict(colors=["#636EFA", "#EF553B", "#00CC96"]),
            )
        ]
    )
    fig.update_layout(
        title="Tier Distribution",
        title_x=0.5,
        title_font=dict(size=22, family="Arial", color="#333"),
    )
    st.plotly_chart(fig)

# Dropdown for tier selection
tiers = ["research", "inference_0", "inference_1"]
selected_tier = st.selectbox("Select a Tier", tiers)

# Display the selected tier's score distribution as a bar chart
uids = [uid for uid, data in metadata.items() if data["tier"] == selected_tier]
if uids:
    scores_tier = [scores[uid] for uid in uids]

    fig = go.Figure(
        data=[
            go.Bar(x=[str(uid) for uid in uids], y=scores_tier, marker_color="#636EFA")
        ],
    )
    fig.update_layout(
        title=f"{selected_tier.capitalize()} Tier Scores",
        xaxis_title="UID",
        yaxis_title="Score",
        xaxis=dict(tickmode="array", tickvals=[str(uid) for uid in uids]),
        width=1200,
        title_font=dict(size=20, family="Arial", color="#333"),
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig)
