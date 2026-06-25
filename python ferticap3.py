import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import numpy as np

# =========================
# CONFIG PAGE
# =========================

st.set_page_config(page_title="Ferticap Dashboard", layout="wide")
st.title("📊 Dashboard Ferticap")

# =========================
# CONNEXION GOOGLE SHEETS
# =========================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key("178LJjutfRAO0cvw4aCJ2RClOuMWv1-I94X0FL8Lcs0c")
worksheet = sheet.worksheet("Labo routine total")

# =========================
# DATA
# =========================

all_values = worksheet.get_all_values()

headers = all_values[1]
rows = all_values[2:]

df = pd.DataFrame(rows, columns=headers)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
df["Comportement"] = pd.to_numeric(df["Comportement"], errors="coerce")

df["Score"] = pd.to_numeric(
    df["Score"].astype(str).str.replace(",", "."),
    errors="coerce"
)

df["Succes"] = df["Comportement"].isin([2, 3, 4]).astype(int)

df["Code animal"] = df["Code animal"].astype(str).str.strip()

df = df[df["Code animal"].notna()]
df = df[df["Code animal"] != ""]
df = df.dropna(subset=["Date"])

# =========================
# VARIABLES BIOLOGIQUES
# =========================

variables_map = {
    "Volume semence (ml)": "Volume semence (ml)",
    "Concentration spz (B/ml)": "Concentration spz (B/ml)",
    "Nb spz éjaculat (B)": "Nb spz éjaculat (B)",
    "% Mobiles": "% Mobiles",
    "Motiles": "Motiles"
}

for col in variables_map.values():
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "."),
            errors="coerce"
        )

# =========================
# SIDEBAR
# =========================

st.sidebar.header("📌 Options")
show_calendar = st.sidebar.checkbox("📅 Calendrier annuel des suivis")

mode = st.sidebar.radio(
    "Graph à afficher",
    [
        "Heatmap",
        "Score global",
        "Score par bouc",
        "Variables biologiques",
        "🏆 Ranking boucs"
    ]
)

# =========================
# INFO SCORE
# =========================

with st.sidebar.expander("ℹ️ Méthode de calcul du score"):
    st.markdown("""
Le score est calculé à partir d’un éjaculat selon la formule suivante :

**Score = (Concentration (B/ml) × Volume éjaculat (ml)) × (% Mobilité) × ((Motilité × 2) / 100)**

### ⚠️ Règle spécifique
- Si la motilité ≤ 2,5 → le score est plafonné à **0,99**

### 📌 Prend en compte :
- Concentration*Volume = Total spz dans l'éjaculat en (M/ml)
- La mobilité pondère la proportion de spermatozoïdes mobiles
- La motilité ajuste la qualité du mouvement

- Un score inférieur à 1 est un mauvais éjaculat, non exploitable
""")

# =========================
# FILTRE DATES
# =========================

df = df.dropna(subset=["Date"])

# =========================
# PREPARATION CALENDRIER SUIVIS
# =========================

suivi_cols = ["Suivi 1", "Suivi 2", "Suivi 3", "Suivi 4"]
existing_cols = [c for c in suivi_cols if c in df.columns]

df_suivi = df.melt(
    id_vars=["Date"],
    value_vars=existing_cols,
    value_name="Suivi"
)

daily = (
    df_suivi.dropna(subset=["Suivi"])
    .groupby("Date")["Suivi"]
    .apply(list)
    .reset_index()
)

df_suivi = df_suivi.dropna(subset=["Suivi"])
df_suivi = df_suivi[df_suivi["Suivi"].astype(str).str.strip() != ""]

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_range = st.sidebar.slider(
    "Période d'analyse",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

start_date, end_date = date_range

df_filtered = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date))
]

# =========================
# RANKING BOUCS (10 DERNIÈRES COLLECTES) ✔ FIXÉ
# =========================

last_10_dates = sorted(df_filtered["Date"].dropna().unique())[-10:]

df_last10 = df_filtered[df_filtered["Date"].isin(last_10_dates)]

ranking_df = (
    df_last10.groupby("Code animal", as_index=False)["Score"]
    .mean()
    .sort_values("Score", ascending=False)
)

ranking_df = ranking_df.rename(columns={
    "Code animal": "Boucs",
    "Score": "Score moyen (10 dernières)"
})

# =========================
# BOUCS AUTO DERNIÈRE COLLECTE
# =========================

boucs = sorted(df["Code animal"].unique())

last_date = df_filtered["Date"].max()

boucs_derniere_collecte = (
    df_filtered[df_filtered["Date"] == last_date]["Code animal"]
    .dropna()
    .unique()
    .tolist()
)

if len(boucs_derniere_collecte) == 0:
    boucs_derniere_collecte = boucs[:5]

selected_boucs = st.sidebar.multiselect(
    "Sélection boucs",
    boucs,
    default=boucs_derniere_collecte
)

