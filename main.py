import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from utils import (
    display_win_loss_matrix,
    display_invalid_rates,
    visualize_battle_count,
    visualize_pairwise_win_fraction,
    transform_battles_data,
    show_matrix_overlap,
)


# Constants
PAGE_TITLE = "Leaderboard - Neural Condense Subnet"
API_BASE_URL = "https://report.condenses.ai/api"
HOTKEY_TO_NAME = {
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator",
    "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3": "OpenTensor Foundation", 
    "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2": "YUMA",
    "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v": "RoundTable21",
    "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ": "Rizzo", 
    "5Eq8b9p6zJMjEXyH9sX4DRMYspnUyorEKq3Zmha1WN6AC4sf": "Cruicible Labs",
}
TIERS = ["research", "inference_0", "inference_1"]
TIER_COLORS = ["#636EFA", "#EF553B", "#00CC96"]

def setup_page():
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.markdown(
        """
        <div align="center">
            <h1 class="header">Neural Condense Subnet</h1>
        </div>
        <div class="divider"></div>
        """,
        unsafe_allow_html=True,
    )

def fetch_latest_reports():
    response = requests.get(f"{API_BASE_URL}/get-metadata")
    data = response.json()
    all_metadata = data.get("metadata", [])
    
    latest_reports = []
    for doc in all_metadata:
        if doc.get("reports"):
            latest_reports.append({
                "uid": doc.get("uid"),
                "_id": doc.get("_id"),
                "hotkey": doc.get("hotkey"),
                "metadata": doc.get("reports")[0].get("metadata"),
                "timestamp": doc.get("reports")[0].get("timestamp")
            })
    return latest_reports

def get_tier_distribution(metadata):
    tier_distribution = {}
    scores = {}
    for uid, data in metadata.items():
        tier = data["tier"]
        scores[uid] = data.get("elo_rating", data.get("score", 0))
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
    return tier_distribution, scores

def display_validator_info(selected_name):
    st.markdown(
        f"""
        <div align="center">
        **Viewing report from {selected_name}**
        
        | Component | Link |
        |-----------|------|
        | 🌐 **Condense-AI & API Document** | [Visit Condense-AI](https://condenses.ai) |
        | 📚 **API Library** | [Explore API Library](https://github.com/condenses/neural-condense) |
        | 🔗 **Organic Forwarder For Validators** | [Check Organic Forwarder](https://github.com/condenses/subnet-organic) |
        | 📦 **Neural Condense Subnet** | [Source Code](https://github.com/condenses/neural-condense-subnet) |

        | **Tier** | **Purpose** | **Context Size** | **Incentive Percentage** | **Supporting Models** |
        |-----------|-------------|------------------|-------------------------|---------------------|
        | `research` | Warmup tier for new LLM model releases | Up to 10000 characters | `100%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        | `inference_0` | Optimized for **long context** in popular LLMs | Up to 15000 characters | `0%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        | `inference_1` | Optimized for **very long context** in popular LLMs | Up to 20000 characters | `0%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        </div>
        """,
        unsafe_allow_html=True,
    )

def plot_tier_distribution(tier_distribution):
    labels = list(tier_distribution.keys())
    values = list(tier_distribution.values())
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=TIER_COLORS),
        )
    ])
    fig.update_layout(
        title="Tier Distribution",
        title_x=0.5,
        title_font=dict(size=18, family="monospace", color="#333"),
    )
    return fig

def plot_scores(uids, scores, selected_uids, color):
    sorted_pairs = sorted(
        zip(uids, [scores[uid] for uid in uids]), 
        key=lambda x: x[1], 
        reverse=True
    )
    sorted_uids, scores_tier = zip(*sorted_pairs)
    
    bar_colors = [
        color if str(uid) not in selected_uids else "#00FFFF" 
        for uid in sorted_uids
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=[str(uid) for uid in sorted_uids],
            y=scores_tier,
            marker_color=bar_colors,
        )
    ])
    
    fig.update_layout(
        title="Score",
        xaxis_title="uid",
        yaxis_title="accuracy",
        xaxis=dict(
            tickmode="array",
            tickvals=[str(uid) for i, uid in enumerate(sorted_uids) if i % 5 == 0],
            ticktext=[str(uid) for i, uid in enumerate(sorted_uids) if i % 5 == 0],
        ),
        title_font=dict(size=14, family="monospace", color="#333"),
        xaxis_tickangle=-45,
        xaxis_type="category",
    )
    return fig

def transform_batch_data(batch_reports):
    records = []
    for report in batch_reports:
        try:
            timestamp = report["timestamp"]
            hotkey = report["_id"].split("-")[0]
            validator_name = HOTKEY_TO_NAME.get(hotkey, "Unknown")
            batch = report["batch_report"]
            for idx, uid in batch["uid"].items():
                records.append({
                    "timestamp": timestamp,
                    "validator_name": validator_name,
                    "uid": uid,
                    "accuracy": batch["accuracy"][str(idx)],
                    "score_change": batch["score_change"].get(str(idx), "N/A"),
                    "invalid_reasons": batch["invalid_reasons"].get(str(idx), ""),
                })
        except Exception as e:
            print(f"Error processing batch report: {e}")
    return pd.DataFrame(records)

def main():
    setup_page()
    
    reports = fetch_latest_reports()
    st.session_state.stats = reports
    
    name_to_hotkey = {v: k for k, v in HOTKEY_TO_NAME.items()}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_name = st.selectbox(
            "Select a validator", 
            list(HOTKEY_TO_NAME.values()), 
            index=0
        )
        hotkey = name_to_hotkey[selected_name]
        st.toast(f"Selected {selected_name}", icon="🔍")
        
    report = next(r for r in reports if r["hotkey"] == hotkey)
    metadata = report["metadata"]
    
    tier_distribution, scores = get_tier_distribution(metadata)
    
    with col1:
        display_validator_info(selected_name)
        
    with col2:
        st.plotly_chart(plot_tier_distribution(tier_distribution))
    
    selected_tier = st.selectbox("Select a Tier", TIERS)
    color = TIER_COLORS[TIERS.index(selected_tier)] if selected_tier in TIERS else "#FFA15A"
    
    uids = [uid for uid, data in metadata.items() if data["tier"] == selected_tier]
    
    if uids:
        widths = st.columns([4, 6])
        with widths[0]:
            st.markdown("**Metadata Table**")
            metadata_df = pd.DataFrame(metadata).transpose()
            metadata_df = metadata_df[metadata_df["tier"].isin(TIERS)]
            selected_uids = st.multiselect("Select UIDs to highlight", metadata_df.index)
            st.dataframe(metadata_df, use_container_width=True)
            
        with widths[1]:
            st.plotly_chart(plot_scores(uids, scores, selected_uids, color))
            
            if selected_uids:
                st.markdown("**Selected UIDs Details**")
                selected_data = metadata_df.loc[selected_uids]
                st.dataframe(selected_data, use_container_width=True)
    else:
        st.write("No scores found for the selected tier.")
        
    last_minutes = st.slider("Last Minutes", min_value=1, max_value=60 * 6, value=60)
    
    batch_reports = requests.get(
        f"{API_BASE_URL}/get-batch-reports/{last_minutes}"
    ).json()["batch_reports"]
    
    data = transform_batch_data(batch_reports)
    show_matrix_overlap(reports)
    display_invalid_rates(data)
    # Format timestamp to be human readable
    data["timestamp"] = pd.to_datetime(data["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    st.subheader("Full Batches Data")
    st.dataframe(data)

if __name__ == "__main__":
    main()
