import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from utils import (display_win_loss_matrix, display_na_rates, visualize_battle_count, visualize_pairwise_win_fraction, transform_battles_data)

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
response = requests.get("https://report.condenses.ai/api/get-metadata")
reports = response.json()
st.session_state.stats = response

# Mapping hotkeys to validator names
hotkey_to_name = {
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator",
    "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v": "RoundTable21",
    "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ": "Rizzo",
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
for report in reports["metadata"]:
    if report["hotkey"] == hotkey:
        break

# Extract metadata and calculate tier distribution
metadata = report["metadata"]

tier_distribution = {}
scores = {}
for uid, data in metadata.items():
    tier = data["tier"]
    scores[uid] = data.get("elo_rating", data.get("score", 0))
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
widths = st.columns([4, 6])
if uids:
    with widths[0]:
        st.markdown("**Metadata Table**")
        metadata_df = pd.DataFrame(metadata).transpose()
        # drop tier not in tiers
        metadata_df = metadata_df[metadata_df["tier"].isin(tiers)]
        # Add multiselect to choose UIDs from metadata table
        selected_uids = st.multiselect("Select UIDs to highlight", metadata_df.index)
        st.dataframe(metadata_df, use_container_width=True)
    with widths[1]:
        # Sort UIDs and their corresponding scores
        sorted_pairs = sorted(
            zip(uids, [scores[uid] for uid in uids]), key=lambda x: x[1], reverse=True
        )
        sorted_uids, scores_tier = zip(*sorted_pairs)
        # Generate the bar chart with highlighted bars
        bar_colors = [
            color if str(uid) not in selected_uids else "#00FFFF" for uid in sorted_uids
        ]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=[str(uid) for uid in sorted_uids],
                    y=scores_tier,
                    marker_color=bar_colors,
                )
            ],
        )
        # Update layout with sorted tick values
        fig.update_layout(
            title="Elo Ranking",
            xaxis_title="uid",
            yaxis_title="elo",
            xaxis=dict(
                tickmode="array",
                # Show only every 5th uid to reduce density
                tickvals=[str(uid) for i, uid in enumerate(sorted_uids) if i % 5 == 0],
                ticktext=[str(uid) for i, uid in enumerate(sorted_uids) if i % 5 == 0],
            ),
            title_font=dict(size=14, family="monospace", color="#333"),
            xaxis_tickangle=-45,
            xaxis_type="category",
        )
        st.plotly_chart(fig)

        # Display table of selected UIDs
        if selected_uids:
            st.markdown("**Selected UIDs Details**")
            selected_data = metadata_df.loc[selected_uids]
            st.dataframe(selected_data, use_container_width=True)
else:
    st.write("No scores found for the selected tier.")

last_minutes = st.slider("Last Minutes", min_value=1, max_value=60 * 6, value=60)


# Sample data extraction
batch_reports = requests.get(
    f"https://report.condenses.ai/api/get-batch-reports/{last_minutes}"
).json()["batch_reports"]



# Data transformation
def transform_data(batch_reports):
    records = []
    battle_logs = {}
    for report in batch_reports:
        timestamp = report["timestamp"]
        batch = report["batch_report"]
        if "perplexity" not in batch:
            continue
        for idx, uid in batch["uid"].items():
            records.append(
                {
                    "timestamp": timestamp,
                    "uid": uid,
                    "perplexity": batch["perplexity"].get(str(idx), "N/A"),
                    "accelerate_metrics": batch["accelerate_metrics"].get(
                        str(idx), "N/A"
                    ),
                    "rating_change": batch["rating_change"].get(str(idx), "N/A"),
                    "invalid_reasons": batch["invalid_reasons"].get(str(idx), ""),
                }
            )
    return pd.DataFrame(records)


data = transform_data(batch_reports)

specific_uids = st.multiselect("Select UIDs to highlight", data["uid"].unique())

if specific_uids:
    data = data[data["uid"].isin(specific_uids)]

# Convert timestamp to human-readable format
data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")
display_na_rates(data, "perplexity")

# Transform the batch reports into battle data
battles_df = transform_battles_data(batch_reports)

win_rates = pd.DataFrame()
for model in battles_df["model_a"].unique():
    model_battles = battles_df[(battles_df["model_a"] == model) | (battles_df["model_b"] == model)]
    total = len(model_battles)
    wins = len(model_battles[
        ((model_battles["model_a"] == model) & (model_battles["winner"] == "model_a")) |
        ((model_battles["model_b"] == model) & (model_battles["winner"] == "model_b"))
    ])
    win_rates.loc[model, "Total Battles"] = total
    win_rates.loc[model, "Wins"] = wins
    win_rates.loc[model, "Win Rate"] = wins / total if total > 0 else 0

win_rates = win_rates.sort_values("Win Rate", ascending=False)
# After creating battles_df, add:
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Battle Count Matrix")
    battle_matrix = visualize_battle_count(battles_df, "Battle Count Between UIDs")
    st.plotly_chart(battle_matrix, key="battle_count_matrix")

with col2:
    st.subheader("Pairwise Win Fraction") 
    win_fraction_matrix = visualize_pairwise_win_fraction(battles_df, "Win Fraction Between UIDs")
    st.plotly_chart(win_fraction_matrix, key="win_fraction_matrix")

with col3:
    st.subheader("Win Rate Analysis")
    st.dataframe(win_rates)

# Line chart for performance metrics
st.subheader("Node Performance Over Time")
metric_choice = st.selectbox(
    "Select Metric to Visualize", ["perplexity", "accelerate_metrics"]
)
filtered_data = data[data[metric_choice] != "N/A"]

fig = px.line(
    filtered_data,
    x="timestamp",
    y=metric_choice,
    color="uid",
    title=f"{metric_choice.capitalize()} Over Time",
    markers=True,
)
st.plotly_chart(fig)

# Invalid reasons analysis
st.subheader("Invalid Reasons")
invalid_data = data[data["invalid_reasons"] != ""]
invalid_summary = invalid_data["invalid_reasons"].value_counts().reset_index()
invalid_summary.columns = ["Reason", "Count"]

fig = px.bar(
    invalid_summary, x="Reason", y="Count", title="Frequency of Invalid Reasons"
)
st.plotly_chart(fig)

# Interactive table
st.subheader("Detailed Data Table")
st.dataframe(data)




