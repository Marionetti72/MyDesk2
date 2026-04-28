"""
MARKET ANALYSIS - FULL PERIOD 2019-2026
================================================
Analisi APPROFONDITA del mercato FTSE MIB su TUTTO il periodo storico
Obiettivo: Identificare pattern, opportunity, titoli vincenti e strategie reali

Periodo: 02.01.2019 - 30.03.2026 (7+ anni di dati)
Titoli: 37 componenti FTSE MIB

Autore: Copilot Trading System
Data: 2026-04-27
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("=" * 100)
print("MARKET ANALYSIS - FULL PERIOD 2019-2026")
print("=" * 100)
print(f"Data Analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# FASE 1: CARICAMENTO DATI COMPLETI
# ============================================================================
print("\n[FASE 1] CARICAMENTO DATI COMPLETI")
print("-" * 100)

try:
    file_path = "DatiEoD.xlsx"
    df_raw = pd.read_excel(file_path, sheet_name='DATA', header=None)
    print(f"✓ File caricato: {file_path}")
except Exception as e:
    print(f"✗ Errore: {e}")
    exit()

# Parsing
titoli_columns = {}
titolo_col_indices = [i for i in range(1, 186, 5)]

for titolo_idx in titolo_col_indices:
    titolo_name = df_raw.iloc[0, titolo_idx]
    if pd.notna(titolo_name):
        titolo_name = str(titolo_name).strip()
        titoli_columns[titolo_name] = {
            'Close': titolo_idx,
            'Open': titolo_idx + 1,
            'High': titolo_idx + 2,
            'Low': titolo_idx + 3,
            'Volume': titolo_idx + 4
        }

# Costruzione DataFrame completo
data_dict = {}
dates = pd.to_datetime(df_raw.iloc[2:, 0], errors='coerce')

for titolo, cols_map in titoli_columns.items():
    data_dict[f'{titolo}_Close'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Close']], errors='coerce').values
    data_dict[f'{titolo}_High'] = pd.to_numeric(df_raw.iloc[2:, cols_map['High']], errors='coerce').values
    data_dict[f'{titolo}_Low'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Low']], errors='coerce').values
    data_dict[f'{titolo}_Volume'] = pd.to_numeric(df_raw.iloc[2:, cols_map['Volume']], errors='coerce').values

df = pd.DataFrame(data_dict)
df['Date'] = dates
df = df.set_index('Date')
df = df.sort_index()
df = df[df.index.notna()]

titoli_list = sorted(list(titoli_columns.keys()))

print(f"✓ Dati caricati: {df.shape}")
print(f"✓ Periodo: {df.index.min().date()} a {df.index.max().date()}")
print(f"✓ Giorni: {len(df)}")
print(f"✓ Titoli: {len(titoli_list)}")

# ============================================================================
# FASE 2: ANALISI PERFORMANCE PER TITOLO
# ============================================================================
print("\n[FASE 2] ANALISI PERFORMANCE PER TITOLO")
print("-" * 100)

performance_data = []

for titolo in titoli_list:
    close_prices = df[f'{titolo}_Close'].dropna()
    
    if len(close_prices) > 0:
        start_price = close_prices.iloc[0]
        end_price = close_prices.iloc[-1]
        total_return = (end_price / start_price - 1) * 100
        
        # CAGR (Compound Annual Growth Rate)
        years = len(close_prices) / 252
        cagr = ((end_price / start_price) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Volatilità annuale
        daily_returns = np.log(close_prices / close_prices.shift(1)).dropna()
        annual_vol = daily_returns.std() * np.sqrt(252) * 100
        
        # Sharpe Ratio
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # Max Drawdown
        cummax = close_prices.expanding().max()
        drawdown = (close_prices - cummax) / cummax * 100
        max_dd = drawdown.min()
        
        # Best/Worst month (FIXED: M -> ME)
        monthly_returns = close_prices.resample('ME').last().pct_change() * 100
        best_month = monthly_returns.max()
        worst_month = monthly_returns.min()
        
        # Disponibilità dati
        data_availability = (len(close_prices) / len(df)) * 100
        
        performance_data.append({
            'Titolo': titolo,
            'Start_Price': start_price,
            'End_Price': end_price,
            'Total_Return_%': total_return,
            'CAGR_%': cagr,
            'Annual_Vol_%': annual_vol,
            'Sharpe': sharpe,
            'Max_DD_%': max_dd,
            'Best_Month_%': best_month,
            'Worst_Month_%': worst_month,
            'Data_Availability_%': data_availability
        })

df_perf = pd.DataFrame(performance_data).sort_values('CAGR_%', ascending=False)

print("\nTOP 15 TITOLI (by CAGR%):")
print("=" * 100)
print(df_perf.head(15)[['Titolo', 'CAGR_%', 'Total_Return_%', 'Annual_Vol_%', 'Max_DD_%', 'Sharpe']].to_string(index=False))

print("\n\nBOTTOM 10 TITOLI (by CAGR%):")
print("=" * 100)
print(df_perf.tail(10)[['Titolo', 'CAGR_%', 'Total_Return_%', 'Annual_Vol_%', 'Max_DD_%', 'Sharpe']].to_string(index=False))

# Export performance completa
df_perf.to_csv('full_period_performance.csv', index=False)
print("\n✓ Esportato: full_period_performance.csv")

# ============================================================================
# FASE 3: ANALISI PERIODI DI OPPORTUNITY
# ============================================================================
print("\n\n[FASE 3] ANALISI PERIODI DI OPPORTUNITY")
print("-" * 100)

# Indice sintetico (media di tutti i titoli)
index_prices = df[[f'{t}_Close' for t in titoli_list]].mean(axis=1)
index_prices = index_prices.dropna()

# Calcolo drawdown storico
cummax = index_prices.expanding().max()
drawdown_pct = (index_prices - cummax) / cummax * 100

# Periodi di stress (drawdown > 10%)
stress_periods = drawdown_pct[drawdown_pct < -10]
recovery_periods = []

print("\nPERIODI DI STRESS (Drawdown > -10%):")
print("=" * 100)

if len(stress_periods) > 0:
    stress_dates = stress_periods.index
    
    # Raggruppa periodi continui
    current_period = [stress_dates[0]]
    for i in range(1, len(stress_dates)):
        if (stress_dates[i] - stress_dates[i-1]).days <= 10:  # Continuità
            current_period.append(stress_dates[i])
        else:
            if len(current_period) > 5:  # Solo periodi significativi
                min_dd = drawdown_pct[current_period].min()
                recovery_periods.append({
                    'Start': current_period[0],
                    'End': current_period[-1],
                    'Duration_Days': (current_period[-1] - current_period[0]).days,
                    'Min_DD_%': min_dd,
                    'Start_Price': index_prices[current_period[0]],
                    'End_Price': index_prices[current_period[-1]]
                })
            current_period = [stress_dates[i]]
    
    if len(current_period) > 5:
        min_dd = drawdown_pct[current_period].min()
        recovery_periods.append({
            'Start': current_period[0],
            'End': current_period[-1],
            'Duration_Days': (current_period[-1] - current_period[0]).days,
            'Min_DD_%': min_dd,
            'Start_Price': index_prices[current_period[0]],
            'End_Price': index_prices[current_period[-1]]
        })

if recovery_periods:
    df_recovery = pd.DataFrame(recovery_periods).sort_values('Min_DD_%')
    print(df_recovery[['Start', 'End', 'Duration_Days', 'Min_DD_%']].to_string(index=False))
    
    print("\n\nMIGLIORI OPPORTUNITY DI ACQUISTO (Max Drawdown):")
    print("=" * 100)
    for idx, row in df_recovery.head(5).iterrows():
        recovery_gain = ((row['End_Price'] - row['Start_Price']) / row['Start_Price']) * 100
        print(f"  {row['Start'].date()} a {row['End'].date()}: DD {row['Min_DD_%']:.2f}% → Recovery {recovery_gain:.2f}%")

# ============================================================================
# FASE 4: ANALISI SEASONALITA' E TREND ANNUALI
# ============================================================================
print("\n\n[FASE 4] ANALISI SEASONALITA' E TREND ANNUALI")
print("-" * 100)

# Performance per anno
annual_data = []
for year in range(2019, 2027):
    year_start = pd.Timestamp(f'{year}-01-01')
    year_end = pd.Timestamp(f'{year}-12-31')
    year_prices = index_prices[(index_prices.index >= year_start) & (index_prices.index <= year_end)]
    
    if len(year_prices) > 0:
        annual_return = (year_prices.iloc[-1] / year_prices.iloc[0] - 1) * 100
        annual_vol = np.log(year_prices / year_prices.shift(1)).std() * np.sqrt(252) * 100
        
        # Min/Max durante l'anno
        min_price = year_prices.min()
        max_price = year_prices.max()
        dd = ((min_price - max_price) / max_price) * 100
        
        annual_data.append({
            'Anno': year,
            'Return_%': annual_return,
            'Volatility_%': annual_vol,
            'Max_DD_%': dd,
            'Min': min_price,
            'Max': max_price
        })

df_annual = pd.DataFrame(annual_data)

print("\nPERFORMANCE ANNUALE:")
print("=" * 100)
print(df_annual[['Anno', 'Return_%', 'Volatility_%', 'Max_DD_%']].to_string(index=False))

# ============================================================================
# FASE 5: VOLATILITA' E REGIMI DI MERCATO
# ============================================================================
print("\n\n[FASE 5] VOLATILITA' E REGIMI DI MERCATO")
print("-" * 100)

# Volatilità rolling (30 giorni)
daily_returns_index = np.log(index_prices / index_prices.shift(1)).dropna()
vol_rolling = daily_returns_index.rolling(30).std() * np.sqrt(252) * 100

print(f"\nVolatilità Media (30gg): {vol_rolling.mean():.2f}%")
print(f"Volatilità Max: {vol_rolling.max():.2f}%")
print(f"Volatilità Min: {vol_rolling.min():.2f}%")
print(f"Volatilità Corrente (ultimi 30gg): {vol_rolling.iloc[-1]:.2f}%")

# Periodi ad alta/bassa volatilità
high_vol_threshold = vol_rolling.quantile(0.75)
low_vol_threshold = vol_rolling.quantile(0.25)

high_vol_days = len(vol_rolling[vol_rolling > high_vol_threshold])
low_vol_days = len(vol_rolling[vol_rolling < low_vol_threshold])

print(f"\nGiorni Ad ALTA Volatilità (>75°): {high_vol_days} ({high_vol_days/len(vol_rolling)*100:.1f}%)")
print(f"Giorni A BASSA Volatilità (<25°): {low_vol_days} ({low_vol_days/len(vol_rolling)*100:.1f}%)")

# ============================================================================
# FASE 6: ANALISI PATTERN - QUANDO COMPRARE
# ============================================================================
print("\n\n[FASE 6] PATTERN ANALYSIS - QUANDO COMPRARE")
print("-" * 100)

# Estrattaglia: Comprare quando il prezzo è sotto la SMA200 ma in recupero
sma200 = index_prices.rolling(200).mean()

# Segnali: Prezzo < SMA200 - 5% E il giorno dopo sale
opportunities = []
for i in range(200, len(index_prices)-1):
    price_today = index_prices.iloc[i]
    price_yesterday = index_prices.iloc[i-1]
    price_tomorrow = index_prices.iloc[i+1]
    sma_today = sma200.iloc[i]
    
    if not np.isnan(sma_today):
        # Prezzo sotto SMA200 del 5%
        if price_today < sma_today * 0.95:
            # Ma sta recuperando (prezzo > ieri)
            if price_tomorrow > price_today:
                next_5_days = index_prices.iloc[i:i+6].mean()
                next_20_days = index_prices.iloc[i:i+21].mean()
                
                gain_5 = ((next_5_days - price_today) / price_today) * 100
                gain_20 = ((next_20_days - price_today) / price_today) * 100
                
                opportunities.append({
                    'Date': index_prices.index[i],
                    'Price': price_today,
                    'SMA200': sma_today,
                    'Discount_%': ((price_today - sma_today) / sma_today) * 100,
                    'Gain_5days_%': gain_5,
                    'Gain_20days_%': gain_20
                })

if opportunities:
    df_opp = pd.DataFrame(opportunities)
    print(f"\nOPPORTUNITA' STORICHE (Prezzo < SMA200-5% + recovery):")
    print(f"Totale: {len(df_opp)} segnali")
    print(f"Gain medio 5 giorni: {df_opp['Gain_5days_%'].mean():.2f}%")
    print(f"Gain medio 20 giorni: {df_opp['Gain_20days_%'].mean():.2f}%")
    print(f"Win rate (Gain>0): {(len(df_opp[df_opp['Gain_5days_%']>0])/len(df_opp)*100):.1f}%")
    
    df_opp.to_csv('historical_opportunities.csv', index=False)
    print(f"\n✓ Esportato: historical_opportunities.csv")

# ============================================================================
# FASE 7: TITOLI PER STRATEGIE SPECIFICHE
# ============================================================================
print("\n\n[FASE 7] RAGGRUPPAMENTO TITOLI PER STRATEGIE")
print("-" * 100)

print("\nTITOLI TREND-FOLLOWING (CAGR > 5%):")
trend_titoli = df_perf[df_perf['CAGR_%'] > 5]['Titolo'].tolist()
print(f"  {trend_titoli}")
print(f"  Totale: {len(trend_titoli)} titoli")

print("\nTITOLI MEAN-REVERSION (CAGR -5% a 5%, High Volatility):")
mean_rev_titoli = df_perf[(df_perf['CAGR_%'] > -5) & (df_perf['CAGR_%'] < 5) & (df_perf['Annual_Vol_%'] > 20)]['Titolo'].tolist()
print(f"  {mean_rev_titoli}")
print(f"  Totale: {len(mean_rev_titoli)} titoli")

print("\nTITOLI LOW-VOLATILITY (Vol < 15%, Sharpe > 0):")
low_vol_titoli = df_perf[(df_perf['Annual_Vol_%'] < 15) & (df_perf['Sharpe'] > 0)]['Titolo'].tolist()
print(f"  {low_vol_titoli}")
print(f"  Totale: {len(low_vol_titoli)} titoli")

# ============================================================================
# FASE 8: CORRELAZIONI E DIVERSIFICAZIONE
# ============================================================================
print("\n\n[FASE 8] ANALISI CORRELAZIONI")
print("-" * 100)

# Returns giornalieri per tutti i titoli
returns_data = {}
for titolo in titoli_list:
    close_prices = df[f'{titolo}_Close'].dropna()
    if len(close_prices) > 1:
        returns = np.log(close_prices / close_prices.shift(1)).dropna()
        returns_data[titolo] = returns

df_returns = pd.DataFrame(returns_data)
corr_matrix = df_returns.corr()

# Correlazione media
avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
print(f"\nCorrelazione Media tra Titoli: {avg_corr:.3f}")

# Coppie meno correlate
print("\nCOPPIE MENO CORRELATE (Best for Diversification):")
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
corr_pairs = sorted(corr_pairs, key=lambda x: x[2])
for t1, t2, corr_val in corr_pairs[:10]:
    print(f"  {t1:20s} - {t2:20s}: {corr_val:7.3f}")

# ============================================================================
# FASE 9: VISUALIZZAZIONI
# ============================================================================
print("\n\n[FASE 9] CREAZIONE VISUALIZZAZIONI")
print("-" * 100)

try:
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    # 1. Indice 2019-2026
    ax1 = axes[0, 0]
    ax1.plot(index_prices.index, index_prices.values, linewidth=2.5, color='darkblue', label='FTSE MIB (Media)')
    ax1.plot(sma200.index, sma200.values, linewidth=2, color='red', alpha=0.7, label='SMA 200')
    ax1.fill_between(index_prices.index, index_prices.values, sma200.values, 
                      where=index_prices.values < sma200.values, alpha=0.2, color='red', label='Undervalued')
    ax1.set_title('FTSE MIB Index 2019-2026 vs SMA200', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=10, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # 2. Drawdown storico
    ax2 = axes[0, 1]
    ax2.fill_between(drawdown_pct.index, 0, drawdown_pct.values, alpha=0.3, color='red')
    ax2.plot(drawdown_pct.index, drawdown_pct.values, linewidth=2, color='darkred')
    ax2.axhline(y=-10, color='orange', linestyle='--', alpha=0.5, label='Stress Level (-10%)')
    ax2.set_title('Drawdown Storico', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Drawdown %', fontsize=10, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Performance annuale
    ax3 = axes[1, 0]
    colors = ['green' if x > 0 else 'red' for x in df_annual['Return_%']]
    ax3.bar(df_annual['Anno'], df_annual['Return_%'], color=colors, alpha=0.7)
    ax3.axhline(y=0, color='black', linewidth=0.8)
    ax3.set_title('Annual Returns 2019-2026', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Return %', fontsize=10, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Volatilità rolling
    ax4 = axes[1, 1]
    ax4.plot(vol_rolling.index, vol_rolling.values, linewidth=2, color='purple', label='Vol 30gg')
    ax4.axhline(y=high_vol_threshold, color='red', linestyle='--', alpha=0.5, label=f'High Vol Threshold')
    ax4.axhline(y=low_vol_threshold, color='green', linestyle='--', alpha=0.5, label=f'Low Vol Threshold')
    ax4.fill_between(vol_rolling.index, 0, vol_rolling.values, alpha=0.2, color='purple')
    ax4.set_title('Rolling Volatility (30 days)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Volatility %', fontsize=10, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('market_analysis_full_2019_2026.png', dpi=150, bbox_inches='tight')
    print(f"✓ Grafico salvato: market_analysis_full_2019_2026.png")
    plt.close()
    
except Exception as e:
    print(f"✗ Errore grafico: {e}")

# ============================================================================
# SUMMARY FINALE
# ============================================================================
print("\n\n" + "=" * 100)
print("SUMMARY - INSIGHTS CHIAVE")
print("=" * 100)

print(f"\n📊 MERCATO GENERALE:")
print(f"   Periodo: 2019-2026 ({len(df)} giorni trading)")
print(f"   Total Return Indice: {((index_prices.iloc[-1] / index_prices.iloc[0] - 1) * 100):.2f}%")
print(f"   CAGR: {((index_prices.iloc[-1] / index_prices.iloc[0]) ** (1 / 7) - 1) * 100:.2f}%")
print(f"   Volatilità Media: {vol_rolling.mean():.2f}%")
print(f"   Max Drawdown: {drawdown_pct.min():.2f}%")

print(f"\n⭐ TOP 5 TITOLI (by CAGR):")
for i, row in df_perf.head(5).iterrows():
    print(f"   {row['Titolo']:20s}: {row['CAGR_%']:7.2f}% ({row['Total_Return_%']:8.2f}% total, Sharpe {row['Sharpe']:5.2f})")

print(f"\n🎯 STRATEGIE CONSIGLIATE:")
print(f"   1. TREND-FOLLOWING su titoli con CAGR > 5% ({len(trend_titoli)} titoli)")
print(f"   2. MEAN-REVERSION su titoli volatili ({len(mean_rev_titoli)} titoli)")
print(f"   3. LOW-VOLATILITY per capital preservation ({len(low_vol_titoli)} titoli)")
if opportunities:
    print(f"   4. OPPORTUNISTIC ENTRY su drawdown > 10% (avg gain +{df_opp['Gain_20days_%'].mean():.2f}% in 20gg)")

print(f"\n📈 PERIODI MIGLIORI PER COMPRARE:")
print(f"   Quando drawdown > -10%")
print(f"   Quando prezzo < SMA200 - 5%")
print(f"   Volatilità alta (> {high_vol_threshold:.1f}%)")

print("\n" + "=" * 100)
print(f"✓ ANALISI COMPLETATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

print("\n✓ File esportati:")
print("  - full_period_performance.csv (performance di ogni titolo)")
print("  - historical_opportunities.csv (segnali storici)")
print("  - market_analysis_full_2019_2026.png (grafici)")
