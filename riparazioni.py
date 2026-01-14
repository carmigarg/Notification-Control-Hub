import tkinter as tk
from tkinter import ttk
import json
import random

FILE_STATO = "componenti.json"

# --- CARICA JSON ESTERNO ---
with open(FILE_STATO, "r", encoding="utf-8") as f:
    stato = json.load(f)

# Campi generali del gioco
stato.setdefault("missione_corrente", 1)
stato.setdefault("punteggio", 0)
stato.setdefault("risorse", 50)
stato.setdefault("strumenti", {"sconto_riparazioni": 0})

# Assicurati che ogni componente abbia "riparato" e "tempo_restante"
for c in stato["componenti"]:
    c.setdefault("riparato", False)
    c.setdefault("tempo_restante", c["tempo_limite"])


# --- FUNZIONI DI SALVATAGGIO E RESET ---
def salva_stato():
    with open(FILE_STATO, "w", encoding="utf-8") as f:
        json.dump(stato, f, indent=4, ensure_ascii=False)

def reset_stato(difficolta=None):
    global stato
    # Ricarica JSON originale
    with open(FILE_STATO, "r", encoding="utf-8") as f:
        stato = json.load(f)

    stato.setdefault("missione_corrente", 1)
    stato.setdefault("punteggio", 0)
    stato.setdefault("risorse", 50)
    stato.setdefault("strumenti", {"sconto_riparazioni": 0})

    for c in stato["componenti"]:
        c.setdefault("riparato", False)
        c.setdefault("tempo_restante", c["tempo_limite"])

    if difficolta:
        applica_difficolta(difficolta)
    aggiorna_gui()
    notifica("✅ Stato resettato!", "success")
    salva_stato()


# --- FUNZIONI DI GIOCO ---
def applica_difficolta(difficolta):
    if difficolta == "facile":
        moltiplicatore = 0.5
    elif difficolta == "medio":
        moltiplicatore = 1
    elif difficolta == "difficile":
        moltiplicatore = 1.5
    else:
        moltiplicatore = 1
    for c in stato["componenti"]:
        c["tempo_restante"] = int(c["tempo_limite"] / moltiplicatore)
        c["tempo_limite"] = int(c["tempo_limite"] / moltiplicatore)


def colore_tempo(c):
    perc = c["tempo_restante"] / c["tempo_limite"]
    if perc <= 0.25:
        return "#e74c3c"
    elif perc <= 0.5:
        return "#f1c40f"
    else:
        return "#2ecc71"


def crea_bottone(master, text, comando, colore="#3498db"):
    btn = tk.Button(master, text=text, command=comando,
                    bg=colore, fg="white", font=("Arial", 11, "bold"),
                    activebackground="#2980b9", activeforeground="white",
                    relief="flat", bd=0, padx=8, pady=4, cursor="hand2")
    def on_enter(e): btn.config(bg="#2980b9")
    def on_leave(e): btn.config(bg=colore)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


combo_counter = 0

def tick_timer():
    changed = False
    for c in stato["componenti"]:
        if not c["riparato"]:
            c["tempo_restante"] -= 1
            if c["tempo_restante"] <= 0:
                c["tempo_restante"] = c["tempo_limite"]
                c["priorita"] += 1
                stato["punteggio"] = max(0, stato["punteggio"] - 10)
                notifica(f"{c['nome']} è peggiorato! -10 punti", "warning")
                changed = True
    if changed:
        aggiorna_gui()
    root.after(1000, tick_timer)


def ripara(c):
    global combo_counter
    costo_effettivo = max(1, int(c["costo"] * (1 - stato["strumenti"]["sconto_riparazioni"])))
    if stato["risorse"] < costo_effettivo:
        notifica("Risorse insufficienti!", "error")
        combo_counter = 0
        return
    stato["risorse"] -= costo_effettivo
    punti = c["priorita"] * 10
    if random.random() < c["rischio_ricaduta"]:
        c["tempo_restante"] = c["tempo_limite"]
        notifica(f"{c['nome']} si è guastato di nuovo!", "warning")
        combo_counter = 0
    else:
        c["riparato"] = True
        extra = 0
        combo_counter += 1
        if combo_counter >= 2:
            extra += combo_counter * 2
        if c["tempo_restante"] > c["tempo_limite"] * 0.5:
            extra += 5
        punti += extra
        stato["punteggio"] += punti
        notifica(f"{c['nome']} riparato! +{punti} punti (+{extra} combo)", "success")
    aggiorna_gui()


def analizza(c):
    c["rischio_ricaduta"] = max(0, c["rischio_ricaduta"] - 0.1)
    c["tempo_restante"] += 5
    notifica(f"{c['nome']} analizzato: rischio ridotto, +5s", "info")
    aggiorna_gui()


def ignora(c):
    stato["punteggio"] = max(0, stato["punteggio"] - 5)
    c["priorita"] += 1
    c["riparato"] = True
    global combo_counter
    combo_counter = 0
    notifica(f"{c['nome']} ignorato: -5 punti, priorità aumentata", "warning")
    aggiorna_gui()


def acquista_strumento():
    if stato["risorse"] < 15:
        notifica("Risorse insufficienti!", "error")
        return
    stato["risorse"] -= 15
    stato["strumenti"]["sconto_riparazioni"] = min(0.5, stato["strumenti"]["sconto_riparazioni"] + 0.1)
    notifica(f"Strumento acquistato! Sconto riparazioni: {int(stato['strumenti']['sconto_riparazioni']*100)}%", "success")
    aggiorna_gui()


