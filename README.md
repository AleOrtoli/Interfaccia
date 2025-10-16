# Network Security Monitor for PLC Networks
Questo progetto è un'applicazione desktop creata in Python che simula un pannello di controllo per la sicurezza informatica (dashboard) di una rete industriale (OT). L'interfaccia visualizza una rete composta da un Orchestrator centrale e quattro dispositivi PLC (Programmable Logic Controller), monitorandone lo stato in tempo reale.

L'applicazione è progettata come strumento didattico per visualizzare concetti di cybersecurity come il rilevamento di minacce, la quarantena di un dispositivo e il processo di recupero manuale gestito da un operatore.

---
## 📜 Descrizione

Il simulatore gestisce dinamicamente lo stato di ogni PLC, che può essere:
* 🟢 **Operativo**: Funzionamento normale.
* 🔴 **Attacco**: Il dispositivo è sotto attacco, viene isolato visivamente e richiede un intervento.
* 🟡 **Recupero**: L'attacco è stato contenuto, ma il dispositivo è in fase di analisi e attende il ripristino manuale.
* ⚫ **Off**: Il dispositivo è spento o non raggiungibile.

Un processo in background simula eventi casuali, come attacchi o guasti, mentre un'area di log mostra le comunicazioni di rete simulate in formato JSON. L'interfaccia è interattiva e richiede all'utente di agire come un operatore di sicurezza per gestire e ripristinare i dispositivi compromessi.

---
## ✨ Funzionalità Principali
* **Simulazione Visiva**: Una mappa grafica della rete con stati dei dispositivi indicati da codici colore.
* **Quarantena Automatica**: Quando un PLC è sotto attacco, la sua connessione all'Orchestrator viene visivamente interrotta per simulare l'isolamento dalla rete.
* **Intervento Manuale a Due Fasi**:
    1.  L'utente deve cliccare su un PLC **sotto attacco (rosso)** per avviare la procedura di recupero.
    2.  Successivamente, deve cliccare sul PLC **in recupero (giallo)** per confermare il ripristino e riportarlo allo stato operativo.
* **Alert Dinamici**: Animazioni pulsanti e finestre di dialogo avvisano l'utente in caso di attacco.
* **Log in Tempo Reale**: Un pannello mostra i messaggi simulati tra i dispositivi.
* **UI Moderna**: L'interfaccia utilizza un tema scuro professionale grazie alla libreria `sv-ttk`.

---
## 🔧 Installazione e Avvio

Per eseguire questo progetto, assicurati di avere **Python 3** installato sul tuo sistema.

**1. Clona la repository:**
```bash
git clone [https://github.com/AleOrtoli/Interfaccia.git](https://github.com/AleOrtoli/Interfaccia.git)
```

**2. Entra nella cartella del progetto:**
```bash
cd Interfaccia
```

**3. Installa le dipendenze:**
Le dipendenze necessarie sono elencate nel file `requirements.txt`. Esegui questo comando per installarle:
```bash
pip install -r requirements.txt
```

**4. Avvia l'applicazione:**
```bash
python Interfaccia.py
```
---
## 📦 Dipendenze
Questo script richiede due librerie Python esterne:

* `Pillow`: Utilizzata per gestire e visualizzare l'icona della finestra.
* `sv-ttk`: Applica il tema grafico scuro e moderno all'interfaccia Tkinter.

La libreria `tkinter` è inclusa nella libreria standard di Python e non necessita di installazione separata.

### File `requirements.txt`
Crea un file chiamato `requirements.txt` nella cartella del tuo progetto e inserisci questo contenuto:
```
Pillow
sv-ttk
```
