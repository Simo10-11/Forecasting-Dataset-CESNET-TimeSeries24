import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F 
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from cesnet_tszoo.datasets import CESNET_TimeSeries24
from cesnet_tszoo.configs import TimeBasedConfig
from cesnet_tszoo.utils.enums import AgreggationType, SourceType, TimeFormat

TARGET_FEATURE_INDEX = 1  # indice feature nella lista features_to_take [n_packets=1]
TS_IDS=0    #indice dell'istituzione da prendere [da 0 a 282]


def inverse_scale_feature(dataset, values): # funzione per scalare indietro i valori predetti o reali (che sono in scala normalizzata) alla scala originale (quella dei dati grezzi) 
    transformers = dataset.get_transformers()   #per scalare i dati ho usato standard scaler che è un transformer
    if isinstance(transformers, np.ndarray):    #mi serve per prendere lo scaler usato per scalare i dati, che è dentro transformers
        transformers = transformers[0]

    scaler = transformers.transformers["base_data"] # prendo lo scaler usato per scalare i dati (base_data) che è uno standard scaler
    n_features = scaler.scale_.shape[0]  # quante feature ha lo scaler (qui 4, perché abbiamo 4 feature in features_to_take)

    values_np = values.detach().cpu().numpy().reshape(-1, 1)    # values è un tensore 1D (N,), lo trasformo in array numpy e lo rendo 2D (N, 1) perché scaler.inverse_transform si aspetta un array 2D (N, n_features)

    #Lo scaler è stato allenato su tutte le feature insieme, quindi: non potrei fare inverse_transform su una sola colonna direttamente
    # costruisco un array (N, n_features) con zeri ovunque tranne la colonna target
    dummy = np.zeros((len(values_np), n_features))
    dummy[:, TARGET_FEATURE_INDEX] = values_np[:, 0]   # metto i valori da scalare nella colonna target, le altre rimangono zero 

    # inverse_transform restituisce (N, nfeatures), prendi solo la colonna target
    return scaler.inverse_transform(dummy)[:, TARGET_FEATURE_INDEX]


def evaluate(model, loader, device):    
    model.eval()
    preds, trues = [], []

    with torch.no_grad():   #non calcolo i gradienti, inutile durante la valutazione
        for X, y in loader: #
            X = torch.from_numpy(X).float().to(device)
            y = torch.from_numpy(y).float().to(device)[:, 0, TARGET_FEATURE_INDEX]  
            preds.append(model(X))  #faccio la forward pass per ottenere le predizioni del modello sulla batch
            trues.append(y)

    # dopo aver ottenuto tutte le predizioni e i valori reali per tutte le batch, li concateno in un unico tensore per calcolare gli errori complessivi
    preds = torch.cat(preds).squeeze() 
    trues = torch.cat(trues).squeeze()

    # calcolo degli errori in scala normalizzata (quella usata per addestrare il modello)
    mse = F.mse_loss(preds, trues)
    mae = F.l1_loss(preds, trues)
    rmse = torch.sqrt(mse)

    return mse.item(), mae.item(), rmse.item(), trues, preds


class LSTMForecast(nn.Module):  
    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):     
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size,    
            num_layers=num_layers,  
            batch_first=True,   #dico che i dati in ingresso hanno la forma (batch_size, seq_len, input_size)
            dropout=dropout,    #applico dropout tra i layer per evitare overfitting, così durante l'addestramento ogni neurone ha una probabilità di 0.2 di essere "spento" (non aggiornato) in ogni batch
           
        )
        self.fc = nn.Linear(hidden_size, 1)     #trasforma la rappresentazione interna della LSTM (batch_size, seq_len, hidden_size) in una singola predizione

    #nella forward pass, passo i dati attraverso la LSTM e poi prendo l'output dell'ultimo timestep
    def forward(self, x):   
        out, _ = self.lstm(x)   
        return self.fc(out[:, -1, :]).squeeze(-1)  


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    losses = [] ##tengo traccia dell'errore dopo ogni batch, poi farò media

    for X, y in loader: #per ogni batch, li converto in tensori torch
        X = torch.from_numpy(X).float().to(device)
        y = torch.from_numpy(y).float().to(device)[:, 0, TARGET_FEATURE_INDEX]  # prendo solo la colonna target dalla batch di y

        optimizer.zero_grad()   #azzero i gradienti prima di fare il backward, altrimenti si accumulano
        preds = model(X)    #faccio la forward pass per ottenere le predizioni del modello sulla batch
        loss = criterion(preds, y)  #calcolo la loss confrontando le predizioni con i valori reali 
        loss.backward() #faccio la backward pass per calcolare i gradienti della loss rispetto ai parametri del modello
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)   ##evito che i gradienti diventino troppo grandi, il che può destabilizzare l'addestramento, portandoli nel caso a 1.0
        optimizer.step()    #aggiorno i parametri del modello usando i gradienti calcolati

        losses.append(loss.item())  #salvo il valore della loss di questa batch in una lista per poi fare la media alla fine dell'epoca

    return torch.tensor(losses).mean().item()   #calcolo la media delle loss di tutte le batch dell'epoca 