def controlla_side_quest():
    if random.random() < 0.2:
        bonus = random.choice(["risorse", "punteggio"])
        if bonus == "risorse":
            stato["risorse"] += 10
            notifica("🎁 Side quest completata! +10 risorse", "success")
        else:
            stato["punteggio"] += 10
            notifica("🎁 Side quest completata! +10 punti", "success")


def notifica(msg, tipo="info"):
    colors = {
        "info": "#3498db",
        "success": "#27ae60",
        "warning": "#f39c12",
        "error": "#e74c3c"
    }
    lbl_notifica.config(text=msg, fg=colors.get(tipo, "white"))
    root.after(2500, lambda: lbl_notifica.config(text=""))


def aggiorna_gui():
    if 'lbl_missione' not in globals(): return
    lbl_missione.config(text=f"🚀 Missione {stato['missione_corrente']}")
    lbl_punteggio.config(text=f"🏆 {stato['punteggio']} punti")
    lbl_risorse.config(text=f"🔋 {stato['risorse']} risorse")

    for w in frame_componenti.winfo_children():
        w.destroy()

    non_riparati = [c for c in stato["componenti"] if not c["riparato"]]
    progress["maximum"] = len(stato["componenti"])
    progress["value"] = len(stato["componenti"]) - len(non_riparati)

    if not non_riparati:
        btn_next.config(state="normal")
        controlla_side_quest()
        return

    for c in non_riparati:
        perc = c["tempo_restante"] / c["tempo_limite"]
        colore = colore_tempo(c)
        lampeggio = "#ff0000" if perc <= 0.25 and int(c["tempo_restante"]) % 2 == 0 else colore

        card = tk.Frame(
            frame_componenti,
            bg="#1a1a1a",
            highlightbackground=lampeggio,
            highlightthickness=3,
            padx=10,
            pady=8
        )
        card.pack(fill="x", pady=6)

        tk.Label(
            card,
            text=f"{c['icona']} {c['nome']}",
            font=("Arial", 13, "bold"),
            fg="white",
            bg="#1a1a1a"
        ).pack(anchor="w")

        tk.Label(
            card,
            text=f"⏱ {c['tempo_restante']}s   ⭐ {c['priorita']}   💰 {c['costo']}   ⚠️ {int(c['rischio_ricaduta']*100)}%",
            fg=lampeggio,
            bg="#1a1a1a",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        btns = tk.Frame(card, bg="#1a1a1a")
        btns.pack(anchor="e", pady=5)

        crea_bottone(btns, "🔧 Ripara", lambda x=c: ripara(x), "#27ae60").pack(side="left", padx=3)
        crea_bottone(btns, "🔍 Analizza", lambda x=c: analizza(x), "#f39c12").pack(side="left", padx=3)
        crea_bottone(btns, "❌ Ignora", lambda x=c: ignora(x), "#e74c3c").pack(side="left", padx=3)

    salva_stato()


def prossima_missione():
    stato["missione_corrente"] += 1
    stato["risorse"] += 20
    for c in stato["componenti"]:
        c["riparato"] = False
        c["priorita"] = max(1, c["priorita"] - 1)
        c["tempo_restante"] = c["tempo_limite"]
    btn_next.config(state="disabled")
    aggiorna_gui()
    notifica(f"🚀 Inizio missione {stato['missione_corrente']}!", "info")


# --- INTERFACCIA GRAFICA ---
root = tk.Tk()
root.title("🚀 Centro Riparazioni Spaziale")
root.geometry("840x650")
root.configure(bg="#0f0f0f")
root.bell = lambda *args, **kwargs: None

def start_gioco(difficolta):
    schermata_iniziale.pack_forget()
    reset_stato(difficolta)
    root.after(1000, tick_timer)

schermata_iniziale = tk.Frame(root, bg="#0f0f0f")
schermata_iniziale.pack(fill="both", expand=True)

tk.Label(schermata_iniziale, text="🚀 Scegli la difficoltà", font=("Arial", 18, "bold"), fg="#00e5ff", bg="#0f0f0f").pack(pady=40)
crea_bottone(schermata_iniziale, "Facile", lambda: start_gioco("facile"), "#27ae60").pack(pady=10)
crea_bottone(schermata_iniziale, "Medio", lambda: start_gioco("medio"), "#f1c40f").pack(pady=10)
crea_bottone(schermata_iniziale, "Difficile", lambda: start_gioco("difficile"), "#e74c3c").pack(pady=10)

header = tk.Frame(root, bg="#0f0f0f")
header.pack(pady=10)
lbl_missione = tk.Label(header, font=("Arial", 18, "bold"), fg="#00e5ff", bg="#0f0f0f")
lbl_missione.pack()
lbl_punteggio = tk.Label(header, fg="white", bg="#0f0f0f", font=("Arial", 12))
lbl_punteggio.pack()
lbl_risorse = tk.Label(header, fg="white", bg="#0f0f0f", font=("Arial", 12))
lbl_risorse.pack()

lbl_notifica = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#0f0f0f")
lbl_notifica.pack(pady=5)

progress = ttk.Progressbar(root, length=440)
progress.pack(pady=8)

frame_componenti = tk.Frame(root, bg="#0f0f0f")
frame_componenti.pack(fill="both", expand=True, padx=12)

btn_next = crea_bottone(root, "➡️ Prossima Missione", prossima_missione, "#27ae60")
btn_next.config(state="disabled")
btn_next.pack(pady=6)

btn_reset = crea_bottone(root, "🔄 Reset Stato", lambda: reset_stato(), "#c0392b")
btn_reset.pack(pady=4)

btn_strumento = crea_bottone(root, "🛠 Acquista Strumento (15 risorse)", acquista_strumento, "#9b59b6")
btn_strumento.pack(pady=4)

root.mainloop()
