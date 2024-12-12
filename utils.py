import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

def display_invalid_rates(invalid_reasons):
    """
    Display a stacked bar chart showing invalid vs valid rates for each UID.
    """
    # Calculate invalid rates for each UID
    invalid_rates = (
        invalid_reasons.groupby("uid")["invalid_reasons"]
        .apply(lambda x: (x != "").mean())  # Calculate proportion of invalid entries
        .reset_index()
        .rename(columns={"invalid_reasons": "Invalid Rate"})
    )
    
    # Add valid rate column
    invalid_rates["Valid Rate"] = 1 - invalid_rates["Invalid Rate"]

    # Create stacked bar chart
    fig = go.Figure()

    # Add Invalid portion
    fig.add_trace(
        go.Bar(
            name="Invalid",
            x=invalid_rates["uid"],
            y=invalid_rates["Invalid Rate"],
            marker_color="#EF553B",
        )
    )

    # Add Valid portion
    fig.add_trace(
        go.Bar(
            name="Valid",
            x=invalid_rates["uid"],
            y=invalid_rates["Valid Rate"],
            marker_color="#636EFA",
        )
    )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title="Invalid/Valid Rate by UID",
        xaxis_title="UID",
        yaxis_title="Proportion",
        yaxis_tickformat=",.0%",
        showlegend=True,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_matrix_overlap(data):
    """
    Display a heatmap showing the overlap of top 30% miners among validators.

    Args:
        data (dict): Dictionary (JSON) containing 'metadata' key as in API response.
    """
    try:
        lst_metadata = []
        # Process each validator's metadata
        for val in data:
            if val['uid'] == 3:
                continue
            sorted_data = dict(
                sorted(
                    val['metadata'].items(),
                    key=lambda item: item[1]['elo_rating'],
                    reverse=True
                )
            )

            top_30_percent = list(sorted_data.keys())[:int(len(sorted_data) * 0.3)]
            meta = {"report_id": val['uid'], "top_30_percent": top_30_percent}
            lst_metadata.append(meta)

        validator_sets = {meta["report_id"]: set(meta["top_30_percent"]) for meta in lst_metadata}
        report_ids = list(validator_sets.keys())

        n = len(report_ids)
        overlap_matrix = [[0]*n for _ in range(n)]

        # Compute overlap counts between each pair of validators
        for i in range(n):
            for j in range(n):
                overlap = validator_sets[report_ids[i]].intersection(validator_sets[report_ids[j]])
                overlap_matrix[i][j] = len(overlap)

        df = pd.DataFrame(overlap_matrix, index=report_ids, columns=report_ids)

        # Plot the heatmap matrix
        fig, ax = plt.subplots(figsize=(3, 2))
        sns.heatmap(df, annot=True, fmt="d", cmap="YlGnBu", cbar=True, ax=ax,annot_kws={"size": 8})
        ax.set_title("Overlap of top 30% miners among validators",fontsize=6)
        ax.set_xlabel("Validators",fontsize=6)
        ax.set_ylabel("Validators",fontsize=6)

        # Show in dashboard
        ax.tick_params(axis='x', labelsize=6)
        ax.tick_params(axis='y', labelsize=6)
        # st.pyplot(fig, use_container_width=False)
        col1, col2, col3 = st.columns([1,1,1])

        with col2:
            st.pyplot(fig, use_container_width=False)

    except Exception as e:
        st.error(f"Error generating overlap matrix: {str(e)}")