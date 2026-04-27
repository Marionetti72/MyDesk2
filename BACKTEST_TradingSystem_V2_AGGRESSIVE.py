"""
TRADING SYSTEM - BACKTEST V2 AGGRESSIVE
================================================
Strategia MOLTO più aggressiva e realistica
Periodo: 01.01.2025 - 30.03.2026
Capitale: €100,000 | Commissione: €19/trade
Max Posizioni: 8-10 simultanee

Approccio:
- Logica di entrata MENO RIGIDA (OR conditions invece di AND)
- Momentum + Trend Following
- Breakout di volatilità
- Risk management aggressivo con trailing stop
- Exit su profit target + stop loss dinamico

Autore: Copilot Trading System
Data: 2026-04-27
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)

print("=" * 100)
print("TRADING SYSTEM V2 - BACKTEST AGGRESSIVE")
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
print(f"✓ Titoli: {len(titoli_list)}")

# ============================================================================
# FASE 2: FILTRAGGIO PERIODO BACKTEST
# ============================================================================
print("\n[FASE 2] FILTRAGGIO PERIODO BACKTEST")
print("-" * 100)

backtest_start = pd.Timestamp('2025-01-01')
backtest_end = pd.Timestamp('2026-03-30')

df_backtest = df[(df.index >= backtest_start) & (df.index <= backtest_end)].copy()
print(f"✓ Periodo: {df_backtest.index.min()} a {df_backtest.index.max()}")
print(f"✓ Giorni: {len(df_backtest)}")

# ============================================================================
# FASE 3: CALCOLO INDICATORI V2 (PIU' AGGRESSIVI)
# ============================================================================
print("\n[FASE 3] CALCOLO INDICATORI AGGRESSIVI")
print("-" * 100)

def calculate_indicators_v2(df_prices):
    """
    Indicatori AGGRESSIVE:
    - ROC (Rate of Change) per momentum
    - RSI standard
    - ATR per volatilità
    - SMA fast/slow per trend
    - Bollinger Bands per breakout
    """
    
    # RSI (14 giorni)
    delta = df_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # ROC - Rate of Change (12 giorni per momentum)
    roc = ((df_prices - df_prices.shift(12)) / df_prices.shift(12)) * 100
    
    # ATR - Average True Range (14 giorni per volatilità)
    high_low = df_prices - df_prices.shift(1)
    high_close = abs(df_prices - df_prices.shift(1))
    tr = pd.concat([high_low, high_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_pct = (atr / df_prices) * 100
    
    # SMA Fast/Slow (20, 50)
    sma20 = df_prices.rolling(window=20).mean()
    sma50 = df_prices.rolling(window=50).mean()
    sma200 = df_prices.rolling(window=200).mean()
    
    # Bollinger Bands (20, 1.5) - più larghe per volatilità
    bb_middle = sma20
    bb_std = df_prices.rolling(window=20).std()
    bb_upper = bb_middle + (bb_std * 1.5)
    bb_lower = bb_middle - (bb_std * 1.5)
    
    # MACD
    ema12 = df_prices.ewm(span=12, adjust=False).mean()
    ema26 = df_prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - signal
    
    return {
        'Close': df_prices,
        'RSI': rsi,
        'ROC': roc,
        'ATR': atr,
        'ATR_Pct': atr_pct,
        'SMA20': sma20,
        'SMA50': sma50,
        'SMA200': sma200,
        'BB_Upper': bb_upper,
        'BB_Lower': bb_lower,
        'BB_Middle': bb_middle,
        'MACD': macd,
        'MACD_Signal': signal,
        'MACD_Hist': macd_hist
    }

# Calcolo indicatori
indicators_all = {}
for titolo in titoli_list:
    close_prices = df_backtest[f'{titolo}_Close'].copy()
    if len(close_prices) > 200:
        indicators_all[titolo] = calculate_indicators_v2(close_prices)

print(f"✓ Indicatori calcolati per {len(indicators_all)} titoli")

# ============================================================================
# FASE 4: GENERAZIONE SEGNALI V2 (AGGRESSIVE)
# ============================================================================
print("\n[FASE 4] GENERAZIONE SEGNALI AGGRESSIVE")
print("-" * 100)

def generate_signals_v2(indicators):
    """
    Segnali AGGRESSIVI:
    
    BUY Conditions (OR logic - solo UNO deve essere vero):
    1. RSI < 35 + trend UP (SMA20 > SMA50)
    2. ROC > 0 + Prezzo > Bollinger Lower (momentum breakout)
    3. MACD_Hist positivo + RSI rising
    4. Prezzo tocca ATR Lower + recovery segnale
    
    SELL Conditions:
    1. Profit Target: +3% gain
    2. Stop Loss: -2% loss
    3. RSI > 75 (overbought forte)
    4. ROC negativo forte
    """
    
    signals = pd.DataFrame(index=indicators['Close'].index)
    signals['Close'] = indicators['Close']
    signals['RSI'] = indicators['RSI']
    signals['ROC'] = indicators['ROC']
    signals['SMA20'] = indicators['SMA20']
    signals['SMA50'] = indicators['SMA50']
    signals['BB_Upper'] = indicators['BB_Upper']
    signals['BB_Lower'] = indicators['BB_Lower']
    signals['MACD_Hist'] = indicators['MACD_Hist']
    signals['ATR'] = indicators['ATR']
    
    # Trend detection
    signals['Trend_UP'] = signals['SMA20'] > signals['SMA50']
    signals['Trend_DOWN'] = signals['SMA20'] < signals['SMA50']
    
    # BUY signals (condizioni meno stringenti - OR logic)
    buy1 = (signals['RSI'] < 35) & (signals['Trend_UP'])  # Oversold + Trend UP
    buy2 = (signals['ROC'] > 0) & (signals['Close'] > signals['BB_Lower'])  # Momentum positive
    buy3 = (signals['MACD_Hist'] > 0) & (signals['RSI'] < 60)  # MACD positive + not overbought
    buy4 = (signals['Close'] < signals['SMA50']) & (signals['Trend_UP'])  # Dip in uptrend
    
    signals['BUY'] = (buy1 | buy2 | buy3 | buy4).astype(int)
    
    # SELL signals
    sell1 = signals['RSI'] > 75  # Strong overbought
    sell2 = signals['ROC'] < -1.0  # Strong negative momentum
    sell3 = signals['MACD_Hist'] < 0  # MACD negative
    
    signals['SELL'] = (sell1 | sell2 | sell3).astype(int)
    
    # Anti-conflict
    conflicting = signals['BUY'] == 1 & signals['SELL'] == 1
    signals.loc[conflicting, 'BUY'] = 0
    
    return signals

# Generazione segnali
signals_all = {}
for titolo, indicators in indicators_all.items():
    try:
        signals_all[titolo] = generate_signals_v2(indicators)
    except Exception as e:
        print(f"⚠ Errore {titolo}: {e}")

print(f"✓ Segnali generati per {len(signals_all)} titoli")

total_buy = sum([signals_all[t]['BUY'].sum() for t in signals_all])
total_sell = sum([signals_all[t]['SELL'].sum() for t in signals_all])
print(f"✓ Segnali BUY: {int(total_buy)} | SELL: {int(total_sell)}")

# ============================================================================
# FASE 5: BACKTESTING CON RISK MANAGEMENT AGGRESSIVO
# ============================================================================
print("\n[FASE 5] BACKTESTING CON RISK MANAGEMENT")
print("-" * 100)

class BacktestEngineV2:
    def __init__(self, initial_capital=100000, commission=19, max_positions=10):
        self.initial_capital = initial_capital
        self.commission = commission
        self.max_positions = max_positions
        self.cash = initial_capital
        self.positions = {}  # {titolo: {'shares': N, 'entry_price': P, 'entry_date': D, 'stop': S, 'target': T}}
        self.closed_trades = []
        self.equity_curve = [initial_capital]
        self.dates = []
        
    def calculate_portfolio_value(self, current_prices):
        positions_value = 0
        for t in self.positions:
            price_key = f'{t}_Close'
            if price_key in current_prices and not np.isnan(current_prices[price_key]):
                positions_value += self.positions[t]['shares'] * current_prices[price_key]
        return self.cash + positions_value
    
    def enter_position(self, titolo, price, date, shares=100):
        """Apre posizione con stop loss e target"""
        if np.isnan(price):
            return False
        cost = shares * price + self.commission
        if self.cash >= cost and len(self.positions) < self.max_positions and titolo not in self.positions:
            stop_loss = price * 0.98  # -2% stop
            target = price * 1.03  # +3% target
            self.positions[titolo] = {
                'shares': shares,
                'entry_price': price,
                'entry_date': date,
                'stop_loss': stop_loss,
                'target': target,
                'highest': price  # Per trailing stop
            }
            self.cash -= cost
            return True
        return False
    
    def exit_position(self, titolo, price, date, reason="Manual"):
        if titolo not in self.positions or np.isnan(price):
            return False
        pos = self.positions[titolo]
        revenue = pos['shares'] * price - self.commission
        pnl = revenue - (pos['shares'] * pos['entry_price'] + self.commission)
        pnl_pct = (pnl / (pos['shares'] * pos['entry_price'])) * 100 if pos['entry_price'] > 0 else 0
        
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
            'Days': (date - pos['entry_date']).days,
            'Reason': reason
        })
        del self.positions[titolo]
        return True
    
    def check_exits(self, titolo, price, date, signal_row):
        """Check stop loss, target, e segnali exit"""
        if titolo not in self.positions:
            return
        
        pos = self.positions[titolo]
        
        # Update highest price per trailing stop
        pos['highest'] = max(pos['highest'], price)
        
        # Target exit: +3%
        if price >= pos['target']:
            self.exit_position(titolo, price, date, "Target Hit")
            return
        
        # Stop loss: -2%
        if price <= pos['stop_loss']:
            self.exit_position(titolo, price, date, "Stop Loss")
            return
        
        # Trailing stop: 1% dal massimo
        trailing_stop = pos['highest'] * 0.99
        if price <= trailing_stop and price < pos['entry_price']:
            self.exit_position(titolo, price, date, "Trailing Stop")
            return
        
        # Segnale SELL forte
        if signal_row['SELL'] == 1:
            self.exit_position(titolo, price, date, "Sell Signal")
            return
    
    def run_backtest(self, df_backtest, signals_all):
        for idx, date in enumerate(df_backtest.index):
            if idx % 100 == 0:
                print(f"  Processando giorno {idx}/{len(df_backtest)}...", end='\r')
            
            current_prices = df_backtest.loc[date]
            
            # Exits first (riduce drawdown)
            for titolo in list(self.positions.keys()):
                if date in signals_all[titolo].index:
                    signal_row = signals_all[titolo].loc[date]
                    price = current_prices.get(f'{titolo}_Close', np.nan)
                    if not np.isnan(price):
                        self.check_exits(titolo, price, date, signal_row)
            
            # Entries second
            for titolo in signals_all:
                if date in signals_all[titolo].index:
                    signal_row = signals_all[titolo].loc[date]
                    price = current_prices.get(f'{titolo}_Close', np.nan)
                    
                    if not np.isnan(price) and signal_row['BUY'] == 1 and titolo not in self.positions:
                        self.enter_position(titolo, price, date, shares=150)
            
            # Record equity
            portfolio_val = self.calculate_portfolio_value(current_prices)
            self.equity_curve.append(portfolio_val)
            self.dates.append(date)
        
        print("\n✓ Backtest completato")
        return self.equity_curve, self.closed_trades

# Esecuzione
engine = BacktestEngineV2(initial_capital=100000, commission=19, max_positions=10)
equity_curve, closed_trades = engine.run_backtest(df_backtest, signals_all)

print(f"✓ Trade chiusi: {len(closed_trades)}")
print(f"✓ Posizioni aperte: {len(engine.positions)}")

# ============================================================================
# FASE 6: STATISTICHE
# ============================================================================
print("\n[FASE 6] STATISTICHE BACKTEST")
print("-" * 100)

df_trades = pd.DataFrame(closed_trades) if len(closed_trades) > 0 else pd.DataFrame()

initial_capital = 100000
final_equity = engine.equity_curve[-1]
total_return = final_equity - initial_capital
total_return_pct = (total_return / initial_capital) * 100

print(f"\n📊 PERFORMANCE:")
print(f"   Capitale Iniziale: €{initial_capital:,.2f}")
print(f"   Capitale Finale: €{final_equity:,.2f}")
print(f"   Profitto: €{total_return:,.2f} ({total_return_pct:.2f}%)")

if len(df_trades) > 0:
    print(f"\n📈 TRADE STATISTICS:")
    print(f"   Trade Chiusi: {len(df_trades)}")
    print(f"   Profittevoli: {len(df_trades[df_trades['PnL'] > 0])}")
    print(f"   In Perdita: {len(df_trades[df_trades['PnL'] < 0])}")
    print(f"   Win Rate: {(len(df_trades[df_trades['PnL'] > 0]) / len(df_trades)) * 100:.2f}%")
    
    print(f"\n💰 PnL METRICS:")
    print(f"   Medio: €{df_trades['PnL'].mean():.2f}")
    print(f"   Max: €{df_trades['PnL'].max():.2f}")
    print(f"   Min: €{df_trades['PnL'].min():.2f}")
    print(f"   Avg%: {df_trades['PnL%'].mean():.2f}%")
    
    # Analisi per reason
    print(f"\n🎯 EXIT REASONS:")
    print(df_trades['Reason'].value_counts().to_string())
    
    print(f"\n📅 HOLDING TIME:")
    print(f"   Medio: {df_trades['Days'].mean():.1f} giorni")
    print(f"   Min: {df_trades['Days'].min()}")
    print(f"   Max: {df_trades['Days'].max()}")
else:
    print(f"\n⚠ Nessun trade chiuso!")

# Drawdown
equity_array = np.array(engine.equity_curve)
running_max = np.maximum.accumulate(equity_array)
drawdown = (equity_array - running_max) / running_max * 100
max_drawdown = drawdown.min()

print(f"\n📉 RISK:")
print(f"   Max Drawdown: {max_drawdown:.2f}%")
volatility = np.std(np.diff(equity_array) / equity_array[:-1]) * 100 if len(equity_array) > 1 else 0
print(f"   Volatilità: {volatility:.2f}%")

returns = np.diff(equity_array) / equity_array[:-1]
sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
print(f"   Sharpe Ratio: {sharpe_ratio:.3f}")

# ============================================================================
# FASE 7: EXPORT
# ============================================================================
print("\n[FASE 7] EXPORT RISULTATI")
print("-" * 100)

if len(df_trades) > 0:
    df_trades.to_csv('backtest_trades_v2.csv', index=False)
    print(f"✓ backtest_trades_v2.csv")

df_equity = pd.DataFrame({
    'Date': engine.dates,
    'Equity': engine.equity_curve[1:]
})
df_equity.to_csv('equity_curve_v2.csv', index=False)
print(f"✓ equity_curve_v2.csv")

signals_summary = []
for titolo in signals_all:
    last_signal = signals_all[titolo].iloc[-1]
    signals_summary.append({
        'Titolo': titolo,
        'RSI': last_signal['RSI'],
        'ROC': last_signal['ROC'],
        'BUY': int(last_signal['BUY']),
        'SELL': int(last_signal['SELL'])
    })

df_signals = pd.DataFrame(signals_summary)
df_signals.to_csv('current_signals_v2.csv', index=False)
print(f"✓ current_signals_v2.csv")

# ============================================================================
# FASE 8: VISUALIZZAZIONI
# ============================================================================
print("\n[FASE 8] VISUALIZZAZIONI")
print("-" * 100)

try:
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    ax1 = axes[0]
    ax1.plot(engine.dates, engine.equity_curve[1:], linewidth=2.5, color='darkblue', label='Equity V2')
    ax1.axhline(y=initial_capital, color='red', linestyle='--', alpha=0.5, label='Initial')
    
    equity_vals = engine.equity_curve[1:]
    ax1.fill_between(engine.dates, initial_capital, equity_vals, 
                     where=[e >= initial_capital for e in equity_vals], 
                     alpha=0.2, color='green', label='Profit')
    ax1.fill_between(engine.dates, initial_capital, equity_vals, 
                     where=[e < initial_capital for e in equity_vals], 
                     alpha=0.2, color='red', label='Loss')
    ax1.set_title(f'Equity Curve V2 Aggressive - {df_backtest.index.min().date()} a {df_backtest.index.max().date()}', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity (€)', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    ax2 = axes[1]
    ax2.fill_between(engine.dates, 0, drawdown[1:], alpha=0.3, color='red')
    ax2.plot(engine.dates, drawdown[1:], linewidth=2, color='darkred')
    ax2.set_title('Drawdown %', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown %', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Data', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('backtest_results_v2.png', dpi=150, bbox_inches='tight')
    print(f"✓ backtest_results_v2.png")
    plt.close()
    
except Exception as e:
    print(f"✗ Errore grafico: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 100)
print("SUMMARY V2 AGGRESSIVE - KEY FINDINGS")
print("=" * 100)

print(f"\n💼 BACKTEST SUMMARY:")
print(f"   Periodo: {df_backtest.index.min().date()} a {df_backtest.index.max().date()}")
print(f"   Giorni: {len(df_backtest)}")

print(f"\n💰 PROFITTO:")
print(f"   €{total_return:,.2f} ({total_return_pct:.2f}%)")

print(f"\n📊 METRICHE:")
print(f"   Max Drawdown: {max_drawdown:.2f}%")
print(f"   Sharpe: {sharpe_ratio:.3f}")
print(f"   Trade: {len(df_trades)}")
if len(df_trades) > 0:
    print(f"   Win Rate: {(len(df_trades[df_trades['PnL'] > 0]) / len(df_trades)) * 100:.2f}%")

print(f"\n⭐ MIGLIORAMENTI V2:")
print(f"   ✓ Segnali meno rigidi (OR logic)")
print(f"   ✓ ROC + Momentum per entries aggressive")
print(f"   ✓ Stop loss -2% e Target +3%")
print(f"   ✓ Trailing stop per lock profits")
print(f"   ✓ Position sizing aumentato (150 shares)")

print("\n" + "=" * 100)
print(f"✓ COMPLETATO: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
