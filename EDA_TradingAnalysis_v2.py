"""
TRADING SYSTEM - EXPLORATORY DATA ANALYSIS (EDA) v2
================================================
Script per analisi approfondita dati EoD FTSE MIB
Analisi: 02.01.2019 - 30.03.2026 (37 titoli)

STRUTTURA CORRETTA:
Riga 1: Nomi titoli (A2A, AMPLIFON, AVIO, AZIMUT, BCA_MEDIOLANUM, ...)
Riga 2: Nomi campi (Date, Close, Open, High, Low, Volume) - RIPETUTI per ogni titolo
Riga 3+: Dati veri

Autore: Copilot Trading System
Versione: 2.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurazione output
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("=" * 80)
print("TRADING SYSTEM - EXPLORATORY DATA ANALYSIS v2")
print("=" * 80)
print(f"Data Analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# FASE 1: CARICAMENTO E VALIDAZIONE DATI
# ============================================================================
print("\n[FASE 1] CARICAMENTO E VALIDAZIONE DATI")
print("-" * 80)

try:
    file_path = "DatiEoD.xlsx"
    xls = pd.ExcelFile(file_path)
    
    print(f"✓ File caricato: {file_path}")
    print(f"✓ Sheet disponibili: {xls.sheet_names}")
    
    # Caricamento foglio DATA (senza header, così ottengo tutto)
    df_raw = pd.read_excel(file_path, sheet_name='DATA', header=None)
    print(f"✓ Foglio DATA caricato: shape {df_raw.shape}")
    
except Exception as e:
    print(f"✗ Errore caricamento file: {e}")
    exit()

# ============================================================================
# FASE 2: PARSING STRUTTURA CORRETTA
# ============================================================================
print("\n[FASE 2] PARSING STRUTTURA")
print("-" * 80)

# Riga 1 (indice 0): Nomi titoli
# Riga 2 (indice 1): Nomi campi
# Riga 3+ (indice 2+): Dati

row_1 = df_raw.iloc[0, :].values
row_2 = df_raw.iloc[1, :].values

print(f"Row 1 (Titoli): {row_1[:10]}... (totale {len(row_1)} colonne)")
print(f"Row 2 (Fields): {row_2[:10]}...")

# Identificazione titoli e loro colonne
titoli_columns = {}
current_titolo = None

for col_idx, (titolo_cell, field_cell) in enumerate(zip(row_1, row_2)):
    # Se la cella di titolo non è NaN/vuota, allora cambia titolo
    if pd.notna(titolo_cell) and str(titolo_cell).strip() != '':
        current_titolo = str(titolo_cell).strip()
        if current_titolo not in titoli_columns:
            titoli_columns[current_titolo] = {}
    
    # Se abbiamo un titolo corrente, mappiamo il field
    if current_titolo is not None and pd.notna(field_cell):
        field_name = str(field_cell).strip()
        titoli_columns[current_titolo][field_name] = col_idx

print(f"\n✓ Titoli identificati: {len(titoli_columns)}")
print(f"✓ Nomi titoli: {list(titoli_columns.keys())[:10]}")

# Costruzione DataFrame strutturato
data_dict = {}
dates = pd.to_datetime(df_raw.iloc[2:, 0], errors='coerce')

for titolo, fields_map in titoli_columns.items():
    if 'Close' in fields_map:
        close_col = fields_map['Close']
        open_col = fields_map.get('Open', close_col)
        high_col = fields_map.get('High', close_col)
        low_col = fields_map.get('Low', close_col)
        volume_col = fields_map.get('Volume', close_col)
        
        data_dict[f'{titolo}_Close'] = pd.to_numeric(df_raw.iloc[2:, close_col], errors='coerce').values
        data_dict[f'{titolo}_Open'] = pd.to_numeric(df_raw.iloc[2:, open_col], errors='coerce').values
        data_dict[f'{titolo}_High'] = pd.to_numeric(df_raw.iloc[2:, high_col], errors='coerce').values
        data_dict[f'{titolo}_Low'] = pd.to_numeric(df_raw.iloc[2:, low_col], errors='coerce').values
        data_dict[f'{titolo}_Volume'] = pd.to_numeric(df_raw.iloc[2:, volume_col], errors='coerce').values

df = pd.DataFrame(data_dict)
df['Date'] = dates
df = df.set_index('Date')
df = df.sort_index()
df = df[df.index.notna()]  # Rimuove date NaN

print(f"\n✓ DataFrame strutturato: shape {df.shape}")
print(f"✓ Date: {df.index.min()} a {df.index.max()}")
print(f"✓ Giorni trading: {len(df)}")

# Lista titoli unica
titoli_list = sorted(list(set([col.split('_')[0] for col in df.columns if col != 'Date'])))
print(f"\n✓ Titoli da analizzare ({len(titoli_list)}): {titoli_list}")

# ============================================================================
# FASE 3: VALIDAZIONE QUALITA' DATI
# ============================================================================
print("\n\n[FASE 3] VALIDAZIONE QUALITÀ DATI")
print("-" * 80)

missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
print(f"\nValori mancanti (Top 15):")
print(missing_pct.head(15))

print(f"\nStatistiche Generali per Titolo:")
print("=" * 80)
for titolo in titoli_list[:10]:  # First 10
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) > 0:
        print(f"\n{titolo}:")
        print(f"  Dati disponibili: {len(close_data)}/{len(df)} ({len(close_data)/len(df)*100:.1f}%)")
        print(f"  Prezzo Min: {close_data.min():.2f} | Max: {close_data.max():.2f} | Media: {close_data.mean():.2f}")
        print(f"  Range: {(close_data.max() - close_data.min()) / close_data.mean() * 100:.1f}%")

# ============================================================================
# FASE 4: ANALISI RENDIMENTI E VOLATILITÀ
# ============================================================================
print("\n\n[FASE 4] ANALISI RENDIMENTI E VOLATILITÀ")
print("-" * 80)

# Calcolo rendimenti logaritmici
returns_dict = {}
for titolo in titoli_list:
    close_prices = df[f'{titolo}_Close'].dropna()
    if len(close_prices) > 1:
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
        returns_dict[titolo] = log_returns

df_returns = pd.DataFrame(returns_dict)

# Statistiche rendimenti
print("\nStatistiche Rendimenti (Log-Returns):")
print("=" * 80)
stats_returns = pd.DataFrame({
    'Media Giornaliera %': df_returns.mean() * 100,
    'Volatilità %': df_returns.std() * 100,
    'Skewness': df_returns.skew(),
    'Kurtosis': df_returns.kurtosis(),
    'Min': df_returns.min() * 100,
    'Max': df_returns.max() * 100,
    'Sharpe Annuale': (df_returns.mean() / df_returns.std()) * np.sqrt(252)
})
stats_returns = stats_returns.sort_values('Volatilità %', ascending=False)
print(stats_returns.to_string())

# Rendimenti annuali
print("\n\nRendimenti Annuali Composti:")
print("=" * 80)
annual_returns = {}
for titolo in titoli_list:
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) > 1:
        ret = (close_data.iloc[-1] / close_data.iloc[0]) ** (252 / len(close_data)) - 1
        annual_returns[titolo] = ret * 100

annual_returns_sorted = sorted(annual_returns.items(), key=lambda x: x[1], reverse=True)
for titolo, ret in annual_returns_sorted:
    print(f"{titolo:20s}: {ret:7.2f}%")

# ============================================================================
# FASE 5: CORRELAZIONI
# ============================================================================
print("\n\n[FASE 5] ANALISI CORRELAZIONI")
print("-" * 80)

corr_matrix = df_returns.corr()
print(f"\nMatrice Correlazioni (First 10 x 10):")
print(corr_matrix.iloc[:10, :10].to_string())

# Correlazioni medie
avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
print(f"\nCorrelazione Media tra Titoli: {avg_corr:.3f}")

# Titoli meno correlati (buoni per diversificazione)
print("\nCoppie Meno Correlate (Top 15):")
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
corr_pairs = sorted(corr_pairs, key=lambda x: x[2])
for t1, t2, corr_val in corr_pairs[:15]:
    print(f"  {t1:20s} - {t2:20s}: {corr_val:7.3f}")

# ============================================================================
# FASE 6: ANALISI VOLATILITÀ E REGIMI
# ============================================================================
print("\n\n[FASE 6] ANALISI VOLATILITÀ E REGIMI DI MERCATO")
print("-" * 80)

# Volatilità rolling (30 giorni)
print("\nVolatilità Rolling 30gg (ultimi 60 giorni):")
print("=" * 80)
for titolo in titoli_list[:15]:  # First 15
    returns = df_returns[titolo].dropna()
    vol_30 = returns.rolling(30).std().tail(60)
    print(f"{titolo:20s}: Media: {vol_30.mean()*100:6.2f}% | Corrente: {vol_30.iloc[-1]*100:6.2f}%")

# Regime detection (High vol vs Low vol)
print("\n\nRegimi di Volatilità (Mercato Globale):")
market_vol = df_returns.mean(axis=1).rolling(30).std()
vol_threshold = market_vol.median()
high_vol_periods = (market_vol > vol_threshold).sum()
low_vol_periods = (market_vol <= vol_threshold).sum()
print(f"Giorni Ad Alta Volatilità: {high_vol_periods} ({high_vol_periods/(high_vol_periods+low_vol_periods)*100:.1f}%)")
print(f"Giorni A Bassa Volatilità: {low_vol_periods} ({low_vol_periods/(high_vol_periods+low_vol_periods)*100:.1f}%)")

# ============================================================================
# FASE 7: ANALISI DRAWDOWN
# ============================================================================
print("\n\n[FASE 7] ANALISI DRAWDOWN MASSIMI")
print("-" * 80)

def calculate_max_drawdown(prices):
    """Calcola il drawdown massimo di una serie di prezzi"""
    cummax = prices.expanding().max()
    drawdown = (prices - cummax) / cummax
    return drawdown.min()

max_drawdowns = {}
for titolo in titoli_list:
    close_prices = df[f'{titolo}_Close'].dropna()
    if len(close_prices) > 1:
        max_dd = calculate_max_drawdown(close_prices)
        max_drawdowns[titolo] = max_dd * 100

print("\nMax Drawdown Storico per Titolo:")
print("=" * 80)
for titolo, dd in sorted(max_drawdowns.items(), key=lambda x: x[1]):
    print(f"{titolo:20s}: {dd:8.2f}%")

# ============================================================================
# FASE 8: ANALISI VOLUME
# ============================================================================
print("\n\n[FASE 8] ANALISI VOLUME E LIQUIDITÀ")
print("-" * 80)

print("\nVolume Medio (ultimi 30 giorni):")
print("=" * 80)
volume_stats = {}
for titolo in titoli_list:
    vol_data = df[f'{titolo}_Volume'].tail(30)
    if len(vol_data) > 0:
        avg_vol = vol_data.mean()
        volume_stats[titolo] = avg_vol
        print(f"{titolo:20s}: {avg_vol:15,.0f} titoli/giorno")

# ============================================================================
# FASE 9: ANALISI TREND (Simple Moving Average)
# ============================================================================
print("\n\n[FASE 9] ANALISI TREND (SMA)")
print("-" * 80)

print("\nTrend Attuali (SMA 20 vs SMA 50):")
print("=" * 80)
for titolo in titoli_list:
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) >= 50:
        sma20 = close_data.tail(20).mean()
        sma50 = close_data.tail(50).mean()
        trend = "UP" if sma20 > sma50 else "DOWN"
        diff_pct = ((sma20 - sma50) / sma50) * 100
        print(f"{titolo:20s}: {trend:4s} ({diff_pct:+7.2f}%)")

# ============================================================================
# FASE 10: RANKING TITOLI (Score Composito)
# ============================================================================
print("\n\n[FASE 10] RANKING COMPLESSIVO TITOLI")
print("-" * 80)

ranking_score = {}
for titolo in titoli_list:
    # Componenti score
    annual_ret = annual_returns.get(titolo, 0)
    volatility = stats_returns.loc[titolo, 'Volatilità %']
    max_dd = max_drawdowns.get(titolo, 0)
    sharpe = stats_returns.loc[titolo, 'Sharpe Annuale']
    
    # Score Composito (Sharpe-like, ma anche considerando DD)
    if volatility > 0:
        risk_adjusted_return = annual_ret / (volatility / 100)
    else:
        risk_adjusted_return = 0
    
    # Penalità per drawdown
    dd_penalty = abs(max_dd) / 100
    
    # Score finale
    score = risk_adjusted_return - (dd_penalty * 2)
    ranking_score[titolo] = {
        'Score': score,
        'Annual_Return_%': annual_ret,
        'Volatility_%': volatility,
        'Max_DD_%': max_dd,
        'Sharpe': sharpe
    }

ranking_df = pd.DataFrame(ranking_score).T
ranking_df = ranking_df.sort_values('Score', ascending=False)

print("\nRanking Titoli per Potenziale Trading:")
print("=" * 80)
print(ranking_df.to_string())

# ============================================================================
# FASE 11: EXPORT RISULTATI
# ============================================================================
print("\n\n[FASE 11] EXPORT RISULTATI")
print("-" * 80)

# Export a CSV per successive analisi
ranking_df.to_csv('ranking_titoli.csv')
stats_returns.to_csv('stats_rendimenti.csv')
corr_matrix.to_csv('correlation_matrix.csv')
df_returns.to_csv('daily_returns.csv')

print("✓ File esportati:")
print("  - ranking_titoli.csv")
print("  - stats_rendimenti.csv")
print("  - correlation_matrix.csv")
print("  - daily_returns.csv")

# ============================================================================
# VISUALIZZAZIONI
# ============================================================================
print("\n\n[VISUALIZZAZIONI]")
print("-" * 80)

try:
    # 1. Scatter: Volatilità vs Rendimento
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    ax1 = axes[0, 0]
    for titolo in titoli_list:
        if titolo in stats_returns.index:
            ax1.scatter(stats_returns.loc[titolo, 'Volatilità %'], 
                       annual_returns.get(titolo, 0), 
                       s=120, alpha=0.6, label=titolo, edgecolors='black', linewidth=0.5)
    ax1.set_xlabel('Volatilità %', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Rendimento Annuale %', fontsize=11, fontweight='bold')
    ax1.set_title('Risk-Return Profile', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='r', linestyle='--', alpha=0.3)
    
    # 2. Distribution rendimenti
    ax2 = axes[0, 1]
    top_5 = ranking_df.head(5).index
    for titolo in top_5:
        if titolo in df_returns.columns:
            ax2.hist(df_returns[titolo].dropna()*100, bins=50, alpha=0.5, label=titolo)
    ax2.set_xlabel('Log-Return %', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Frequenza', fontsize=11, fontweight='bold')
    ax2.set_title('Distribuzione Rendimenti Giornalieri (Top 5)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    
    # 3. Correlazione heatmap (top 15)
    ax3 = axes[1, 0]
    top_15_corr = corr_matrix.iloc[:15, :15]
    sns.heatmap(top_15_corr, cmap='coolwarm', center=0, ax=ax3, cbar_kws={'label': 'Correlation'}, 
                annot=False, square=True)
    ax3.set_title('Matrice Correlazioni (First 15 Titoli)', fontsize=12, fontweight='bold')
    
    # 4. Cumulative Returns
    ax4 = axes[1, 1]
    for titolo in top_5:
        if titolo in df_returns.columns:
            cum_ret = (1 + df_returns[titolo]).cumprod() - 1
            ax4.plot(cum_ret.index, cum_ret.values * 100, label=titolo, linewidth=2.5)
    ax4.set_xlabel('Data', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Rendimento Cumulato %', fontsize=11, fontweight='bold')
    ax4.set_title('Rendimenti Cumulati (Top 5 Titoli)', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('EDA_Analysis_1.png', dpi=150, bbox_inches='tight')
    print("✓ Grafico salvato: EDA_Analysis_1.png")
    plt.close()
    
except Exception as e:
    print(f"✗ Errore nella creazione del grafico: {e}")

# ============================================================================
# SUMMARY FINALE
# ============================================================================
print("\n\n" + "=" * 80)
print("SUMMARY EDA - KEY FINDINGS")
print("=" * 80)

print(f"\n📊 DATASET OVERVIEW:")
print(f"   • Periodo: {df.index.min().date()} a {df.index.max().date()}")
print(f"   • Giorni Trading: {len(df)}")
print(f"   • Titoli Analizzati: {len(titoli_list)}")

print(f"\n📈 RENDIMENTI:")
print(f"   • Rendimento Medio Annuale: {np.mean(list(annual_returns.values())):.2f}%")
print(f"   • Migliore Performer: {annual_returns_sorted[0][0]} ({annual_returns_sorted[0][1]:.2f}%)")
print(f"   • Peggiore Performer: {annual_returns_sorted[-1][0]} ({annual_returns_sorted[-1][1]:.2f}%)")

print(f"\n📉 RISCHIO:")
print(f"   • Volatilità Media: {stats_returns['Volatilità %'].mean():.2f}%")
print(f"   • Drawdown Massimo Medio: {np.mean(list(max_drawdowns.values())):.2f}%")
print(f"   • Correlazione Media: {avg_corr:.3f}")

print(f"\n⭐ TOP 5 TITOLI (By Risk-Adjusted Score):")
for i, (titolo, row) in enumerate(ranking_df.head(5).iterrows(), 1):
    print(f"   {i}. {titolo:20s} (Score: {row['Score']:7.2f})")

print(f"\n🎯 PROSSIMI STEP:")
print(f"   1. Sviluppo strategie di trading multi-indicatore")
print(f"   2. Backtesting dal 01.01.2025")
print(f"   3. Ottimizzazione parametri")
print(f"   4. Implementazione VBA Excel")

print("\n" + "=" * 80)
print(f"✓ ANALISI COMPLETATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

print("\n✓ Grafico disponibile: EDA_Analysis_1.png")
print("✓ CSV esportati: ranking_titoli.csv, stats_rendimenti.csv, correlation_matrix.csv, daily_returns.csv")
