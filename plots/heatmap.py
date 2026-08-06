
import matplotlib.pyplot as plt
import seaborn as sns


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

    return fig
