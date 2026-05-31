# Dataset-CESNET-TimeSeries24
> Guida pratica per tesisti: dataset, libreria e codice per esperimenti di **forecasting del traffico di rete**.

---

## Indice

1. [Il Dataset: CESNET-TimeSeries24](#1-il-dataset-cesnet-timeseries24)
2. [Features del Dataset](#2-features-del-dataset)
3. [La Libreria: CESNET TS-Zoo](#3-la-libreria-cesnet-ts-zoo)
4. [Installazione](#4-installazione)

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

## Riferimenti

- 📄 **Paper dataset:** Koumar et al., *CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting*, Scientific Data, 2025. [DOI](https://doi.org/10.1038/s41597-025-04603-x)
- 📄 **Paper libreria:** Kureš et al., *CESNET TS-Zoo: A Library for Reproducible Analysis of Network Traffic Time Series*, CNSM 2025.
- 📦 **GitHub:** [github.com/CESNET/cesnet-tszoo](https://github.com/CESNET/cesnet-tszoo)
- 📖 **Documentazione:** [cesnet.github.io/cesnet-tszoo](https://cesnet.github.io/cesnet-tszoo/)
- 🗃️ **Dataset su Zenodo:** [zenodo.org/records/13382427](https://zenodo.org/records/13382427)

