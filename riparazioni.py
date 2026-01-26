import tkinter as tk
from tkinter import ttk, messagebox
import json
import random
import os

FILE_STATO = "componenti.json"


if not os.path.exists(FILE_STATO):
    messagebox.showerror("Errore", f"File {FILE_STATO} non trovato!")
    exit()

with open(FILE_STATO, "r", encoding="utf-8") as f:
    stato = json.load(f)


stato.setdefault("missione_corrente", 1)
stato.setdefault("punteggio", 0)
stato.setdefault("risorse", 50)
stato.setdefault("strumenti", {"sconto_riparazioni": 0})

for c in stato["componenti"]:
    c.setdefault("riparato", False)
    c.setdefault("tempo_restante", c["tempo_limite"])
    c.setdefault("priorita", 1)


gioco_avviato = False
combo_counter = 0


def salva_stato():
    with open(FILE_STATO, "w", encoding="utf-8") as f:
        json.dump(stato, f, indent=4, ensure_ascii=False)

def reset_stato(difficolta=None):
    global stato, combo_counter
    with open(FILE_STATO, "r", encoding="utf-8") as f:
        stato = json.load(f)
    for c in stato["componenti"]:
        c["riparato"] = False
        c["tempo_restante"] = c["tempo_limite"]
    stato["missione_corrente"] = 1
    stato["punteggio"] = 0
    stato["risorse"] = 50
    stato["strumenti"] = {"sconto_riparazioni": 0}
    combo_counter = 0
    if difficolta:
        applica_difficolta(difficolta)
    aggiorna_gui()
    salva_stato()
    notifica("✅ Stato resettato!", "success")

def applica_difficolta(difficolta):
    moltiplicatore = {"facile":0.5, "medio":1, "difficile":1.5}.get(difficolta, 1)
    for c in stato["componenti"]:
        c["tempo_restante"] = int(c["tempo_limite"] / moltiplicatore)
        c["tempo_limite"] = int(c["tempo_limite"] / moltiplicatore)

def colore_tempo(c):
    perc = c["tempo_restante"] / c["tempo_limite"]
    return "#e74c3c" if perc <= 0.25 else "#f1c40f" if perc <= 0.5 else "#2ecc71"

def crea_bottone(master, text, comando, colore="#3498db"):
    btn = tk.Button(master, text=text, command=comando, bg=colore, fg="white",
                    font=("Arial",11,"bold"), relief="flat", bd=0, padx=8, pady=4, cursor="hand2")
    btn.bind("<Enter>", lambda e: btn.config(bg="#2980b9"))
    btn.bind("<Leave>", lambda e: btn.config(bg=colore))
    return btn

def tick_timer():
    if not gioco_avviato:
        return
    changed = False
    for c in stato["componenti"]:
        if not c["riparato"]:
            c["tempo_restante"] -= 1
            if c["tempo_restante"] <= 0:
                c["tempo_restante"] = c["tempo_limite"]
                c["priorita"] += 1
                stato["punteggio"] = max(0, stato["punteggio"]-10)
                notifica(f"{c['nome']} peggiorato! -10 punti","warning")
                changed = True
    if changed: aggiorna_gui()
    root.after(1000, tick_timer)

def ripara(c):
    global combo_counter
    if not gioco_avviato:
        notifica("❌ Inizia una missione prima di riparare","error")
        return
    costo_eff = max(1, int(c["costo"]*(1-stato["strumenti"]["sconto_riparazioni"])))
    if stato["risorse"] < costo_eff:
        notifica("Risorse insufficienti!", "error")
        combo_counter = 0
        return
    stato["risorse"] -= costo_eff
    punti = c["priorita"]*10
    if random.random() < c["rischio_ricaduta"]:
        c["tempo_restante"] = c["tempo_limite"]
        notifica(f"{c['nome']} si è guastato di nuovo!","warning")
        combo_counter = 0
    else:
        c["riparato"] = True
        combo_counter += 1
        extra = (combo_counter*2 if combo_counter>=2 else 0) + (5 if c["tempo_restante"]>c["tempo_limite"]*0.5 else 0)
        punti += extra
        stato["punteggio"] += punti
        notifica(f"{c['nome']} riparato! +{punti} punti (+{extra} combo)","success")
    aggiorna_gui()

def analizza(c):
    if not gioco_avviato:
        notifica("❌ Inizia una missione prima di analizzare","error")
        return
    c["rischio_ricaduta"] = max(0, c["rischio_ricaduta"]-0.1)
    c["tempo_restante"] += 5
    notifica(f"{c['nome']} analizzato: rischio ridotto, +5s","info")
    aggiorna_gui()

def ignora(c):
    global combo_counter
    if not gioco_avviato:
        notifica("❌ Inizia una missione prima di ignorare","error")
        return
    stato["punteggio"] = max(0, stato["punteggio"]-5)
    c["priorita"] +=1
    c["riparato"]=True
    combo_counter = 0
    notifica(f"{c['nome']} ignorato: -5 punti, priorità aumentata","warning")
    aggiorna_gui()

def acquista_strumento():
    global gioco_avviato
    if not gioco_avviato:
        notifica("❌ Inizia una missione prima di acquistare strumenti","error")
        return
    if stato["risorse"] < 15:
        notifica("Risorse insufficienti!", "error")
        return
    stato["risorse"] -= 15
    stato["strumenti"]["sconto_riparazioni"] = min(0.5, stato["strumenti"]["sconto_riparazioni"] + 0.1)
    notifica(f"Strumento acquistato! Sconto riparazioni: {int(stato['strumenti']['sconto_riparazioni']*100)}%","success")
    aggiorna_gui()

