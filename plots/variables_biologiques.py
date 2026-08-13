import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def resample_series(series, periode):

    if periode == "Jour":
        return series

    if periode == "Semaine":
        return series.resample("W").mean()

    if periode == "2 semaines":
        return series.resample("2W").mean()

    if periode == "Mois":
        return series.resample("ME").mean()

    return series


def afficher_variables_biologiques(
    df_filtered,
    selected_boucs,
    periode,
    lissage,
):
    st.subheader("📊 Variables biologiques")

    variables_map = {
        "Volume semence (ml)": "Volume semence (ml)",
        "Concentration spz (B/ml)": "Concentration spz (B/ml)",
        "Nb spz éjaculat (B)": "Nb spz éjaculat (B)",
        "% Mobiles": "% Mobiles",
        "Motiles": "Motiles",
        "Suivi des sauts": "Suivi des sauts",
    }

    selected_vars = st.sidebar.multiselect(
        "Variables biologiques",
        list(variables_map.keys()),
        default=[
            "Volume semence (ml)",
            "Concentration spz (B/ml)",
            "Suivi des sauts",
        ],
        key="selected_bio",
    )

    filtrer_boucs = st.sidebar.checkbox(
        "Filtrer par boucs sélectionnés",
        value=False,
        key="filtrer_boucs_bio",
    )

    afficher_individuels = st.sidebar.checkbox(
        "Afficher une courbe par bouc",
        value=False,
        key="individuels_bio",
    )

    if len(selected_vars) == 0:
        st.info("Sélectionnez au moins une variable.")
        return

    if filtrer_boucs:

        if not selected_boucs:
            st.warning("Aucun bouc sélectionné.")
            return

        data_bio = df_filtered[
            df_filtered["Code animal"].isin(selected_boucs)
        ].copy()

    else:
        data_bio = df_filtered.copy()

    if data_bio.empty:
        st.warning("Aucune donnée disponible.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    for var in selected_vars:

        col = variables_map[var]

        if col not in data_bio.columns:
            st.warning(f"Variable absente : {col}")
            continue

        data_bio[col] = (
            data_bio[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
        )

        data_bio[col] = pd.to_numeric(
            data_bio[col],
            errors="coerce",
        )

        if afficher_individuels:

            for bouc in selected_boucs:

                data_bouc = data_bio[
                    data_bio["Code animal"] == bouc
                ]

                if col == "Suivi des sauts":

                    serie = (
                        data_bouc
                        .groupby("Date")[col]
                        .sum()
                        .sort_index()
                        .fillna(0)
                    )

                else:

                    serie = (
                        data_bouc
                        .groupby("Date")[col]
                        .mean()
                        .sort_index()
                        .fillna(0)
                    )

                if len(serie) == 0:
                    continue

                serie = resample_series(
                    serie,
                    periode,
                )

                if col != "Suivi des sauts" and lissage > 1:

                    serie = (
                        serie
                        .rolling(
                            window=lissage,
                            min_periods=1,
                        )
                        .mean()
                    )

                ax.plot(
                    serie.index,
                    serie.values,
                    marker="o",
                    label=f"{var} - {bouc}",
                )

        else:

            if col == "Suivi des sauts":

                serie = (
                    data_bio
                    .groupby("Date")[col]
                    .sum()
                    .sort_index()
                    .fillna(0)
                )

            else:

                serie = (
                    data_bio
                    .groupby("Date")[col]
                    .mean()
                    .sort_index()
                    .fillna(0)
                )

            if len(serie) == 0:
                continue

            serie = resample_series(
                serie,
                periode,
            )

            if col != "Suivi des sauts" and lissage > 1:

                serie = (
                    serie
                    .rolling(
                        window=lissage,
                        min_periods=1,
                    )
                    .mean()
                )

            ax.plot(
                serie.index,
                serie.values,
                marker="o",
                label=var,
            )

    ax.set_title("Évolution des variables biologiques")

    if "Suivi des sauts" in selected_vars:
        ax.set_ylabel("Nombre de sauts")
    else:
        ax.set_ylabel("Valeur moyenne")

    ax.grid(True)
    ax.legend()

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m/%y")
    )

    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator()
    )

    fig.autofmt_xdate(rotation=45)

    st.pyplot(fig)
