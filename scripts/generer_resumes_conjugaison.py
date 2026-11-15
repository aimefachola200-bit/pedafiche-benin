"""Génère la collection « Conjugaison sans faute » : résumés originaux au format SCOLARIS
(règle, méthode, exemple, exercices corrigés, vocabulaire), du CI au CM2.

Usage : python scripts/generer_resumes_conjugaison.py
Sortie : pedafiche/data/resumes_complements/conjugaison.json
"""
import json
from pathlib import Path

SORTIE = Path(__file__).resolve().parent.parent / "pedafiche" / "data" / "resumes_complements" / "conjugaison.json"
MOIS = {"Septembre": ("I", 0), "Octobre": ("I", 1), "Novembre": ("I", 2), "Décembre": ("I", 3),
        "Janvier": ("II", 4), "Février": ("II", 5), "Mars": ("II", 6), "Avril": ("III", 7),
        "Mai": ("III", 8), "Juin": ("III", 9)}
MENTION = "Résumé original — à valider par le conseiller pédagogique"
DONNEES: list[tuple] = []


def R(cours, mois, titre, regle, methode, exemple, exos, vocab):
    DONNEES.append((cours, mois, titre, regle, methode, exemple, exos, vocab))


# ------------------------------------------------------------------------------ CI
R("CI", "Octobre", "Le verbe dit ce que l'on fait",
  "Le verbe est un mot qui dit ce que quelqu'un fait. Dans « Awa chante », le verbe est « chante ».",
  "Je demande : qu'est-ce que la personne fait ? Le mot qui répond est le verbe.",
  "Koffi mange l'igname pilée. Que fait Koffi ? Il mange. Le verbe est « mange ».",
  [("Trouve le verbe : Le coq chante.", "chante"), ("Trouve le verbe : Les enfants jouent dans la cour.", "jouent"),
   ("Trouve le verbe : Maman lave le linge.", "lave")], ["verbe", "phrase", "action"])
R("CI", "Novembre", "Aujourd'hui, hier, demain",
  "Aujourd'hui, c'est maintenant : c'est le présent. Hier, c'est déjà fini : c'est le passé. Demain, ça n'est pas encore arrivé : c'est le futur.",
  "Je cherche le petit mot qui dit quand : aujourd'hui, hier ou demain.",
  "Hier, Awa a lavé le linge. Aujourd'hui, elle lave le linge. Demain, elle lavera le linge.",
  [("Hier, Koffi a joué au ballon. C'est le présent, le passé ou le futur ?", "le passé"),
   ("Demain, nous irons au marché. C'est le présent, le passé ou le futur ?", "le futur"),
   ("Aujourd'hui, je lis un livre. C'est le présent, le passé ou le futur ?", "le présent")],
  ["présent", "passé", "futur"])
R("CI", "Décembre", "Je, tu, il, elle : qui fait l'action ?",
  "Pour dire qui fait l'action, on utilise : je (moi), tu (toi), il (un garçon), elle (une fille). Le verbe change un peu : je chante, tu chantes, il chante.",
  "Je regarde qui fait l'action, puis j'écris le verbe qui va avec.",
  "Je chante. Tu chantes. Il chante. Elle chante.",
  [("Complète : Tu … (chanter).", "chantes"), ("Complète : Elle … (danser).", "danse"),
   ("Complète : Je … (jouer).", "joue")], ["je", "tu", "il", "elle"])
R("CI", "Janvier", "Le verbe être : je suis, tu es, il est",
  "Le verbe être dit comment on est ou où on est : je suis, tu es, il est, elle est.",
  "Je regarde qui parle ou de qui on parle, puis je choisis suis, es ou est.",
  "Je suis à l'école. Tu es grand. Awa est contente.",
  [("Complète : Je … content.", "suis"), ("Complète : Tu … en classe.", "es"), ("Complète : Koffi … grand.", "est")],
  ["être", "suis", "es", "est"])
R("CI", "Février", "Le verbe avoir : j'ai, tu as, il a",
  "Le verbe avoir dit ce que l'on possède : j'ai, tu as, il a, elle a. Devant une voyelle, je devient j' : j'ai.",
  "Je regarde qui parle ou de qui on parle, puis je choisis ai, as ou a.",
  "J'ai un cahier. Tu as un stylo. Koffi a un ballon.",
  [("Complète : J'… une ardoise.", "ai"), ("Complète : Tu … faim.", "as"), ("Complète : Awa … une robe neuve.", "a")],
  ["avoir", "ai", "as", "a"])
