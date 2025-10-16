# Network Security Monitor for ICS Networks (Kafka Client)

This project is a desktop application created in Python that acts as a security control panel (dashboard) for an industrial (OT) network. The interface connects to an **Apache Kafka** broker to display and manage the real-time status of two "Shield" devices and a central "Orchestrator."

The application is no longer just a simulation but a **functional Kafka client** designed to:
1.  **Receive** status and attack messages sent by the shields.
2.  **Implement** an orchestrator's logic to automatically respond to threats.
3.  **Send** countermeasure and configuration commands to the shields.
4.  **Visualize** the entire process in an intuitive graphical interface.

---

## Table of Contents
* [Description](#-descrizione)
* [Main Features](#-funzionalità-principali)
* [Installation and Startup](#-installazione-e-avvio)
    * [Step 1: Apache Kafka Setup](#passo-1-configurazione-di-apache-kafka)
    * [Step 2: Python Project Setup](#passo-2-configurazione-del-progetto-python)
    * [Step 3: Start the Application](#passo-3-avvio-dellapplicazione)
* [Verifying Operation](#-verifica-del-funzionamento)
* [Dependencies](#-dipendenze)

---

## 📜 Descrizione

The dashboard dynamically monitors the status of each Shield, which can be:
* 🟢 **OPERATIONAL**: The shield is functioning normally.
* 🔴 **ATTACK**: The shield has detected a threat. The orchestrator will send a countermeasure.
* 🟡 **RECOVERY**: The countermeasure has been applied. The shield is in a recovery phase.
* ⚫ **OFF**: The shield is off or unreachable.

The orchestration logic is automatic: in response to an attack message received via Kafka, the orchestrator sends specific commands (e.g., `nftables` firewall rules) to neutralize the threat and, subsequently, to restore normal operations.

---

## ✨ Funzionalità Principali
* **Apache Kafka Integration**: The application is a true Kafka client that produces and consumes messages, making it integrable into a real architecture.
* **Automatic Orchestration Logic**: It autonomously responds to attack events according to defined rules, sending mitigation and restoration commands.
* **Event Simulation (Injector)**: A control panel allows simulating messages sent by the shields in three modes:
    1.  **Manual**: By entering a single JSON in a text box.
    2.  **From File**: By sending all test logs from the `json.txt` file in sequence.
    3.  **Automatic**: By sending a random log to a random shield at 10-second intervals.
* **Real-Time Visualization**: A graphical map of the network with statuses and IP addresses that update based on received messages.
* **Modern UI**: The interface uses a professional dark theme thanks to the `sv-ttk` library.

---

## 🔧 Installazione e Avvio

To run the project, you need **Python 3**, **Java 17+**, and **Apache Kafka**.

### Passo 1: Configurazione di Apache Kafka
The application requires a running Kafka broker.

**1a. Download and Start the Server (KRaft mode, without ZooKeeper)**

1.  Download [Apache Kafka](https://kafka.apache.org/downloads) and extract it to a simple folder (e.g., `C:\kafka`).
2.  Open a **Command Prompt** or **PowerShell** and navigate to the Kafka folder.
3.  Generate a cluster ID. **Copy the generated ID**.
    ```bash
    bin\windows\kafka-storage.bat random-uuid
    ```
4.  Format the storage directory using the ID you just copied.
    ```bash
    bin\windows\kafka-storage.bat format -t YOUR_CLUSTER_ID -c config\kraft\server.properties
    ```
5.  Start the Kafka server. **This terminal must remain open.**
    ```bash
    bin\windows\kafka-server-start.bat config\kraft\server.properties
    ```

**1b. Create the Topics**

Open a **second terminal** and create the 4 topics required for communication:
```bash
# Topic for messages from SHIELD_1 to Orchestrator
bin\windows\kafka-topics.bat --create --topic ics.orchestrator.shield_1 --bootstrap-server localhost:9092

# Topic for messages from SHIELD_2 to Orchestrator
bin\windows\kafka-topics.bat --create --topic ics.orchestrator.shield_2 --bootstrap-server localhost:9092

# Topic for responses from Orchestrator to SHIELD_1
bin\windows\kafka-topics.bat --create --topic ics.shield_1 --bootstrap-server localhost:9092

# Topic for responses from Orchestrator to SHIELD_2
bin\windows\kafka-topics.bat --create --topic ics.shield_2 --bootstrap-server localhost:9092
```

### Passo 2: Configurazione del Progetto Python

1.  Clone or download the project into a local folder.
2.  Ensure the `json.txt` file is in the same folder as the Python script.
3.  Install the necessary libraries via `pip`.
    ```bash
    pip install kafka-python pillow sv-ttk
    ```

### Passo 3: Avvio dell'Applicazione

Once the Kafka server is running, open a **new terminal**, navigate to the project folder, and run the script:
```bash
python Interfaccia.py
```

---

## 🔍 Verifica del Funzionamento
To verify that the Orchestrator is sending responses correctly, you can use a command-line tool to "listen" to a topic.

1.  Open a **new terminal** (a third one, besides the Kafka server and the UI).
2.  Run this command to listen for messages sent to `SHIELD_1`:
    ```bash
    bin\windows\kafka-console-consumer.bat --topic ics.shield_1 --bootstrap-server localhost:9092
    ```
3.  From the graphical interface, simulate an attack on `SHIELD_1`.
4.  Observe the "consumer" terminal: you will see the `action` message sent by the Orchestrator appear in real-time.

---

## 📦 Dipendenze
This script requires the following Python libraries:

* `kafka-python`: For communication with the Apache Kafka broker.
* `Pillow`: To manage the window icon.
* `sv-ttk`: To apply the modern graphical theme to the interface.

### requirements.txt File
If you prefer, you can create a `requirements.txt` file with this content and install everything with `pip install -r requirements.txt`.
```
kafka-python
Pillow
sv-ttk
```
