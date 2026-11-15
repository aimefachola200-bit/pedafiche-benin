"""Contenu original — Français CI : lecture-écriture, 42 leçons (ordre des lettres du programme).

Contrainte pédagogique vérifiée automatiquement : un mot ou une phrase « à lire » n'emploie que des
lettres déjà enseignées, aucun son non encore vu (nasales, ou/eu/au avant leur leçon, c/g doux, s=[z]…).
"""
import re
import unicodedata

# (numéro, titre, lettres nouvelles, mots, phrases)
LECONS = [
 (1, "la lettre a-A", "a", ["a"], []),
 (2, "la lettre l-L", "l", ["la"], []),
 (3, "la lettre t-T", "t", ["tata"], []),
 (4, "la lettre o-O", "o", ["lot", "Lola", "Toto"], []),
 (5, "la lettre p-P", "p", ["papa", "pot", "top"], []),
 (6, "la lettre i-I", "i", ["tipi", "lit", "papi", "pli"], []),
 (7, "la lettre b-B", "b", ["bol", "boa", "bal", "bip"], []),
 (8, "la lettre é-E", "é", ["été", "bébé", "Léa", "télé"], []),
 (9, "la lettre m-M", "m", ["mal", "moto", "mot", "mil", "Mia"], []),
 (10, "les majuscules A-L-T-O", "", ["Ali", "Lola", "Toto", "Léa"], []),
 (11, "la lettre e-E", "e", ["pile", "lime", "pelote", "belle", "tape", "tome"], []),
 (12, "la lettre d-D", "d", ["dame", "date", "dodo", "idée", "madame", "dé"], []),
 (13, "les mots outils le - la - l'", "", [], ["La dame a la moto.", "Le bébé a le bol.", "Léa a l'idée."]),
 (14, "la lettre u-U", "u", ["mule", "tutu", "bulle", "utile", "ému", "Lulu"], []),
 (15, "la lettre n-N", "n", ["lune", "dune", "banane", "nid", "mine", "natte"], []),
 (16, "les mots outils un - une", "", [], ["Léa a une banane.", "Ali a un bol.", "Toto a un nid."]),
 (17, "la lettre s-S", "s", ["salade", "sol", "tapis", "sable", "bus", "tasse", "poste"], []),
 (18, "la lettre f-F", "f", ["fil", "fée", "sofa", "fini", "fume", "fade"], []),
 (19, "le mot outil est", "", [], ["Léa est une fée.", "Le sofa est fini.", "La tomate est molle.", "Toto est un as."]),
 (20, "la lettre è-È", "è", ["sème", "tète", "dès", "mène", "pèle"], []),
 (21, "la lettre v-V", "v", ["vélo", "ville", "vite", "lave", "vide", "avis", "vive"], []),
 (22, "les lettres muettes e-t-d-s à la fin des mots", "", ["petit", "bas", "lit", "nid", "sud", "dos", "tapis", "début", "salut"], []),
 (23, "la lettre c-C", "c", ["café", "cube", "cabane", "sac", "cave", "cabine", "calme"], []),
 (24, "la lettre j-J", "j", ["jupe", "jus", "joli", "judo", "juste", "jade"], []),
 (25, "la lettre g-G", "g", ["gomme", "galop", "gala", "légume", "gobelet", "gamelle"], []),
 (26, "la lettre k-K", "k", ["kilo", "kaki", "koala", "képi", "ski", "Koffi", "Kodjo"], []),
 (27, "la lettre e muette à la fin des mots", "", ["table", "tomate", "salle", "école", "balle", "pomme", "plume"], []),
 (28, "la lettre r-R", "r", ["rat", "radio", "robe", "rue", "livre", "arbre", "porte", "tarte", "carte", "mur"], []),
 (29, "la lettre h-H", "h", ["habit", "haricot", "hiver", "hélas", "Hugo"], []),
 (30, "les mots outils il - elle", "", [], ["Il a une moto.", "Elle est belle.", "Elle a une robe.", "Il lit un livre.", "Il porte un sac.", "Elle lave la table."]),
 (31, "les lettres q-Q et qu-QU", "q", ["coq", "que", "quel", "quatre", "marque", "disque", "toque"], []),
 (32, "la lettre w-W", "w", ["watt", "kiwi", "web", "wapiti", "Wali"], []),
 (33, "la lettre ê-Ê", "ê", ["fête", "tête", "bête", "forêt", "rêve", "être", "même"], []),
 (34, "la lettre z-Z", "z", ["zèbre", "zéro", "zone", "zoo", "riz", "gaz", "zigzag", "azur"], []),
 (35, "la lettre y-Y", "y", ["stylo", "pyjama", "yoyo", "Yao", "kayak", "Yves"], []),
 (36, "la lettre x-X", "x", ["taxi", "boxe", "six", "dix", "axe", "Alex", "Max"], []),
 (37, "le mot outil et", "", [], ["Ali a un sac et une robe.", "Léa a une table et un livre.", "Koffi a un vélo et une moto."]),
 (38, "le groupe de lettres ou-OU", "", ["pou", "cou", "sou", "loup", "jour", "route", "poule", "boule", "souris", "four"], []),
 (39, "le groupe de lettres eu-EU", "", ["feu", "bleu", "jeu", "deux", "neuf", "peur", "fleur", "couleur", "heure"], []),
 (40, "le groupe de lettres au-AU", "", ["auto", "jaune", "Paul", "saut", "taupe", "aurore", "haut", "sauté"], []),
 (41, "le groupe de lettres on-ON", "", ["bon", "mon", "son", "pont", "ballon", "melon", "salon", "savon", "violon", "bonbon"], []),
 (42, "le groupe de lettres om-OM", "", ["nom", "pompe", "ombre", "tombe", "bombe", "nombre", "combat", "compte"], []),
]
# bilans d'intégration : (après la leçon, titre, mots, phrases)
INTEGRATIONS = [
 (8, "Intégration 1 — lettres a l t o p i b é", ["tipi", "lit", "bol", "bal", "bébé", "été", "Léa", "papi", "pli"], []),
 (20, "Intégration 2 — jusqu'à la lettre è", [], ["La dame a une moto.", "Le bébé a un bol.", "Léa est une fée."]),
 (31, "Intégration 3 — jusqu'aux lettres q-qu", [], ["Elle a une robe.", "Il porte un sac.", "Il lit un livre sur la table.", "Elle lave la salade."]),
 (42, "Intégration 4 — tous les graphèmes étudiés", [], ["Koffi joue au ballon.", "Yao joue du violon.", "Le violon a un bon son."]),
]
LETTRES_PAR_LECON = {n: new for n, _t, new, _m, _p in LECONS}
OUTILS = {"le", "la", "l", "un", "une", "est", "et", "il", "elle", "a", "au", "du", "sur", "de"}
DIGRAPHES = {"ou": 38, "eu": 39, "au": 40, "on": 41, "om": 42}   # groupes autorisés à partir de leur leçon
VOYELLES = "aeiouyéèê"