R("CI", "Mars", "Un seul ou plusieurs : il chante, ils chantent",
  "Quand une seule personne agit, le verbe est au singulier : il chante. Quand plusieurs personnes agissent, le verbe est au pluriel : ils chantent. À l'écrit, le verbe prend souvent -nt à la fin.",
  "Je compte qui agit : un seul ou plusieurs ?",
  "L'oiseau chante. Les oiseaux chantent.",
  [("Complète : Les filles (danser) …", "dansent"), ("Complète : L'enfant (jouer) …", "joue"),
   ("Complète : Les poules (picorer) …", "picorent")], ["singulier", "pluriel"])
# ------------------------------------------------------------------------------ CP
R("CP", "Octobre", "L'infinitif : le nom du verbe",
  "L'infinitif est le nom du verbe : c'est la forme qu'on trouve dans le dictionnaire. Il se termine souvent par -er (chanter), parfois par -ir (finir) ou -re (prendre).",
  "Pour trouver l'infinitif, je mets « je veux » devant : je veux manger.",
  "Elles dansent → danser ; tu finis → finir ; il prend → prendre.",
  [("Quel est l'infinitif de « elle mange » ?", "manger"), ("Quel est l'infinitif de « ils jouent » ?", "jouer"),
   ("Quel est l'infinitif de « tu finis » ?", "finir")], ["infinitif", "dictionnaire"])
R("CP", "Novembre", "Le présent des verbes en -er",
  "Au présent, les verbes en -er ont les terminaisons -e, -es, -e, -ons, -ez, -ent : je chante, tu chantes, il chante, nous chantons, vous chantez, ils chantent.",
  "Je trouve l'infinitif, j'enlève -er pour garder le radical, puis j'ajoute la terminaison de la personne.",
  "danser → je danse, tu danses, il danse, nous dansons, vous dansez, ils dansent.",
  [("Nous (chanter) …", "chantons"), ("Vous (danser) …", "dansez"), ("Ils (jouer) …", "jouent")],
  ["radical", "terminaison", "présent"])
R("CP", "Décembre", "Le verbe être au présent",
  "Je suis, tu es, il (elle) est, nous sommes, vous êtes, ils (elles) sont.",
  "Je cherche qui fait l'action et je choisis la forme qui va avec.",
  "Nous sommes à l'école. Vous êtes en classe. Les élèves sont attentifs.",
  [("Complète : Nous … au marché.", "sommes"), ("Complète : Vous … contents.", "êtes"),
   ("Complète : Les élèves … sages.", "sont")], ["être", "présent"])
R("CP", "Janvier", "Le verbe avoir au présent",
  "J'ai, tu as, il (elle) a, nous avons, vous avez, ils (elles) ont.",
  "Je cherche qui fait l'action et je choisis la forme qui va avec.",
  "Nous avons un jardin. Vous avez un cahier. Les enfants ont des livres.",
  [("Complète : Nous … deux chèvres.", "avons"), ("Complète : Vous … raison.", "avez"),
   ("Complète : Elles … soif.", "ont")], ["avoir", "présent"])
R("CP", "Février", "Le verbe aller au présent",
  "Aller est un verbe à part : je vais, tu vas, il (elle) va, nous allons, vous allez, ils (elles) vont.",
  "Je cherche qui fait l'action et je choisis la forme qui va avec.",
  "Je vais à l'école. Nous allons au marché de Pobè. Ils vont au champ.",
  [("Complète : Tu … au puits.", "vas"), ("Complète : Nous … au marché.", "allons"),
   ("Complète : Les élèves … en récréation.", "vont")], ["aller", "présent"])
R("CP", "Mars", "Le verbe faire au présent",
  "Je fais, tu fais, il (elle) fait, nous faisons, vous faites, ils (elles) font.",
  "Je cherche qui fait l'action et je choisis la forme qui va avec.",
  "Maman fait la cuisine. Nous faisons nos devoirs. Les enfants font du sport.",
  [("Complète : Tu … ton lit.", "fais"), ("Complète : Vous … du bruit.", "faites"),
   ("Complète : Ils … leurs devoirs.", "font")], ["faire", "présent"])
