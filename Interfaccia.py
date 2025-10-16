import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import time
import threading
import random
import base64
import io
import os
import copy
from PIL import Image, ImageTk
import sv_ttk
from kafka import KafkaProducer, KafkaConsumer
from queue import Queue, Empty

# --- Icona della finestra (in base64 per non avere file esterni) ---
WINDOW_ICON_B64 = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACxUlEQVR4nLVWzWscVRD+7s7uxG6S1ChptNsmFH8hXAn1oFB86EGIIAiCoHhQQRA99ODBP/ADevEgCHpQ8KCI4kEQvHjxp4ggWFSLFR8k1mBsmnezu/feGJvN7mRqEw8Mu/Pu+82b92ZmVgT+o4B54FrgI+AX4AHQnU4B/jOANuA1cE8k/wG+AZ4CPgbeBwYdxgD9wBngKvAV8AmYd5E51gGXgEHAe+AW8BfYBTYBP4KzWW8B8Lw5AnqAR8AzYBrYBNwA9gI/gHcVuF4B5gA7gfvAfeAKsN/0nAP2AZ+BG8B34BZwA7gfHAcqge3AJ+AycA8Yk4kK2A5cBLYSy5wDrgf3gf/AB+AocA4Yg8WkAbYDq4E3wBVgS+AisK/z4gC4AqwHdgLXgTvAXeB0/jBglQe4FjgBlNgGfAFWAn+Ba8C3oN/20wS2AnuBB8B+YAjYBPwAFgb/O5mS2A5sA/YAu4EfwLfgC9A/6dUCJgI/gS3APuA+cAj4CmwGvgC/gP/Av0y/AbkY3bYCV4F1gZPgO+AC8B74DPwA3gK/gP/8F3gHnAt+AfcB/YDdwA/gGfAJ+B68A/q7+jQwsB6YB0wFvgLXA7eBLUALYCewGPgD3A/uBR8C94Bvwd9Uv9/AcuBu8C+gY3AI+Au8AZ4DPwLfgL2h/n8wB6sK8rQZ2AzuBC8B+YA8wFXgB7AeuBc9/P/ALiEWW7YAGYMdsV2BV5s1+AFsBf4C3gDngXlYn1QG/gI3AK+Ap8A/4DPwK7Ac+A3cB/T74BdgM7AJeAfcBW4FdwH7gMfAX+Ap8Bf5X/t0EfgIXgL7m/0AuwgGgP0rA630+w+2fK1csvsY6A9wP7AcuA7uAnYAVwLvgIfA78E0kO+2BfcA7YCPwN5LtzpIM/gGfO615kLIDvI0wAbgG/AJuBy6B/J+i01Mg+wS2ATux/FzAZuAn8A0cBX5/A9zP5K58204KjM9X3rL8h3J/iPNDrYBLwF/gPXA7cBL4DPwGvif0Wv3OqyjAseK/kHHAc+A+8D/3f2h//8D/Av8/w/8H6zL3n2/G5fJpAAAAAElFTSuQmCC==='

# --- Configurazione dei Dispositivi e della Rete ---
PLC_IDS = ["SHIELD_1", "SHIELD_2"]
PLC_POSITIONS = {"SHIELD_1": (250, 150), "SHIELD_2": (250, 390)}
ORCHESTRATOR_ID = "ORCHESTRATOR"
ORCHESTRATOR_POS = (600, 270)

# --- Configurazione KAFKA ---
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
ORCHESTRATOR_TOPICS = ['ics.orchestrator.shield_1', 'ics.orchestrator.shield_2']

# --- Configurazione della Simulazione ---
DEVICE_SIZE_PLC = 80
DEVICE_SIZE_ORCHESTRATOR = 90
UPDATE_INTERVAL_MS = 100
RECOVERY_TIMEOUT_S = 20
AUTO_INJECT_INTERVAL_S = 10

# --- Palette Colori e Stili Grafici ---
THEME_BG = "#212121"
CANVAS_BG = "#2b2b2b"
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#0D47A1"
STATE_COLORS = {
    "OPERATIONAL": "#1B5E20", "ATTACK": "#B71C1C",
    "RECOVERY": "#F57F17", "OFF": "#424242",
}
ATTACK_PULSE_COLOR = "#F44336"

