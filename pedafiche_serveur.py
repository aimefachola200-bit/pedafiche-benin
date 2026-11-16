# -*- coding: utf-8 -*-
"""pédafiche pour Windows : démarre l'application sur ce PC (sans Internet) et l'ouvre dans le navigateur.

Les données (comptes, fiches, notes) sont dans %LOCALAPPDATA%\\PedaFiche. Fermer la petite fenêtre arrête pédafiche."""
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser

PORT = int(os.environ.get("PEDAFICHE_PORT", "5050"))


def dossier_donnees():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".pedafiche")
    d = os.path.join(base, "PedaFiche") if os.environ.get("LOCALAPPDATA") else base
    os.makedirs(d, exist_ok=True)
    return d


def cle_secrete(d):
    p = os.path.join(d, "cle.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    k = secrets.token_hex(32)
    with open(p, "w", encoding="utf-8") as f:
        f.write(k)
    return k


def port_occupe(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def preparer():
    d = dossier_donnees()
    os.environ.setdefault("PEDAFICHE_DB", os.path.join(d, "pedafiche.db"))
    os.environ.setdefault("PEDAFICHE_SECRET", cle_secrete(d))
    os.environ["PEDAFICHE_AUTONOME"] = "1"
    return d


def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    url = f"http://127.0.0.1:{PORT}"
    if port_occupe(PORT):                      # déjà lancé : on ouvre simplement le navigateur
        webbrowser.open(url)
        return
    d = preparer()
    erreur = {"msg": None}

    def serveur():
        try:
            from pedafiche.web import create_app
            try:
                from waitress import serve
                serve(create_app(), host="127.0.0.1", port=PORT, threads=8)
            except ImportError:                # secours : serveur de Werkzeug
                from werkzeug.serving import make_server
                make_server("127.0.0.1", PORT, create_app(), threaded=True).serve_forever()
        except Exception as e:  # noqa: BLE001
            erreur["msg"] = str(e)

    threading.Thread(target=serveur, daemon=True).start()
    if "--sans-fenetre" in sys.argv:           # essais automatiques
        while True:
            time.sleep(60)

    import tkinter as tk
    from tkinter import messagebox
    BLEU, FOND, GRIS, VERT, ROUGE = "#1F4E79", "#F4F6F9", "#667085", "#1B7F3B", "#B42318"
    fen = tk.Tk()
    fen.title("pédafiche")
    fen.configure(bg=FOND)
    fen.resizable(False, False)
    try:
        from pedafiche import __version__ as v
    except Exception:  # noqa: BLE001
        v = ""
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pedafiche", "web", "static", "icons", "pedafiche.ico")
    if os.path.exists(ico):
        try:
            fen.iconbitmap(ico)
        except tk.TclError:
            pass
    haut = tk.Frame(fen, bg=BLEU)
    haut.pack(fill="x")
    tk.Label(haut, text="pédafiche", bg=BLEU, fg="white", font=("Segoe UI", 15, "bold"), padx=18, pady=10).pack(side="left")
    tk.Label(haut, text=f"v{v}", bg=BLEU, fg="#DCE6F2", font=("Segoe UI", 9), padx=12).pack(side="right")
    corps = tk.Frame(fen, bg=FOND, padx=18, pady=14)
    corps.pack(fill="both")
    etat = tk.Label(corps, text="● Démarrage…", bg=FOND, fg=GRIS, font=("Segoe UI", 11, "bold"))
    etat.pack(anchor="w")
    tk.Label(corps, text="pédafiche fonctionne sur ce PC, sans Internet.\nVos données restent sur cet ordinateur.",
             justify="left", bg=FOND, fg=GRIS, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 0))
    bt = tk.Frame(fen, bg=FOND, padx=18, pady=12)
    bt.pack(fill="x")
    style = dict(font=("Segoe UI", 10), padx=12, pady=5, relief="flat", cursor="hand2", bd=0)

    def quitter():
        if messagebox.askyesno("Arrêter pédafiche", "Arrêter pédafiche ?"):
            fen.destroy()
            os._exit(0)

    tk.Button(bt, text="Ouvrir pédafiche", command=lambda: webbrowser.open(url), bg=BLEU, fg="white", **style).pack(side="left")
    tk.Button(bt, text="Dossier des données", command=lambda: os.startfile(d) if sys.platform.startswith("win") else None,  # noqa: S606
              bg="white", fg=BLEU, **style).pack(side="left", padx=6)
    tk.Button(bt, text="Arrêter", command=quitter, bg="white", fg=ROUGE, **style).pack(side="right")
    tk.Label(fen, text="Laissez cette fenêtre ouverte (vous pouvez la réduire).", bg=FOND, fg=GRIS,
             font=("Segoe UI", 8), padx=18).pack(anchor="w")
    tk.Label(fen, text="Conception : Maître Aimé FACHOLA", bg=FOND, fg=GRIS, font=("Segoe UI", 8, "italic"), pady=6).pack()
    fen.protocol("WM_DELETE_WINDOW", quitter)
    debut, ouvert = time.time(), {"fait": False}

    def surveiller():
        if erreur["msg"]:
            etat.config(text="● Erreur : " + erreur["msg"][:70], fg=ROUGE)
            return
        if port_occupe(PORT):
            etat.config(text="● pédafiche est en marche", fg=VERT)
            if not ouvert["fait"]:
                ouvert["fait"] = True
                webbrowser.open(url)
        elif time.time() - debut > 30:
            etat.config(text="● Le serveur ne répond pas", fg=ROUGE)
        fen.after(1500, surveiller)

    fen.after(800, surveiller)
    fen.mainloop()


if __name__ == "__main__":
    main()