R("CP", "Avril", "Le verbe s'accorde avec le sujet",
  "Le verbe s'accorde avec son sujet. Si le sujet est au singulier, le verbe est au singulier (il joue) ; si le sujet est au pluriel, le verbe est au pluriel (ils jouent).",
  "Je pose la question « qui est-ce qui ? » devant le verbe. La réponse est le sujet.",
  "La petite fille chante. Les petites filles chantent.",
  [("Complète : La petite fille (chanter) …", "chante"), ("Complète : Les petites filles (chanter) …", "chantent"),
   ("Complète : Koffi et Awa (jouer) …", "jouent")], ["sujet", "accord"])
# ------------------------------------------------------------------------------ CE1
R("CE1", "Octobre", "La phrase négative : ne … pas",
  "Pour dire non, on entoure le verbe avec ne … pas. Devant une voyelle, ne devient n'.",
  "Je place ne avant le verbe et pas après le verbe.",
  "Koffi ne joue pas. Awa n'écoute pas.",
  [("Mets à la forme négative : Il mange.", "Il ne mange pas."),
   ("Mets à la forme négative : Nous chantons.", "Nous ne chantons pas."),
   ("Mets à la forme négative : Tu aimes le piment.", "Tu n'aimes pas le piment.")],
  ["forme négative", "ne … pas"])
R("CE1", "Novembre", "Être et avoir à l'imparfait",
  "Être : j'étais, tu étais, il était, nous étions, vous étiez, ils étaient. Avoir : j'avais, tu avais, il avait, nous avions, vous aviez, ils avaient. L'imparfait dit ce qui durait ou se répétait autrefois.",
  "Je repère « autrefois », « quand j'étais petit », puis j'utilise l'imparfait.",
  "Autrefois, nous étions petits et nous avions peur du noir.",
  [("Complète : Hier, nous … fatigués. (être)", "étions"), ("Complète : Autrefois, tu … un petit chien. (avoir)", "avais"),
   ("Complète : Les enfants … contents. (être)", "étaient")], ["imparfait", "autrefois"])
R("CE1", "Janvier", "Le verbe prendre au présent",
  "Je prends, tu prends, il (elle) prend, nous prenons, vous prenez, ils (elles) prennent.",
  "Je me souviens : au pluriel, nous prenons s'écrit avec un seul n, mais ils prennent en a deux.",
  "Je prends mon cartable. Vous prenez le chemin de l'école. Ils prennent leur repas.",
  [("Complète : Je … mon cartable.", "prends"), ("Complète : Vous … le bus.", "prenez"),
   ("Complète : Ils … leur repas.", "prennent")], ["prendre", "présent"])
R("CE1", "Février", "Le verbe et son sujet : bien accorder",
  "Le sujet peut être loin du verbe. Le verbe s'accorde toujours avec son sujet, pas avec le mot placé juste avant lui.",
  "Je cherche le sujet avec « qui est-ce qui ? », puis j'accorde le verbe.",
  "Les enfants du village chantent. Le chant des oiseaux réveille le village.",
  [("Complète : Les élèves de la classe (écouter) … le maître.", "écoutent"),
   ("Complète : Le chant des oiseaux (réveiller) … le village.", "réveille"),
   ("Complète : Awa et sa sœur (puiser) … de l'eau.", "puisent")], ["sujet", "accord"])
R("CE1", "Avril", "Le verbe venir au présent",
  "Je viens, tu viens, il (elle) vient, nous venons, vous venez, ils (elles) viennent.",
  "Au singulier, je viens, tu viens, il vient. Au pluriel, nous venons, vous venez, ils viennent.",
  "Je viens de l'école. Nous venons de Cotonou. Elles viennent à pied.",
  [("Complète : Je … de l'école.", "viens"), ("Complète : Nous … de Cotonou.", "venons"),
   ("Complète : Elles … à pied.", "viennent")], ["venir", "présent"])
