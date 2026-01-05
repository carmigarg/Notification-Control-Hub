import threading
import time
import json
import random

LOCK = threading.Lock()


def carica_stato():
    with open("stato.json", "r", encoding="utf-8") as f:
        return json.load(f)

def salva_stato(stato):
    with open("stato.json", "w", encoding="utf-8") as f:
        json.dump(stato, f, indent=4)


def ripara(componente, stato):
    nome = componente["nome"]
    tempo_limite = componente["tempo_limite"]
    priorita = componente["priorita"]
    costo = componente["costo"]
    rischio = componente.get("rischio_ricaduta", 0)

    print(f"\n⚠️ {nome} danneggiato! Tempo limite: {tempo_limite} secondi")
    print(f"Azioni disponibili: [r]ipara ({costo} risorse), [i]gnora, [a]nalizza")
    
    inizio = time.time()
    scelta = input(f"Cosa vuoi fare con {nome}? ").strip().lower()
    tempo_impiegato = time.time() - inizio

    with LOCK:
        if scelta == "r":
            if stato["risorse"] < costo:
                print(f"❌ Non hai abbastanza risorse per riparare {nome}!")
            elif tempo_impiegato > tempo_limite:
                print(f"❌ Tempo scaduto! {nome} non riparato.")
                stato["risorse"] -= costo // 2  
            else:
                stato["risorse"] -= costo
                punti = int((tempo_limite - tempo_impiegato) * 10) * priorita
                stato["punteggio"] += punti
                componente["riparato"] = True
               
                if random.random() < rischio:
                    componente["riparato"] = False
                    print(f"⚠️ {nome} è guasto di nuovo subito dopo la riparazione!")
                else:
                    print(f"✅ {nome} riparato! +{punti} punti, -{costo} risorse")
        elif scelta == "a":
            print(f"🔍 Analisi di {nome}: priorità {priorita}, tempo limite {tempo_limite} sec, costo riparazione {costo}, rischio ricaduta {rischio*100}%")
           
            componente["priorita"] += 1
            print(f"✨ Priorità temporaneamente aumentata a {componente['priorita']}")
        else:
            print(f"⚠️ Hai ignorato {nome}!")

        salva_stato(stato)


def missione(stato):
    print(f"\n🎮 Missione {stato['missione_corrente']}")
    componenti_non_riparati = [c for c in stato["componenti"] if not c.get("riparato", False)]
    
    threads = []
    while componenti_non_riparati:
      
        ondata = componenti_non_riparati[:2]
        componenti_non_riparati = componenti_non_riparati[2:]

        for c in ondata:
            t = threading.Thread(target=ripara, args=(c, stato))
            threads.append(t)
            t.start()

        time.sleep(random.randint(3,6))

    for t in threads:
        t.join()

    print(f"\n🚨 Missione {stato['missione_corrente']} terminata!")
    print(f"🏆 Punteggio: {stato['punteggio']}, Risorse: {stato['risorse']}")

def main():
    reset = input("Vuoi ricominciare da zero? (s/n): ").strip().lower()
    if reset == "s":
        stato = {
            "missione_corrente": 1,
            "punteggio": 0,
            "risorse": 50,
            "componenti": [
                {"nome": "Motore principale", "tempo_limite": 15, "priorita": 5, "costo": 10, "riparato": False, "rischio_ricaduta": 0.1},
                {"nome": "Generatore elettrico", "tempo_limite": 10, "priorita": 3, "costo": 8, "riparato": False, "rischio_ricaduta": 0.1},
                {"nome": "Sistema radar", "tempo_limite": 12, "priorita": 4, "costo": 9, "riparato": False, "rischio_ricaduta": 0.05},
                {"nome": "Armeria", "tempo_limite": 8, "priorita": 2, "costo": 5, "riparato": False, "rischio_ricaduta": 0.05},
                {"nome": "Sistema comunicazioni", "tempo_limite": 10, "priorita": 3, "costo": 7, "riparato": False, "rischio_ricaduta": 0.1}
            ]
        }
        salva_stato(stato)
    else:
        stato = carica_stato()

    while True:
        missione(stato)
        stato["missione_corrente"] += 1
     
        for c in stato["componenti"]:
            c["riparato"] = False
            c["priorita"] = max(c["priorita"] - 1, 1)
        salva_stato(stato)

        cont = input("Vuoi proseguire con la prossima missione? (s/n): ").strip().lower()
        if cont != "s":
            print("🛑 Gioco terminato. Grazie per aver giocato!")
            break

if __name__ == "__main__":
    main()
