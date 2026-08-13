import pandas as pd
import streamlit as st


def afficher_rations(worksheet):

    # =========================
    # LECTURE GOOGLE SHEETS
    # =========================

    all_values = worksheet.get_all_values()

    if len(all_values) < 2:
        st.warning(
            "Aucune donnée disponible dans l'onglet Rations."
        )
        return

    # Première ligne = en-têtes
    headers = all_values[0]
    rows = all_values[1:]

    df = pd.DataFrame(
        rows,
        columns=headers
    )

    # =========================
    # NETTOYAGE
    # =========================

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df["Date (à partir de)"] = pd.to_datetime(
        df["Date (à partir de)"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(
        subset=["Date (à partir de)"]
    )

    if df.empty:
        st.warning(
            "Aucune date de ration valide."
        )
        return

    # =========================
    # DATE ACTUELLE
    # =========================

    aujourd_hui = pd.Timestamp.today().normalize()

    # On garde uniquement les rations déjà en vigueur
    df = df[
        df["Date (à partir de)"] <= aujourd_hui
    ].copy()

    if df.empty:
        st.warning(
            "Aucune ration en vigueur."
        )
        return

    # Date de début de la ration actuelle
    date_ration = df["Date (à partir de)"].max()

    rations = df[
        df["Date (à partir de)"] == date_ration
    ].copy()

    # =========================
    # TITRE
    # =========================

    st.title("🥣 Rations")

    st.caption(
        f"Ration en vigueur depuis le "
        f"{date_ration:%d/%m/%Y}"
    )

    # =========================
    # UNE CARTE PAR SEXE
    # =========================

    sexes = ["♂", "♀"]

    col1, col2 = st.columns(2)

    colonnes = {
        "Concentrée (g)": "Concentrée (g)",
        "Equivalent gobelet": "Equivalent gobelet",
        "Reférence": "Reférence",
        "Foin": "Foin",
    }

    for col, sexe in zip(
        [col1, col2],
        sexes
    ):

        ration = rations[
            rations["Sexe"].astype(str).str.strip()
            == sexe
        ]

        with col:

            if ration.empty:

                st.warning(
                    f"Aucune ration définie pour {sexe}"
                )

                continue

            ration = ration.iloc[-1]

            st.subheader(
                f"{sexe} "
                + (
                    "Boucs"
                    if sexe == "♂"
                    else "Chèvres"
                )
            )

            concentree = ration[
                "Concentrée (g)"
            ]

            gobelet = ration[
                "Equivalent gobelet"
            ]

            reference = ration[
                "Reférence"
            ]

            foin = ration[
                "Foin"
            ]

            st.metric(
                "🥣 Concentrée",
                f"{concentree} g"
            )

            st.metric(
                "🥛 Équivalent gobelet",
                str(gobelet)
            )

            st.write(
                f"**Référence :** {reference}"
            )

            st.write(
                f"**🌾 Foin :** {foin}"
            )
