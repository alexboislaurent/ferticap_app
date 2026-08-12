
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

def create_heatmap(data):

    fig, ax = plt.subplots(
        figsize=(16, 6)
    )

    sns.heatmap(
        data,
        cmap="RdYlGn",
        cbar=False,
        ax=ax,
        linewidths=0.5,
        linecolor="black"
    )

    ax.set_yticklabels(
        ax.get_yticklabels(),
        rotation=0
    )

    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=45,
        ha="right"
    )

    # Légende
    legend_elements = [
        Patch(facecolor="green", edgecolor="black", label="À sauté"),
        Patch(facecolor="red", edgecolor="black", label="Refus"),
        Patch(facecolor="white", edgecolor="black", label="Absent")
    ]

    ax.legend(
        handles=legend_elements,
        title="Légende",
        loc="upper left",
        bbox_to_anchor=(1.02, 1)
    )

    return fig