# --- Configurazioni specifiche per ogni shield ---
SHIELD_SPECIFIC_CONFIGS = {
    "SHIELD_1": {
        "plc_ip": "84.3.251.18",
        "interfaces": {"internal": "192.168.10.1", "external": "84.3.251.17"},
        "arp_table": [{"ip": "84.3.251.18", "mac": "00:80:f4:03:fb:12"}],
        "scada_net": ["84.3.251.18", "84.3.251.101", "84.3.251.102"]
    },
    "SHIELD_2": {
        "plc_ip": "84.3.251.20",
        "interfaces": {"internal": "192.168.10.2", "external": "84.3.251.19"},
        "arp_table": [{"ip": "84.3.251.20", "mac": "74:46:a0:bd:a7:1b"}],
        "scada_net": ["84.3.251.20", "84.3.251.103", "84.3.251.104"]
    }
}


# --- Classe per gestire la logica dell'Orchestrator ---
class Orchestrator:
    # (Questa classe rimane invariata)
    def __init__(self, log_callback, kafka_producer):
        self.log = log_callback
        self.producer = kafka_producer
        self.active_attacks = {}
        self.ddos_thresholds = {}

    def process_message(self, msg, shield_id):
        msg_type = msg.get("type")
        # QUESTO LOG È PER I MESSAGGI RICEVUTI DALL'ORCHESTRATORE
        log_entry = f"<- {shield_id} to {ORCHESTRATOR_ID}: Received '{msg_type}'\n{json.dumps(msg, indent=2)}"
        self.log(log_entry, "info")

        if msg_type == "configuration_request":
            self.handle_config_request(shield_id)
        elif msg_type == "number_of_packets":
            packets = int(msg.get("data", 0))
            new_threshold = int(packets * 2.5) + 100
            self.ddos_thresholds[shield_id] = new_threshold
            self.send_config(shield_id, new_threshold)
        elif msg_type == "attack":
            self.handle_attack(msg, shield_id)
        elif msg_type == "executed_response":
            self.handle_executed_response(msg, shield_id)
    
    def _send_to_shield(self, shield_id, message_dict, tag_key="recovery"):
        topic = f'ics.{shield_id.lower()}'
        self.producer.send(topic, value=message_dict)
        # QUESTO LOG È PER I MESSAGGI INVIATI DALL'ORCHESTRATORE
        log_entry = f"-> {ORCHESTRATOR_ID} to {shield_id}: Sending '{message_dict.get('type')}'\n{json.dumps(message_dict, indent=2)}"
        self.log(log_entry, tag_key)

    def handle_config_request(self, shield_id):
        self.log(f"Responding to configuration request from {shield_id}...", "info")
        initial_threshold = 100000
        self.ddos_thresholds[shield_id] = initial_threshold
        self.send_config(shield_id, initial_threshold)

    def send_config(self, shield_id, ddos_threshold):
        shield_config = SHIELD_SPECIFIC_CONFIGS.get(shield_id)
        if not shield_config:
            self.log(f"ERROR: No specific configuration found for {shield_id}.", "attack")
            return
            
        config_data = {
            "plc": shield_config["plc_ip"],
            "arp_table": shield_config["arp_table"],
            "scan": shield_config["scada_net"],
            "ddos_threshold": ddos_threshold
        }
        message = {"type": "configuration", "timestamp": time.time(), "data": config_data}
        self._send_to_shield(shield_id, message, tag_key="info")

    def handle_attack(self, msg, shield_id):
        attack_data = msg.get("data", {})
        gid = int(attack_data.get("sig_generator", 0))
        sid = int(attack_data.get("sig_id", 0))

        if shield_id in self.active_attacks and self.active_attacks[shield_id].get('response_sent'):
            self.log(f"Ignoring duplicate attack notification from {shield_id}.", "recovery")
            return

        shield_config = SHIELD_SPECIFIC_CONFIGS.get(shield_id, {})
        script = self.generate_response_script(gid, sid, attack_data, shield_config)
        if not script:
            self.log(f"No action required for attack ({gid},{sid}) on {shield_id}.", "info")
            return

        response_id = f"resp-{int(time.time())}-{random.randint(100, 999)}"
        self.active_attacks[shield_id] = { "response_id": response_id, "timestamp": time.time(), "script": script, "response_sent": True, "handle": None }
        action_message = { "type": "action", "timestamp": time.time(), "id": response_id, "script": base64.b64encode(script.encode()).decode() }
        self._send_to_shield(shield_id, action_message, tag_key="attack")

    def generate_response_script(self, gid, sid, data, shield_config):
        ip_src = data.get("ip_src", "0.0.0.0")
        mac_src = data.get("mac_src", "00:00:00:00:00:00")
        threshold = self.ddos_thresholds.get(data.get("shield_id"), 100000)
        scada_net = shield_config.get("scada_net", [])

        if gid == 2:
            proto = "tcp" if sid == 1000002 else "icmp"
            return f"nft add rule bridge filter forward ip protocol {proto} limit rate {threshold}/second accept\nnft add rule bridge filter forward ip protocol {proto} drop"
        elif gid == 3:
            if ip_src not in scada_net:
                return f"nft add rule bridge filter forward ip saddr {ip_src} drop"
        elif gid == 112:
            return f"nft add rule bridge filter forward ether saddr {mac_src} drop"
        return ""

    def handle_executed_response(self, msg, shield_id):
        response_id = msg.get("id")
        if shield_id in self.active_attacks and self.active_attacks[shield_id]["response_id"] == response_id:
            try:
                output_b64 = msg.get("output", "")
                handle_info = json.loads(base64.b64decode(output_b64).decode())
                self.active_attacks[shield_id]["handle"] = handle_info.get("handle")
                self.log(f"Successfully applied response {response_id} on {shield_id}.", "recovery")
            except Exception as e:
                self.log(f"Error processing 'executed_response' from {shield_id}: {e}", "attack")

    def check_for_recovery(self):
        now = time.time()
        for shield_id, attack_info in list(self.active_attacks.items()):
            if now - attack_info["timestamp"] > RECOVERY_TIMEOUT_S:
                handle = attack_info.get("handle")
                if handle:
                    scripts = [f"nft delete rule bridge filter forward handle {h}" for h in handle]
                    script = "\n".join(scripts)
                    action_message = { "type": "action", "timestamp": now, "id": f"rec-{int(now)}", "script": base64.b64encode(script.encode()).decode() }
                    self._send_to_shield(shield_id, action_message, tag_key="recovery")
                    del self.active_attacks[shield_id]


