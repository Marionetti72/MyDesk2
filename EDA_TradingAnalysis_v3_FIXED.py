"""
TRADING SYSTEM - EXPLORATORY DATA ANALYSIS (EDA) v3 - FIXED
================================================
Script per analisi approfondita dati EoD FTSE MIB
Analisi: 02.01.2019 - 30.03.2026 (37 titoli)

STRUTTURA CORRETTA IDENTIFICATA:
- Titoli nelle colonne: 1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96, 101, 106, 111, 116, 121, 126, 131, 136, 141, 146, 151, 156, 161, 166, 171, 176, 181
- Campi: Close (0), Open (1), High (2), Low (3), Volume (4) rispetto al titolo
- Colonna 0: Date

Autore: Copilot Trading System
Versione: 3.0 FIXED
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

print("=" * 90)
print("TRADING SYSTEM - EXPLORATORY DATA ANALYSIS v3 - FIXED")
print("=" * 90)
print(f"Data Analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# FASE 1: CARICAMENTO E PARSING STRUTTURA CORRETTA
# ============================================================================
print("\n[FASE 1] CARICAMENTO E PARSING STRUTTURA")
print("-" * 90)

try:
    file_path = "DatiEoD.xlsx"
    df_raw = pd.read_excel(file_path, sheet_name='DATA', header=None)
    
    print(f"✓ File caricato: {file_path}")
    print(f"✓ Shape totale: {df_raw.shape}")
    
except Exception as e:
    print(f"✗ Errore caricamento file: {e}")
    exit()

# Identificazione titoli (ogni 5 colonne partendo da colonna 1)
titoli_columns = {}
titolo_col_indices = [i for i in range(1, 186, 5)]  # 1, 6, 11, 16, 21, ...

print(f"\n✓ Colonne titoli identificate: {titolo_col_indices}")

for titolo_idx in titolo_col_indices:
    titolo_name = df_raw.iloc[0, titolo_idx]  # Nome titolo dalla riga 1
    
    if pd.notna(titolo_name):
        titolo_name = str(titolo_name).strip()
        
        # Mapping colonne relative a questo titolo
        titoli_columns[titolo_name] = {
            'Close': titolo_idx,
            'Open': titolo_idx + 1,
            'High': titolo_idx + 2,
            'Low': titolo_idx + 3,
            'Volume': titolo_idx + 4
        }

print(f"\n✓ Titoli identificati: {len(titoli_columns)}")
print(f"✓ Lista titoli: {list(titoli_columns.keys())}")

# Costruzione DataFrame strutturato
data_dict = {}
dates = pd.to_datetime(df_raw.iloc[2:, 0], errors='coerce')

for titolo, cols_map in titoli_columns.items():
    data_dict[f'{titolo}_Close'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Close']], errors='coerce').values
    data_dict[f'{titolo}_Open'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Open']], errors='coerce').values
    data_dict[f'{titolo}_High'] = pd.to_numeric(df_raw.iloc[2:, cols_map['High']], errors='coerce').values
    data_dict[f'{titolo}_Low'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Low']], errors='coerce').values
    data_dict[f'{titolo}_Volume'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Volume']], errors='coerce').values

df = pd.DataFrame(data_dict)
df['Date'] = dates
df = df.set_index('Date')
df = df.sort_index()
df = df[df.index.notna()]

print(f"\n✓ DataFrame strutturato: shape {df.shape}")
print(f"✓ Date: {df.index.min()} a {df.index.max()}")
print(f"✓ Giorni trading: {len(df)}")

titoli_list = sorted(list(titoli_columns.keys()))
print(f"✓ Titoli da analizzare: {len(titoli_list)}")

# ============================================================================
# FASE 2: VALIDAZIONE QUALITA' DATI
# ============================================================================
print("\n\n[FASE 2] VALIDAZIONE QUALITÀ DATI")
print("-" * 90)

missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
print(f"\nValori mancanti (Top 10):")
print(missing_pct.head(10))

print(f"\nStatistiche per Titolo (Sample di 5):")
print("=" * 90)
for titolo in titoli_list[:5]:
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) > 0:
        print(f"\n{titolo}:")
        print(f"  Disponibilità: {len(close_data)}/{len(df)} ({len(close_data)/len(df)*100:.1f}%)")
        print(f"  Prezzo: Min={close_data.min():.2f}, Max={close_data.max():.2f}, Media={close_data.mean():.2f}")

# ============================================================================
# FASE 3: ANALISI RENDIMENTI E VOLATILITÀ
# ============================================================================
print("\n\n[FASE 3] ANALISI RENDIMENTI E VOLATILITÀ")
print("-" * 90)

returns_dict = {}
for titolo in titoli_list:
    close_prices = df[f'{titolo}_Close'].dropna()
    if len(close_prices) > 1:
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
        returns_dict[titolo] = log_returns

df_returns = pd.DataFrame(returns_dict)

# Statistiche rendimenti
print("\nStatistiche Rendimenti (Log-Returns):")
print("=" * 90)
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
print("=" * 90)
annual_returns = {}
for titolo in titoli_list:
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) > 1:
        ret = (close_data.iloc[-1] / close_data.iloc[0]) ** (252 / len(close_data)) - 1
        annual_returns[titolo] = ret * 100

annual_returns_sorted = sorted(annual_returns.items(), key=lambda x: x[1], reverse=True)
for titolo, ret in annual_returns_sorted:
    print(f"{titolo:25s}: {ret:7.2f}%")

# ============================================================================
# FASE 4: CORRELAZIONI
# ============================================================================
print("\n\n[FASE 4] ANALISI CORRELAZIONI")
print("-" * 90)

corr_matrix = df_returns.corr()
print(f"\nMatrice Correlazioni (First 10 x 10):")
print(corr_matrix.iloc[:10, :10].to_string())

avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
print(f"\nCorrelazione Media tra Titoli: {avg_corr:.3f}")

print("\nCoppie Meno Correlate (Top 10):")
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
corr_pairs = sorted(corr_pairs, key=lambda x: x[2])
for t1, t2, corr_val in corr_pairs[:10]:
    print(f"  {t1:20s} - {t2:20s}: {corr_val:7.3f}")

# ============================================================================
# FASE 5: ANALISI VOLATILITÀ E REGIMI
# ============================================================================
print("\n\n[FASE 5] ANALISI VOLATILITÀ E REGIMI DI MERCATO")
print("-" * 90)

print("\nVolatilità Rolling 30gg (ultimi 60 giorni) - Sample:")
print("=" * 90)
for titolo in titoli_list[:10]:
    returns = df_returns[titolo].dropna()
    vol_30 = returns.rolling(30).std().tail(60)
    if len(vol_30) > 0:
        print(f"{titolo:25s}: Media={vol_30.mean()*100:6.2f}% | Corrente={vol_30.iloc[-1]*100:6.2f}%")

# ============================================================================
# FASE 6: ANALISI DRAWDOWN
# ============================================================================
print("\n\n[FASE 6] ANALISI DRAWDOWN MASSIMI")
print("-" * 90)

def calculate_max_drawdown(prices):
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
print("=" * 90)
for titolo, dd in sorted(max_drawdowns.items(), key=lambda x: x[1]):
    print(f"{titolo:25s}: {dd:8.2f}%")

# ============================================================================
# FASE 7: ANALISI VOLUME
# ============================================================================
print("\n\n[FASE 7] ANALISI VOLUME E LIQUIDITÀ")
print("-" * 90)

print("\nVolume Medio (ultimi 30 giorni):")
print("=" * 90)
volume_stats = {}
for titolo in titoli_list:
    vol_data = df[f'{titolo}_Volume'].tail(30)
    if len(vol_data) > 0:
        avg_vol = vol_data.mean()
        volume_stats[titolo] = avg_vol
        print(f"{titolo:25s}: {avg_vol:15,.0f}")

# ============================================================================
# FASE 8: ANALISI TREND
# ============================================================================
print("\n\n[FASE 8] ANALISI TREND (SMA 20 vs 50)")
print("-" * 90)

print("\nTrend Attuali:")
print("=" * 90)
for titolo in titoli_list:
    close_data = df[f'{titolo}_Close'].dropna()
    if len(close_data) >= 50:
        sma20 = close_data.tail(20).mean()
        sma50 = close_data.tail(50).mean()
        trend = "UP" if sma20 > sma50 else "DOWN"
        diff_pct = ((sma20 - sma50) / sma50) * 100
        print(f"{titolo:25s}: {trend:4s} ({diff_pct:+7.2f}%)")

# ============================================================================
# FASE 9: RANKING TITOLI
# ============================================================================
print("\n\n[FASE 9] RANKING COMPLESSIVO TITOLI")
print("-" * 90)

ranking_score = {}
for titolo in titoli_list:
    annual_ret = annual_returns.get(titolo, 0)
    volatility = stats_returns.loc[titolo, 'Volatilità %']
    max_dd = max_drawdowns.get(titolo, 0)
    sharpe = stats_returns.loc[titolo, 'Sharpe Annuale']
    
    if volatility > 0:
        risk_adjusted_return = annual_ret / (volatility / 100)
    else:
        risk_adjusted_return = 0
    
    dd_penalty = abs(max_dd) / 100
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
print("=" * 90)
print(ranking_df.to_string())

# ============================================================================
# FASE 10: EXPORT RISULTATI
# ============================================================================
print("\n\n[FASE 10] EXPORT RISULTATI")
print("-" * 90)

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
print("-" * 90)

try:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Risk-Return Scatter
    ax1 = axes[0, 0]
    for titolo in titoli_list:
        ax1.scatter(stats_returns.loc[titolo, 'Volatilità %'], 
                   annual_returns.get(titolo, 0), 
                   s=120, alpha=0.6, label=titolo, edgecolors='black', linewidth=0.5)
    ax1.set_xlabel('Volatilità %', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Rendimento Annuale %', fontsize=11, fontweight='bold')
    ax1.set_title('Risk-Return Profile', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='r', linestyle='--', alpha=0.3)
    ax1.legend(fontsize=7, loc='best')
    
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
    
    # 3. Correlazione heatmap
    ax3 = axes[1, 0]
    top_15 = corr_matrix.iloc[:15, :15]
    sns.heatmap(top_15, cmap='coolwarm', center=0, ax=ax3, cbar_kws={'label': 'Correlation'}, 
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
print("\n\n" + "=" * 90)
print("SUMMARY EDA - KEY FINDINGS")
print("=" * 90)

print(f"\n📊 DATASET OVERVIEW:")
print(f"   • Periodo: {df.index.min().date()} a {df.index.max().date()}")
print(f"   • Giorni Trading: {len(df)}")
print(f"   • Titoli Analizzati: {len(titoli_list)}")
print(f"   • Titoli: {titoli_list}")

print(f"\n📈 RENDIMENTI:")
print(f"   • Rendimento Medio Annuale: {np.mean(list(annual_returns.values())):.2f}%")
print(f"   • Migliore Performer: {annual_returns_sorted[0][0]} ({annual_returns_sorted[0][1]:.2f}%)")
print(f"   • Peggiore Performer: {annual_returns_sorted[-1][0]} ({annual_returns_sorted[-1][1]:.2f}%)")

print(f"\n📉 RISCHIO:")
print(f"   • Volatilità Media: {stats_returns['Volatilità %'].mean():.2f}%")
print(f"   • Drawdown Massimo Medio: {np.mean(list(max_drawdowns.values())):.2f}%")
print(f"   • Correlazione Media: {avg_corr:.3f}")

print(f"\n⭐ TOP 10 TITOLI (By Risk-Adjusted Score):")
for i, (titolo, row) in enumerate(ranking_df.head(10).iterrows(), 1):
    print(f"   {i:2d}. {titolo:25s} (Score: {row['Score']:7.2f}, Sharpe: {row['Sharpe']:6.2f})")

print(f"\n🎯 PROSSIMI STEP:")
print(f"   1. Sviluppo strategie di trading multi-indicatore")
print(f"   2. Backtesting dal 01.01.2025")
print(f"   3. Ottimizzazione parametri")
print(f"   4. Implementazione VBA Excel")

print("\n" + "=" * 90)
print(f"✓ ANALISI COMPLETATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 90)

print("\n✓ Output disponibili:")
print("  - ranking_titoli.csv")
print("  - stats_rendimenti.csv")
print("  - correlation_matrix.csv")
print("  - daily_returns.csv")
print("  - EDA_Analysis_1.png")
