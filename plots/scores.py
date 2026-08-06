import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def create_score_global(score, lissage):

    if lissage > 1:
        score = (
            score
            .rolling(
                window=lissage,
                min_periods=1
            )
            .mean()
        )


    fig, ax = plt.subplots(
        figsize=(12,5)
    )


    ax.plot(
        score.index,
        score.values,
        marker="o"
    )


    ax.grid(True)

    ax.set_title(
        "Score moyen global"
    )

    ax.set_ylabel(
        "Score"
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


    return fig
