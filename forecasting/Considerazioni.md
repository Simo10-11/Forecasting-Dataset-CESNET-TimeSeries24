# LSTM Forecasting — CESNET TimeSeries24

Modello di forecasting basato su rete LSTM per la previsione del traffico di rete su serie temporali del dataset **CESNET TimeSeries24**.

---

## Panoramica

Il modello è una rete LSTM per forecasting multivariato su serie temporali di traffico di rete. Utilizza finestre di 24 ore di tre feature (`n_flows`, `n_packets`, `n_bytes`) per predire il valore di `n_packets` al passo temporale successivo.

Il training è supervisionato con split temporale (train / validation / test) e normalizzazione `StandardScaler` applicata esclusivamente sui dati di training per evitare data leakage.

Durante il training il modello vede migliaia di finestre scorrevoli:

```
[ora 1 → 24] → predice ora 25
[ora 2 → 25] → predice ora 26
...
```

Per ognuna impara ad associare quella sequenza al valore successivo. Ogni previsione è quindi condizionata esclusivamente alle 24 ore immediatamente precedenti.

Le prestazioni variano sensibilmente a seconda dell'istituzione. Il modello ottiene risultati buoni su serie con un andamento regolare (TS 0, TS 201), mentre fatica sulle serie con picchi acuti e irregolari (TS 51, TS 169).

---

## Comportamento del modello

Il modello è un buon *seguace della media*: segue bene l'andamento generale del traffico, ma tende a smussare i picchi e i cali bruschi. Questo comportamento è una conseguenza diretta dell'ottimizzazione con MSE, che penalizza gli errori grandi in modo quadratico e spinge il modello a stare vicino alla media del training set, minimizzando il rischio ma producendo previsioni conservative sugli estremi.

---

## Criticità

**Assenza di informazioni temporali:**
Il modello non sa se sta osservando un martedì alle 9:00 o un sabato alle 3:00 — un'informazione fondamentale per prevedere il traffico di rete, che segue pattern giornalieri e settimanali ben definiti. La feature temporale (`id_time`) è stata esclusa perché non veniva normalizzata correttamente dallo `StandardScaler`, causando problemi con l'intero dataset. Sarà oggetto di un prossimo possibile sviluppo.

**Loss MSE e smussamento degli estremi:**
La MSE spinge il modello verso la media e lo penalizza poco sugli errori nei momenti tranquilli, molto sui picchi. Il risultato sono previsioni conservative che non riproducono i picchi e down.

**Variabilità tra istituzioni:**
Il modello viene addestrato separatamente per ogni istituzione e le prestazioni dipendono fortemente dalla struttura della serie temporale. Istituzioni con traffico molto irregolare o con picchi rari sono sistematicamente più difficili da prevedere.

---


## Dataset

[CESNET TimeSeries24](https://github.com/CESNET/cesnet-tszoo) — serie temporali di traffico di rete aggregate per istituzione, aggregazione oraria.