# --- GUI Principale ---
class NetworkSecurityMonitor(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("ICS Network Security Monitor (Kafka Client)")
        self.geometry("1400x900")
        self.images = {}
        self._load_icons()
        sv_ttk.set_theme("dark")
        self.plc_statuses = {pid: {"state": "OFF", "attack_type": None, "configured": False} for pid in PLC_IDS}
        self.visual_elements = {}
        self.animation_state = {}
        self.message_queue = Queue()
        self.log_templates = []
        self.auto_inject_enabled = tk.BooleanVar(value=False)
        self._load_log_templates()
        try:
            self.producer = KafkaProducer( bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8') )
            self.orchestrator = Orchestrator(self.log_message_from_thread, self.producer)
        except Exception as e:
            messagebox.showerror("Kafka Error", f"Could not connect to Kafka Producer at {KAFKA_BOOTSTRAP_SERVERS}.\nPlease ensure Kafka is running.\n\nError: {e}")
            self.destroy()
            return
        self._configure_layout()
        self._create_widgets()
        self.draw_network_layout()
        self.kafka_thread = threading.Thread(target=self.kafka_listener, daemon=True)
        self.kafka_thread.start()
        self.recovery_thread = threading.Thread(target=self.recovery_checker, daemon=True)
        self.recovery_thread.start()
        self.auto_injector_thread = threading.Thread(target=self.auto_injector_loop, daemon=True)
        self.auto_injector_thread.start()
        self.after(UPDATE_INTERVAL_MS, self.update_gui_and_process_queue)

    def _load_icons(self):
        try:
            win_icon_data = base64.b64decode(WINDOW_ICON_B64)
            win_img = Image.open(io.BytesIO(win_icon_data))
            self.images['window_icon'] = ImageTk.PhotoImage(win_img)
            self.wm_iconphoto(True, self.images['window_icon'])
        except Exception as e:
            print(f"Error loading icons: {e}")

    def _load_log_templates(self):
        try:
            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, 'json.txt')
            with open(file_path, 'r') as f: content = f.read()
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try: self.log_templates.append(json.loads(line))
                    except json.JSONDecodeError: continue
            if self.log_templates: print(f"Loaded {len(self.log_templates)} log templates from json.txt")
            else: print("Warning: No valid log templates found in json.txt.")
        except FileNotFoundError: messagebox.showwarning("Warning", "json.txt not found. The log injector will not work.")
        except Exception as e: messagebox.showerror("Error", f"Failed to load json.txt: {e}")

    def _configure_layout(self):
        self.configure(bg=THEME_BG)
        self.grid_columnconfigure(0, weight=3, uniform="group1")
        self.grid_columnconfigure(1, weight=2, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

    def _create_widgets(self):
        left_panel = ttk.Frame(self, padding=10); left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_panel.grid_rowconfigure(0, weight=1); left_panel.grid_rowconfigure(2, weight=0); left_panel.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(left_panel, bg=CANVAS_BG, highlightthickness=1, highlightbackground=ACCENT_COLOR); self.canvas.grid(row=0, column=0, sticky="nsew")
        injector_frame = ttk.Labelframe(left_panel, text="File & Auto Injector", padding=10); injector_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        injector_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(injector_frame, text="Target Shield:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.injector_shield_target = ttk.Combobox(injector_frame, values=PLC_IDS, state="readonly"); self.injector_shield_target.current(0)
        self.injector_shield_target.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.inject_button = ttk.Button(injector_frame, text="Inject All From File", command=self.inject_messages_from_file); self.inject_button.grid(row=0, column=2, padx=5, pady=5)
        auto_inject_check = ttk.Checkbutton(injector_frame, text=f"Auto-Inject Random (every {AUTO_INJECT_INTERVAL_S}s)", variable=self.auto_inject_enabled, command=self.toggle_auto_inject)
        auto_inject_check.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        manual_injector_frame = ttk.Labelframe(left_panel, text="Manual Log Inserter", padding=10); manual_injector_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        manual_injector_frame.grid_columnconfigure(0, weight=1)
        self.manual_log_text = tk.Text(manual_injector_frame, height=4, bg="#1e1e1e", fg=TEXT_COLOR, relief=tk.FLAT, font=('Consolas', 9)); self.manual_log_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.manual_log_text.insert("1.0", '{ "type": "attack", "data":{...} }')
        manual_send_button = ttk.Button(manual_injector_frame, text="Send Manual Log", command=self.send_manual_log); manual_send_button.grid(row=0, column=1, padx=5, pady=5, sticky="ns")
        log_frame = ttk.Frame(self, padding=(10, 10, 20, 10)); log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        log_frame.grid_rowconfigure(1, weight=1); log_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(log_frame, text="Communication Log", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="#1e1e1e", fg=TEXT_COLOR, state=tk.DISABLED, font=('Consolas', 10), relief=tk.FLAT, borderwidth=0)
        self.log_area.grid(row=1, column=0, sticky="nsew")

    def draw_network_layout(self):
        x_o, y_o = ORCHESTRATOR_POS
        size_o = DEVICE_SIZE_ORCHESTRATOR / 2
        orch_id = self.canvas.create_rectangle(x_o - size_o, y_o - size_o, x_o + size_o, y_o + size_o, fill=ACCENT_COLOR, outline="white", width=3)
        text_id = self.canvas.create_text(x_o, y_o, text=ORCHESTRATOR_ID, fill="white", font=('Segoe UI', 12, 'bold'))
        self.visual_elements[ORCHESTRATOR_ID] = {'shape': orch_id, 'text': text_id}
        for plc_id in PLC_IDS:
            x_p, y_p = PLC_POSITIONS[plc_id]
            size_p = DEVICE_SIZE_PLC / 2
            color = STATE_COLORS.get(self.plc_statuses[plc_id]['state'], '#333')
            shape_id = self.canvas.create_rectangle(x_p - size_p, y_p - size_p, x_p + size_p, y_p + size_p, fill=color, outline='#616161', width=2, tags=plc_id)
            text_id_label = self.canvas.create_text(x_p, y_p + size_p + 15, text=plc_id, fill=TEXT_COLOR, font=('Segoe UI', 10))
            state_text_id = self.canvas.create_text(x_p, y_p, text=self.plc_statuses[plc_id]['state'], fill="white", font=('Segoe UI', 9, 'bold'))
            ip_font = ('Consolas', 8)
            ip_text_ext = self.canvas.create_text(x_p + size_p + 10, y_p - 8, anchor="w", text="", fill=TEXT_COLOR, font=ip_font, state=tk.HIDDEN)
            ip_text_int = self.canvas.create_text(x_p + size_p + 10, y_p + 8, anchor="w", text="", fill=TEXT_COLOR, font=ip_font, state=tk.HIDDEN)
            alert_font = ('Arial', int(DEVICE_SIZE_PLC * 0.7), 'bold')
            alert_id = self.canvas.create_text(x_p, y_p, text="!", fill=ATTACK_PULSE_COLOR, font=alert_font, state=tk.HIDDEN)
            self.visual_elements[plc_id] = {'shape': shape_id, 'label': text_id_label, 'alert': alert_id, 'state_text': state_text_id, 'ip_ext': ip_text_ext, 'ip_int': ip_text_int}
            self.canvas.create_line(x_p, y_p, x_o, y_o, fill=ACCENT_COLOR, width=1.5, dash=(6, 4))

    def update_gui_and_process_queue(self):
        try:
            while not self.message_queue.empty():
                shield_id, msg_dict = self.message_queue.get_nowait()
                self.process_incoming_message(shield_id, msg_dict)
        except Empty:
            pass
        for plc_id, config in self.plc_statuses.items():
            elements = self.visual_elements.get(plc_id)
            if not elements: continue
            current_state = config['state']
            new_color = STATE_COLORS.get(current_state, "#333333")
            self.canvas.itemconfig(elements['shape'], fill=new_color)
            self.canvas.itemconfig(elements['state_text'], text=current_state)
            if config.get("configured", False):
                interfaces = SHIELD_SPECIFIC_CONFIGS.get(plc_id, {}).get("interfaces", {})
                self.canvas.itemconfig(elements['ip_ext'], text=f"Ext: {interfaces.get('external', 'N/A')}", state=tk.NORMAL)
                self.canvas.itemconfig(elements['ip_int'], text=f"Int: {interfaces.get('internal', 'N/A')}", state=tk.NORMAL)
            else:
                self.canvas.itemconfig(elements['ip_ext'], state=tk.HIDDEN)
                self.canvas.itemconfig(elements['ip_int'], state=tk.HIDDEN)
            is_under_attack = (current_state == "ATTACK")
            if is_under_attack and plc_id not in self.animation_state:
                self.canvas.itemconfig(elements['alert'], state=tk.NORMAL)
                self.animation_state[plc_id] = True
                self.animate_attack(plc_id, pulse_on=True)
            elif not is_under_attack and plc_id in self.animation_state:
                self.canvas.itemconfig(elements['alert'], state=tk.HIDDEN)
                self.canvas.itemconfig(elements['shape'], outline='#616161', width=2)
                del self.animation_state[plc_id]
        self.after(UPDATE_INTERVAL_MS, self.update_gui_and_process_queue)
    
    def process_incoming_message(self, shield_id, msg):
        msg_type = msg.get("type")
        
        # --- MODIFICA: Logica di gestione messaggi spostata qui ---
        # Questo metodo ora gestisce sia messaggi DALLO SHIELD che DALL'ORCHESTRATORE
        
        # Gestisce i messaggi inviati DALL'ORCHESTRATORE a questo shield
        if msg_type == "configuration":
            self.plc_statuses[shield_id]["configured"] = True
            log_entry = f"GUI: Configuration received for {shield_id}. IPs will be displayed."
            self.log_message_from_thread(log_entry, "info")

        # Gestisce i messaggi inviati DALLO SHIELD all'orchestratore
        else:
            current_state = self.plc_statuses[shield_id]['state']
            if msg_type in ["start", "pktcap_started", "pktcap_running", "alive", "configuration_request"]:
                if current_state == "OFF": self.set_plc_state(shield_id, "OPERATIONAL")
            elif msg_type == "stop": 
                self.set_plc_state(shield_id, "OFF")
                self.plc_statuses[shield_id]["configured"] = False
            elif msg_type == "attack":
                attack_data = msg.get("data", {}); gid = int(attack_data.get("sig_generator", 0)); sid = int(attack_data.get("sig_id", 0))
                self.set_plc_state(shield_id, "ATTACK", f"gid={gid}, sid={sid}")
            elif msg_type == "executed_response":
                if "rec-" in msg.get("id", ""): self.set_plc_state(shield_id, "OPERATIONAL")
                elif current_state == "ATTACK": self.set_plc_state(shield_id, "RECOVERY")
            
            # Inoltra il messaggio all'orchestratore per l'elaborazione della logica
            self.orchestrator.process_message(msg, shield_id)

    def animate_attack(self, plc_id, pulse_on):
        if plc_id not in self.animation_state: return
        elements = self.visual_elements[plc_id]
        outline_color = ATTACK_PULSE_COLOR if pulse_on else "white"
        outline_width = 3 if pulse_on else 2
        self.canvas.itemconfig(elements['shape'], outline=outline_color, width=outline_width)
        self.after(600, self.animate_attack, plc_id, not pulse_on)

    def log_message(self, message, tag_key="info"):
        self.log_area.config(state=tk.NORMAL)
        tag_config = { "attack": {"foreground": STATE_COLORS["ATTACK"], "font": ('Consolas', 10, 'bold')}, "recovery": {"foreground": STATE_COLORS["RECOVERY"], "font": ('Consolas', 10, 'italic')}, "alive": {"foreground": STATE_COLORS["OPERATIONAL"]}, "info": {"foreground": "#9E9E9E"} }
        self.log_area.tag_config(tag_key, **tag_config.get(tag_key, tag_config["info"]))
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ", ("time",)); self.log_area.tag_config("time", foreground="#757575")
        self.log_area.insert(tk.END, f"{message}\n\n", (tag_key,)); self.log_area.see(tk.END); self.log_area.config(state=tk.DISABLED)

    def log_message_from_thread(self, message, tag_key="info"):
        self.after(0, self.log_message, message, tag_key)

    def set_plc_state(self, plc_id, new_state, attack_type=None):
        if plc_id not in self.plc_statuses: return
        self.plc_statuses[plc_id]['state'] = new_state; self.plc_statuses[plc_id]['attack_type'] = attack_type
        log_map = { "ATTACK": f"EVENT: Shield '{plc_id}' is under ATTACK ({attack_type})!", "OFF": f"EVENT: Shield '{plc_id}' went OFFLINE.", "RECOVERY": f"EVENT: Shield '{plc_id}' enters RECOVERY phase.", "OPERATIONAL": f"EVENT: Shield '{plc_id}' is now OPERATIONAL." }
        log_msg = log_map.get(new_state)
        tag_map = {"ATTACK": "attack", "RECOVERY": "recovery", "OPERATIONAL": "alive"}
        if log_msg: self.log_message_from_thread(log_msg, tag_map.get(new_state, "info"))
    
    def kafka_listener(self):
        try:
            # --- MODIFICA: Ascolta su tutti i topic per intercettare anche le risposte di configurazione ---
            all_topics = ORCHESTRATOR_TOPICS + [f'ics.{pid.lower()}' for pid in PLC_IDS]
            consumer = KafkaConsumer( *all_topics, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_deserializer=lambda v: json.loads(v.decode('utf-8')), auto_offset_reset='latest' )

            for message in consumer:
                topic = message.topic
                msg_value = message.value
                
                # Determina a quale shield il messaggio è destinato o da quale proviene
                # Questo permette alla GUI di sapere quale elemento aggiornare
                shield_id = ""
                if "orchestrator" in topic:
                    shield_id = f"SHIELD_{topic.split('_')[-1].upper()}"
                else:
                    shield_id = f"SHIELD_{topic.split('.')[-1].split('_')[-1].upper()}"
                
                if shield_id in PLC_IDS:
                    self.message_queue.put((shield_id, msg_value))

        except Exception as e:
            self.log_message_from_thread(f"Kafka Consumer Error: {e}. Please restart.", "attack")

    def recovery_checker(self):
        while True:
            self.orchestrator.check_for_recovery(); time.sleep(5)

    def auto_injector_loop(self):
        while True:
            time.sleep(AUTO_INJECT_INTERVAL_S)
            if self.auto_inject_enabled.get():
                if not self.log_templates: continue
                try:
                    target_shield = random.choice(PLC_IDS)
                    target_topic = f'ics.orchestrator.{target_shield.lower()}'
                    log_template = copy.deepcopy(random.choice(self.log_templates))
                    log_template['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
                    self.producer.send(target_topic, value=log_template)
                    self.producer.flush()
                    self.log_message_from_thread(f"Auto-Inject: Sent random '{log_template['type']}' event to {target_shield}.", "recovery")
                except Exception as e:
                    self.log_message_from_thread(f"Auto-Inject Error: {e}", "attack")
    
    def toggle_auto_inject(self):
        if self.auto_inject_enabled.get():
            self.inject_button.config(state=tk.DISABLED)
            self.log_message_from_thread("Automatic random injection ENABLED.", "recovery")
        else:
            self.inject_button.config(state=tk.NORMAL)
            self.log_message_from_thread("Automatic random injection DISABLED.", "info")

    def inject_messages_from_file(self):
        target_shield = self.injector_shield_target.get()
        if not target_shield: messagebox.showwarning("Warning", "Please select a target shield."); return
        target_topic = f'ics.orchestrator.{target_shield.lower()}'
        try:
            script_dir = os.path.dirname(__file__); file_path = os.path.join(script_dir, 'json.txt')
            with open(file_path, 'r') as f: content = f.read()
            json_objects = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try: json_objects.append(json.loads(line))
                    except json.JSONDecodeError: continue
            if not json_objects: messagebox.showinfo("Info", "No valid JSON messages found in json.txt."); return
            self.log_message_from_thread(f"Injecting {len(json_objects)} messages from json.txt to {target_shield} on topic {target_topic}", "recovery")
            for obj in json_objects:
                obj['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
                self.producer.send(target_topic, value=obj); self.producer.flush()
                time.sleep(0.5)
            self.log_message_from_thread("Injection complete.", "recovery")
        except FileNotFoundError: messagebox.showerror("Error", f"The file 'json.txt' was not found.\n\nLooking for: {file_path}")
        except Exception as e: messagebox.showerror("Error", f"An error occurred during injection: {e}")

    def send_manual_log(self):
        target_shield = self.injector_shield_target.get()
        if not target_shield: messagebox.showwarning("Warning", "Please select a target shield."); return
        log_content = self.manual_log_text.get("1.0", tk.END).strip()
        if not log_content: messagebox.showwarning("Warning", "The text box is empty."); return
        try:
            log_obj = json.loads(log_content)
        except json.JSONDecodeError: messagebox.showerror("Error", "The text is not a valid JSON."); return
        target_topic = f'ics.orchestrator.{target_shield.lower()}'
        log_obj['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        try:
            self.producer.send(target_topic, value=log_obj)
            self.producer.flush()
            self.log_message_from_thread(f"Manual Inject: Sent '{log_obj['type']}' event to {target_shield}.", "recovery")
        except Exception as e: messagebox.showerror("Error", f"Failed to send message to Kafka: {e}")

    def on_closing(self):
        if self.producer:
            self.producer.close()
        self.destroy()

if __name__ == "__main__":
    app = NetworkSecurityMonitor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()