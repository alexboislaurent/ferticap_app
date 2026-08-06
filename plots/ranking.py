import matplotlib.pyplot as plt
import streamlit as st


def show_ranking(
        ranking_last10,
        ranking_year,
        ranking_alltime,
        current_year
):

    st.subheader(
        "🏆 Performance des boucs - 10 dernières collectes"
    )


    col_graph, col_podium = st.columns([2, 1])


    # =========================
    # GRAPHIQUE TOP 10
    # =========================

    with col_graph:

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        ax.barh(
            ranking_last10.index,
            ranking_last10["Score_moyen"]
        )


        for i, (_, row) in enumerate(
            ranking_last10.iterrows()
        ):

            ax.text(
                row["Score_moyen"] + 0.05,
                i,
                f'{row["Taux_reussite"]:.0f}% '
                f'({int(row["Nb_succes"])}/{int(row["Nb_total"])})',
                va="center"
            )


        ax.invert_yaxis()

        ax.set_xlabel(
            "Score moyen"
        )

        ax.set_title(
            "Top 10 - 10 dernières collectes"
        )

        ax.grid(True)


        st.pyplot(fig)

        plt.close(fig)



    # =========================
    # PODIUM + ROI
    # =========================

    with col_podium:

        st.markdown(
            "### 🏆 Podium des champions"
        )


        if len(ranking_last10) >= 3:

            top3 = ranking_last10.head(3)


            podium = [
                (
                    top3.index[1],
                    "🥈",
                    "2ème"
                ),
                (
                    top3.index[0],
                    "🥇",
                    "1er"
                ),
                (
                    top3.index[2],
                    "🥉",
                    "3ème"
                )
            ]


            cols = st.columns(3)


            for col, (bouc, medaille, place) in zip(
                cols,
                podium
            ):

                with col:

                    score = top3.loc[
                        bouc,
                        "Score_moyen"
                    ]

                    taux = top3.loc[
                        bouc,
                        "Taux_reussite"
                    ]


                    st.markdown(
                        f"""
                        <div style="
                        text-align:center;
                        border:1px solid #ddd;
                        border-radius:15px;
                        padding:10px;
                        ">

                        <div style="font-size:40px;">
                        {medaille}
                        </div>

                        <h4>{bouc}</h4>

                        <div style="
                        font-size:22px;
                        font-weight:bold;
                        ">
                        {score:.2f}
                        </div>

                        <div>
                        {taux:.0f}% réussite
                        </div>

                        <div>
                        {place}
                        </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


        else:

            st.info(
                "Pas assez de boucs pour créer un podium."
            )


        # =========================
        # IMAGE ROI DU TROUPEAU
        # =========================

        st.markdown(
            "### 👑 Le roi du troupeau"
        )

        st.image(
            "images/bouc_409.jpg",
            width=220
        )



    # =========================
    # ANNEE EN COURS
    # =========================

    st.subheader(
        f"📅 Performance des boucs - {current_year}"
    )


    create_bar_chart(
        ranking_year,
        f"Année {current_year}"
    )



    # =========================
    # HISTORIQUE COMPLET
    # =========================

    st.subheader(
        "📈 Performance des boucs - Historique complet"
    )


    create_bar_chart(
        ranking_alltime,
        "Historique complet"
    )



def create_bar_chart(
        data,
        title
):

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )


    ax.barh(
        data.index,
        data["Score_moyen"]
    )


    ax.invert_yaxis()

    ax.set_xlabel(
        "Score moyen"
    )

    ax.set_title(
        title
    )

    ax.grid(True)


    st.pyplot(fig)

    plt.close(fig)
