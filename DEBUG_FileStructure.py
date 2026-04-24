"""
DEBUG SCRIPT - Verifica struttura file Excel
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("DEBUG - LETTURA STRUTTURA FILE EXCEL")
print("=" * 80)

# Caricamento senza header per vedere la struttura grezza
try:
    df_raw = pd.read_excel("DatiEoD.xlsx", sheet_name='DATA', header=None)
    print(f"\n✓ File caricato correttamente")
    print(f"✓ Shape: {df_raw.shape}")
    
    print("\n" + "=" * 80)
    print("PRIME 5 RIGHE E PRIME 30 COLONNE (RAW)")
    print("=" * 80)
    print(df_raw.iloc[0:5, 0:30].to_string())
    
    print("\n" + "=" * 80)
    print("NOMI COLONNE RILEVATE (Riga 1 - indice 0)")
    print("=" * 80)
    print(df_raw.iloc[0, :].to_string())
    
    print("\n" + "=" * 80)
    print("NOMI CAMPI (Riga 2 - indice 1)")
    print("=" * 80)
    print(df_raw.iloc[1, :].to_string())
    
    print("\n" + "=" * 80)
    print("DATI ESEMPIO (Riga 3 - indice 2)")
    print("=" * 80)
    print(df_raw.iloc[2, :].to_string())
    
    print("\n" + "=" * 80)
    print("COLONNE NON-NULL (Riga 1)")
    print("=" * 80)
    header_row = df_raw.iloc[0, :]
    non_null_cols = header_row[header_row.notna()].to_dict()
    for col_idx, titolo in non_null_cols.items():
        print(f"Colonna {col_idx}: {titolo}")
    
    print("\n" + "=" * 80)
    print("COLONNE DATAFRAME FINALE")
    print("=" * 80)
    print(f"Totale colonne: {len(df_raw.columns)}")
    print(f"Colonne: {list(df_raw.columns[:20])}...")

except Exception as e:
    print(f"✗ Errore: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✓ DEBUG COMPLETATO")
print("=" * 80)
