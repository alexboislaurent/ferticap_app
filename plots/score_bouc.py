import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def create_score_bouc(
    data,
    selected_boucs,
    lissage
):

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    # =========================
    # PREPARATION DES DONNEES
    # =========================

    data = data.copy()

    # Index en datetime
    data.index = pd.to_datetime(
        data.index
    )

    # Scores numériques
    data = data.apply(
        pd.to_numeric,
        errors="coerce"
    )

    courbes_tracees = 0

    # =========================
    # COURBES
    # =========================

    for b in selected_boucs:

        if b not in data.columns:
            continue

        serie = data[b].dropna()

        if serie.empty:
            continue

        # Lissage
        if lissage > 1:

            serie = (
                serie
                .rolling(
                    window=lissage,
                    min_periods=1
                )
                .mean()
            )

        ax.plot(
            serie.index,
            serie.values,
            marker="o",
            linewidth=2,
            label=str(b)
        )

        courbes_tracees += 1

    # =========================
    # TITRE / AXES
    # =========================

    ax.set_title(
        "Score par bouc"
    )

    ax.set_ylabel(
        "Score"
    )

    ax.grid(
        True,
        alpha=0.3
    )

    # =========================
    # LEGENDE / MESSAGE
    # =========================

    if courbes_tracees > 0:

        ax.legend()

    else:

        ax.text(
            0.5,
            0.5,
            "Aucune donnée disponible pour les boucs sélectionnés",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=14
        )

    # =========================
    # DATES
    # =========================

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m/%y")
    )

    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator()
    )

    fig.autofmt_xdate(
        rotation=45
    )

    fig.tight_layout()

    return fig