def _norm(m):
    return m.lower().replace("'", "")


def lettres_connues(num):
    s = set()
    for n, _t, new, _m, _p in LECONS:
        if n <= num:
            s.update(new)
    return s


def violations_mot(mot, num):
    """Liste des raisons pour lesquelles `mot` ne peut pas être lu à la leçon `num`."""
    w, v = _norm(mot), []
    if w in {"un", "une"} and num >= 16:
        return v
    if w in OUTILS:
        return v
    conn = lettres_connues(num)
    for c in w:
        if c.isalpha() and c not in conn and not (c == "e" and num >= 11):
            v.append(f"lettre « {c} » non enseignée")
    for dg, lec in DIGRAPHES.items():
        if dg in w and num < lec and not re.search(rf"{dg}(?=[{VOYELLES}mn])", w) and dg not in ("om",) :
            v.append(f"groupe « {dg} » non enseigné")
    if re.search(r"(?<![mn])(?:a|e|i|u|y)[nm](?![aeiouyéèêhnm])", w) or re.search(r"(?:ai|ei|oi|ui|eau|ch|ph|gn)", w):
        v.append("son non enseigné (nasale ou graphème complexe)")
    for m in re.finditer(r"(o)([nm])(?![aeiouyéèêhnm])", w):
        lec = 41 if m.group(2) == "n" else 42
        if num < lec:
            v.append(f"groupe « o{m.group(2)} » non enseigné")
    if re.search(r"c(?=[eiyéèê])", w) or re.search(r"g(?=[eiyéèê])", w):
        v.append("c/g doux non enseigné")
    if re.search(rf"[{VOYELLES}]s[{VOYELLES}]", w):
        v.append("s entre deux voyelles ([z]) non enseigné")
    return v


def violations_phrase(phrase, num):
    out = []
    for tok in re.findall(r"[A-Za-zéèêàùç']+", phrase):
        for part in tok.split("'"):
            if part:
                out += [f"{part} : {x}" for x in violations_mot(part, num)]
    return out


def verifier():
    """Retourne la liste des anomalies de toutes les leçons et intégrations."""
    err = []
    for n, titre, _new, mots, phrases in LECONS:
        for m in mots:
            err += [f"L{n} {m} : {x}" for x in violations_mot(m, n)]
        for p in phrases:
            err += [f"L{n} « {p} » : {x}" for x in violations_phrase(p, n)]
    for n, titre, mots, phrases in INTEGRATIONS:
        for m in mots:
            err += [f"I{n} {m} : {x}" for x in violations_mot(m, n)]
        for p in phrases:
            err += [f"I{n} « {p} » : {x}" for x in violations_phrase(p, n)]
    return err


def syllabes(num, nb=8):
    """Syllabes à lire (consonne + voyelle) construites avec les lettres connues et vérifiées."""
    new = LETTRES_PAR_LECON[num]
    conn = lettres_connues(num)
    voy = [v for v in "aoiéeuèê" if v in conn]
    con = [c for c in "lptbmdnsfvcjgkrhqwzx" if c in conn]
    out = []
    if new and new in "aoiéeuèê":
        for c in con:
            s = c + new
            if not violations_mot(s, num) and s not in ("ce",):
                out.append(s)
    elif new:
        for v in voy:
            s = new + v
            if not violations_mot(s, num):
                out.append(s)
    return out[:nb]


def decompte(mot, lettre):
    return sum(1 for c in mot.lower() if c == lettre.lower())
