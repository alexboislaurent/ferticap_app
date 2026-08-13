import pandas as pd
import streamlit as st


SEUIL_PERTE_POIDS = 7
SEUIL_VOLUME = 0.5
SEUIL_CONCENTRATION = 3
NB_COLLECTES_PERFORMANCE = 5


def analyser_perte_poids(data_bouc):

    if "Valeure Pesée" not in data_bouc.columns:
        return None

    poids = data_bouc[
        data_bouc["Valeure Pesée"].notna()
    ][
        ["Date", "Valeure Pesée"]
    ].copy()

    if poids.empty:
        return None

    poids["Valeure Pesée"] = pd.to_numeric(
        poids["Valeure Pesée"],
        errors="coerce"
    )

    poids = (
        poids
        .dropna(subset=["Valeure Pesée"])
        .sort_values("Date")
    )

    if poids.empty:
        return None

    dernier = poids.iloc[-1]

    date_limite = (
        dernier["Date"]
        - pd.Timedelta(days=30)
    )

    anciens = poids[
        poids["Date"] <= date_limite
    ]

    if anciens.empty:
        return None

    reference = anciens.iloc[-1]

    poids_reference = float(
        reference["Valeure Pesée"]
    )

    poids_dernier = float(
        dernier["Valeure Pesée"]
    )

    if poids_reference <= 0:
        return None

    perte = (
        (poids_reference - poids_dernier)
        / poids_reference
        * 100
    )

    if perte < SEUIL_PERTE_POIDS:
        return None

    return {
        "perte": perte,
        "poids_reference": poids_reference,
        "poids_dernier": poids_dernier,
        "date_reference": reference["Date"],
        "date_dernier": dernier["Date"],
    }


def analyser_performance(data_bouc):

    colonnes = [
        "Date",
        "Volume semence (ml)",
        "Concentration spz (B/ml)",
    ]

    if not all(
        col in data_bouc.columns
        for col in colonnes
    ):
        return None

    performances = (
        data_bouc[colonnes]
        .sort_values("Date")
        .tail(5)
        .copy()
    )

    # Il faut au moins 5 collectes
    if len(performances) < 5:
        return None

    # Absence de donnée = 0
    performances["Volume semence (ml)"] = pd.to_numeric(
        performances["Volume semence (ml)"],
        errors="coerce"
    ).fillna(0)

    performances["Concentration spz (B/ml)"] = pd.to_numeric(
        performances["Concentration spz (B/ml)"],
        errors="coerce"
    ).fillna(0)

    # Une collecte est insuffisante si :
    # volume < 0,5 ml OU concentration < 3 B/ml
    performances["Insuffisant"] = (
        (performances["Volume semence (ml)"] < SEUIL_VOLUME)
        |
        (performances["Concentration spz (B/ml)"] < SEUIL_CONCENTRATION)
    )

    # ALERTE UNIQUEMENT si les 5 dernières collectes
    # sont toutes insuffisantes
    if not performances["Insuffisant"].all():
        return None

    return {
        "nb_insuffisantes": 5,
        "nb_collectes": 5,
        "dernieres_collectes": performances,
    }


def analyser_bouc(data_bouc):

    perte_poids = analyser_perte_poids(
        data_bouc
    )

    performance = analyser_performance(
        data_bouc
    )

    if perte_poids is None and performance is None:
        return None

    return {
        "poids": perte_poids,
        "performance": performance,
    }


def afficher_boucs_surveillance(
    df,
    boucs_presents_derniere_collecte
):

    st.title("🚨 Boucs à surveiller")

    resultats = []

    for bouc in boucs_presents_derniere_collecte:

        data_bouc = df[
            df["Code animal"] == bouc
        ].copy()

        analyse = analyser_bouc(
            data_bouc
        )

        if analyse is not None:
            resultats.append({
                "Bouc": bouc,
                **analyse,
            })

    # =========================
    # AUCUNE ALERTE
    # =========================

    if not resultats:

        st.success(
            "✅ Aucun bouc à surveiller actuellement."
        )

        return

    # =========================
    # RESUME
    # =========================

    st.error(
        f"🚨 {len(resultats)} bouc(s) à surveiller"
    )

    # =========================
    # TABLEAU COMPACT
    # =========================

    lignes = []

    for resultat in resultats:

        bouc = resultat["Bouc"]
        poids = resultat["poids"]
        performance = resultat["performance"]

        # -------------------------
        # Poids
        # -------------------------

        if poids is not None:

            texte_poids = (
                f"🔴 -{poids['perte']:.1f} % "
                f"({poids['poids_reference']:.1f} → "
                f"{poids['poids_dernier']:.1f} kg)"
            )

        else:

            texte_poids = "✅ Normal"

        # -------------------------
        # Performance
        # -------------------------

        if performance is not None:

            texte_performance = (
                f"🔴 {performance['nb_insuffisantes']}/"
                f"{performance['nb_collectes']} "
                f"collectes faibles"
            )

        else:

            texte_performance = "✅ Normal"

        # -------------------------
        # Motif global
        # -------------------------

        if (
            poids is not None
            and performance is not None
        ):

            motif = "⚠️ Poids + performance"

        elif poids is not None:

            motif = "⚖️ Poids"

        else:

            motif = "📉 Performance"

        lignes.append({
            "🐐 Bouc": bouc,
            "Motif": motif,
            "⚖️ Poids": texte_poids,
            "📉 Performance": texte_performance,
        })

    # =========================
    # AFFICHAGE
    # =========================

    tableau = pd.DataFrame(
        lignes
    )

    st.dataframe(
        tableau,
        use_container_width=True,
        hide_index=True,
        height=420,
    )
