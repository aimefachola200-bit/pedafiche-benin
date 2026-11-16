# -*- coding: utf-8 -*-
"""Démarrage de pédafiche à l'intérieur de l'application Android autonome (sans Internet).
Le serveur tourne sur l'appareil (http://127.0.0.1:PORT) ; données dans le dossier privé de l'application."""
import os
import secrets
import socket
import threading

PORT_FIXE = 8766
_serveur = {"url": None}


def _port_libre(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _metadonnees_tolerantes():
    import importlib.metadata as md
    origine = md.version

    def version(nom):
        try:
            return origine(nom)
        except md.PackageNotFoundError:
            return "0"
    md.version = version


def _cle(dossier):
    p = os.path.join(dossier, "cle.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    k = secrets.token_hex(32)
    with open(p, "w", encoding="utf-8") as f:
        f.write(k)
    return k


def demarrer(dossier_donnees, dossier_web):
    if _serveur["url"]:
        return _serveur["url"]
    os.makedirs(dossier_donnees, exist_ok=True)
    os.environ["PEDAFICHE_DB"] = os.path.join(dossier_donnees, "pedafiche.db")
    os.environ["PEDAFICHE_SECRET"] = _cle(dossier_donnees)
    os.environ["PEDAFICHE_AUTONOME"] = "1"
    _metadonnees_tolerantes()
    from werkzeug.serving import make_server
    from pedafiche.web import create_app

    port = PORT_FIXE if _port_libre(PORT_FIXE) else 0
    serveur = make_server("127.0.0.1", port, create_app(), threaded=True)
    port = serveur.server_port
    threading.Thread(target=serveur.serve_forever, name="pedafiche", daemon=True).start()
    _serveur["url"] = f"http://127.0.0.1:{port}"
    return _serveur["url"]
