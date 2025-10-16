# Network Security Monitor per Reti ICS (Client Kafka)

Questo progetto è un'applicazione desktop creata in Python che funge da pannello di controllo per la sicurezza (dashboard) di una rete industriale (OT). L'interfaccia si collega a un broker **Apache Kafka** per visualizzare e gestire in tempo reale lo stato di due dispositivi "Shield" e di un "Orchestrator" centrale.

L'applicazione non è più solo una simulazione, ma un **client Kafka funzionale** progettato per:
1.  **Ricevere** messaggi di stato e di attacco inviati dagli shield.
2.  **Implementare** la logica di un orchestratore per rispondere automaticamente alle minacce.
3.  **Inviare** comandi di contromisura e configurazione agli shield.
4.  **Visualizzare** l'intero processo in un'interfaccia grafica intuitiva.
   
---

## Indice dei Contenuti
* [Descrizione](#-descrizione)
* [Funzionalità Principali](#-funzionalità-principali)
* [Installazione e Avvio](#-installazione-e-avvio)
    * [Passo 1: Configurazione di Apache Kafka](#passo-1-configurazione-di-apache-kafka)
    * [Passo 2: Configurazione del Progetto Python](#passo-2-configurazione-del-progetto-python)
    * [Passo 3: Avvio dell'Applicazione](#passo-3-avvio-dellapplicazione)
* [Verifica del Funzionamento](#-verifica-del-funzionamento)
* [Dipendenze](#-dipendenze)

---

## 📜 Descrizione

La dashboard monitora dinamicamente lo stato di ogni Shield, che può essere:
* 🟢 **OPERATIONAL**: Lo shield funziona normalmente.
* 🔴 **ATTACK**: Lo shield ha rilevato una minaccia. L'orchestratore invierà una contromisura.
* 🟡 **RECOVERY**: La contromisura è stata applicata. Lo shield è in fase di recupero.
* ⚫ **OFF**: Lo shield è spento o non connesso.

La logica di orchestrazione è automatica: in risposta a un messaggio di attacco ricevuto via Kafka, l'orchestratore invia comandi specifici (es. regole firewall `nftables`) per neutralizzare la minaccia e, successivamente, per ripristinare la normalità.

---

## ✨ Funzionalità Principali
* **Integrazione con Apache Kafka**: L'applicazione è un vero client Kafka che produce e consuma messaggi, rendendola integrabile in un'architettura reale.
* **Logica di Orchestrazione Automatica**: Risponde autonomamente agli eventi di attacco secondo le regole definite, inviando comandi di mitigazione e ripristino.
* **Simulazione di Eventi (Injector)**: Un pannello di controllo permette di simulare i messaggi inviati dagli shield in tre modalità:
    1.  **Manuale**: Inserendo un singolo JSON in una casella di testo.
    2.  **Da File**: Inviando in sequenza tutti i log di test presenti nel file `json.txt`.
    3.  **Automatica**: Inviando un log casuale a uno shield casuale a intervalli di 10 secondi.
* **Visualizzazione in Tempo Reale**: Una mappa grafica della rete con stati e indirizzi IP che si aggiornano in base ai messaggi ricevuti.
* **UI Moderna**: L'interfaccia utilizza un tema scuro professionale grazie alla libreria `sv-ttk`.

---

## 🔧 Installazione e Avvio

Per eseguire il progetto, sono necessari **Python 3**, **Java 17+** e **Apache Kafka**.

### Passo 1: Configurazione di Apache Kafka
L'applicazione richiede un broker Kafka in esecuzione.

**1a. Download e Avvio del Server (modalità KRaft, senza ZooKeeper)**

1.  Scarica [Apache Kafka](https://kafka.apache.org/downloads) ed estrailo in una cartella semplice (es. `C:\kafka`).
2.  Apri un **Prompt dei comandi** o **PowerShell** e naviga nella cartella di Kafka.
3.  Genera un ID per il cluster. **Copia l'ID generato**.
    ```bash
    bin\windows\kafka-storage.bat random-uuid
    ```
4.  Formatta la directory di storage usando l'ID appena copiato.
    ```bash
    bin\windows\kafka-storage.bat format -t TUO_CLUSTER_ID -c config\kraft\server.properties
    ```
5.  Avvia il server Kafka. **Questo terminale deve rimanere aperto.**
    ```bash
    bin\windows\kafka-server-start.bat config\kraft\server.properties
    ```

**1b. Creazione dei Topic**

Apri un **secondo terminale** e crea i 4 topic necessari per la comunicazione:
```bash
# Topic per i messaggi da SHIELD_1 a Orchestrator
bin\windows\kafka-topics.bat --create --topic ics.orchestrator.shield_1 --bootstrap-server localhost:9092

# Topic per i messaggi da SHIELD_2 a Orchestrator
bin\windows\kafka-topics.bat --create --topic ics.orchestrator.shield_2 --bootstrap-server localhost:9092

# Topic per le risposte da Orchestrator a SHIELD_1
bin\windows\kafka-topics.bat --create --topic ics.shield_1 --bootstrap-server localhost:9092

# Topic per le risposte da Orchestrator a SHIELD_2
bin\windows\kafka-topics.bat --create --topic ics.shield_2 --bootstrap-server localhost:9092
```

### Passo 2: Configurazione del Progetto Python

1.  Clona o scarica il progetto in una cartella locale.
2.  Assicurati che il file `json.txt` sia presente nella stessa cartella dello script Python.
3.  Installa le librerie necessarie tramite `pip`.
    ```bash
    pip install kafka-python pillow sv-ttk
    ```

### Passo 3: Avvio dell'Applicazione

Una volta che il server Kafka è in esecuzione, apri un **nuovo terminale**, naviga nella cartella del progetto e avvia lo script:
```bash
python Interfaccia.py
```

---

## 🔍 Verifica del Funzionamento
Per verificare che l'Orchestrator stia inviando correttamente le risposte, puoi usare uno strumento da riga di comando per "ascoltare" un topic.

1.  Apri un **nuovo terminale** (il terzo, oltre a quello del server Kafka e della UI).
2.  Esegui questo comando per metterti in ascolto dei messaggi inviati a `SHIELD_1`:
    ```bash
    bin\windows\kafka-console-consumer.bat --topic ics.shield_1 --bootstrap-server localhost:9092
    ```
3.  Dall'interfaccia grafica, simula un attacco verso `SHIELD_1`.
4.  Osserva il terminale del "consumer": vedrai apparire in tempo reale il messaggio di tipo `action` inviato dall'Orchestrator.

---

## 📦 Dipendenze
Questo script richiede le seguenti librerie Python:

* `kafka-python`: Per la comunicazione con il broker Apache Kafka.
* `Pillow`: Per gestire l'icona della finestra.
* `sv-ttk`: Per applicare il tema grafico moderno all'interfaccia.

### File `requirements.txt`
Se preferisci, puoi creare un file `requirements.txt` con questo contenuto e installare tutto con `pip install -r requirements.txt`.
```
kafka-python
Pillow
sv-ttk
```
