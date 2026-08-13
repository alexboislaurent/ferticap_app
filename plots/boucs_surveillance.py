import pandas as pd
import streamlit as st


SEUIL_PERTE_POIDS = 8
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
        .tail(NB_COLLECTES_PERFORMANCE)
        .copy()
    )

    if len(performances) < NB_COLLECTES_PERFORMANCE:
        return None

    performances["Volume semence (ml)"] = pd.to_numeric(
        performances["Volume semence (ml)"],
        errors="coerce"
    ).fillna(0)

    performances["Concentration spz (B/ml)"] = pd.to_numeric(
        performances["Concentration spz (B/ml)"],
        errors="coerce"
    ).fillna(0)

    performances["Insuffisant"] = (
        (performances["Volume semence (ml)"] < SEUIL_VOLUME)
        |
        (
            performances["Concentration spz (B/ml)"]
            < SEUIL_CONCENTRATION
        )
    )

    nb_insuffisantes = int(
        performances["Insuffisant"].sum()
    )

    if nb_insuffisantes == 0:
        return None

    return {
        "nb_insuffisantes": nb_insuffisantes,
        "nb_collectes": NB_COLLECTES_PERFORMANCE,
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


def afficher_boucs_surveillance(df):

    st.title("🚨 Boucs à surveiller")

    resultats = []

    boucs = sorted(
        df["Code animal"]
        .dropna()
        .unique()
    )

    for bouc in boucs:

        data_bouc = df[
            df["Code animal"] == bouc
        ].copy()

        analyse = analyser_bouc(
            data_bouc
        )

        if analyse is not None:

            resultats.append({
                "bouc": bouc,
                **analyse,
            })

    if not resultats:

        st.success(
            "✅ Aucun bouc ne présente actuellement "
            "de critère d'alerte."
        )
        return

    st.warning(
        f"⚠️ {len(resultats)} bouc(s) à surveiller"
    )

    for resultat in resultats:

        bouc = resultat["bouc"]
        poids = resultat["poids"]
        performance = resultat["performance"]

        st.subheader(
            f"🐐 {bouc}"
        )

        c1, c2 = st.columns(2)

        # =========================
        # ALERTE POIDS
        # =========================

        with c1:

            if poids is not None:

                st.error(
                    f"⚖️ Perte de poids : "
                    f"-{poids['perte']:.1f} %"
                )

                st.write(
                    f"{poids['poids_reference']:.1f} kg "
                    f"→ "
                    f"{poids['poids_dernier']:.1f} kg"
                )

                st.caption(
                    f"Du {poids['date_reference']:%d/%m/%Y} "
                    f"au {poids['date_dernier']:%d/%m/%Y}"
                )

            else:

                st.info(
                    "⚖️ Pas d'alerte poids"
                )

        # =========================
        # ALERTE PERFORMANCE
        # =========================

        with c2:

            if performance is not None:

                nb = performance[
                    "nb_insuffisantes"
                ]

                st.error(
                    f"📉 Performance faible : "
                    f"{nb}/{performance['nb_collectes']} "
                    f"collectes"
                )

                st.write(
                    f"Volume < {SEUIL_VOLUME} ml "
                    f"ou concentration < "
                    f"{SEUIL_CONCENTRATION} B/ml"
                )

                st.caption(
                    "Les données absentes sont comptées comme 0."
                )

            else:

                st.info(
                    "📈 Pas d'alerte performance"
                )

        st.divider()
