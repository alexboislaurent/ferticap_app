import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def create_score_bouc(
        data,
        selected_boucs,
        lissage
):

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )


    for b in selected_boucs:

        if b in data.columns:

            serie = data[b]


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
                label=b
            )


    ax.set_title(
        "Score par bouc"
    )

    ax.legend()

    ax.grid(True)


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
