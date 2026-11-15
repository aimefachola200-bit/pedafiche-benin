import conftest  # noqa: F401
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import cahiers_ci_lecture as ci
import cahiers_contenu_dictees as dic
import cahiers_contenu_es_ea as esea
import cahiers_contenu_vol2_francais as fr2
import cahiers_contenu_vol2_maths as ma2


def test_regle_de_decodage_ci():
    assert ci.verifier() == []                      # aucun mot ni phrase hors des lettres enseignées
    assert len(ci.LECONS) == 42 and len(ci.INTEGRATIONS) == 4


def test_validateur_detecte_les_erreurs():
    assert ci.violations_mot("banque", 31)          # nasale non enseignée
    assert ci.violations_mot("citron", 41)          # c doux
    assert ci.violations_mot("bon", 20)             # « on » avant sa leçon
    assert not ci.violations_mot("ballon", 41)


def test_structure_des_fiches():
    for lot in (ma2.MATHS_CI, ma2.MATHS_CP, ma2.MATHS_CM2, fr2.FR_CI, fr2.FR_CP, fr2.FR_CE1, fr2.FR_CM2, fr2.GRAMMAIRE, esea.LECONS):
        for titre, retiens, qr, cles in lot:
            assert titre and retiens and cles and len(qr) >= 3
            assert all(q and r for q, r in qr)
    assert len(dic.DICTEES) == 13
    for d in dic.DICTEES:
        assert d[6] and len(d[4]) == 3


def test_generation_des_trois_volumes(tmp_path):
    import generer_cahiers_revision as v1
    import generer_cahiers_revision_vol2 as v2
    import generer_cahiers_ci_lecture as v3
    for mod, nom in ((v1, "v1.pdf"), (v2, "v2.pdf"), (v3, "v3.pdf")):
        p = Path(mod.construire(str(tmp_path / nom)))
        assert p.read_bytes()[:4] == b"%PDF" and p.stat().st_size > 20000