R("CE1", "Mai", "Le verbe pouvoir au présent",
  "Je peux, tu peux, il (elle) peut, nous pouvons, vous pouvez, ils (elles) peuvent.",
  "Pouvoir dit ce qu'on est capable de faire ou ce qu'on a le droit de faire.",
  "Je peux porter ce seau. Vous pouvez sortir. Elles peuvent jouer.",
  [("Complète : Tu … porter ce seau.", "peux"), ("Complète : Nous … sortir.", "pouvons"),
   ("Complète : Ils … courir vite.", "peuvent")], ["pouvoir", "présent"])
# ------------------------------------------------------------------------------ CE2
R("CE2", "Octobre", "é, er, ez : comment choisir ?",
  "À la fin d'un verbe, le son [e] s'écrit é (participe passé), er (infinitif) ou ez (avec vous). Je remplace par « vendre » : si ça va, j'écris er. Je remplace par « vendu » : si ça va, j'écris é.",
  "Je teste avec vendre / vendu. Avec le sujet « vous », j'écris ez.",
  "Il va chanter (il va vendre). Elle a lavé (elle a vendu). Vous portez (sujet : vous).",
  [("Complète avec é, er ou ez : Elle a lav… le linge.", "lavé"), ("Complète avec é, er ou ez : Vous port… des seaux.", "portez"),
   ("Complète avec é, er ou ez : Il va chant… à la fête.", "chanter")], ["infinitif", "participe passé"])
R("CE2", "Novembre", "Le présent des verbes en -cer et -ger",
  "Avec nous, les verbes en -cer prennent une cédille (nous commençons) et les verbes en -ger gardent un e (nous mangeons), pour garder le même son.",
  "Devant -ons, j'écris ç ou ge pour que la lettre c ou g garde son son doux.",
  "Nous commençons le travail. Nous mangeons du riz.",
  [("Complète : Nous (commencer) … le travail.", "commençons"), ("Complète : Nous (manger) … du riz.", "mangeons"),
   ("Complète : Ils (lancer) … le ballon.", "lancent")], ["cédille", "radical"])
R("CE2", "Janvier", "Pouvoir et vouloir au présent",
  "Pouvoir : je peux, tu peux, il peut, nous pouvons, vous pouvez, ils peuvent. Vouloir : je veux, tu veux, il veut, nous voulons, vous voulez, ils veulent.",
  "Au singulier, je mets x, x, t. Au pluriel, le radical change : ils peuvent, ils veulent.",
  "Tu peux venir avec nous. Nous voulons partir. Ils veulent jouer.",
  [("Complète : Tu … venir avec nous. (pouvoir)", "peux"), ("Complète : Nous … partir. (vouloir)", "voulons"),
   ("Complète : Ils … jouer. (vouloir)", "veulent")], ["pouvoir", "vouloir"])
R("CE2", "Février", "Le futur simple : les radicaux irréguliers",
  "Certains verbes changent de radical au futur : être → je serai, avoir → j'aurai, aller → j'irai, faire → je ferai, venir → je viendrai, voir → je verrai, pouvoir → je pourrai, vouloir → je voudrai. Les terminaisons sont toujours -ai, -as, -a, -ons, -ez, -ont.",
  "J'apprends le radical du futur, puis j'ajoute la terminaison.",
  "Demain, nous irons au champ. L'an prochain, je ferai du football.",
  [("Complète : Demain, nous (aller) … au champ.", "irons"), ("Complète : L'an prochain, je (faire) … du football.", "ferai"),
   ("Complète : Vous (venir) … nous voir.", "viendrez")], ["futur", "radical"])
R("CE2", "Mars", "Le verbe mettre au présent",
  "Je mets, tu mets, il (elle) met, nous mettons, vous mettez, ils (elles) mettent. Permettre et promettre se conjuguent de la même façon.",
  "Au singulier : mets, mets, met. Au pluriel, je garde les deux t.",
  "Je mets la table. Nous mettons nos cahiers dans le sac.",
  [("Complète : Je … la table.", "mets"), ("Complète : Nous … nos cahiers dans le sac.", "mettons"),
   ("Complète : Elles … leurs pagnes.", "mettent")], ["mettre", "présent"])
