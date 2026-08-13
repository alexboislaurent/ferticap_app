import streamlit as st


def preparer_boucs(df, df_filtered):
    """
    Prépare la liste des boucs et identifie ceux
    présents à la dernière date de la période sélectionnée.
    """

    boucs = sorted(
        df["Code animal"].dropna().unique()
    )

    last_date = df_filtered["Date"].max()

    boucs_derniere_collecte = (
        df_filtered[
            df_filtered["Date"] == last_date
        ]["Code animal"]
        .dropna()
        .unique()
        .tolist()
    )

    # Sécurité si aucune collecte dans la période
    if not boucs_derniere_collecte:
        boucs_derniere_collecte = boucs.copy()

    # Boucs de la dernière collecte en premier
    boucs = (
        sorted(boucs_derniere_collecte)
        + sorted(
            b for b in boucs
            if b not in boucs_derniere_collecte
        )
    )

    return boucs, boucs_derniere_collecte


def get_bouc_tv(
    mode_tv,
    compteur_tv,
    modes_tv,
    boucs_derniere_collecte,
):
    """
    Détermine quel bouc afficher sur la page Bouc TV.
    """

    if not mode_tv or not boucs_derniere_collecte:
        return None

    nb_passages_bouc = sum(
        1
        for i in range(compteur_tv + 1)
        if modes_tv[i % len(modes_tv)] == "Bouc TV"
    ) - 1

    return boucs_derniere_collecte[
        nb_passages_bouc % len(boucs_derniere_collecte)
    ]


def afficher_selection_boucs(
    boucs,
    boucs_derniere_collecte,
):
    """
    Affiche la sélection des boucs dans la sidebar
    et retourne la liste des boucs sélectionnés.
    """

    st.sidebar.markdown("### 🐐 Sélection des boucs")

    # Sélection automatique des boucs actuels
    if st.sidebar.button(
        "🟢 Sélectionner les boucs actuels"
    ):
        for bouc in boucs:
            st.session_state[
                f"bouc_{bouc}"
            ] = bouc in boucs_derniere_collecte

    # Tout sélectionner
    if st.sidebar.button("☑ Tout sélectionner"):
        for bouc in boucs:
            st.session_state[
                f"bouc_{bouc}"
            ] = True

    # Tout désélectionner
    if st.sidebar.button("☐ Tout désélectionner"):
        for bouc in boucs:
            st.session_state[
                f"bouc_{bouc}"
            ] = False

    selected_boucs = []

    for bouc in boucs:

        # Valeur par défaut
        if f"bouc_{bouc}" not in st.session_state:
            st.session_state[
                f"bouc_{bouc}"
            ] = bouc in boucs_derniere_collecte

        label = (
            f"🟢 {bouc}"
            if bouc in boucs_derniere_collecte
            else f"⚪ {bouc}"
        )

        if st.sidebar.checkbox(
            label,
            key=f"bouc_{bouc}",
        ):
            selected_boucs.append(bouc)

    return selected_boucs