#.item() per ottenere un numero da un tensore



def main():
    # print("SOURCE TYPES:")  #source type disponibili per capire quali sono le opzioni che posso mettere in source_type 
    # for s in SourceType:
    #     print(s)

    # print("\nAGGREGATIONS:")    #aggregazioni disponibili per capire quali sono le opzioni che posso mettere in aggregation
    # for a in AgreggationType:
    #     print(a)

    dataset = CESNET_TimeSeries24.get_dataset(  #crea il dataset con i parametri specificati
        data_root="./data/cesnet_dataset",
        source_type=SourceType.INSTITUTIONS,
        aggregation=AgreggationType.AGG_1_HOUR,
        dataset_type="time_based",
        display_details=True,
    )
    available_ids = dataset.get_available_ts_indices()  #prendo gli id disponibili (ogni id è una istituzione/time series diversa) 
    institution_id = int(available_ids['id_institution'][TS_IDS])  # voglio solo un id di una istituzione, se voglio un altro id cambio indice [0] 

    config = TimeBasedConfig(
    ts_ids=[institution_id],        # lista con UN solo ID reale
    train_time_period=0.6,          # 60% dei timestep per il train
    val_time_period=0.20,           # 20% per la validation
    test_time_period=0.20,          # 20% per il test
    features_to_take=["n_flows", "n_packets", "n_bytes"], #feature da prendere in input 
    sliding_window_size=24,         # finestra di 24 ore in input
    sliding_window_prediction_size=1,  # predici 1 passo avanti
    random_state=42,
    transform_with="standard_scaler",  # normalizzazione 
    include_ts_id=False,    
    include_time=False,     #sarebbe utile sapere l'ora del giorno o il giorno della settimana, ma per ora non lo includo perchè non me lo normalizza e crea problemi al modello

    )

    dataset.set_dataset_config_and_initialize(config)   #setta la configurazione del dataset
    print(dataset.dataset_config)  
 
  
    single_ts_id = institution_id   
    print(f"\n Ho selezionato l'isituzione con ts_id: {single_ts_id}")

    #CORRELAZIONE TRA LE FEATURE TAKEN DELLA SINGOLA ISTITUZIONE
    # # prendi i dati grezzi come DataFrame
    # train_df = dataset.get_train_df()

    # # matrice di correlazione
    # corr = train_df.corr()

    # # guarda solo la correlazione con n_packets
    # print(corr["n_packets"].sort_values(ascending=False))

    # Prendo i dataloader per train, val e test della singola istituzione selezionata
    train_loader = dataset.get_train_dataloader(ts_id=single_ts_id)
    val_loader   = dataset.get_val_dataloader(ts_id=single_ts_id)
    test_loader  = dataset.get_test_dataloader(ts_id=single_ts_id)
    

    # Per debug, prendo una batch da ogni loader e stampo le forme di X e y
    X_train, y_train = next(iter(train_loader))
    X_val, y_val = next(iter(val_loader))
    X_test, y_test = next(iter(test_loader))

    
    print("\n===== SHAPES =====")
    print("TRAIN")
    print("X_train shape:", X_train.shape)  #corretto vedere X_train shape: (1, 24, 4) perchè ho una sola istituzione, quindi batch size 1, finestra di 24 ore, e 4 feature in input
    print("y_train shape:", y_train.shape)
    print("\nVALIDATION")
    print("X_val shape:", X_val.shape)
    print("y_val shape:", y_val.shape)
    print("\nTEST")
    print("X_test shape:", X_test.shape)
    print("y_test shape:", y_test.shape)

    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")   # uso la GPU se è disponibile, altrimenti uso la CPU
    print(f"Device: {device}")

    # input_size è il numero di feature in ingresso per ogni timestep
    input_size = X_train.shape[-1]  #X_train.shape = (batch_size, window_size, features), prendo l'ultima dimensione quindi il numero di features
    print(f"Features in input: {input_size}")

    model = LSTMForecast(input_size=input_size).to(device)  #creo il modello LSTM e lo porto sul device
    criterion = nn.MSELoss()    #loss function per regressione, voglio minimizzare la MSE tra predizioni e valori reali
    optimizer = optim.Adam(model.parameters(), lr=1e-3) 
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5) #

    epochs = 30 #numero massimo di epoche
    patience = 5    # se per 5 epoche consecutive non vedo miglioramenti nella MSE di validazione, fermo il training per evitare overfitting e risparmiare tempo
    best_val = float("inf") #tengo traccia del miglior modello, all'inzio è infinito così ogni modello sarà meglio dell'inizio
    counter = 0 #contatore per vedere quante epoche non si migliroano consecutivamente

    for epoch in range(1, epochs + 1):  # ciclo di training per tutte le epoche 

        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device) #alleno per un'epoca

        val_mse, val_mae, val_rmse, _, _ = evaluate(model, val_loader, device)  #valuto il modello sulla validation set dopo ogni epoca per vedere se sta migliorando 
        scheduler.step(val_mse) #dico al scheduler di monitorare la MSE di validazione, se non migliora per tot epoche, riduce learning rate (così il modello diventa più preciso)

        print(
            f"Epoca {epoch} | Train MSE: {train_loss:.4f} | Val MSE: {val_mse:.4f} | "
            f"Val MAE: {val_mae:.4f} | Val RMSE: {val_rmse:.4f}"
        )

        if val_mse < best_val:  #se la MSE di validazione è meglio del miglior modello per ora, lo aggiorno
            best_val = val_mse
            counter = 0
            torch.save(model.state_dict(), "best_model_single_institution.pt")
            print(" Miglior modello salvato")
        else:   
            counter += 1
            if counter >= patience:
                print("Nessun miglioramento per 5 epoche, stop training.")
                break

    model.load_state_dict(torch.load("best_model_single_institution.pt"))

    
    test_mse, test_mae, test_rmse, trues, preds = evaluate(model, test_loader, device)  #valuto il modello finale sul test set
    
    trues_orig = inverse_scale_feature(dataset, trues)
    preds_orig = inverse_scale_feature(dataset, preds)

    # Calcolo degli errori in scala originale (n_packets)
    trues_np = np.array(trues_orig).reshape(-1) 
    preds_np = np.array(preds_orig).reshape(-1)
    mse_orig = np.mean((preds_np - trues_np) ** 2)
    mae_orig = np.mean(np.abs(preds_np - trues_np))
    rmse_orig = float(np.sqrt(mse_orig))
    range_valori = trues_np.max() - trues_np.min()
    nrmse = (rmse_orig / range_valori) * 100  # in percentuale

    print("\n========== METRICHE IN SCALA ORIGINALE ==========")
    print(f"TS ID scelto: {single_ts_id}")
    print("MSE (scala originale):", round(mse_orig, 4)) #round per arrotondare a 4 cifre decimali, così è più leggibile
    print("MAE (scala originale):", round(mae_orig, 4))
    print("RMSE (scala originale):", round(rmse_orig, 4))
    print(f"NRMSE: {round(nrmse, 2)}%")

    # Plot dei primi 200 valori predetti vs reali in scala originale
    n = min(300, len(trues_orig))  # ogni punto = 1 ora (un singolo timestep predetto)
    plt.figure(figsize=(14, 5)) 
    plt.plot(trues_orig[:n], label="True", color="blue")   
    plt.plot(preds_orig[:n], label="LSTM Pred", color="red", linestyle="--")    
    plt.title(f"LSTM Forecasting - n_packets, singola istituzione ts_id={single_ts_id}")
    plt.xlabel("Timestep (ore)")
    plt.ylabel("n_packets")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("forecast_single_institution_n_packets.png", dpi=300)
    print("Plot salvato in forecast_single_institution_n_packets.png")


if __name__ == "__main__":
    main()