import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from utils import (
    display_invalid_rates,
    show_matrix_overlap,
)
from datetime import datetime

# Constants
PAGE_TITLE = "Leaderboard - Neural Condense Subnet"
API_BASE_URL = "https://report.condenses.ai/api"
HOTKEY_TO_NAME = {
    "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1": "Taostats Validator",
    "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3": "OpenTensor Foundation", 
    "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2": "YUMA",
    "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v": "RoundTable21",
    "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ": "Rizzo", 
}
TIERS = ["universal"]
TIER_COLORS = ["#636EFA", "#EF553B", "#00CC96","#AB63FA"]


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


@st.cache_resource(ttl=60 * 10)
def fetch_latest_reports():
    response = requests.get(f"{API_BASE_URL}/get-metadata")
    data = response.json()
    all_metadata = data.get("metadata", [])

    latest_reports = []
    for doc in all_metadata:
        if doc.get("reports"):
            latest_reports.append(
                {
                    "uid": doc.get("uid"),
                    "_id": doc.get("_id"),
                    "hotkey": doc.get("hotkey"),
                    "metadata": doc.get("reports")[0].get("metadata"),
                    "timestamp": doc.get("reports")[0].get("timestamp"),
                }
            )
    return latest_reports


def get_tier_distribution(metadata):
    tier_distribution = {}
    scores = {}
    for uid, data in metadata.items():
        tier = data["tier"]
        scores[uid] = data.get("elo_rating", data.get("score", 0))
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
    return tier_distribution, scores


