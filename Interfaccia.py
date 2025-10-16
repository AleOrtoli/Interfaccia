import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import time
import threading
import random
import base64
import io
from PIL import Image, ImageTk

# --- Import del tema e applicazione ---
import sv_ttk

# --- Icona della finestra (in base64 per non avere file esterni) ---
ICON_B64 = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACxUlEQVR4nLVWzWscVRD+7s7uxG6S1ChptNsmFH8hXAn1oFB86EGIIAiCoHhQQRA99ODBP/ADevEgCHpQ8KCI4kEQvHjxp4ggWFSLFR8k1mBsmnezu/feGJvN7mRqEw8Mu/Pu+82b92ZmVgT+o4B54FrgI+AX4AHQnU4B/jOANuA1cE8k/wG+AZ4CPgbeBwYdxgD9wBngKvAV8AmYd5E51gGXgEHAe+AW8BfYBTYBP4KzWW8B8Lw5AnqAR8AzYBrYBNwA9gI/gHcVuF4B5gA7gfvAfeAKsN/0nAP2AZ+BG8B34BZwA7gfHAcqge3AJ+AycA8Yk4kK2A5cBLYSy5wDrgf3gf/AB+AocA4Yg8WkAbYDq4E3wBVgS+AisK/z4gC4AqwHdgLXgTvAXeB0/jBglQe4FjgBlNgGfAFWAn+Ba8C3oN/20wS2AnuBB8B+YAjYBPwAFgb/O5mS2A5sA/YAu4EfwLfgC9A/6dUCJgI/gS3APuA+cAj4CmwGvgC/gH/Av0y/AbkY3bYCV4F1gZPgO+AC8B74DPwA3gK/gP/8F3gHnAt+AfcB/YDdwA/gGfAJ+B68A/q7+jQwsB6YB0wFvgLXA7eBLUALYCewGPgD3A/uBR8C94Bvwd9Uv9/AcuBu8C+gY3AI+Au8AZ4DPwLfgL2h/n8wB6sK8rQZ2AzuBC8B+YA8wFXgB7AeuBc9/P/ALiEWW7YAGYMdsV2BV5s1+AFsBf4C3gDngXlYn1QG/gI3AK+Ap8A/4DPwK7Ac+A3cB/T74BdgM7AJeAfcBW4FdwH7gMfAX+Ap8Bf5X/t0EfgIXgL7m/0AuwgGgP0rA630+w+2fK1/eQkY6A9wP7AcuA7uAnYAVwLvgIfA78E0kO+2BfcA7YCPwN5LtzpIM/gGfO615kLIDvI0wAbgG/AJuBy6B/J+i01Mg+wS2ATux/FzAZuAn8A0cBX5/A9zP5K58204KjM9X3rL8h3J/iPNDrYBLwF/gPXA7cBL4DPwGvif0Wv3OqyjAseK/kHHAc+A+8D/3f2h//8D/Av8/w/8H6zL3n2/G5fJpAAAAAElFTSuQmCC==='

# --- Configurazione dei Dispositivi ---
PLC_CONFIG = {
    "PLC1": {"state": "OFF", "pos": (120, 120)},
    "PLC2": {"state": "OFF", "pos": (480, 120)},
    "PLC3": {"state": "OFF", "pos": (120, 480)},
    "PLC4": {"state": "OFF", "pos": (480, 480)},
}

ORCHESTRATOR_ID = "ORCHESTRATOR"
ORCHESTRATOR_POS = (300, 300)
DEVICE_SIZE_PLC = 60
DEVICE_SIZE_ORCHESTRATOR = 90
UPDATE_INTERVAL_MS = 1000
ALIVE_MESSAGE_INTERVAL_S = 10

# --- Palette Colori e Stili Grafici ---
THEME_BG = "#212121"
CANVAS_BG = "#2b2b2b"
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#00bfff"

STATE_COLORS = {
    "OPERATIVO": "#4CAF50",
    "ATTACCO": "#F44336",
    "RECUPERO": "#FFC107",
    "OFF": "#616161",
}
ATTACK_PULSE_COLOR = "#FF5252"

