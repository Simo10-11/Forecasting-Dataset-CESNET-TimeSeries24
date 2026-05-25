# Dataset-CESNET-TimeSeries24
> Guida pratica per tesisti: dataset, libreria e codice per esperimenti di **forecasting del traffico di rete**.

---

## Indice

1. [Il Dataset: CESNET-TimeSeries24](#1-il-dataset-cesnet-timeseries24)
2. [Features del Dataset](#2-features-del-dataset)
3. [La Libreria: CESNET TS-Zoo](#3-la-libreria-cesnet-ts-zoo)
4. [Installazione](#4-installazione)
5. [Setup Base per il Forecasting](#5-setup-base-per-il-forecasting)
6. [Preprocessing](#6-preprocessing)
7. [Pipeline Completa di Forecasting](#7-pipeline-completa-di-forecasting)
8. [Benchmark Predefiniti](#8-benchmark-predefiniti)
9. [Esportare e Importare Configurazioni](#9-esportare-e-importare-configurazioni)
10. [Metriche di Valutazione](#10-metriche-di-valutazione)
11. [Note per Federated Learning](#11-note-per-federated-learning)

---

## 1. Il Dataset: CESNET-TimeSeries24

Il **CESNET-TimeSeries24** è un dataset reale di traffico di rete raccolto dalla rete ISP accademica ceca **CESNET3**, che fornisce accesso a Internet a istituzioni pubbliche e di ricerca in tutta la Repubblica Ceca (~500.000 utenti giornalieri).

### Statistiche chiave

| Proprietà | Valore |
|---|---|
| Durata della raccolta | **40 settimane** |
| IP address monitorati | **>275.000** |
| Istituzioni | **283** |
| Subnet istituzionali | **548** |
| IP flow totali | **66 miliardi** |
| Pacchetti totali | **4 trilioni** |
| Dati trasmessi | **~3.7 petabyte** |
| Metriche per time series | **12** |
| Granularità temporali | **3** (10 min, 1 ora, 1 giorno) |

### Livelli di aggregazione (`source_type`)

Il dataset offre time series a **tre livelli gerarchici**:

| `source_type` | Descrizione | N. entità |
|---|---|---|
| `"ips"` | Singoli indirizzi IP | >275.000 |
| `"institutions"` | Aggregato per istituzione | 283 |
| `"institution_subnets"` | Aggregato per subnet istituzionale | 548 |

> **💡 Consiglio per il forecasting:** Inizia con `"institutions"` (granularità oraria). Le time series istituzionali sono più regolari e meno sparse rispetto agli IP singoli.

### Granularità temporale (`aggregation`)

| `aggregation` | Intervallo | Timestep in 40 settimane | Use case |
|---|---|---|---|
| `"10_minutes"` | 10 min | ~40.320 | Anomaly detection fine-grained |
| `"1_hour"` | 1 ora | ~6.720 | **Forecasting (raccomandato)** |
| `"1_day"` | 1 giorno | ~280 | Trend analysis |

---

## 2. Features del Dataset

Ogni datapoint è un vettore di **12 metriche** calcolate aggregando i flow IP nell'intervallo temporale.

### Metriche Volumetriche Semplici

| Feature | Tipo | Descrizione |
|---|---|---|
| `n_flows` | int | Numero totale di IP flow nell'intervallo |
| `n_packets` | int | Numero totale di pacchetti trasmessi |
| `n_bytes` | int | Numero totale di byte trasmessi |

### Metriche Volumetriche Uniche

| Feature | Tipo | Descrizione |
|---|---|---|
| `n_dest_ip` | int | Numero di IP destinazione **unici** contattati |
| `n_dest_asn` | int | Numero di ASN (Autonomous System Number) destinazione unici |
| `n_dest_port` | int | Numero di porte di trasporto destinazione uniche |

### Metriche di Rapporto (Ratios)

| Feature | Tipo | Descrizione |
|---|---|---|
| `tcp_udp_ratio_packets` | float | Rapporto TCP/UDP a livello di pacchetti |
| `tcp_udp_ratio_bytes` | float | Rapporto TCP/UDP a livello di byte |
| `dir_ratio_packets` | float | Rapporto direzionale dei pacchetti (inbound/outbound) |
| `dir_ratio_bytes` | float | Rapporto direzionale dei byte (inbound/outbound) |

### Metriche Medie

| Feature | Tipo | Descrizione |
|---|---|---|
| `avg_duration` | float | Durata media dei flow (in secondi) |
| `avg_ttl` | float | Time To Live (TTL) medio dei pacchetti |

### Feature aggiuntiva

| Feature | Tipo | Descrizione |
|---|---|---|
| `id_time` | int | Identificatore univoco dell'intervallo temporale (usato internamente) |

> **💡 Per il forecasting:** Le feature più predittive e regolari sono tipicamente `n_flows`, `n_packets`, `n_bytes`. Le ratio e le medie sono più rumorose a livello di singolo IP ma più stabili a livello istituzionale.

---

## 3. La Libreria: CESNET TS-Zoo

**TS-Zoo** è una libreria Python che gestisce tutto il ciclo di vita degli esperimenti con il dataset CESNET-TimeSeries24:

```
Download → Configurazione → Splitting → Preprocessing → Output (DataFrame / NumPy / DataLoader)
```

### Architettura della libreria

```
cesnet_tszoo/
├── datasets/          # Classi dataset (CESNET_TimeSeries24, CESNET_AGG23)
├── configs/           # Configurazioni (TimeBasedConfig, SeriesBasedConfig, DisjointTimeBasedConfig)
├── benchmarks/        # Benchmark predefiniti caricabili via hash
└── preprocesses/
    ├── transformers/  # Scaler (StandardScaler, MinMax, Robust, ...)
    ├── fillers/       # Gap filling (Forward, Mean, Linear interpolation, ...)
    └── handlers/      # Anomaly handling (Z-score, IQR, ...)
```

### Strategie di splitting disponibili

| Config | Quando usarla |
|---|---|
| `TimeBasedConfig` | **Forecasting** — split cronologico, tutti gli identificatori in tutti i set |
| `SeriesBasedConfig` | Classificazione, similarity search — split per entità |
| `DisjointTimeBasedConfig` | Valutazione della generalizzazione — split sia temporale che per entità |

### Formati di output supportati

| Metodo | Formato | Uso tipico |
|---|---|---|
| `get_train_df()` | `pandas.DataFrame` | Analisi esplorativa, modelli statistici |
| `get_train_numpy()` | `numpy.ndarray` | Sklearn, modelli classici |
| `get_train_dataloader()` | `torch.utils.data.DataLoader` | PyTorch, reti neurali, FL |

---

## 4. Installazione

```bash
pip install cesnet-tszoo
```

**Requisiti:** Python ≥ 3.10

**Dipendenze principali:** `pandas`, `numpy`, `torch`, `h5py`

---

## 5. Setup Base per il Forecasting

### 5.1 Inizializzazione del dataset

```python
from cesnet_tszoo.datasets import CESNET_TimeSeries24

# Al primo utilizzo: scarica automaticamente il file HDF5 (~GB) dallo storage S3
# Nei run successivi: carica direttamente dal path locale
dataset = CESNET_TimeSeries24.get_dataset(
    data_root="./data",              # Directory dove salvare/cercare il dataset
    source_type="institutions",      # Livello: "ips", "institutions", "institution_subnets"
    aggregation="1_hour",            # Granularità: "10_minutes", "1_hour", "1_day"
    dataset_type="time_based"        # Tipo di split da usare
)
```

### 5.2 Configurazione per il forecasting (TimeBasedConfig)

```python
from cesnet_tszoo.configs import TimeBasedConfig

config = TimeBasedConfig(
    # --- Selezione dati ---
    ts_ids=1.0,                          # Usa il 100% degli identificatori disponibili
    # ts_ids=[1, 5, 42, 100],            # oppure lista specifica di ID

    # --- Split temporale ---
    train_time_period=0.6,               # 60% del periodo temporale per training
    val_time_period=0.2,                 # 20% per validazione
    test_time_period=0.2,                # 20% per test

    # --- Metriche da includere ---
    features_to_take=["n_flows", "n_packets", "n_bytes"],  # None = tutte le 12

    # --- Sliding window per forecasting ---
    sliding_window_size=168,             # Lookback: 168 ore = 7 giorni di contesto
    sliding_window_prediction_size=24,   # Horizon: predici le prossime 24 ore
    sliding_window_step=1,               # Step: sposta la finestra di 1 timestep

    # --- Preprocessing ---
    nan_threshold=0.5,                   # Escludi time series con >50% di NaN
    fill_missing_with="forward_filler",  # Riempi i gap con il valore precedente
    handle_anomalies_with="z-score",     # Gestisci outlier con Z-score
    transform_with="standard_scaler",    # Normalizza (zero mean, unit variance)

    # --- Opzioni aggiuntive ---
    add_time=True,                       # Includi il timestamp nei dati
)
```

### 5.3 Applicare la configurazione e caricare i dati

```python
# Applica la config: questo scatena il preprocessing
dataset.set_dataset_config_and_initialize(config)

# --- Come DataFrame (analisi / modelli statistici) ---
train_df = dataset.get_train_df()
val_df   = dataset.get_val_df()
test_df  = dataset.get_test_df()

print(f"Train shape: {train_df.shape}")
print(train_df.head())

# --- Come NumPy array ---
train_X, train_y = dataset.get_train_numpy()  # (N, window, features), (N, horizon, features)

# --- Come PyTorch DataLoader (per reti neurali) ---
train_loader = dataset.get_train_dataloader(batch_size=64, num_workers=4)
val_loader   = dataset.get_val_dataloader(batch_size=64)
test_loader  = dataset.get_test_dataloader(batch_size=64)
```

---

## 6. Preprocessing

Il preprocessing viene applicato in automatico nell'ordine: **filtraggio → anomaly handling → gap filling → scaling → sliding window**.

### 6.1 Filtraggio

```python
config = TimeBasedConfig(
    # Filtra per percentuale massima di NaN (0.0 = nessun NaN tollerato, 1.0 = tutti accettati)
    nan_threshold=0.5,

    # Seleziona solo alcune feature
    features_to_take=["n_flows", "n_packets", "n_bytes", "n_dest_ip"],

    # Seleziona un sottoinsieme di identificatori
    ts_ids=0.5,        # 50% casuale degli ID
    # ts_ids=[1, 2, 3] # oppure lista esplicita
)
```

### 6.2 Anomaly Handling

```python
config = TimeBasedConfig(
    handle_anomalies_with="z-score",         # Z-score (media ± k*std)
    # handle_anomalies_with="iqr",           # Interquartile Range
    # handle_anomalies_with=MyCustomHandler, # classe personalizzata
)
```

### 6.3 Gap Filling

```python
config = TimeBasedConfig(
    default_values=0,                          # Valore di pre-riempimento
    fill_missing_with="forward_filler",        # Propaga il valore precedente
    # fill_missing_with="mean_filler",         # Media dei valori precedenti
    # fill_missing_with="linear_interpolation" # Interpolazione lineare
)
```

### 6.4 Scaling / Trasformazione

```python
config = TimeBasedConfig(
    transform_with="standard_scaler",    # Zero mean, unit variance  ← consigliato per NN
    # transform_with="min_max_scaler",   # Scala in [0, 1]
    # transform_with="robust_scaler",    # Mediana + IQR (robusto agli outlier)
    # transform_with="log_scaler",       # Trasformazione logaritmica
)
```

> ⚠️ Lo scaler viene **fittato solo sul training set** e applicato a val/test, evitando il data leakage.

---

## 7. Pipeline Completa di Forecasting

Di seguito una pipeline end-to-end con un modello LSTM in PyTorch.

```python
import torch
import torch.nn as nn
from cesnet_tszoo.datasets import CESNET_TimeSeries24
from cesnet_tszoo.configs import TimeBasedConfig

# ─────────────────────────────────────────────
# 1. Dataset & Config
# ─────────────────────────────────────────────
dataset = CESNET_TimeSeries24.get_dataset(
    data_root="./data",
    source_type="institutions",
    aggregation="1_hour",
    dataset_type="time_based"
)

config = TimeBasedConfig(
    ts_ids=1.0,
    train_time_period=0.6,
    val_time_period=0.2,
    test_time_period=0.2,
    features_to_take=["n_flows", "n_packets", "n_bytes"],
    sliding_window_size=168,          # 7 giorni lookback
    sliding_window_prediction_size=24,# 24 ore horizon
    sliding_window_step=1,
    nan_threshold=0.5,
    fill_missing_with="forward_filler",
    handle_anomalies_with="z-score",
    transform_with="standard_scaler",
)

dataset.set_dataset_config_and_initialize(config)

train_loader = dataset.get_train_dataloader(batch_size=64, num_workers=2)
val_loader   = dataset.get_val_dataloader(batch_size=64)
test_loader  = dataset.get_test_dataloader(batch_size=64)

# ─────────────────────────────────────────────
# 2. Modello LSTM
# ─────────────────────────────────────────────
class LSTMForecaster(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, horizon):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc   = nn.Linear(hidden_size, output_size * horizon)
        self.horizon = horizon
        self.output_size = output_size

    def forward(self, x):
        # x: (batch, seq_len, features)
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])                          # Prendi l'ultimo timestep
        return out.view(-1, self.horizon, self.output_size)   # (batch, horizon, features)

N_FEATURES = 3   # n_flows, n_packets, n_bytes
HORIZON    = 24
model = LSTMForecaster(
    input_size=N_FEATURES, hidden_size=128,
    num_layers=2, output_size=N_FEATURES, horizon=HORIZON
)

# ─────────────────────────────────────────────
# 3. Training loop
# ─────────────────────────────────────────────
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.MSELoss()
device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def train_epoch(loader):
    model.train()
    total_loss = 0
    for X, y in loader:
        X, y = X.to(device).float(), y.to(device).float()
        optimizer.zero_grad()
        pred = model(X)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def eval_epoch(loader):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for X, y in loader:
            X, y = X.to(device).float(), y.to(device).float()
            pred = model(X)
            total_loss += criterion(pred, y).item()
    return total_loss / len(loader)

EPOCHS = 20
for epoch in range(EPOCHS):
    train_loss = train_epoch(train_loader)
    val_loss   = eval_epoch(val_loader)
    print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train MSE: {train_loss:.4f} | Val MSE: {val_loss:.4f}")

# ─────────────────────────────────────────────
# 4. Valutazione finale sul test set
# ─────────────────────────────────────────────
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

model.eval()
all_preds, all_targets = [], []
with torch.no_grad():
    for X, y in test_loader:
        pred = model(X.to(device).float()).cpu().numpy()
        all_preds.append(pred)
        all_targets.append(y.numpy())

preds   = np.concatenate(all_preds)
targets = np.concatenate(all_targets)

mae  = mean_absolute_error(targets.reshape(-1), preds.reshape(-1))
rmse = np.sqrt(mean_squared_error(targets.reshape(-1), preds.reshape(-1)))
print(f"\nTest MAE:  {mae:.4f}")
print(f"Test RMSE: {rmse:.4f}")
```

---

## 8. Benchmark Predefiniti

TS-Zoo include benchmark standardizzati per il forecasting. Usarli garantisce **riproducibilità e comparabilità** con altri lavori.

```python
from cesnet_tszoo.benchmarks import load_benchmark

# Carica un benchmark predefinito tramite il suo hash identificativo
# (gli hash disponibili sono nella documentazione ufficiale)
benchmark = load_benchmark(
    "<benchmark_hash>",
    data_root="./data"
)

# Il dataset viene restituito già configurato e inizializzato
dataset = benchmark.get_initialized_dataset()

# I DataLoader sono pronti all'uso
train_loader = dataset.get_train_dataloader(batch_size=64)
val_loader   = dataset.get_val_dataloader(batch_size=64)
test_loader  = dataset.get_test_dataloader(batch_size=64)
```

> 📎 Lista dei benchmark disponibili: [cesnet.github.io/cesnet-tszoo/benchmarks](https://cesnet.github.io/cesnet-tszoo/benchmarks/)

---

## 9. Esportare e Importare Configurazioni

Fondamentale per la **riproducibilità** degli esperimenti (necessario per la tesi!).

```python
# ── Dopo aver configurato il dataset ──

# Salva la configurazione su file
dataset.save_config(identifier="esperimento_lstm_24h")
# → crea: esperimento_lstm_24h.json

# ── In un altro script / run ──

# Ricarica la configurazione identica
dataset.import_config(identifier="esperimento_lstm_24h")

# Il dataset riparte con la stessa identica configurazione
# (stesse partizioni, stesso preprocessing, stesso scaler fittato)
```

> 💡 **Tip:** Committa il file `.json` sul tuo repository Git insieme al codice. Chi vuole replicare i tuoi risultati non deve fare altro che clonare il repo e lanciare lo script.

---

## 10. Metriche di Valutazione

Le metriche standard usate in letteratura per il forecasting su questo dataset:

```python
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate(y_true, y_pred):
    y_true_flat = y_true.reshape(-1)
    y_pred_flat = y_pred.reshape(-1)

    mae  = mean_absolute_error(y_true_flat, y_pred_flat)
    mse  = mean_squared_error(y_true_flat, y_pred_flat)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_true_flat, y_pred_flat)

    # MAPE — attenzione: evita divisioni per zero su valori nulli
    mask = y_true_flat != 0
    mape = np.mean(np.abs((y_true_flat[mask] - y_pred_flat[mask]) / y_true_flat[mask])) * 100

    print(f"MAE:  {mae:.4f}")
    print(f"MSE:  {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")
    print(f"MAPE: {mape:.2f}%")
    return {"mae": mae, "mse": mse, "rmse": rmse, "r2": r2, "mape": mape}

results = evaluate(targets, preds)
```

> **Nota:** In letteratura (paper con CESNET-TimeSeries24) valori più bassi di RMSE/MAE e più alti di R² indicano prestazioni migliori.

---

## 11. Note per Federated Learning

Se il tuo obiettivo di tesi è applicare il **Federated Learning** al forecasting:

### Partizione dei dati tra client

```python
# Ogni istituzione → un client federato
# Usa SeriesBasedConfig per assegnare istituzioni diverse a train/val/test
from cesnet_tszoo.configs import SeriesBasedConfig

config = SeriesBasedConfig(
    time_period="all",
    train_ts=0.6,   # 60% delle istituzioni → client di training
    val_ts=0.2,     # 20% → client di validazione
    test_ts=0.2,    # 20% → client di test (mai visti in training)
    features_to_take=["n_flows", "n_packets", "n_bytes"],
    sliding_window_size=168,
    sliding_window_prediction_size=24,
    transform_with="standard_scaler",
)
```

### Ottenere i DataLoader per singola istituzione

```python
# Itera sugli ID delle istituzioni per costruire i DataLoader locali
for institution_id in dataset.train_ids:
    local_loader = dataset.get_train_dataloader(
        ts_ids=[institution_id],
        batch_size=32
    )
    # → addestra il modello locale del client con local_loader
```

### Raccomandazioni

| Aspetto | Raccomandazione |
|---|---|
| Aggregation level | `"institutions"` — dati più regolari, meno sparsità |
| Granularità temporale | `"1_hour"` — buon compromesso regolarità/dettaglio |
| Features iniziali | `n_flows`, `n_packets`, `n_bytes` |
| Scaler | `standard_scaler` — fittato localmente su ogni client |
| Splitting | `SeriesBasedConfig` per cross-silo FL |
| Riproducibilità | Salva sempre la config con `dataset.save_config()` |

---

## Riferimenti

- 📄 **Paper dataset:** Koumar et al., *CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting*, Scientific Data, 2025. [DOI](https://doi.org/10.1038/s41597-025-04603-x)
- 📄 **Paper libreria:** Kureš et al., *CESNET TS-Zoo: A Library for Reproducible Analysis of Network Traffic Time Series*, CNSM 2025.
- 📦 **GitHub:** [github.com/CESNET/cesnet-tszoo](https://github.com/CESNET/cesnet-tszoo)
- 📖 **Documentazione:** [cesnet.github.io/cesnet-tszoo](https://cesnet.github.io/cesnet-tszoo/)
- 🗃️ **Dataset su Zenodo:** [zenodo.org/records/13382427](https://zenodo.org/records/13382427)

