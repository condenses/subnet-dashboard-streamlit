import streamlit as st
import requests
import plotly.graph_objects as go

# Set up page configuration with a custom layout and favicon
st.set_page_config(page_title="Leaderboard - Neural Condense Subnet", layout="wide")

# Centered page title and navigation links
st.markdown(
    """
    <div align="center">
        <h1 class="header">Neural Condense Subnet</h1>
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
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator",
    "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v": "RoundTable21"
}
name_to_hotkey = {v: k for k, v in hotkey_to_name.items()}

# Columns layout
col1, col2 = st.columns([2, 1])

# User selection for validators in the left column
with col1:
    selected_name = st.selectbox(
        "Select a validator", list(hotkey_to_name.values()), index=0
    )
    hotkey = name_to_hotkey[selected_name]
    st.toast(f"Selected {selected_name}", icon="🔍")
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
<div align="center">

**Viewing report from {selected_name}**                                                                                                                                        

| Component                                | Link                                                              |
|------------------------------------------|-------------------------------------------------------------------|
| 🌐 **Condense-AI & API Document**                        | [Visit Condense-AI](https://condenses.ai)                         |
| 📚 **API Library**                        | [Explore API Library](https://github.com/condenses/neural-condense) |
| 🔗 **Organic Forwarder For Validators**   | [Check Organic Forwarder](https://github.com/condenses/subnet-organic) |
| 📦 **Neural Condense Subnet**                       | [Source Code](https://github.com/condenses/neural-condense-subnet)                   |

| **Tier**       | **Purpose**                           | **Context Size**         | **Incentive Percentage**     | **Supporting Models**               |
|----------------|---------------------------------------|---------------------------|---------------|--------------------------------------|
| `research`     | Warmup tier for new LLM model releases | Up to 10000 characters                  | `100%`  | `mistralai/Mistral-7B-Instruct-v0.2` |
| `inference_0`  | Optimized for **long context** in popular LLMs | Up to 15000 characters       | `0%`         | `mistralai/Mistral-7B-Instruct-v0.2` |
| `inference_1`  | Optimized for **very long context** in popular LLMs | Up to 20000 characters       | `0%`         | `mistralai/Mistral-7B-Instruct-v0.2` |

</div>
        """,
        unsafe_allow_html=True,
    )
colors = ["#636EFA", "#EF553B", "#00CC96"]
# Pie chart for tier distribution in the right column
labels = list(tier_distribution.keys())
values = list(tier_distribution.values())
with col2:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=colors),
            )
        ]
    )
    fig.update_layout(
        title="Tier Distribution",
        title_x=0.5,
        title_font=dict(size=18, family="monospace", color="#333"),
    )
    st.plotly_chart(fig)

# Dropdown for tier selection
tiers = ["research", "inference_0", "inference_1"]
selected_tier = st.selectbox("Select a Tier", tiers)
if selected_tier in labels:
    color = colors[labels.index(selected_tier)]
else:
    color = "#FFA15A"

# Display the selected tier's score distribution as a bar chart
uids = [uid for uid, data in metadata.items() if data["tier"] == selected_tier]
widths = st.columns([1, 3, 1])
if uids:
    with widths[1]:

        scores_tier = [scores[uid] for uid in uids]

        fig = go.Figure(
            data=[
                go.Bar(x=[str(uid) for uid in uids], y=scores_tier, marker_color=color)
            ],
        )
        fig.update_layout(
            title=f"Last epoch scores",
            xaxis_title="UID",
            yaxis_title="Score",
            xaxis=dict(tickmode="array", tickvals=[str(uid) for uid in uids]),
            title_font=dict(size=14, family="monospace", color="#333"),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

else:
    st.write("No scores found for the selected tier.")