R("CE2", "Mai", "L'imparfait des verbes en -cer et -ger",
  "À l'imparfait, les verbes en -cer prennent ç devant a (je commençais) et les verbes en -ger prennent ge devant a (je mangeais). Avec nous et vous, il n'y a pas de cédille ni de e : nous commencions, nous mangions.",
  "Je regarde la lettre qui suit : devant a, j'écris ç ou ge ; devant i, rien de plus.",
  "Autrefois, je mangeais à midi. Autrefois, nous commencions à sept heures.",
  [("Complète : Autrefois, je (manger) … à midi.", "mangeais"),
   ("Complète : Autrefois, nous (commencer) … le travail à sept heures.", "commencions"),
   ("Complète : Autrefois, les enfants (lancer) … des cailloux.", "lançaient")], ["imparfait", "cédille"])
# ------------------------------------------------------------------------------ CM1
R("CM1", "Octobre", "Les verbes en -yer au présent",
  "Les verbes en -oyer, -uyer, -ayer changent y en i devant un e muet : je nettoie, tu nettoies, il nettoie, ils nettoient. Le y revient avec nous et vous : nous nettoyons, vous nettoyez. Payer admet les deux formes : je paie ou je paye.",
  "Si la terminaison est muette (e, es, ent), j'écris i ; si elle se prononce (ons, ez), j'écris y.",
  "Je nettoie la cour. Nous envoyons une lettre. Ils essuient les bancs.",
  [("Complète : Je (nettoyer) … la cour.", "nettoie"), ("Complète : Nous (envoyer) … une lettre.", "envoyons"),
   ("Complète : Ils (essuyer) … les bancs.", "essuient")], ["verbe en -yer", "e muet"])
R("CM1", "Novembre", "L'imparfait des verbes en -ier, -uer, -ouer",
  "À l'imparfait, avec nous et vous, la terminaison -ions ou -iez s'ajoute au radical : nous jouions, vous jouiez ; mais les verbes qui finissent par -ier gardent leur i : nous étudiions, vous étudiiez.",
  "Je cherche le radical, puis j'ajoute -ions ou -iez ; pour étudier ou crier, j'entends deux i.",
  "Nous étudiions le soir. Nous jouions dans la cour.",
  [("Complète : Nous (étudier) … hier soir.", "étudiions"),
   ("Complète : Quand vous étiez petits, vous (crier) … très fort.", "criiez"),
   ("Complète : Nous (jouer) … dans la cour.", "jouions")], ["imparfait", "radical"])
R("CM1", "Décembre", "Être et avoir au subjonctif présent",
  "Être : que je sois, que tu sois, qu'il soit, que nous soyons, que vous soyez, qu'ils soient. Avoir : que j'aie, que tu aies, qu'il ait, que nous ayons, que vous ayez, qu'ils aient. On utilise le subjonctif après il faut que, je voudrais que, je souhaite que.",
  "Je repère il faut que, je veux que, je souhaite que : j'emploie alors le subjonctif.",
  "Il faut que tu sois à l'heure. Je voudrais qu'il ait du courage.",
  [("Complète : Il faut que tu (être) … à l'heure.", "sois"), ("Complète : Je voudrais qu'il (avoir) … du courage.", "ait"),
   ("Complète : Il faut que nous (être) … prudents.", "soyons")], ["subjonctif", "il faut que"])
R("CM1", "Février", "L'impératif de aller, faire, dire, prendre",
  "Aller : va, allons, allez. Faire : fais, faisons, faites. Dire : dis, disons, dites. Prendre : prends, prenons, prenez. À l'impératif, on n'écrit pas le sujet.",
  "Je repère un ordre ou un conseil : j'utilise la forme sans sujet. Va prend un s devant y : vas-y.",
  "Va au tableau. Faites attention. Prends ton cahier.",
  [("Complète : (Aller) … au tableau, Awa.", "Va"), ("Complète : (Faire) … attention, les enfants.", "Faites"),
   ("Complète : (Prendre) … ton cahier, Koffi.", "Prends")], ["impératif", "ordre"])