# =========================
# PARAMÈTRES
# =========================

periode = st.sidebar.selectbox(
    "Regroupement temporel",
    ["Jour", "Semaine", "2 semaines", "Mois"]
)

lissage = st.sidebar.slider(
    "Lissage",
    1, 10, 3
)

# =========================
# PREP DATA
# =========================

heatmap = df_filtered.pivot_table(
    index="Code animal",
    columns="Date",
    values="Succes",
    aggfunc="max"
).sort_index(axis=1)

score_global = (
    df_filtered.groupby("Date")["Score"]
    .mean()
    .dropna()
    .sort_index()
)

score_par_bouc = df_filtered.pivot_table(
    index="Date",
    columns="Code animal",
    values="Score",
    aggfunc="mean"
).sort_index()

# =========================
# DONNÉES RANKING BOUCS
# =========================

def calc_ranking_with_success(data):

    tmp = data.copy()

    tmp = tmp[tmp["Comportement"].notna()]

    tmp["Succes"] = tmp["Comportement"].isin([2, 3, 4])

    result = (
        tmp.groupby("Code animal")
        .agg(
            Score_moyen=("Score", "mean"),
            Nb_succes=("Succes", "sum"),
            Nb_total=("Succes", "count")
        )
    )

    result["Taux_reussite"] = (
        result["Nb_succes"] /
        result["Nb_total"] * 100
    )

    result = result.sort_values(
        "Score_moyen",
        ascending=False
    )

    return result


# 10 dernières collectes
last_10_dates = sorted(
    df_filtered["Date"].dropna().unique()
)[-10:]

df_last10 = df_filtered[
    df_filtered["Date"].isin(last_10_dates)
]

# Année en cours
current_year = pd.Timestamp.today().year

df_year = df_filtered[
    df_filtered["Date"].dt.year == current_year
]

ranking_last10 = calc_ranking_with_success(df_last10)
ranking_year = calc_ranking_with_success(df_year)
ranking_alltime = calc_ranking_with_success(df)

# =========================
# RESAMPLE
# =========================

def resample_series(series):
    if periode == "Jour":
        return series
    if periode == "Semaine":
        return series.resample("W").mean()
    if periode == "2 semaines":
        return series.resample("2W").mean()
    if periode == "Mois":
        return series.resample("ME").mean()
    return series

def get_color(suivis):
    if len(suivis) > 1:
        return "purple"
    if "FCO" in suivis:
        return "red"
    if "LNCR" in suivis:
        return "blue"
    return "gray"

# =========================
# HEATMAP
# =========================

if mode == "Heatmap":
    st.subheader("Heatmap succès")

    fig, ax = plt.subplots(figsize=(16, 6))

    sns.heatmap(
        heatmap,
        cmap="RdYlGn",
        cbar=False,
        ax=ax,
        linewidths=0.5,
        linecolor="black"
    )

    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    st.pyplot(fig)

 # =========================
# CALENDRIER SUIVIS (VERSION PROPRE)
# =========================

if show_calendar:

    st.subheader("📅 Calendrier annuel des suivis")

    import calendar as cal

    year = df["Date"].dt.year.max()

    # -------------------------
    # 1. Construire table propre Date -> Suivis
    # -------------------------

    suivi_cols = ["Suivi 1", "Suivi 2", "Suivi 3", "Suivi 4"]
    existing_cols = [c for c in suivi_cols if c in df.columns]

    df_suivi = df.melt(
        id_vars=["Date"],
        value_vars=existing_cols,
        value_name="Suivi"
    )

    df_suivi = df_suivi.dropna(subset=["Suivi"])
    df_suivi["Suivi"] = df_suivi["Suivi"].astype(str).str.strip()
    df_suivi = df_suivi[df_suivi["Suivi"] != ""]

    # regroupement par date
    daily = (
        df_suivi.groupby("Date")["Suivi"]
        .apply(lambda x: list(set(x)))
        .reset_index()
    )

    # -------------------------
    # 2. couleur par type
    # -------------------------

    def get_color(suivis):
        if not isinstance(suivis, list):
            return "white"
        if "FCO" in suivis and "LNCR" in suivis:
            return "purple"
        if "FCO" in suivis:
            return "red"
        if "LNCR" in suivis:
            return "blue"
        if len(suivis) > 0:
            return "orange"
        return "white"

    # mapping date -> couleur
    color_map = {}

    for _, row in daily.iterrows():
        d = row["Date"].date()
        color_map[d] = get_color(row["Suivi"])

    # -------------------------
    # 3. FIGURE calendrier mensuel
    # -------------------------

    fig, axes = plt.subplots(3, 4, figsize=(18, 10))
    axes = axes.flatten()

    for month in range(1, 13):

        ax = axes[month - 1]
        ax.set_title(calendar.month_name[month], fontsize=12)
        ax.set_axis_off()

        month_matrix = cal.monthcalendar(year, month)

        for i, week in enumerate(month_matrix):
            for j, day in enumerate(week):

                if day == 0:
                    continue

                date_obj = pd.Timestamp(year, month, day).date()
                color = color_map.get(date_obj, "white")

                ax.add_patch(
                    plt.Rectangle(
                        (j, -i),
                        1,
                        1,
                        facecolor=color,
                        edgecolor="black",
                        lw=0.4
                    )
                )

                # numéro du jour
                ax.text(
                    j + 0.5,
                    -i + 0.5,
                    str(day),
                    ha="center",
                    va="center",
                    fontsize=7
                )

        ax.set_xlim(0, 7)
        ax.set_ylim(-6, 1)

    plt.tight_layout()
    st.pyplot(fig)

