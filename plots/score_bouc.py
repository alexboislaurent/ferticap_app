import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def create_score_bouc(
        data,
        selected_boucs,
        lissage
    data,
    selected_boucs,
    lissage
):

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    # Sécurité : index en datetime
    data = data.copy()
    data.index = pd.to_datetime(data.index)

    for b in selected_boucs:

        if b in data.columns:
    # Sécurité : score numérique
    data = data.apply(
        pd.to_numeric,
        errors="coerce"
    )

            serie = data[b]
    courbes_tracees = 0

    for b in selected_boucs:

            if lissage > 1:
        if b not in data.columns:
            continue

                serie = (
                    serie
                    .rolling(
                        window=lissage,
                        min_periods=1
                    )
                    .mean()
                )
        serie = data[b].dropna()

        if serie.empty:
            continue

            ax.plot(
                serie.index,
                serie.values,
                marker="o",
                label=b
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

    ax.set_title(
        "Score par bouc"
    )

    ax.legend()
    ax.set_ylabel(
        "Score"
    )

    ax.grid(True)
    ax.grid(
        True,
        alpha=0.3
    )

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