class PLC_Orchestrator_Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Security Monitor")
        self.geometry("1000x700")

        try:
            icon_data = base64.b64decode(ICON_B64)
            image = Image.open(io.BytesIO(icon_data))
            self.icon = ImageTk.PhotoImage(image)
            self.wm_iconphoto(True, self.icon)
        except Exception as e:
            print(f"Errore caricamento icona: {e}")

        sv_ttk.set_theme("dark")

        self.plc_statuses = PLC_CONFIG.copy()
        self.visual_elements = {}
        self.animation_state = {}

        self._configure_layout()
        self._create_widgets()

        self.draw_devices()
        self.draw_connections()

        self.simulation_thread = threading.Thread(target=self.plc_simulation_loop, daemon=True)
        self.simulation_thread.start()

        self.after(UPDATE_INTERVAL_MS, self.update_gui)

    def _configure_layout(self):
        self.configure(bg=THEME_BG)
        self.grid_columnconfigure(0, weight=3, uniform="group1")
        self.grid_columnconfigure(1, weight=2, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

    def _create_widgets(self):
        canvas_frame = ttk.Frame(self, padding=10)
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame, bg=CANVAS_BG, highlightthickness=1, highlightbackground=ACCENT_COLOR)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        log_frame = ttk.Frame(self, padding=(10, 10, 20, 10))
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(log_frame, text="Communication Log", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                  bg="#1e1e1e", fg=TEXT_COLOR, 
                                                  state=tk.DISABLED, font=('Consolas', 10),
                                                  relief=tk.FLAT, borderwidth=0)
        self.log_area.grid(row=1, column=0, sticky="nsew")

    def draw_connections(self):
        x_o, y_o = ORCHESTRATOR_POS
        for plc_id, config in self.plc_statuses.items():
            x_p, y_p = config['pos']
            line_id = self.canvas.create_line(x_o, y_o, x_p, y_p, 
                                              fill=ACCENT_COLOR, width=1.5, dash=(6, 4))
            if plc_id in self.visual_elements:
                self.visual_elements[plc_id]['connection'] = line_id

    def draw_devices(self):
        x_o, y_o = ORCHESTRATOR_POS
        size = DEVICE_SIZE_ORCHESTRATOR / 2
        orch_id = self.canvas.create_oval(x_o - size, y_o - size, x_o + size, y_o + size,
                                          fill=ACCENT_COLOR, outline="white", width=3)
        text_id = self.canvas.create_text(x_o, y_o, text=ORCHESTRATOR_ID, fill="white", font=('Segoe UI', 12, 'bold'))
        self.visual_elements[ORCHESTRATOR_ID] = {'shape': orch_id, 'text': text_id}

        for plc_id, config in self.plc_statuses.items():
            x, y = config['pos']
            size = DEVICE_SIZE_PLC / 2
            color = STATE_COLORS.get(config['state'], "#333333")
            shape_id = self.canvas.create_rectangle(x - size, y - size, x + size, y + size,
                                                     fill=color, outline=TEXT_COLOR, width=2, tags=plc_id)
            text_id = self.canvas.create_text(x, y + size + 15, text=plc_id, fill=TEXT_COLOR, font=('Segoe UI', 10))
            
            alert_font = ('Arial', int(DEVICE_SIZE_PLC * 0.8), 'bold')
            alert_ids = []
            border_offset = 2

            for dx, dy in [(-border_offset, -border_offset), (border_offset, -border_offset), 
                           (-border_offset, border_offset), (border_offset, border_offset)]:
                border_id = self.canvas.create_text(x + dx, y + dy, text="!", fill="white",
                                                    font=alert_font, state=tk.HIDDEN)
                alert_ids.append(border_id)

            main_id = self.canvas.create_text(x, y, text="!", fill=ATTACK_PULSE_COLOR,
                                              font=alert_font, state=tk.HIDDEN)
            alert_ids.append(main_id)
            
            self.visual_elements[plc_id] = {'shape': shape_id, 'text': text_id, 'alert': alert_ids}

    def on_canvas_click(self, event):
        """Gestisce il click del mouse per risolvere attacchi e ripristinare i PLC."""
        item_id = self.canvas.find_withtag("current")
        if not item_id: return

        tags = self.canvas.gettags(item_id[0])
        if not tags: return

        plc_id = tags[0]

        if plc_id in self.plc_statuses:
            current_state = self.plc_statuses[plc_id]['state']

            if current_state == "ATTACCO":
                risposta = messagebox.askyesno(
                    "Conferma Intervento",
                    f"Il PLC '{plc_id}' è sotto attacco!\n\nVuoi tentare di isolare la minaccia e avviare la procedura di recupero?"
                )
                if risposta:
                    self.set_plc_state_and_log(plc_id, "RECUPERO")

            elif current_state == "RECUPERO":
                risposta = messagebox.askyesno(
                    "Conferma Ripristino",
                    f"Il PLC '{plc_id}' è in fase di recupero.\n\nVuoi ripristinarlo allo stato OPERATIVO?"
                )
                if risposta:
                    self.set_plc_state_and_log(plc_id, "OPERATIVO")

    def update_gui(self):
        for plc_id, config in self.plc_statuses.items():
            if plc_id not in self.visual_elements: continue

            elements = self.visual_elements[plc_id]
            current_state = config['state']
            
            new_color = STATE_COLORS.get(current_state, "#333333")
            self.canvas.itemconfig(elements['shape'], fill=new_color)

            connection_id = elements.get('connection')
            if connection_id:
                if current_state == 'ATTACCO':
                    self.canvas.itemconfig(connection_id, state=tk.HIDDEN)
                else:
                    self.canvas.itemconfig(connection_id, state=tk.NORMAL)

            is_under_attack = (current_state == "ATTACCO")
            if is_under_attack and plc_id not in self.animation_state:
                for item_id in elements['alert']:
                    self.canvas.itemconfig(item_id, state=tk.NORMAL)
                self.animation_state[plc_id] = True
                self.animate_attack(plc_id, pulse_on=True)
            elif not is_under_attack and plc_id in self.animation_state:
                for item_id in elements['alert']:
                    self.canvas.itemconfig(item_id, state=tk.HIDDEN)
                self.canvas.itemconfig(elements['shape'], outline=TEXT_COLOR)
                del self.animation_state[plc_id]

        self.after(UPDATE_INTERVAL_MS, self.update_gui)

    def animate_attack(self, plc_id, pulse_on):
        if plc_id not in self.animation_state:
            return

        elements = self.visual_elements[plc_id]
        
        outline_color = ATTACK_PULSE_COLOR if pulse_on else TEXT_COLOR
        self.canvas.itemconfig(elements['shape'], outline=outline_color)

        alert_color = ATTACK_PULSE_COLOR if pulse_on else STATE_COLORS["ATTACCO"]
        main_alert_id = elements['alert'][-1]
        self.canvas.itemconfig(main_alert_id, fill=alert_color)

        self.after(600, self.animate_attack, plc_id, not pulse_on)

    def log_message(self, message):
        self.log_area.config(state=tk.NORMAL)
        
        if "ATTACCO" in message:
            tag = "attack"
            self.log_area.tag_config("attack", foreground=STATE_COLORS["ATTACCO"], font=('Consolas', 10, 'bold'))
        elif "RECUPERO" in message or "RECOVERY" in message:
            tag = "recovery"
            self.log_area.tag_config("recovery", foreground=STATE_COLORS["RECUPERO"], font=('Consolas', 10, 'italic'))
        elif "ALIVE" in message:
            tag = "alive"
            self.log_area.tag_config("alive", foreground=STATE_COLORS["OPERATIVO"])
        else:
            tag = "info"
            self.log_area.tag_config("info", foreground="#9E9E9E")

        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ", ("time",))
        self.log_area.tag_config("time", foreground="#757575")
        self.log_area.insert(tk.END, f"{message}\n\n", (tag,))
        
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def set_plc_state_and_log(self, plc_id, new_state):
        if plc_id not in self.plc_statuses:
            return

        self.plc_statuses[plc_id]['state'] = new_state
        
        log_map = {
            "ATTACCO": f"*** EVENT *** PLC '{plc_id}' detected an ATTACK!",
            "OFF": f"*** EVENT *** PLC '{plc_id}' went OFFLINE.",
            "RECUPERO": f"*** EVENT *** PLC '{plc_id}' is in RECOVERY phase.",
            "OPERATIVO": f"*** EVENT *** PLC '{plc_id}' is back to OPERATIONAL."
        }
        log_msg = log_map.get(new_state)
        
        if log_msg:
            self.after(0, self.log_message, log_msg)
        
        if new_state == "ATTACCO":
            self.trigger_alert(plc_id)

    def trigger_alert(self, plc_id):
        self.after(0, lambda: messagebox.showwarning(
            "🚨 SECURITY ALERT 🚨",
            f"PLC '{plc_id}' is under attack!\nImmediate action required."
        ))

    def send_alive_message(self, plc_id):
        if self.plc_statuses[plc_id]['state'] == "OFF":
            self.set_plc_state_and_log(plc_id, "OPERATIVO")
        
        message = {
            "source": plc_id, "destination": ORCHESTRATOR_ID,
            "type": "ALIVE", "timestamp": time.time(),
            "status": self.plc_statuses[plc_id]['state']
        }
        json_message = json.dumps(message, indent=2)
        log = f"-> {plc_id}: Sending ALIVE signal.\n{json_message}"
        self.after(0, self.log_message, log)

    def plc_simulation_loop(self):
        last_alive_time = {plc_id: 0 for plc_id in self.plc_statuses}
        
        while True:
            time.sleep(1)
            current_time = time.time()
            
            for plc_id in self.plc_statuses:
                if current_time - last_alive_time[plc_id] >= ALIVE_MESSAGE_INTERVAL_S:
                    self.send_alive_message(plc_id)
                    last_alive_time[plc_id] = current_time

            if random.random() < 0.07:
                plc_to_change = random.choice(list(self.plc_statuses.keys()))
                current_state = self.plc_statuses[plc_to_change]['state']
                
                new_state = current_state

                if current_state == "OPERATIVO":
                    if random.random() < 0.2:
                        new_state = random.choice(["ATTACCO", "OFF"])
                elif current_state == "ATTACCO":
                    # Il PLC rimane sotto attacco finché l'utente non interviene
                    pass
                elif current_state == "RECUPERO":
                    # Il PLC rimane in recupero finché l'utente non interviene
                    pass
                elif current_state == "OFF":
                    if random.random() < 0.5:
                        new_state = "OPERATIVO"
                
                if new_state != current_state:
                    self.set_plc_state_and_log(plc_to_change, new_state)

if __name__ == "__main__":
    app = PLC_Orchestrator_Monitor()
    app.mainloop()