"""
TRADING SYSTEM - BACKTEST E GENERAZIONE SEGNALI
================================================
Notebook completo per backtesting strategia multi-indicatore
Periodo: 01.01.2025 - 24.04.2026
Capitale: €100,000 | Commissione: €19/trade
Max Posizioni: 8-10 simultanee

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

# Configurazione output
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("=" * 100)
print("TRADING SYSTEM - BACKTEST E GENERAZIONE SEGNALI")
print("=" * 100)
print(f"Data Analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# FASE 1: CARICAMENTO DATI
# ============================================================================
print("\n[FASE 1] CARICAMENTO DATI")
print("-" * 100)

try:
    file_path = "DatiEoD.xlsx"
    df_raw = pd.read_excel(file_path, sheet_name='DATA', header=None)
    print(f"✓ File caricato: {file_path}")
except Exception as e:
    print(f"✗ Errore: {e}")
    exit()

# Parsing struttura
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

# Costruzione DataFrame
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

titoli_list = sorted(list(titoli_columns.keys()))

print(f"✓ Dati caricati: {df.shape}")
print(f"✓ Periodo: {df.index.min()} a {df.index.max()}")
print(f"✓ Titoli: {len(titoli_list)}")

# ============================================================================
# FASE 2: FILTRAGGIO DATI PER BACKTEST (01.01.2025 - 24.04.2026)
# ============================================================================
print("\n[FASE 2] FILTRAGGIO PERIODO BACKTEST")
print("-" * 100)

backtest_start = pd.Timestamp('2025-01-01')
backtest_end = pd.Timestamp('2026-04-24')

df_backtest = df[(df.index >= backtest_start) & (df.index <= backtest_end)].copy()
print(f"✓ Periodo backtest: {df_backtest.index.min()} a {df_backtest.index.max()}")
print(f"✓ Giorni trading disponibili: {len(df_backtest)}")

# ============================================================================
# FASE 3: CALCOLO INDICATORI
# ============================================================================
print("\n[FASE 3] CALCOLO INDICATORI")
print("-" * 100)

def calculate_indicators(df_prices):
    """Calcola RSI, MACD, Bollinger Bands, SMA per una serie di prezzi"""
    
    # RSI (14 giorni)
    delta = df_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    ema12 = df_prices.ewm(span=12, adjust=False).mean()
    ema26 = df_prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    
    # Bollinger Bands (20, 2)
    sma20 = df_prices.rolling(window=20).mean()
    std20 = df_prices.rolling(window=20).std()
    bb_upper = sma20 + (std20 * 2)
    bb_lower = sma20 - (std20 * 2)
    
    # SMA (50, 200)
    sma50 = df_prices.rolling(window=50).mean()
    sma200 = df_prices.rolling(window=200).mean()
    
    return {
        'RSI': rsi,
        'MACD': macd_line,
        'MACD_Signal': signal_line,
        'MACD_Hist': macd_histogram,
        'BB_Upper': bb_upper,
        'BB_Lower': bb_lower,
        'BB_Middle': sma20,
        'SMA50': sma50,
        'SMA200': sma200
    }

# Calcolo indicatori per ogni titolo
indicators_all = {}
for titolo in titoli_list:
    close_prices = df_backtest[f'{titolo}_Close'].copy()
    if len(close_prices) > 200:  # Almeno 200 giorni per SMA200
        indicators_all[titolo] = calculate_indicators(close_prices)

print(f"✓ Indicatori calcolati per {len(indicators_all)} titoli")

# ============================================================================
# FASE 4: GENERAZIONE SEGNALI
# ============================================================================
print("\n[FASE 4] GENERAZIONE SEGNALI DI TRADING")
print("-" * 100)

def generate_signals(indicators, rsi_oversold=30, rsi_overbought=70, macd_threshold=0):
    """
    Genera segnali BUY/SELL basati su indicatori
    
    BUY Signal:
    - RSI < 30 (oversold) + MACD positive
    - Prezzo tocca Bollinger Lower + SMA50 > SMA200 (uptrend)
    
    SELL Signal:
    - RSI > 70 (overbought) + MACD negative
    - Prezzo tocca Bollinger Upper + SMA50 < SMA200 (downtrend)
    """
    
    signals = pd.DataFrame(index=indicators['RSI'].index)
    signals['RSI'] = indicators['RSI']
    signals['MACD'] = indicators['MACD']
    signals['MACD_Hist'] = indicators['MACD_Hist']
    signals['Price_vs_BB_Upper'] = indicators['BB_Upper']
    signals['Price_vs_BB_Lower'] = indicators['BB_Lower']
    signals['SMA50'] = indicators['SMA50']
    signals['SMA200'] = indicators['SMA200']
    
    # Segnale BUY
    signals['BUY'] = (
        (signals['RSI'] < rsi_oversold) &  # RSI oversold
        (signals['MACD_Hist'] > macd_threshold) &  # MACD positive
        (signals['SMA50'] > signals['SMA200'])  # Trend up
    ).astype(int)
    
    # Segnale SELL
    signals['SELL'] = (
        (signals['RSI'] > rsi_overbought) &  # RSI overbought
        (signals['MACD_Hist'] < -macd_threshold) &  # MACD negative
        (signals['SMA50'] < signals['SMA200'])  # Trend down
    ).astype(int)
    
    # Consolidamento: se BUY e SELL contemporaneamente, no segnale
    signals.loc[signals['BUY'] == 1 & signals['SELL'] == 1, 'BUY'] = 0
    signals.loc[signals['BUY'] == 1 & signals['SELL'] == 1, 'SELL'] = 0
    
    return signals

# Generazione segnali per ogni titolo
signals_all = {}
for titolo, indicators in indicators_all.items():
    signals_all[titolo] = generate_signals(indicators)

print(f"✓ Segnali generati per {len(signals_all)} titoli")

# Statistiche segnali
total_buy_signals = sum([signals_all[t]['BUY'].sum() for t in signals_all])
total_sell_signals = sum([signals_all[t]['SELL'].sum() for t in signals_all])
print(f"✓ Totale segnali BUY: {total_buy_signals}")
print(f"✓ Totale segnali SELL: {total_sell_signals}")

# ============================================================================
# FASE 5: BACKTESTING
# ============================================================================
print("\n[FASE 5] BACKTESTING STRATEGIA")
print("-" * 100)

class BacktestEngine:
    def __init__(self, initial_capital=100000, commission=19, max_positions=10):
        self.initial_capital = initial_capital
        self.commission = commission
        self.max_positions = max_positions
        self.cash = initial_capital
        self.positions = {}  # {titolo: {'shares': N, 'entry_price': P, 'entry_date': D}}
        self.closed_trades = []
        self.portfolio_value = [initial_capital]
        self.equity_curve = [initial_capital]
        self.dates = []
        
    def calculate_portfolio_value(self, current_prices):
        """Calcola valore totale portfolio"""
        positions_value = sum([
            self.positions[t]['shares'] * current_prices.get(f'{t}_Close', 0)
            for t in self.positions
        ])
        return self.cash + positions_value
    
    def enter_position(self, titolo, price, date, shares=100):
        """Apre una posizione LONG"""
        cost = shares * price + self.commission
        if self.cash >= cost and len(self.positions) < self.max_positions:
            self.positions[titolo] = {
                'shares': shares,
                'entry_price': price,
                'entry_date': date
            }
            self.cash -= cost
            return True
        return False
    
    def exit_position(self, titolo, price, date):
        """Chiude una posizione"""
        if titolo in self.positions:
            pos = self.positions[titolo]
            revenue = pos['shares'] * price - self.commission
            pnl = revenue - (pos['shares'] * pos['entry_price'] + self.commission)
            pnl_pct = (pnl / (pos['shares'] * pos['entry_price'])) * 100
            
            self.cash += revenue
            self.closed_trades.append({
                'Titolo': titolo,
                'EntryDate': pos['entry_date'],
                'EntryPrice': pos['entry_price'],
                'ExitDate': date,
                'ExitPrice': price,
                'Shares': pos['shares'],
                'PnL': pnl,
                'PnL%': pnl_pct,
                'Days': (date - pos['entry_date']).days
            })
            del self.positions[titolo]
            return True
        return False
    
    def run_backtest(self, df_backtest, signals_all):
        """Esegue il backtest"""
        for date in df_backtest.index:
            current_prices = df_backtest.loc[date]
            
            # Genera segnali per questo giorno
            for titolo in signals_all:
                if date in signals_all[titolo].index:
                    signal_row = signals_all[titolo].loc[date]
                    price = current_prices.get(f'{titolo}_Close', np.nan)
                    
                    if not np.isnan(price):
                        # BUY Signal
                        if signal_row['BUY'] == 1 and titolo not in self.positions:
                            self.enter_position(titolo, price, date)
                        
                        # SELL Signal
                        if signal_row['SELL'] == 1 and titolo in self.positions:
                            self.exit_position(titolo, price, date)
            
            # Record equity
            portfolio_val = self.calculate_portfolio_value(current_prices)
            self.equity_curve.append(portfolio_val)
            self.dates.append(date)
        
        return self.equity_curve, self.closed_trades

# Esecuzione backtest
engine = BacktestEngine(initial_capital=100000, commission=19, max_positions=10)
equity_curve, closed_trades = engine.run_backtest(df_backtest, signals_all)

print(f"✓ Backtest completato")
print(f"✓ Trade chiusi: {len(closed_trades)}")
print(f"✓ Posizioni aperte: {len(engine.positions)}")

# ============================================================================
# FASE 6: STATISTICHE BACKTEST
# ============================================================================
print("\n[FASE 6] STATISTICHE BACKTEST")
print("-" * 100)

df_trades = pd.DataFrame(closed_trades)

initial_capital = 100000
final_equity = engine.equity_curve[-1]
total_return = final_equity - initial_capital
total_return_pct = (total_return / initial_capital) * 100

print(f"\n📊 PERFORMANCE BACKTEST:")
print(f"   Capitale Iniziale: €{initial_capital:,.2f}")
print(f"   Capitale Finale: €{final_equity:,.2f}")
print(f"   Profitto Totale: €{total_return:,.2f}")
print(f"   Profitto %: {total_return_pct:.2f}%")

if len(df_trades) > 0:
    print(f"\n📈 STATISTICHE TRADE:")
    print(f"   Trade Chiusi: {len(df_trades)}")
    print(f"   Trade Profittevoli: {len(df_trades[df_trades['PnL'] > 0])}")
    print(f"   Trade in Perdita: {len(df_trades[df_trades['PnL'] < 0])}")
    print(f"   Win Rate: {(len(df_trades[df_trades['PnL'] > 0]) / len(df_trades)) * 100:.2f}%")
    
    print(f"\n💰 METRICHE PnL:")
    print(f"   PnL Medio: €{df_trades['PnL'].mean():.2f}")
    print(f"   PnL Max: €{df_trades['PnL'].max():.2f}")
    print(f"   PnL Min: €{df_trades['PnL'].min():.2f}")
    print(f"   PnL% Medio: {df_trades['PnL%'].mean():.2f}%")
    
    print(f"\n📅 HOLDING:")
    print(f"   Giorni Medi: {df_trades['Days'].mean():.1f}")
    print(f"   Giorni Min: {df_trades['Days'].min()}")
    print(f"   Giorni Max: {df_trades['Days'].max()}")

# Calcolo Drawdown
equity_array = np.array(engine.equity_curve)
running_max = np.maximum.accumulate(equity_array)
drawdown = (equity_array - running_max) / running_max * 100
max_drawdown = drawdown.min()

print(f"\n📉 RISK METRICS:")
print(f"   Max Drawdown: {max_drawdown:.2f}%")
print(f"   Volatilità: {np.std(np.diff(equity_array) / equity_array[:-1]) * 100:.2f}%")

# Sharpe Ratio
returns = np.diff(equity_array) / equity_array[:-1]
sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
print(f"   Sharpe Ratio: {sharpe_ratio:.3f}")

# ============================================================================
# FASE 7: EXPORT RISULTATI
# ============================================================================
print("\n[FASE 7] EXPORT RISULTATI")
print("-" * 100)

# Export trade chiusi
df_trades_export = df_trades.copy()
df_trades_export.to_csv('backtest_trades.csv', index=False)
print(f"✓ Export: backtest_trades.csv")

# Export equity curve
df_equity = pd.DataFrame({
    'Date': engine.dates,
    'Equity': engine.equity_curve[1:]  # Skip primo valore
})
df_equity.to_csv('equity_curve.csv', index=False)
print(f"✓ Export: equity_curve.csv")

# Export segnali attuali (ultimi 30 giorni)
signals_summary = []
for titolo in signals_all:
    last_date = signals_all[titolo].index[-1]
    last_signal = signals_all[titolo].iloc[-1]
    buy_signal = last_signal['BUY']
    sell_signal = last_signal['SELL']
    rsi = last_signal['RSI']
    macd = last_signal['MACD']
    
    signals_summary.append({
        'Titolo': titolo,
        'Data': last_date,
        'RSI': rsi,
        'MACD': macd,
        'BUY': buy_signal,
        'SELL': sell_signal
    })

df_signals = pd.DataFrame(signals_summary)
df_signals = df_signals.sort_values('Date', ascending=False)
df_signals.to_csv('current_signals.csv', index=False)
print(f"✓ Export: current_signals.csv")

# ============================================================================
# FASE 8: VISUALIZZAZIONI
# ============================================================================
print("\n[FASE 8] VISUALIZZAZIONI")
print("-" * 100)

try:
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # 1. Equity Curve
    ax1 = axes[0]
    ax1.plot(engine.dates, engine.equity_curve[1:], linewidth=2.5, color='darkblue', label='Equity')
    ax1.axhline(y=initial_capital, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.fill_between(engine.dates, initial_capital, engine.equity_curve[1:], 
                     where=[e >= initial_capital for e in engine.equity_curve[1:]], 
                     alpha=0.2, color='green', label='Profit')
    ax1.fill_between(engine.dates, initial_capital, engine.equity_curve[1:], 
                     where=[e < initial_capital for e in engine.equity_curve[1:]], 
                     alpha=0.2, color='red', label='Loss')
    ax1.set_title(f'Equity Curve - Backtest {df_backtest.index.min().date()} a {df_backtest.index.max().date()}', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity (€)', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # 2. Drawdown
    ax2 = axes[1]
    ax2.fill_between(engine.dates, 0, drawdown[1:], alpha=0.3, color='red')
    ax2.plot(engine.dates, drawdown[1:], linewidth=2, color='darkred', label='Drawdown')
    ax2.set_title('Drawdown %', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown %', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Data', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower right')
    
    plt.tight_layout()
    plt.savefig('backtest_results.png', dpi=150, bbox_inches='tight')
    print(f"✓ Grafico salvato: backtest_results.png")
    plt.close()
    
except Exception as e:
    print(f"✗ Errore nella creazione del grafico: {e}")

# ============================================================================
# SUMMARY FINALE
# ============================================================================
print("\n\n" + "=" * 100)
print("SUMMARY BACKTEST - KEY FINDINGS")
print("=" * 100)

print(f"\n💼 BACKTEST SUMMARY:")
print(f"   Periodo: {df_backtest.index.min().date()} a {df_backtest.index.max().date()}")
print(f"   Giorni Trading: {len(df_backtest)}")
print(f"   Titoli Analizzati: {len(signals_all)}")

print(f"\n💰 PROFITTO:")
print(f"   Capitale Iniziale: €{initial_capital:,.2f}")
print(f"   Capitale Finale: €{final_equity:,.2f}")
print(f"   Profitto: €{total_return:,.2f} ({total_return_pct:.2f}%)")

print(f"\n📊 PERFORMANCE METRICHE:")
print(f"   Max Drawdown: {max_drawdown:.2f}%")
print(f"   Sharpe Ratio: {sharpe_ratio:.3f}")
print(f"   Trade Totali Chiusi: {len(df_trades)}")
if len(df_trades) > 0:
    print(f"   Win Rate: {(len(df_trades[df_trades['PnL'] > 0]) / len(df_trades)) * 100:.2f}%")
    print(f"   PnL Medio: €{df_trades['PnL'].mean():.2f}")

print(f"\n⭐ PROSSIMI STEP:")
print(f"   1. Analizzare i trade chiusi (backtest_trades.csv)")
print(f"   2. Verificare equity curve (equity_curve.csv)")
print(f"   3. Controllare segnali attuali (current_signals.csv)")
print(f"   4. Discutere ottimizzazioni e parametri")

print("\n" + "=" * 100)
print(f"✓ ANALISI COMPLETATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

print("\n✓ Output disponibili:")
print("  - backtest_trades.csv (dettagli di tutti i trade)")
print("  - equity_curve.csv (andamento capitale)")
print("  - current_signals.csv (segnali attuali)")
print("  - backtest_results.png (grafici equity e drawdown)")
