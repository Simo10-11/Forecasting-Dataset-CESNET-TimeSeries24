# Dataset-CESNET-TimeSeries24
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
@@ -27,83 +26,99 @@ Il **CESNET-TimeSeries24** è un dataset reale di traffico di rete raccolto dall
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

 
### Feature Temporale
 
| Feature | Tipo | Descrizione |
|---|---|---|
| `n_flows` | int | Numero totale di IP flow nell'intervallo |
| `n_packets` | int | Numero totale di pacchetti trasmessi |
| `n_bytes` | int | Numero totale di byte trasmessi |

### Metriche Volumetriche Uniche

| `id_time` | int | Identificatore univoco per ogni intervallo di aggregazione nella time series, usato per segmentare il dataset in specifici periodi temporali per l'analisi. |
 
### Metriche Volumetriche
 
| Feature | Tipo | Descrizione |
|---|---|---|
| `n_dest_ip` | int | Numero di IP destinazione **unici** contattati |
| `n_dest_asn` | int | Numero di ASN (Autonomous System Number) destinazione unici |
| `n_dest_port` | int | Numero di porte di trasporto destinazione uniche |

### Metriche di Rapporto (Ratios)

| `n_flows` | int | Numero totale di flow osservati nell'intervallo di aggregazione, indica il volume di sessioni o connessioni distinte per l'indirizzo IP. |
| `n_packets` | int | Numero totale di pacchetti trasmessi durante l'intervallo di aggregazione, riflette il volume di traffico a livello di pacchetto per l'indirizzo IP. |
| `n_bytes` | int | Numero totale di byte trasmessi durante l'intervallo di aggregazione, rappresenta il volume di dati per l'indirizzo IP. |
 
### Metriche di Destinazione (IP singoli)
 
> Presenti nelle time series **non ri-aggregate** (livello IP singolo).
 
| Feature | Tipo | Descrizione |
|---|---|---|
| `tcp_udp_ratio_packets` | float | Rapporto TCP/UDP a livello di pacchetti |
| `tcp_udp_ratio_bytes` | float | Rapporto TCP/UDP a livello di byte |
| `dir_ratio_packets` | float | Rapporto direzionale dei pacchetti (inbound/outbound) |
| `dir_ratio_bytes` | float | Rapporto direzionale dei byte (inbound/outbound) |

### Metriche Medie

| `n_dest_ip` | int | Numero di indirizzi IP destinazione unici contattati durante l'intervallo, mostra la diversità degli endpoint raggiunti. |
| `n_dest_asn` | int | Numero di Autonomous System Number (ASN) destinazione unici contattati durante l'intervallo, indica la diversità delle reti raggiunte. |
| `n_dest_port` | int | Numero di porte di trasporto destinazione uniche contattate durante l'intervallo, rappresenta la varietà dei servizi acceduti. |
 
### Metriche di Destinazione (ri-aggregate)
 
> Presenti nelle time series **ri-aggregate** (istituzioni, subnet) — sostituiscono `n_dest_ip`, `n_dest_asn`, `n_dest_port`.
 
| Feature | Tipo | Descrizione |
|---|---|---|
| `avg_duration` | float | Durata media dei flow (in secondi) |
| `avg_ttl` | float | Time To Live (TTL) medio dei pacchetti |

### Feature aggiuntiva

| `sum_n_dest_ip` | int | Somma del numero di indirizzi IP destinazione unici. |
| `avg_n_dest_ip` | float | Media del numero di indirizzi IP destinazione unici. |
| `std_n_dest_ip` | float | Deviazione standard del numero di indirizzi IP destinazione unici. |
| `sum_n_dest_asn` | int | Somma del numero di ASN destinazione unici. |
| `avg_n_dest_asn` | float | Media del numero di ASN destinazione unici. |
| `std_n_dest_asn` | float | Deviazione standard del numero di ASN destinazione unici. |
| `sum_n_dest_ports` | int | Somma del numero di porte di trasporto destinazione uniche. |
| `avg_n_dest_ports` | float | Media del numero di porte di trasporto destinazione uniche. |
| `std_n_dest_ports` | float | Deviazione standard del numero di porte di trasporto destinazione uniche. |
 
### Metriche di Rapporto (Ratios)
 
| Feature | Tipo | Range | Descrizione |
|---|---|---|---|
| `tcp_udp_ratio_packets` | float | [0, 1] | Rapporto tra pacchetti TCP e UDP: 1 = tutti i pacchetti su TCP, 0 = tutti i pacchetti su UDP. |
| `tcp_udp_ratio_bytes` | float | [0, 1] | Rapporto tra byte TCP e UDP, stessa regola di `tcp_udp_ratio_packets`. |
| `dir_ratio_packets` | float | [0, 1] | Rapporto direzionale dei pacchetti: 1 = tutti i pacchetti in uscita, 0 = tutti i pacchetti in entrata. |
| `dir_ratio_bytes` | float | [0, 1] | Rapporto direzionale dei byte, stessa regola di `dir_ratio_packets`. |
 
### Metriche Medie
 
| Feature | Tipo | Descrizione |
|---|---|---|
| `id_time` | int | Identificatore univoco dell'intervallo temporale (usato internamente) |

> **💡 Per il forecasting:** Le feature più predittive e regolari sono tipicamente `n_flows`, `n_packets`, `n_bytes`. Le ratio e le medie sono più rumorose a livello di singolo IP ma più stabili a livello istituzionale.

| `avg_duration` | float | Durata media dei flow IP durante l'intervallo di aggregazione, misura la lunghezza tipica delle sessioni. |
| `avg_ttl` | float | Time To Live (TTL) medio dei flow IP durante l'intervallo di aggregazione, fornisce informazioni sulla durata di vita dei pacchetti. |
 
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
@@ -114,42 +129,41 @@ cesnet_tszoo/
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
