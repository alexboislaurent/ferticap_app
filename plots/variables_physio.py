import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def resample_series_physio(series, periode):

    if periode == "Jour":
        return series

    if periode == "Semaine":
        return series.resample("W").mean()

    if periode == "2 semaines":
        return series.resample("2W").mean()

    if periode == "Mois":
        return series.resample("ME").mean()

    return series


def afficher_variables_physio(
    df_filtered,
    selected_boucs,
):
    st.subheader("🫀 Variables physiologiques")

    variables_map = {
        "Poids (kg)": "Valeure Pesée",
        "CS (cm)": "Valeur CS",
    }

    selected_vars = st.sidebar.multiselect(
        "Variables physiologiques",
        list(variables_map.keys()),
        default=[
            "Poids (kg)",
            "CS (cm)",
        ],
        key="selected_physio",
    )

    periode = st.sidebar.selectbox(
        "Regroupement physiologique",
        [
            "Jour",
            "Semaine",
            "2 semaines",
            "Mois",
        ],
        index=0,
        key="periode_physio",
    )

    filtrer_boucs = st.sidebar.checkbox(
        "Filtrer par boucs sélectionnés",
        value=False,
        key="filtrer_boucs_physio",
    )

    afficher_individuels = st.sidebar.checkbox(
        "Afficher une courbe par bouc",
        value=False,
        key="individuels_physio",
    )

    if len(selected_vars) == 0:
        st.info("Sélectionnez au moins une variable.")
        return

    if filtrer_boucs:

        if not selected_boucs:
            st.warning("Aucun bouc sélectionné.")
            return

        data = df_filtered[
            df_filtered["Code animal"].isin(selected_boucs)
        ].copy()

    else:

        data = df_filtered.copy()

    if data.empty:
        st.warning("Aucune donnée physiologique disponible.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    for var in selected_vars:

        col = variables_map[var]

        if col not in data.columns:
            st.warning(f"Variable absente : {col}")
            continue

        data[col] = pd.to_numeric(
            data[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )

        if afficher_individuels:

            for bouc in selected_boucs:

                data_bouc = data[
                    data["Code animal"] == bouc
                ]

                serie = (
                    data_bouc
                    .dropna(subset=[col])
                    .groupby("Date")[col]
                    .mean()
                    .sort_index()
                )

                if len(serie) == 0:
                    continue

                serie = resample_series_physio(
                    serie,
                    periode,
                )

                ax.plot(
                    serie.index,
                    serie.values,
                    marker="o",
                    label=f"{var} - {bouc}",
                )

        else:

            serie = (
                data
                .dropna(subset=[col])
                .groupby("Date")[col]
                .mean()
                .sort_index()
            )

            if len(serie) == 0:
                continue

            serie = resample_series_physio(
                serie,
                periode,
            )

            ax.plot(
                serie.index,
                serie.values,
                marker="o",
                label=var,
            )

    ax.set_title("Évolution des variables physiologiques")
    ax.set_ylabel("Valeur")
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
