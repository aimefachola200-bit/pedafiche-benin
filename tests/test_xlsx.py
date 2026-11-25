"""Excel (v2.5.1) : modèle des élèves et feuille de notes, aller-retour."""
import pytest

openpyxl = pytest.importorskip("openpyxl")
from pedafiche import xlsx_io as X


ELEVES = [{"id": 1, "nom": "ADJOVI", "prenom": "Koffi", "sexe": "M", "naissance": "12/03/2017", "telephone": "0196000000", "matricule": ""},
          {"id": 2, "nom": "HOUNKPATIN", "prenom": "Awa", "sexe": "F", "naissance": "", "telephone": "", "matricule": "M2"}]


def test_eleves_aller_retour():
    octets = X.modele_eleves("CE1", ELEVES)
    liste, err = X.lire_eleves(octets, "CE1")
    assert err is None and [e["nom"] for e in liste] == ["ADJOVI", "HOUNKPATIN"]
    assert liste[0]["sexe"] == "M" and liste[0]["naissance"] == "12/03/2017" and liste[1]["sexe"] == "F"


def test_notes_aller_retour_et_controles():
    ev = {"id": 5, "titre": "Devoir 1", "matiere": "maths", "bareme": 20}
    octets = X.modele_notes(ELEVES, ev, {1: 15.5, 2: None}, "Maths")
    res, msg = X.lire_notes(octets, ELEVES, ev, "maths")
    assert res == {1: 15.5} and not msg
    wb = openpyxl.load_workbook(__import__("io").BytesIO(octets))
    ws = wb.active
    ws.cell(row=3, column=4, value="25")
    ws.cell(row=4, column=4, value="12,5")
    tampon = __import__("io").BytesIO()
    wb.save(tampon)
    res, msg = X.lire_notes(tampon.getvalue(), ELEVES, ev, "maths")
    assert res == {2: 12.5} and any("hors" in m for m in msg)