def display_project_info():
    st.markdown(
        f"""
        <div align="center">
        
        | Component | Link |
        |-----------|------|
        | 🌐 **Condense-AI & API Document** | [Visit Condense-AI](https://condenses.ai) |
        | 📚 **API Library** | [Explore API Library](https://github.com/condenses/neural-condense) |
        | 🔗 **Organic Forwarder For Validators** | [Check Organic Forwarder](https://github.com/condenses/subnet-organic) |
        | 📦 **Neural Condense Subnet** | [Source Code](https://github.com/condenses/neural-condense-subnet) |

        | **Tier** | **Purpose** | **Context Size** | **Incentive Percentage** | **Supporting Models** |
        |-----------|-------------|------------------|-------------------------|---------------------|
        | `research` | Warmup tier for new LLM model releases | Up to 15000 characters | `60%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        | `universal` | Compress text representation for various models | Up to 15000 characters | `40%` | `meta-llama/Llama-3.1-8B-Instruct` |
        | `inference_0` | Optimized for **long context** in popular LLMs | Up to 15000 characters | `0%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        | `inference_1` | Optimized for **very long context** in popular LLMs | Up to 20000 characters | `0%` | `mistralai/Mistral-7B-Instruct-v0.2` |
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(ttl=60 * 10)
def fetch_coldkey_uid_map():
    """Fetch UIDs for the selected coldkey using the API."""
    response = requests.get(f"{API_BASE_URL}/get_coldkey_report/")
    if response.status_code == 200:
        return response.json().get("coldkey_uid_map", [])
    else:
        return []


def plot_tier_distribution(tier_distribution):
    labels = list(tier_distribution.keys())
    values = list(tier_distribution.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=TIER_COLORS),
            )
        ]
    )
    fig.update_layout(
        title="Tier Distribution",
        title_x=0.5,
        title_font=dict(size=18, family="monospace", color="#333"),
    )
    return fig


def plot_scores(uids, scores, selected_uids, uids_coldkey, color):
    sorted_pairs = sorted(
        zip(uids, [scores[uid] for uid in uids]), key=lambda x: x[1], reverse=True
    )
    sorted_uids, scores_tier = zip(*sorted_pairs)

    bar_colors = [
        "#00FFFF" if str(uid) in selected_uids or str(uid) in uids_coldkey else color
        for uid in sorted_uids
    ]
    fig = go.Figure(
        data=[
            go.Bar(
                x=[str(uid) for uid in sorted_uids],
                y=scores_tier,
                marker_color=bar_colors,
            )
        ]
    )

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
            timestamp = datetime.fromtimestamp(report["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            hotkey = report["_id"].split("-")[0]
            validator_name = HOTKEY_TO_NAME.get(hotkey, "Unknown")
            batch = report["batch_report"]
            for idx, uid in batch["uid"].items():
                records.append(
                    {
                        "timestamp": timestamp,
                        "validator_name": validator_name,
                        "uid": uid,
                        "accuracy": batch["accuracy"][str(idx)],
                        "score_change": batch["score_change"].get(str(idx), "N/A"),
                        "invalid_reasons": batch["invalid_reasons"].get(str(idx), ""),
                    }
                )
        except Exception as e:
            print(f"Error processing batch report: {e}")
    return pd.DataFrame(records)

def format_time_diff(timestamp):
    if pd.isna(timestamp):
        return None
    
    now = pd.Timestamp.now()
    diff = now - pd.Timestamp(timestamp)
    
    # Convert timedelta to human readable format
    minutes = int(diff.total_seconds() / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)
    
    if days > 0:
        elapsed = f"{days} days ago"
    elif hours > 0:
        elapsed = f"{hours} hours ago"
    else:
        elapsed = f"{minutes} minutes ago"
        
    return f"{timestamp} ({elapsed})"

@st.cache_resource(ttl=60 * 10)
def fetch_batch_data(last_minutes):
    # Fetch batch reports from the API
    batch_reports = requests.get(
        f"{API_BASE_URL}/get-batch-reports/{last_minutes}"
    ).json()["batch_reports"]

    # Transform batch reports into a DataFrame
    data = transform_batch_data(batch_reports)
    return data

@st.cache_resource(ttl=60 * 10)
def get_lastest_time(val_name, metadata, last_minutes):
    data = fetch_batch_data(last_minutes)
    # Mmap UID to Tier
    uid_to_tier = {}
    for uid, meta_data in metadata.items():
        tier = meta_data["tier"]
        uid_to_tier[str(uid)] = tier

    # Map tier for each UID in the batch report
    data["tier"] = (data["uid"].astype(str)).map(uid_to_tier).fillna("Unknown")
    data = data[data["tier"].isin(TIERS)]
    data = data[data["validator_name"] == val_name]

    # Format the timestamp for better readability
    data["timestamp"] = pd.to_datetime(data["timestamp"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Assuming your dataframe is called 'df' with columns: timestamp, validator_name, tier

    data = (data.groupby(['validator_name', 'tier'])['timestamp']
                .max()
                .unstack(fill_value=None)
                .rename(columns={
                    'universal': 'universal_last_timestamp',
                })
                .reset_index())
    
    data['universal_last_timestamp'] = data['universal_last_timestamp'].apply(format_time_diff) if 'universal_last_timestamp' in data.columns else None
    # If any validator is missing either tier, the columns will contain NaN values
    return data

def get_metadata_df(metadata, selected_tier, coldkey_uid_map):
    metadata_df = pd.DataFrame(metadata).transpose()
    metadata_df = metadata_df[metadata_df["tier"] == selected_tier]
    metadata_df.reset_index(level=0, inplace=True)
    metadata_df.rename(columns={"index": "UID"}, inplace=True)
    coldkey_map_df = pd.DataFrame(
        list(coldkey_uid_map.items()), columns=["UID", "Coldkey"]
    )
    # join 2 df
    metadata_df = metadata_df.merge(coldkey_map_df, on="UID", how="left")
    return metadata_df

def extract_data(reports, hotkeys, hotkey_to_name, last_minutes, batch_data):
    df = None
    for hotkey in hotkeys:
        report = next(r for r in reports if r["hotkey"] == hotkey)
        metadata = report["metadata"]
        data = get_lastest_time(hotkey_to_name[hotkey], metadata, last_minutes)
        tier_distribution, scores = get_tier_distribution(metadata)
        
        # get 0 % of accuracy
        agg_data = (batch_data.groupby('validator_name')
              .agg({'accuracy': lambda x: (x == 0.0).mean() * 100})  # Calculate percentage of scores < 5
              .rename(columns={'accuracy': '0 accuracy_%'})
              .reset_index())  # Reset index to make validator_name a column again
        data = data.merge(agg_data, on='validator_name', how='left')

        if df is None:
            df = data
        else:
            df = pd.concat([df, data], axis=0)
    return df

def main():
    setup_page()

    reports = fetch_latest_reports()
    st.session_state.stats = reports
    name_to_hotkey = {v: k for k, v in HOTKEY_TO_NAME.items()}
    last_minutes = st.slider(
            "Last Minutes", min_value=1, max_value=60 * 6, value=120
    )
    batch_data = fetch_batch_data(last_minutes)

    st.header("Information Summary")
    display_project_info()
    coldkey_uid_map = fetch_coldkey_uid_map()
    hotkey_to_name = {k: v for k, v in HOTKEY_TO_NAME.items()}

    hotkeys = list(HOTKEY_TO_NAME.keys())
    df  = extract_data(reports, hotkeys, hotkey_to_name, last_minutes, batch_data)
    
    st.subheader("Validators Information")
    st.write("If the last time steps received is >= 2hours, the validator backend is down")
    st.dataframe(df, use_container_width=True)

    selected_name = st.selectbox(
        "Select a validator", list(HOTKEY_TO_NAME.values()), index=0
    )
    hotkey = name_to_hotkey[selected_name]
    st.toast(f"Selected {selected_name}", icon="🔍")

    try:
        report = next(r for r in reports if r["hotkey"] == hotkey)
    except StopIteration:
        report = None

    if report:
        metadata = report["metadata"]
        update_timestamp: float = report["timestamp"]
        update_timestamp = datetime.fromtimestamp(update_timestamp)
        tier_distribution, scores = get_tier_distribution(metadata)

        selected_tier = st.selectbox("Select a Tier", TIERS)
        color = (
            TIER_COLORS[TIERS.index(selected_tier)]
            if selected_tier in TIERS
            else "#FFA15A"
        )

        uids = [uid for uid, data in metadata.items() if data["tier"] == selected_tier]
        if uids:
            widths = st.columns([4, 6])
            with widths[0]:
                st.markdown("**Metadata Table**")
                metadata_df = pd.DataFrame(metadata).transpose()
                metadata_df = metadata_df[metadata_df["tier"].isin(TIERS)]
                selected_uids = st.multiselect(
                    "Select UIDs to highlight", metadata_df.index
                )
                st.dataframe(metadata_df, use_container_width=True)
                # Checkbox to display coldkey-UID map
                if st.checkbox("Show Coldkey-UID Map"):
                    st.subheader("Coldkey-UID Map")
                    coldkey_map_df = pd.DataFrame(
                        list(coldkey_uid_map.items()), columns=["UID", "Coldkey"]
                    )
                    st.dataframe(coldkey_map_df, use_container_width=True)

                # Selectbox for coldkey selection
                selected_coldkeys = st.multiselect(
                    "Select Coldkey(s) to Highlight",
                    list(set(coldkey_uid_map.values())),
                    default=None,
                )

                if selected_coldkeys:
                    # Gather all UIDs for the selected coldkeys
                    uids_coldkey = [
                        str(uid)
                        for uid, ck in coldkey_uid_map.items()
                        if ck in selected_coldkeys
                    ]
                else:
                    uids_coldkey = []

            with widths[1]:
                st.plotly_chart(
                    plot_scores(uids, scores, selected_uids, uids_coldkey, color)
                )

                if selected_uids or uids_coldkey:
                    st.markdown("**Selected UIDs Details**")

                    highlighted_uids = list(set(selected_uids) | set(uids_coldkey))

                    selected_data = metadata_df.loc[
                        metadata_df.index.intersection(highlighted_uids)
                    ]

                    # Display the filtered data
                    if not selected_data.empty:
                        st.dataframe(selected_data, use_container_width=True)
                    else:
                        st.write("No details available for the selected UIDs.")
                else:
                    st.write("No scores found for the selected tier.")

        @st.cache_resource(ttl=60 * 10)
        def get_pyg_batch_data(data, metadata):
            # Mmap UID to Tier
            uid_to_tier = {}
            for uid, meta_data in metadata.items():
                tier = meta_data["tier"]
                uid_to_tier[str(uid)] = tier

            # Map tier for each UID in the batch report
            data["tier"] = (data["uid"].astype(str)).map(uid_to_tier).fillna("Unknown")

            # Map UID to Coldkey
            uid_to_coldkey = {str(uid): coldkey for uid, coldkey in coldkey_uid_map.items()}
            data["coldkey"] = data["uid"].astype(str).map(uid_to_coldkey).fillna("Unknown")

            # Format the timestamp for better readability
            data["timestamp"] = pd.to_datetime(data["timestamp"]).dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Integrate pygwalker for data exploration
            from pygwalker.api.streamlit import StreamlitRenderer
            pyg_app = StreamlitRenderer(data)

            return pyg_app

        pyg_app = get_pyg_batch_data(batch_data, metadata)
        pyg_app.explorer()

if __name__ == "__main__":
    main()