# =========================
# SCORE GLOBAL
# =========================

elif mode == "Score global":
    st.subheader("Score moyen global")

    score = resample_series(score_global)
    score = score.rolling(lissage, min_periods=1).mean()

    fig, ax = plt.subplots()

    ax.plot(score.index, score.values, marker="o")
    ax.grid(True)

    ax.set_title("Score moyen global")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=45)

    st.pyplot(fig)

# =========================
# SCORE PAR BOUC
# =========================

elif mode == "Score par bouc":
    st.subheader("Score par bouc")

    data = resample_series(score_par_bouc)

    fig, ax = plt.subplots(figsize=(14, 6))

    for b in selected_boucs:
        if b in data.columns:
            serie = data[b].rolling(lissage, min_periods=1).mean()

            ax.plot(
                serie.index,
                serie.values,
                marker="o",
                label=b
            )

    ax.set_title("Score par bouc")
    ax.legend()
    ax.grid(True)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=45)

    st.pyplot(fig)

# =========================
# VARIABLES BIOLOGIQUES
# =========================

elif mode == "Variables biologiques":
    st.subheader("📊 Variables biologiques")

    selected_vars = st.sidebar.multiselect(
        "Variables",
        list(variables_map.keys()),
        default=["Volume semence (ml)", "Concentration spz (B/ml)"]
    )

    fig, ax = plt.subplots(figsize=(14, 6))

    for var in selected_vars:
        col = variables_map[var]

        if col in df_filtered.columns:
            serie = (
                df_filtered.groupby("Date")[col]
                .mean()
                .dropna()
                .sort_index()
            )

            ax.plot(
                serie.index,
                serie.values,
                marker="o",
                label=var
            )

    ax.set_title("Variables biologiques")
    ax.legend()
    ax.grid(True)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=45)

    st.pyplot(fig)


# =========================
# RANKING BOUCS
# =========================

elif mode == "🏆 Ranking boucs":

    # --------------------------------------------------
    # 10 dernières collectes
    # --------------------------------------------------

    st.subheader("🏆 Performance des boucs - 10 dernières collectes")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        ranking_last10.index,
        ranking_last10["Score_moyen"]
    )

    for i, (_, row) in enumerate(ranking_last10.iterrows()):
        ax.text(
            row["Score_moyen"] + 0.1,
            i,
            f'{row["Taux_reussite"]:.0f}% ({int(row["Nb_succes"])}/{int(row["Nb_total"])})',
            va="center"
        )

    ax.invert_yaxis()
    ax.set_xlabel("Score moyen")
    ax.set_title("10 dernières collectes")
    ax.grid(True)

    st.pyplot(fig)

    # --------------------------------------------------
    # Année en cours
    # --------------------------------------------------

    st.subheader(f"📅 Performance des boucs - {current_year}")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        ranking_year.index,
        ranking_year["Score_moyen"]
    )

    for i, (_, row) in enumerate(ranking_year.iterrows()):
        ax.text(
            row["Score_moyen"] + 0.1,
            i,
            f'{row["Taux_reussite"]:.0f}% ({int(row["Nb_succes"])}/{int(row["Nb_total"])})',
            va="center"
        )

    ax.invert_yaxis()
    ax.set_xlabel("Score moyen")
    ax.set_title(f"Année {current_year}")
    ax.grid(True)

    st.pyplot(fig)

    # --------------------------------------------------
    # Historique complet
    # --------------------------------------------------

    st.subheader("📈 Performance des boucs - All Time")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        ranking_alltime.index,
        ranking_alltime["Score_moyen"]
    )

    for i, (_, row) in enumerate(ranking_alltime.iterrows()):
        ax.text(
            row["Score_moyen"] + 0.1,
            i,
            f'{row["Taux_reussite"]:.0f}% ({int(row["Nb_succes"])}/{int(row["Nb_total"])})',
            va="center"
        )

    ax.invert_yaxis()
    ax.set_xlabel("Score moyen")
    ax.set_title("Historique complet")
    ax.grid(True)

    st.pyplot(fig)
