"""Réglages de l'application (surchargeables par variables d'environnement)."""
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent
DATA = RACINE / "data"
ANNEE = os.environ.get("PEDAFICHE_ANNEE", "2026-2027")
DB = os.environ.get("PEDAFICHE_DB", str(RACINE.parent / "instance" / "pedafiche.db"))
SECRET_KEY = os.environ.get("PEDAFICHE_SECRET", "changer-cette-cle-en-production")

# Mention « Conception » imprimée en pied de chaque fiche, résumé et épreuve.
CONCEPTEUR = os.environ.get("PEDAFICHE_CONCEPTEUR", "Maître Aimé FACHOLA")
CONCEPTEUR_TEL = os.environ.get("PEDAFICHE_CONCEPTEUR_TEL", "+229 01 96 51 03 33")


def secondaire() -> bool:           # utilisé par la banque d'épreuves d'EPS
    return False
