import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
).sort_index

# =========================
# DONNÉES RANKING BOUCS
# =========================

# 10 dernières collectes
last_10_dates = sorted(df_filtered["Date"].dropna().unique())[-10:]

df_last10 = df_filtered[
    df_filtered["Date"].isin(last_10_dates)
]

ranking_last10 = (
    df_last10.groupby("Code animal")["Score"]
    .mean()
    .sort_values(ascending=False)
)

# Année en cours
current_year = pd.Timestamp.today().year

df_year = df_filtered[
    df_filtered["Date"].dt.year == current_year
]

ranking_year = (
    df_year.groupby("Code animal")["Score"]
    .mean()
    .sort_values(ascending=False)
)

# Historique complet
ranking_alltime = (
    df.groupby("Code animal")["Score"]
    .mean()
    .sort_values(ascending=False)
)

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

    
    # =========================
    # FORMAT DES DATES
    # =========================

    # X axis
    ax.set_xticklabels(
        [pd.to_datetime(t.get_text()).strftime("%d/%m/%y") for t in ax.get_xticklabels()],
        rotation=45,
        ha="right"
    )

    # Y axis (si besoin)
    ax.set_yticklabels(
        ax.get_yticklabels(),
        rotation=0
    )

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
        ranking_last10.values
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
        ranking_year.values
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
        ranking_alltime.values
    )

    ax.invert_yaxis()
    ax.set_xlabel("Score moyen")
    ax.set_title("Historique complet")
    ax.grid(True)

    st.pyplot(fig)
