"""Base SQLite : comptes, classes, affectations, emplois du temps personnalisés, suivi."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  identifiant TEXT NOT NULL UNIQUE,
  nom TEXT NOT NULL, prenom TEXT DEFAULT '',
  role TEXT NOT NULL CHECK (role IN ('admin','directeur','enseignant')),
  mdp_hash TEXT NOT NULL, actif INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS classes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL, cours TEXT NOT NULL, ecole TEXT DEFAULT '',
  circonscription TEXT DEFAULT '', effectif INTEGER DEFAULT 0, annee TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS affectations (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  classe_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, classe_id));
CREATE TABLE IF NOT EXISTS edt_classe (
  classe_id INTEGER PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE, contenu TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS suivi (
  classe_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  fiche_id TEXT NOT NULL, date_realisee TEXT, observation TEXT DEFAULT '',
  PRIMARY KEY (classe_id, fiche_id));
CREATE TABLE IF NOT EXISTS mes_fiches (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  classe_id INTEGER REFERENCES classes(id) ON DELETE SET NULL, cours TEXT NOT NULL, base_id TEXT DEFAULT '',
  titre TEXT NOT NULL, matiere TEXT NOT NULL, contenu TEXT NOT NULL, partage INTEGER NOT NULL DEFAULT 0,
  cree TEXT NOT NULL, maj TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS eleves (
  id INTEGER PRIMARY KEY AUTOINCREMENT, classe_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  matricule TEXT DEFAULT '', nom TEXT NOT NULL, prenom TEXT DEFAULT '', sexe TEXT DEFAULT '',
  naissance TEXT DEFAULT '', tuteur TEXT DEFAULT '', telephone TEXT DEFAULT '', actif INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS presences (
  eleve_id INTEGER NOT NULL REFERENCES eleves(id) ON DELETE CASCADE, jour TEXT NOT NULL,
  statut TEXT NOT NULL CHECK (statut IN ('P','A','R')), justifie INTEGER NOT NULL DEFAULT 0, motif TEXT DEFAULT '',
  PRIMARY KEY (eleve_id, jour));
CREATE TABLE IF NOT EXISTS evals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, classe_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  titre TEXT NOT NULL, matiere TEXT NOT NULL, jour TEXT NOT NULL, bareme REAL NOT NULL DEFAULT 10,
  periode TEXT NOT NULL DEFAULT 'T1', coef REAL NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS notes (
  eval_id INTEGER NOT NULL REFERENCES evals(id) ON DELETE CASCADE,
  eleve_id INTEGER NOT NULL REFERENCES eleves(id) ON DELETE CASCADE, valeur REAL,
  PRIMARY KEY (eval_id, eleve_id));
CREATE TABLE IF NOT EXISTS journal (
  id INTEGER PRIMARY KEY AUTOINCREMENT, classe_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  jour TEXT NOT NULL, creneau TEXT DEFAULT '', matiere TEXT DEFAULT '', titre TEXT NOT NULL,
  fiche_id TEXT DEFAULT '', realise TEXT NOT NULL DEFAULT 'oui', observation TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS annonces (
  id INTEGER PRIMARY KEY AUTOINCREMENT, auteur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  titre TEXT NOT NULL, corps TEXT NOT NULL, cree TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS annonces_lues (
  annonce_id INTEGER NOT NULL REFERENCES annonces(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, lu TEXT NOT NULL,
  PRIMARY KEY (annonce_id, user_id));
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT, quand TEXT NOT NULL, user_id INTEGER, identifiant TEXT DEFAULT '',
  action TEXT NOT NULL, detail TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS tentatives (
  identifiant TEXT PRIMARY KEY, n INTEGER NOT NULL DEFAULT 0, bloque_jusqua TEXT DEFAULT '');
CREATE INDEX IF NOT EXISTS i_eleves ON eleves(classe_id);
CREATE INDEX IF NOT EXISTS i_journal ON journal(classe_id, jour);
CREATE INDEX IF NOT EXISTS i_evals ON evals(classe_id);
"""


def connexion() -> sqlite3.Connection:
    Path(config.DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def init() -> None:
    with connexion() as c:
        c.executescript(SCHEMA)


def q(sql: str, params=(), un: bool = False):
    with connexion() as c:
        cur = c.execute(sql, params)
        rows = cur.fetchall()
    return (rows[0] if rows else None) if un else rows


def ex(sql: str, params=()) -> int:
    with connexion() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


def edt_de_la_classe(classe_id: int, cours: str) -> dict:
    from . import edt
    r = q("SELECT contenu FROM edt_classe WHERE classe_id=?", (classe_id,), un=True)
    return json.loads(r["contenu"]) if r else edt.edt_defaut(cours)


def enregistrer_edt(classe_id: int, edt_dict: dict) -> None:
    ex("INSERT INTO edt_classe(classe_id, contenu) VALUES (?,?) "
       "ON CONFLICT(classe_id) DO UPDATE SET contenu=excluded.contenu",
       (classe_id, json.dumps(edt_dict, ensure_ascii=False)))
