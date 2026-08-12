import calendar as cal
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


COLOR_MAP = {
    "FCO": "blue",
    "LNCR": "red",
    "CS": "green",
    "Pesée": "pink",
    "TUB": "yellow",
}


def get_color_list(suivis):

    colors = []

    for suivi in suivis:

        suivi = str(suivi).strip()

        colors.append(
            COLOR_MAP.get(suivi, "gray")
        )

    # Suppression des doublons
    colors = list(dict.fromkeys(colors))

    return colors or ["white"]


def prepare_calendar_data(df):

    suivi_cols = [
        "Suivi 1",
        "Suivi 2",
        "Suivi 3",
        "Suivi 4"
    ]

    existing_cols = [
        c for c in suivi_cols
        if c in df.columns
    ]

    if not existing_cols:
        return {}

    data = df.melt(
        id_vars=["Date"],
        value_vars=existing_cols,
        value_name="Suivi"
    )

    data["Suivi"] = (
        data["Suivi"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["Suivi"].notna()
        & (data["Suivi"] != "")
    ]

    daily = (
        data
        .groupby("Date")["Suivi"]
        .apply(list)
    )

    return {
        date.date(): get_color_list(suivis)
        for date, suivis in daily.items()
    }


def afficher_calendrier(df):

    st.subheader(
        "📅 Calendrier annuel des suivis"
    )

    color_map = prepare_calendar_data(df)

    # =========================
    # LEGENDE
    # =========================

    st.markdown("### Légende")

    cols = st.columns(len(COLOR_MAP))

    for col, (label, color) in zip(
        cols,
        COLOR_MAP.items()
    ):

        with col:

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:8px;
                    margin-bottom:10px;
                ">
                    <span style="
                        display:inline-block;
                        width:18px;
                        height:18px;
                        background-color:{color};
                        border:1px solid black;
                    "></span>
                    <span>{label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # =========================
    # ANNEES
    # =========================

    base_year = df["Date"].dt.year.max()

    years = [
        base_year - i
        for i in range(11)
    ]

    highlight_months = {
        1, 4, 5, 8, 9, 12
    }

    # =========================
    # CALENDRIERS
    # =========================

    for year in years:

        st.markdown(
            f"### 📅 Année {year}"
        )

        fig, axes = plt.subplots(
            3,
            4,
            figsize=(18, 10)
        )

        axes = axes.flatten()

        for month in range(1, 13):

            ax = axes[month - 1]

            ax.set_title(
                cal.month_name[month]
            )

            ax.axis("off")

            month_matrix = cal.monthcalendar(
                year,
                month
            )

            for i, week in enumerate(
                month_matrix
            ):

                for j, day in enumerate(week):

                    if day == 0:
                        continue

                    date = pd.Timestamp(
                        year,
                        month,
                        day
                    ).date()

                    colors = color_map.get(
                        date,
                        ["white"]
                    )

                    # Une couleur
                    if len(colors) == 1:

                        ax.add_patch(
                            plt.Rectangle(
                                (j, -i),
                                1,
                                1,
                                facecolor=colors[0],
                                edgecolor="black",
                                lw=0.4
                            )
                        )

                    # Plusieurs suivis
                    else:

                        ax.add_patch(
                            plt.Rectangle(
                                (j, -i),
                                1,
                                1,
                                facecolor="white",
                                edgecolor="black",
                                lw=0.4
                            )
                        )

                        colors = colors[:4]
                        step = 1 / len(colors)

                        for k, color in enumerate(colors):

                            ax.add_patch(
                                plt.Rectangle(
                                    (
                                        j + k * step,
                                        -i
                                    ),
                                    step,
                                    1,
                                    facecolor=color,
                                    edgecolor="none"
                                )
                            )

            ax.set_xlim(0, 7)
            ax.set_ylim(-6, 1)

            if month in highlight_months:

                ax.add_patch(
                    plt.Rectangle(
                        (0, -6),
                        7,
                        7,
                        fill=False,
                        edgecolor="yellow",
                        linewidth=3
                    )
                )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)
