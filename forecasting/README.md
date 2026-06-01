# LSTM Forecasting — CESNET TimeSeries24

Progetto di forecasting del traffico di rete su dati reali della rete accademica ceca CESNET3, utilizzando un modello LSTM per predire il numero di pacchetti (`n_packets`) di una singola istituzione un'ora in avanti.

---

## Panoramica

Il programma carica i dati di traffico di rete dal dataset **CESNET-TimeSeries24**, seleziona una singola istituzione e allena un modello LSTM per prevedere il traffico futuro a partire da una finestra temporale di 24 ore.

Il flusso del programma è il seguente:

1. **Caricamento del dataset** — scarica e inizializza il dataset CESNET-TimeSeries24 con aggregazione oraria
2. **Configurazione** — suddivide i dati cronologicamente in train (60%), validation (20%) e test (20%), applicando normalizzazione con Standard Scaler
3. **Training** — allena il modello LSTM con early stopping e learning rate scheduling, salvando il miglior modello in base alla validation loss
4. **Valutazione** — calcola le metriche di errore (MSE, MAE, RMSE, NRMSE) in scala originale sul test set
5. **Visualizzazione** — genera un plot dei valori predetti vs reali e lo salva come immagine PNG

---

## Requisiti

- Python **3.10** o superiore
- GPU opzionale ma consigliata (CUDA) — il programma funziona anche su CPU

---

## Dipendenze

Le librerie necessarie sono:

| Libreria | Versione consigliata |
|---|---|
| `torch` | ≥ 2.0 |
| `numpy` | ≥ 1.24 |
| `matplotlib` | ≥ 3.7 |
| `pandas` | ≥ 2.0 |
| `seaborn` | ≥ 0.12 |
| `cesnet-tszoo` | ≥ 2.2.0 |
| `ipython` | ≥ 8.0 |

---

## Installazione

### 1. Clona il repository

```bash
git clone <url-della-repository>
cd Forecasting-Dataset-CESNET-TimeSeries24 
```

### 2. Crea e attiva l'ambiente virtuale

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Installa le dipendenze

```bash
pip install torch numpy matplotlib pandas seaborn cesnet-tszoo ipython
```

---

## Avvio

```bash
cd forecasting
python3 forecasting_single_institution.py
```

Al primo avvio il dataset verrà scaricato automaticamente nella cartella `./data/cesnet_dataset`.

---

## Output

- **Metriche sul test set** — MSE, MAE, RMSE e NRMSE in scala originale stampate a terminale
- **Plot** — `forecast_single_institution_n_packets.png` con i primi n timestep predetti vs reali
- **Modello salvato** — `best_model_single_institution.pt` con i pesi del miglior modello

---

## Dataset

Il dataset utilizzato è [CESNET-TimeSeries24](https://zenodo.org/records/13382427), pubblicato da Koumar et al. in *CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting*, Scientific Data, 2025.
