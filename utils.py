import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go


def display_win_loss_matrix(data):
    """
    Display a win/loss matrix visualization for UIDs based on their rating changes.

    Args:
        data (pd.DataFrame): DataFrame containing columns 'uid', 'timestamp', and 'rating_change'
    """
    if len(data) == 0:
        st.info(
            "No data available for win/loss matrix. Please select a time range with data."
        )
        return

    try:
        # Create matrix of wins/losses between UIDs
        unique_uids = data["uid"].unique()
        matrix_df = pd.DataFrame(0, index=unique_uids, columns=unique_uids)

        def parse_rating_change(x):
            if x == "N/A":
                return None
            try:
                before, after = map(float, x.split("->"))
                return 1 if after > before else 0
            except:
                return None

        # Group and process batches
        for _, group in data.groupby("timestamp"):
            is_wins = group["rating_change"].map(parse_rating_change)
            uids = group["uid"].values

            for i in range(len(uids)):
                for j in range(i + 1, len(uids)):
                    uid1, uid2 = uids[i], uids[j]
                    win1, win2 = is_wins.iloc[i], is_wins.iloc[j]

                    if win1 is None and win2 is None:
                        continue
                    elif win1 is None:
                        matrix_df.at[uid1, uid2] -= 1
                        matrix_df.at[uid2, uid1] += 1
                    elif win2 is None:
                        matrix_df.at[uid1, uid2] += 1
                        matrix_df.at[uid2, uid1] -= 1
                    elif win1 > win2:
                        matrix_df.at[uid1, uid2] += 1
                        matrix_df.at[uid2, uid1] -= 1
                    elif win1 < win2:
                        matrix_df.at[uid1, uid2] -= 1
                        matrix_df.at[uid2, uid1] += 1

        # Create heatmap
        fig = px.imshow(
            matrix_df,
            labels=dict(x="Opponent UID", y="UID", color="Win/Loss Count"),
            title="Win/Loss Matrix (Positive = Wins, Negative = Losses)",
            color_continuous_scale=[
                "#FF4B4B",
                "#FFFFFF",
                "#4B7BFF",
            ],  # Changed colors to brighter red and blue
            aspect="auto",
            color_continuous_midpoint=0,
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="Opponent UID",
            yaxis_title="UID",
            title_x=0.0,
            font=dict(size=10),
            margin=dict(t=50, l=50, r=50, b=50),
            xaxis=dict(
                showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)"
            ),
            yaxis=dict(
                showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)"
            ),
        )

        fig.update_traces(
            hovertemplate="UID: %{y}<br>Opponent: %{x}<br>Score: %{z}<extra></extra>"
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error generating win/loss matrix: {str(e)}")


def display_na_rates(data, metric):
    """
    Display a stacked bar chart showing N/A vs non-N/A rates for each UID.

    Args:
        data (pd.DataFrame): DataFrame containing the data
        metric (str): Column name to analyze for N/A rates
    """

    # Calculate N/A rates for each UID
    na_counts = (
        data.groupby("uid")[metric]
        .apply(
            lambda x: (x == "N/A")
            .value_counts(normalize=True)
            .reindex([True, False])
            .fillna(0)
        )
        .unstack()
    )

    # Rename columns for clarity
    na_counts.columns = ["N/A Rate", "Valid Rate"]

    # Create stacked bar chart
    fig = go.Figure()

    # Add N/A portion
    fig.add_trace(
        go.Bar(
            name="N/A",
            x=na_counts.index,
            y=na_counts["N/A Rate"],
            marker_color="#EF553B",
        )
    )

    # Add valid data portion
    fig.add_trace(
        go.Bar(
            name="Valid",
            x=na_counts.index,
            y=na_counts["Valid Rate"],
            marker_color="#636EFA",
        )
    )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title=f"Availability by UID",
        xaxis_title="UID",
        yaxis_title="Proportion",
        yaxis_tickformat=",.0%",
        showlegend=True,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(fig, use_container_width=True)



def compute_pairwise_win_fraction(battles):
    # Times each model wins as Model A
    a_win_ptbl = pd.pivot_table(
        battles[battles['winner'] == "model_a"],
        index="model_a", columns="model_b", aggfunc="size", fill_value=0
    )

    # Table counting times each model wins as Model B
    b_win_ptbl = pd.pivot_table(
        battles[battles['winner'] == "model_b"],
        index="model_a", columns="model_b", aggfunc="size", fill_value=0
    )

    # Table counting number of A-B pairs
    num_battles_ptbl = pd.pivot_table(
        battles,
        index="model_a", columns="model_b", aggfunc="size", fill_value=0
    )

    # Computing the proportion of wins for each model as A and as B
    # against all other models
    row_beats_col_freq = (
        (a_win_ptbl + b_win_ptbl.T) /
        (num_battles_ptbl + num_battles_ptbl.T)
    )

    # Arrange ordering according to proportion of wins
    prop_wins = row_beats_col_freq.mean(axis=1).sort_values(ascending=False)
    model_names = list(prop_wins.keys())
    row_beats_col = row_beats_col_freq.loc[model_names, model_names]
    return row_beats_col

def visualize_pairwise_win_fraction(battles, title):
    row_beats_col = compute_pairwise_win_fraction(battles)
    # Sort by UID number
    ordering = sorted(row_beats_col.index, key=lambda x: int(x.split('_')[1]))
    row_beats_col = row_beats_col.loc[ordering, ordering]
    
    fig = px.imshow(
        row_beats_col,
        color_continuous_scale='RdBu', 
        text_auto=".2f",
        title=title
    )
    fig.update_layout(
        xaxis_title="Model B: Loser",
        yaxis_title="Model A: Winner", 
        xaxis_side="top",
        height=600,
        width=600,
        title_y=0.07,
        title_x=0.5
    )
    fig.update_traces(
        hovertemplate="Model A: %{y}<br>Model B: %{x}<br>Fraction of A Wins: %{z}<extra></extra>"
    )
    return fig



def transform_battles_data(batch_reports):
    battles = []
    for report in batch_reports:
        timestamp = report["timestamp"]
        batch = report["batch_report"]
        task = report["task"]
        
        # Get all UIDs and their rating changes
        for i in range(len(batch["uid"])):
            for j in range(i + 1, len(batch["uid"])):
                uid_a = batch["uid"][str(i)]
                uid_b = batch["uid"][str(j)]
                
                # Extract rating changes
                rating_a = batch["rating_change"][str(i)]
                rating_b = batch["rating_change"][str(j)]
                
                # Parse rating changes to determine winner
                old_rating_a, new_rating_a = map(int, rating_a.split(" -> "))
                old_rating_b, new_rating_b = map(int, rating_b.split(" -> "))
                
                winner = "tie"
                if new_rating_a - old_rating_a > new_rating_b - old_rating_b:
                    winner = "model_a"
                elif new_rating_b - old_rating_b > new_rating_a - old_rating_a:
                    winner = "model_b"
                
                battles.append({
                    "model_a": f"UID_{uid_a}",
                    "model_b": f"UID_{uid_b}",
                    "winner": winner,
                    "task": task,
                    "timestamp": timestamp
                })
    
    return pd.DataFrame(battles)

def visualize_battle_count(battles, title):
    ptbl = pd.pivot_table(battles, index="model_a", columns="model_b", aggfunc="size",
                         fill_value=0)
    battle_counts = ptbl + ptbl.T
    
    # Sort by UID number
    ordering = sorted(battle_counts.index, key=lambda x: int(x.split('_')[1]))
    
    fig = px.imshow(battle_counts.loc[ordering, ordering],
                    title=title, text_auto=True)
    fig.update_layout(
        xaxis_title="Model B", 
        yaxis_title="Model A",
        xaxis_side="top",
        height=600,
        width=600,
        title_y=0.07,
        title_x=0.5
    )
    fig.update_traces(
        hovertemplate="Model A: %{y}<br>Model B: %{x}<br>Count: %{z}<extra></extra>"
    )
    return fig