def controlla_side_quest():
    if random.random()<0.2:
        bonus=random.choice(["risorse","punteggio"])
        if bonus=="risorse":
            stato["risorse"]+=10
            notifica("🎁 Side quest completata! +10 risorse","success")
        else:
            stato["punteggio"]+=10
            notifica("🎁 Side quest completata! +10 punti","success")

def notifica(msg, tipo="info"):
    colors = {"info":"#3498db","success":"#27ae60","warning":"#f39c12","error":"#e74c3c"}
    lbl_notifica.config(text=msg, fg=colors.get(tipo,"white"))
    root.after(2500, lambda: lbl_notifica.config(text=""))

def aggiorna_gui():
    lbl_missione.config(text=f"🚀 Missione {stato['missione_corrente']}")
    lbl_punteggio.config(text=f"🏆 {stato['punteggio']} punti")
    lbl_risorse.config(text=f"🔋 {stato['risorse']} risorse")
    for w in frame_componenti.winfo_children():
        w.destroy()

    if not gioco_avviato:
        return

    non_riparati=[c for c in stato["componenti"] if not c["riparato"]]
    progress["maximum"]=len(stato["componenti"])
    progress["value"]=len(stato["componenti"])-len(non_riparati)

    if not non_riparati:
        btn_next.config(state="normal")
        controlla_side_quest()
        return

    for c in non_riparati:
        col=colore_tempo(c)
        lampeggio="#ff0000" if c["tempo_restante"]/c["tempo_limite"]<=0.25 and int(c["tempo_restante"])%2==0 else col
        card=tk.Frame(frame_componenti,bg="#1a1a1a",highlightbackground=lampeggio,highlightthickness=3,padx=10,pady=8)
        card.pack(fill="x",pady=6)
        tk.Label(card,text=f"{c['icona']} {c['nome']}",font=("Arial",13,"bold"),fg="white",bg="#1a1a1a").pack(anchor="w")
        tk.Label(card,text=f"⏱ {c['tempo_restante']}s ⭐ {c['priorita']} 💰 {c['costo']} ⚠️ {int(c['rischio_ricaduta']*100)}%",fg=lampeggio,bg="#1a1a1a",font=("Arial",11,"bold")).pack(anchor="w")
        btns=tk.Frame(card,bg="#1a1a1a")
        btns.pack(anchor="e",pady=5)
        crea_bottone(btns,"🔧 Ripara",lambda x=c: ripara(x),"#27ae60").pack(side="left",padx=3)
        crea_bottone(btns,"🔍 Analizza",lambda x=c: analizza(x),"#f39c12").pack(side="left",padx=3)
        crea_bottone(btns,"❌ Ignora",lambda x=c: ignora(x),"#e74c3c").pack(side="left",padx=3)

    salva_stato()

def prossima_missione():
    global gioco_avviato
    stato["missione_corrente"] += 1
    stato["risorse"] += 20
    for c in stato["componenti"]:
        c["riparato"] = False
        c["tempo_restante"] = c["tempo_limite"]
        c["priorita"] = max(1, c["priorita"]-1)
    btn_next.config(state="disabled")
    aggiorna_gui()
    notifica(f"🚀 Inizio missione {stato['missione_corrente']}!","info")

def start_gioco_difficolta(difficolta):
    global gioco_avviato
    schermata_iniziale.pack_forget()
    gioco_avviato = True
    reset_stato(difficolta)
    root.after(1000, tick_timer)
    aggiorna_gui()


root = tk.Tk()
root.title("🚀 Centro Riparazioni Spaziale")
root.geometry("840x650")
root.configure(bg="#0f0f0f")

schermata_iniziale = tk.Frame(root,bg="#0f0f0f")
schermata_iniziale.pack(fill="both",expand=True)
tk.Label(schermata_iniziale,text="🚀 Scegli la difficoltà",font=("Arial",18,"bold"),fg="#00e5ff",bg="#0f0f0f").pack(pady=40)
crea_bottone(schermata_iniziale,"Facile",lambda:start_gioco_difficolta("facile"),"#27ae60").pack(pady=10)
crea_bottone(schermata_iniziale,"Medio",lambda:start_gioco_difficolta("medio"),"#f1c40f").pack(pady=10)
crea_bottone(schermata_iniziale,"Difficile",lambda:start_gioco_difficolta("difficile"),"#e74c3c").pack(pady=10)

header=tk.Frame(root,bg="#0f0f0f"); header.pack(pady=10)
lbl_missione=tk.Label(header,font=("Arial",18,"bold"),fg="#00e5ff",bg="#0f0f0f"); lbl_missione.pack()
lbl_punteggio=tk.Label(header,fg="white",bg="#0f0f0f",font=("Arial",12)); lbl_punteggio.pack()
lbl_risorse=tk.Label(header,fg="white",bg="#0f0f0f",font=("Arial",12)); lbl_risorse.pack()
lbl_notifica=tk.Label(root,text="",font=("Arial",12,"bold"),bg="#0f0f0f"); lbl_notifica.pack(pady=5)
progress=ttk.Progressbar(root,length=440); progress.pack(pady=8)
frame_componenti=tk.Frame(root,bg="#0f0f0f"); frame_componenti.pack(fill="both",expand=True,padx=12)

btn_next=crea_bottone(root,"➡️ Prossima Missione",prossima_missione,"#27ae60"); btn_next.pack(pady=6)
btn_next.config(state="disabled")
btn_reset=crea_bottone(root,"🔄 Reset Stato",lambda: reset_stato(),"#c0392b"); btn_reset.pack(pady=4)
btn_strumento=crea_bottone(root,"🛠 Acquista Strumento (15 risorse)",acquista_strumento,"#9b59b6"); btn_strumento.pack(pady=4)

root.mainloop()
