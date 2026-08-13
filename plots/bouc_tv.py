import os
import pandas as pd
import streamlit as st


# =====================================================
# ALERTES
# =====================================================

def calculer_alerte_poids(data_historique):

    if "Valeure Pesée" not in data_historique.columns:
        return None

    poids = (
        data_historique[
            data_historique["Valeure Pesée"].notna()
        ][
            ["Date", "Valeure Pesée"]
        ]
        .sort_values("Date")
        .copy()
    )

    if poids.empty:
        return None

    dernier = poids.iloc[-1]

    date_limite = (
        dernier["Date"] - pd.Timedelta(days=30)
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

    perte_pourcentage = (
        (poids_reference - poids_dernier)
        / poids_reference
        * 100
    )

    if perte_pourcentage >= 5:

        return {
            "perte": perte_pourcentage,
            "poids_reference": poids_reference,
            "poids_dernier": poids_dernier,
            "date_reference": reference["Date"],
            "date_dernier": dernier["Date"],
        }

    return None


def calculer_alerte_performance(data_historique):

    colonnes = [
        "Date",
        "Volume semence (ml)",
        "Concentration spz (B/ml)",
    ]

    if not all(
        col in data_historique.columns
        for col in colonnes
    ):
        return None

    performances = (
        data_historique[
            colonnes
        ]
        .sort_values("Date")
        .tail(5)
        .copy()
    )

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

    performances["Performance insuffisante"] = (
        (performances["Volume semence (ml)"] < 0.5)
        |
        (performances["Concentration spz (B/ml)"] < 3)
    )

    if performances["Performance insuffisante"].all():

        return {
            "collectes": performances
        }

    return None


def afficher_alertes(data_historique):

    alerte_poids = calculer_alerte_poids(
        data_historique
    )

    alerte_performance = calculer_alerte_performance(
        data_historique
    )

    if (
        alerte_poids is None
        and alerte_performance is None
    ):
        return

    st.error("🚨 ALERTES SUR LE BOUC")

    if alerte_poids is not None:

        st.warning(
            f"⚖️ **Perte de poids de "
            f"{alerte_poids['perte']:.1f} %** "
            f"entre le "
            f"{alerte_poids['date_reference']:%d/%m/%Y} "
            f"({alerte_poids['poids_reference']:.1f} kg) "
            f"et le "
            f"{alerte_poids['date_dernier']:%d/%m/%Y} "
            f"({alerte_poids['poids_dernier']:.1f} kg)."
        )

    if alerte_performance is not None:

        st.warning(
            "📉 **Baisse de performance détectée :** "
            "volume < 0,5 ml ou concentration < 3 B/ml "
            "sur les 5 dernières collectes."
        )


# =====================================================
# FICHE BOUC TV
# =====================================================
def calculer_tendances(data_historique):

    colonnes = [
        "Date",
        "Volume semence (ml)",
        "Concentration spz (B/ml)",
        "% Mobiles",
        "Motiles",
    ]

    colonnes_existantes = [
        col
        for col in colonnes
        if col in data_historique.columns
    ]

    if "Date" not in colonnes_existantes:
        return {}

    data = (
        data_historique[colonnes_existantes]
        .sort_values("Date")
        .copy()
    )

    data = data.tail(10)

    if len(data) < 10:
        return {}

    resultats = {}

    variables = [
        "Volume semence (ml)",
        "Concentration spz (B/ml)",
        "% Mobiles",
        "Motiles",
    ]

    for variable in variables:

        if variable not in data.columns:
            continue

        serie = pd.to_numeric(
            data[variable],
            errors="coerce"
        )

        ancienne = serie.iloc[:5].mean()
        recente = serie.iloc[5:].mean()

        if pd.isna(ancienne) or ancienne == 0:
            continue

        variation = (
            (recente - ancienne)
            / ancienne
            * 100
        )

        resultats[variable] = {
            "ancienne": ancienne,
            "recente": recente,
            "variation": variation,
        }

    return resultats
    
def afficher_bouc_tv(
    df,
    bouc,
    df_historique=None
):

    if bouc is None:
        st.warning("Aucun bouc disponible.")
        return

    # =================================================
    # DONNÉES DU BOUC
    # =================================================

    data_bouc = df[
        df["Code animal"] == bouc
    ].copy()

    tendances = calculer_tendances(
    data_historique
    )    

    if data_bouc.empty:
        st.warning(
            f"Aucune donnée pour le bouc {bouc}."
        )
        return

    # Historique complet pour les alertes
    if df_historique is None:
        df_historique = df

    data_historique = df_historique[
        df_historique["Code animal"] == bouc
    ].copy()

    # La période est déjà filtrée
    data_periode = data_bouc.copy()

    # =================================================
    # ALERTES
    # =================================================

    afficher_alertes(
        data_historique
    )

    # =================================================
    # TRI PAR DATE
    # =================================================

    data_mesures = (
        data_bouc
        .sort_values("Date")
        .copy()
    )

    # =================================================
    # DERNIER POIDS
    # =================================================

    dernier_poids = None
    date_dernier_poids = None

    if "Valeure Pesée" in data_mesures.columns:

        poids_data = data_mesures[
            data_mesures["Valeure Pesée"].notna()
        ]

        if not poids_data.empty:

            dernier_poids = (
                poids_data.iloc[-1]["Valeure Pesée"]
            )

            date_dernier_poids = (
                poids_data.iloc[-1]["Date"]
            )

    # =================================================
    # DERNIÈRE CS
    # =================================================

    derniere_cs = None
    date_derniere_cs = None

    if "Valeur CS" in data_mesures.columns:

        cs_data = data_mesures[
            data_mesures["Valeur CS"].notna()
        ]

        if not cs_data.empty:

            derniere_cs = (
                cs_data.iloc[-1]["Valeur CS"]
            )

            date_derniere_cs = (
                cs_data.iloc[-1]["Date"]
            )

    # =================================================
    # PERFORMANCES
    # =================================================

    nb_sauts = (
        data_periode["Comportement"]
        .isin([2, 3, 4])
        .sum()
    )

    volume_moyen = pd.to_numeric(
        data_periode["Volume semence (ml)"],
        errors="coerce"
    ).mean()

    concentration_moyenne = pd.to_numeric(
        data_periode["Concentration spz (B/ml)"],
        errors="coerce"
    ).mean()

    mobilite_moyenne = pd.to_numeric(
        data_periode["% Mobiles"],
        errors="coerce"
    ).mean()

    motilite_moyenne = pd.to_numeric(
        data_periode["Motiles"],
        errors="coerce"
    ).mean()

    nb_collectes = len(data_periode)

    # =================================================
    # PHOTO
    # =================================================

    photo = f"images/bouc_{bouc}.jpg"

    # =================================================
    # TITRE
    # =================================================

    st.title(
        f"🐐 Bouc {bouc}"
    )

    st.caption(
        "Performances sur la période sélectionnée"
    )

    # =================================================
    # COLONNES
    # =================================================

    col_photo, col_stats = st.columns(
        [1.3, 1]
    )

    # =================================================
    # PHOTO
    # =================================================

    with col_photo:

        if os.path.exists(photo):

            st.image(
                photo,
                width=550
            )

        else:

            st.warning(
                f"📷 Photo non disponible "
                f"pour le bouc {bouc}"
            )

    # =================================================
    # STATISTIQUES
    # =================================================

    with col_stats:

        st.subheader(
            "📊 Performances"
        )

        volume_txt = (
            f"{volume_moyen:.1f} ml"
            if pd.notna(volume_moyen)
            else "—"
        )

        concentration_txt = (
            f"{concentration_moyenne:.1f} B/ml"
            if pd.notna(concentration_moyenne)
            else "—"
        )

        mobilite_txt = (
            f"{mobilite_moyenne:.1f} %"
            if pd.notna(mobilite_moyenne)
            else "—"
        )

        motilite_txt = (
            f"{motilite_moyenne:.1f}"
            if pd.notna(motilite_moyenne)
            else "—"
        )

        poids_txt = (
            f"{float(dernier_poids):.1f} kg"
            if dernier_poids is not None
            else "—"
        )

        cs_txt = (
            f"{float(derniere_cs):.1f} cm"
            if derniere_cs is not None
            else "—"
        )

        # =========================
        # TENDANCES
        # =========================

        if tendances:

            st.subheader(
                "📈 Tendances récentes"
            )

            noms = {
                "Volume semence (ml)": "💧 Volume",
                "Concentration spz (B/ml)": "🔬 Concentration",
                "% Mobiles": "🏃 Mobilité",
                "Motiles": "🦘 Motilité",
            }

            for variable, valeur in tendances.items():

                variation = valeur["variation"]

                if variation > 5:
                    symbole = "🟢 ↑"

                elif variation < -5:
                    symbole = "🔴 ↓"

                else:
                    symbole = "🟡 →"

                st.write(
                    f"**{noms[variable]} :** "
                    f"{symbole} "
                    f"{variation:+.1f} %"
                )

        # =================================================
        # LIGNE 1
        # =================================================

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "🦘 Nombre de sauts",
                nb_sauts
            )

        with c2:
            st.metric(
                "📅 Nombre de collectes",
                nb_collectes
            )

        # =================================================
        # LIGNE 2
        # =================================================

        c3, c4 = st.columns(2)

        with c3:
            st.metric(
                "💧 Volume moyen",
                volume_txt
            )

        with c4:
            st.metric(
                "🔬 Concentration moyenne",
                concentration_txt
            )

        # =================================================
        # LIGNE 3
        # =================================================

        c5, c6 = st.columns(2)

        with c5:
            st.metric(
                "🏃 Mobilité moyenne",
                mobilite_txt
            )

        with c6:
            st.metric(
                "🦘 Motilité moyenne",
                motilite_txt
            )

        # =================================================
        # LIGNE 4
        # =================================================

        c7, c8 = st.columns(2)

        with c7:
            st.metric(
                "⚖️ Dernier poids",
                poids_txt,
                delta=(
                    f"{date_dernier_poids:%d/%m/%Y}"
                    if date_dernier_poids is not None
                    else None
                )
            )

        with c8:
            st.metric(
                "📏 Dernière CS",
                cs_txt,
                delta=(
                    f"{date_derniere_cs:%d/%m/%Y}"
                    if date_derniere_cs is not None
                    else None
                )
            )