R("CM1", "Mars", "Futur ou conditionnel ? -rai ou -rais",
  "Le futur exprime quelque chose de certain : je mangerai demain. Le conditionnel exprime un souhait ou une condition : je mangerais si j'avais faim. Les deux ont le même radical, mais les terminaisons diffèrent : -ai, -as, -a au futur ; -ais, -ais, -ait au conditionnel.",
  "Je remplace je par nous : nous mangerons (futur) ou nous mangerions (conditionnel).",
  "Demain, je partirai tôt. Si j'avais le temps, je viendrais te voir.",
  [("Complète au futur : Demain, je (partir) … tôt.", "partirai"),
   ("Complète au conditionnel : Si j'avais le temps, je (venir) … te voir.", "viendrais"),
   ("Complète au conditionnel : Si tu travaillais, tu (réussir) … .", "réussirais")], ["futur", "conditionnel"])
R("CM1", "Mai", "Le présent de partir, sortir, dormir",
  "Au singulier, ces verbes perdent la dernière consonne du radical : je pars, tu pars, il part ; je sors ; je dors. Au pluriel, elle revient : nous partons, vous partez, ils partent.",
  "Au singulier, je n'entends pas la consonne finale : je pars, il part. Au pluriel, je l'entends : nous partons.",
  "Je sors de la classe. Nous partons au champ. Ils dorment sous la moustiquaire.",
  [("Complète : Je (sortir) … de la classe.", "sors"), ("Complète : Ils (dormir) … sous la moustiquaire.", "dorment"),
   ("Complète : Nous (partir) … au champ.", "partons")], ["troisième groupe", "présent"])
# ------------------------------------------------------------------------------ CM2
R("CM2", "Septembre", "L'accord du participe passé avec avoir",
  "Avec avoir, le participe passé s'accorde avec le complément d'objet direct (COD) seulement si ce COD est placé avant le verbe. Sinon, il reste invariable.",
  "Je cherche le COD (j'ai mangé quoi ?). S'il est avant le verbe, j'accorde ; s'il est après, je n'accorde pas.",
  "J'ai mangé les mangues. Les mangues que j'ai mangées étaient sucrées.",
  [("Complète : Les mangues que Koffi a (cueillir) … étaient mûres.", "cueillies"),
   ("Complète : Voici la lettre que j'ai (écrire) … .", "écrite"),
   ("Complète : Les élèves ont (terminer) … leurs devoirs.", "terminé")], ["participe passé", "COD"])
R("CM2", "Octobre", "Le participe passé des verbes du 3e groupe",
  "Les verbes du 3e groupe ont des participes passés variés : prendre → pris, mettre → mis, faire → fait, dire → dit, écrire → écrit, voir → vu, vouloir → voulu, pouvoir → pu, venir → venu, ouvrir → ouvert.",
  "Pour savoir si la fin est é, i, u, s ou t, je mets le participe au féminin : pris → prise, écrit → écrite.",
  "Il a pris son cahier. La lettre est écrite. Elle a ouvert la porte.",
  [("Écris le participe passé de « prendre ».", "pris"), ("Écris le participe passé de « écrire ».", "écrit"),
   ("Écris le participe passé de « ouvrir ».", "ouvert")], ["participe passé", "troisième groupe"])
R("CM2", "Novembre", "Le subjonctif présent de aller, faire, pouvoir, vouloir",
  "Aller : que j'aille, que nous allions. Faire : que je fasse. Pouvoir : que je puisse. Vouloir : que je veuille, que nous voulions. Ces verbes changent de radical au subjonctif.",
  "Je repère il faut que, je souhaite que, bien que, avant que : j'emploie le subjonctif.",
  "Il faut que j'aille au marché. Je souhaite qu'il puisse venir.",
  [("Complète : Il faut que j'(aller) … au marché.", "aille"), ("Complète : Il faut que tu (faire) … tes devoirs.", "fasses"),
   ("Complète : Je souhaite qu'il (pouvoir) … venir.", "puisse")], ["subjonctif", "radical irrégulier"])
R("CM2", "Décembre", "La voix passive",
  "À la voix passive, le sujet subit l'action. Elle se forme avec le verbe être conjugué + le participe passé, qui s'accorde avec le sujet. L'auteur de l'action s'introduit par « par ».",
  "Je transforme : le COD devient sujet, le sujet devient complément d'agent introduit par par.",
  "Le maître félicite les élèves. → Les élèves sont félicités par le maître.",
  [("Mets au passif : Awa lave la cour.", "La cour est lavée par Awa."),
   ("Mets au passif : Les paysans récoltent le maïs.", "Le maïs est récolté par les paysans."),
   ("Quel auxiliaire sert à former le passif ?", "être")], ["voix passive", "complément d'agent"])
