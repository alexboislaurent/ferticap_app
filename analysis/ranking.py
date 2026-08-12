import pandas as pd


def calc_ranking_with_success(data, nb_collectes=None):

    tmp = data.copy()

    # =========================
    # SCORE
    # =========================

    tmp["Score"] = pd.to_numeric(
        tmp["Score"],
        errors="coerce"
    )

    # =========================
    # SUCCÈS
    # =========================

    tmp["Succes"] = (
        tmp["Comportement"].isin([2, 3, 4])
    )

    # =========================
    # RANKING 10 DERNIÈRES COLLECTES
    # =========================

    if nb_collectes is not None:

        # Date de dernière collecte disponible
        derniere_date = tmp["Date"].max()

        resultats = []

        for bouc, groupe in tmp.groupby("Code animal"):

            groupe = groupe.sort_values("Date")

            derniere_collecte_bouc = groupe["Date"].max()

            nb_succes = int(groupe["Succes"].sum())

            # ==========================================
            # BOUC DISPARU AVANT LA FIN DES 10 COLLECTES
            # ==========================================

            bouc_disparu = (
                derniere_collecte_bouc < derniere_date
            )

            if bouc_disparu:

                # Score des collectes où le bouc était présent
                score_total = groupe["Score"].fillna(0).sum()

                # Les collectes après sa disparition = 0
                score_moyen = (
                    score_total / nb_collectes
                )

            else:

                # Bouc encore présent :
                # on ignore les scores vides / échecs
                scores_valides = groupe.loc[
                    groupe["Score"].notna(),
                    "Score"
                ]

                if len(scores_valides) > 0:
                    score_moyen = scores_valides.mean()
                else:
                    score_moyen = 0

            resultats.append({
                "Code animal": bouc,
                "Score_moyen": score_moyen,
                "Nb_succes": nb_succes,
                "Nb_total": nb_collectes
            })

        result = pd.DataFrame(resultats)

        result = result.set_index("Code animal")

    # =========================
    # ANNÉE / HISTORIQUE
    # =========================

    else:

        # Pour les autres rankings :
        # moyenne des scores disponibles
        tmp["Score"] = tmp["Score"].fillna(0)

        result = (
            tmp.groupby("Code animal")
            .agg(
                Score_moyen=("Score", "mean"),
                Nb_succes=("Succes", "sum"),
                Nb_total=("Succes", "size")
            )
        )

    # =========================
    # TAUX DE RÉUSSITE
    # =========================

    result["Taux_reussite"] = (
        result["Nb_succes"]
        / result["Nb_total"]
        * 100
    )

    return result.sort_values(
        "Score_moyen",
        ascending=False
    )