R("CM2", "Janvier", "Les verbes en -indre : craindre, peindre, joindre",
  "Je crains, tu crains, il craint, nous craignons, vous craignez, ils craignent. Au pluriel, le radical devient craign-. Participes passés : craint, peint, joint.",
  "Au singulier, je n'écris pas le d : je crains. Au pluriel, j'écris -gn- : nous craignons.",
  "Je crains l'orage. Nous peignons la porte. Ils joignent leurs efforts.",
  [("Complète : Je (craindre) … l'orage.", "crains"), ("Complète : Nous (peindre) … la porte.", "peignons"),
   ("Complète : Ils (joindre) … leurs efforts.", "joignent")], ["verbes en -indre", "radical"])
R("CM2", "Février", "Les verbes en -uire : conduire, construire, produire",
  "Je conduis, tu conduis, il conduit, nous conduisons, vous conduisez, ils conduisent. Participe passé : conduit, construit, produit.",
  "Au singulier, la terminaison est -s, -s, -t. Au pluriel, le s du radical se prononce [z] : nous conduisons.",
  "Le chauffeur conduit prudemment. Nous construisons une case.",
  [("Complète : Le chauffeur (conduire) … prudemment.", "conduit"), ("Complète : Nous (construire) … une case.", "construisons"),
   ("Complète : Ces champs (produire) … beaucoup de maïs.", "produisent")], ["verbes en -uire", "participe passé"])
R("CM2", "Mars", "Le passé simple des verbes du 3e groupe à la 3e personne",
  "Être : il fut, ils furent. Avoir : il eut, ils eurent. Faire : il fit, ils firent. Dire : il dit, ils dirent. Venir : il vint, ils vinrent. Prendre : il prit, ils prirent. Voir : il vit, ils virent. Pouvoir : il put, ils purent. Vouloir : il voulut, ils voulurent. Le passé simple raconte des actions terminées dans un récit.",
  "Je repère un récit au passé : j'utilise il … ou ils … au passé simple pour les actions principales.",
  "Le roi vint au village. Les chasseurs prirent la route.",
  [("Complète au passé simple : Le roi (venir) … au village.", "vint"),
   ("Complète au passé simple : Ils (prendre) … la route.", "prirent"),
   ("Complète au passé simple : Elle (être) … très courageuse.", "fut")], ["passé simple", "récit"])
R("CM2", "Avril", "Verbe ou autre mot ? a/à, est/et, ont/on, sont/son",
  "A, est, ont, sont sont des formes de verbes (avoir ou être). À, et, on, son sont d'autres mots. Pour vérifier, je remplace : a → avait, est → était, ont → avaient, sont → étaient.",
  "Je remplace par l'imparfait : si la phrase reste correcte, c'est le verbe.",
  "Koffi a un frère (avait). Awa est contente (était). Ils sont venus avec son ami.",
  [("Choisis a ou à : Koffi … un frère.", "a"), ("Choisis ont ou on : Les enfants … joué.", "ont"),
   ("Choisis est ou et : Awa … contente.", "est")], ["homophones", "auxiliaire"])


def construire() -> list[dict]:
    out = []
    compteur: dict = {}
    for cours, mois, titre, regle, methode, exemple, exos, vocab in DONNEES:
        compteur[cours] = compteur.get(cours, 0) + 1
        n = compteur[cours]
        tri, idx = MOIS[mois]
        out.append({
            "id": f"rx-{cours.lower()}-conj-{n:02d}", "cours": cours, "matiere": "francais",
            "domaine": "Conjugaison", "sous_domaine": "Conjugaison", "outil": "Conjugaison",
            "collection": "Conjugaison sans faute", "titre": titre, "regle": regle, "methode": methode,
            "exemple": exemple, "exercices": [{"q": q, "r": r} for q, r in exos], "vocabulaire": vocab,
            "mention": MENTION, "mois": mois, "trimestre": tri, "ordre": [idx, 80, n], "ancres": [],
        })
    return out


if __name__ == "__main__":
    data = construire()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(data), "résumés écrits dans", SORTIE)
