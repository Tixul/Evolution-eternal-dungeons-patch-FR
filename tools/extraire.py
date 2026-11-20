"""Catalogue COMPLET du texte d'Evolution (E) -> out/catalogue.tsv

    python -I -B tools/extraire.py ROM [SORTIE.tsv]

Colonnes : adresse CPU (hex) · type · texte lisible (codes en {xx}, ligne = /).
Types :
  SCRIPT  boîte de dialogue (commande 01 du script des scènes)
  ECRAN   chaîne à position fixe (commandes 43..4B)
  MENU    chaîne pointée par une commande 18 (lieu) ou 19 (option de menu)
  COMBAT  texte de la commande 0A du script de combat (0x220000.., 0x384000..0x3ABB17)
  POINTE  chaîne pointée par une valeur 32 bits (objets, capacités, monstres, système…)
  AUTRE   texte lisible sans pointeur repéré (morceaux assemblés par le code : boutique, système,
          menu de combat…) — À REVOIR À LA MAIN (où commence la chaîne, qui la lit)
Bruit graphique filtré : chaînes pointées hors des zones de texte connues.
"""
import re
import struct
import sys

sys.path.insert(0, __import__('os').path.dirname(__file__))
import script as S   # noqa: E402
import pointes as P  # noqa: E402

BASE = 0x200000
# zones (fichier) où un pointeur peut viser du vrai texte
ZONES_TEXTE = [(0x08000, 0x30000), (0x184000, 0x1E8000)]
ZONES_COMBAT = [(0x20000, 0x30000), (0x184000, 0x1ABB18)]


def dans(o, zones):
    return any(lo <= o < hi for lo, hi in zones)


def plausible(s):
    """Rejette le bruit : il faut des mots, peu de codes graphiques."""
    if not re.search(rb'[A-Z]{2}', s):
        return False
    hauts = sum(1 for x in s if x >= 0x60)
    return hauts <= len(s) // 3 and not re.search(rb'UUUU|ZUZU', s)


def combat(d, exclus):
    out = {}
    for lo, hi in ZONES_COMBAT:
        for m in re.finditer(rb'\x0a', d[lo:hi]):
            o = lo + m.start() + 1
            if o in exclus:
                continue
            i = o
            while d[i] != 0 and i - o < 120:
                i += 1
            s = d[o:i]
            if not s or not all(1 <= x < 0x60 for x in s) or not re.search(rb'[A-Z]{2}', s):
                continue
            if d[i + 1] == 0x0B or d[o - 2] in (0x00, 0x0B) or d[o - 3] == 0x43:
                out[o] = s
    # « 43 0A | 0A TEXTE 00 » : le 1er 0A est le paramètre de la commande 43 ; le candidat qui
    # commence un octet trop tôt (texte = « {0A}TEXTE ») chevauche le vrai -> on l'écarte
    for o in sorted(out):
        if o + 1 in out and out[o][:1] == b'\x0a':
            del out[o]
    return out


def catalogue(d):
    an = S.Analyse(d)
    an.graines_maitre()
    an.parcourir()
    lignes = {}
    for a, op, p, t in an.textes:
        lignes[p - BASE] = ('SCRIPT' if op == 1 else 'ECRAN', t)
    for s, t in an.chaines.items():
        lignes.setdefault(s - BASE, ('MENU', t))
    exclus = set()
    for a, (op, n) in an.vu.items():
        exclus.update(range(a - BASE, a - BASE + n))
    zone_combat = set()
    for o, s in combat(d, exclus).items():
        lignes.setdefault(o, ('COMBAT', s))
        zone_combat.update(range(o - 1, o + len(s) + 1))   # opcode 0A compris
    exclus = exclus | zone_combat   # un « pointeur » dans du script de combat n'est pas une chaîne
    # chaînes pointées
    import struct
    for i in range(len(d) - 3):
        v = struct.unpack_from('<I', d, i)[0]
        o = v - BASE
        if not (0 <= o < len(d)) or o in lignes or o in exclus or not dans(o, ZONES_TEXTE):
            continue
        if d[o - 1] != 0:
            continue
        s = P.chaine(d, o)
        if s is not None and plausible(s) and not any(x in exclus for x in range(o, o + len(s) + 1)):
            lignes[o] = ('POINTE', s)
    cov = bytearray(len(d))
    for o, (t, s) in lignes.items():
        cov[o:o + len(s) + 1] = b'\x01' * (len(s) + 1)
    for o in exclus:
        cov[o] = 1
    for lo, hi in ZONES_TEXTE:
        for m in re.finditer(rb'[\x20-\x5f\x01\x13]{5,}', d[lo:hi]):
            o, s = lo + m.start(), m.group()
            if (re.search(rb'[A-Z]{3}', s) and not re.search(rb'UUUU|ZUZU', s)
                    and len(re.findall(rb'[A-Z ]', s)) / len(s) > 0.8 and not any(cov[o:o + len(s)])):
                lignes[o] = ('AUTRE', s)
    return lignes


def largeurs(b):
    """Largeur visible de chaque ligne (codes de contrôle ignorés, insertions comptées 0)."""
    out, n, i = [], 0, 0
    while i < len(b):
        c = b[i]
        if c == 0x01:
            out.append(n)
            n = 0
        elif c in S.CODE_PARAM:
            i += S.CODE_PARAM[c]
        elif c >= 0x10:
            n += 1
        i += 1
    out.append(n)
    return out


PAS = (0x8, 0xC, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x40, 0x50, 0x60, 0x80, 0x100)


def limites(d, lignes):
    """Place permise (colonnes, lignes) pour chaque texte.
    SCRIPT/COMBAT : 18×3 par boîte. Chaînes pointées : regroupées par CHAMP de table (pointeurs à pas
    fixe : pas p tel que p+s et p+2s, ou p-s, pointent aussi un texte) ; limite = le plus grand du champ.
    Le reste : sa propre taille."""
    lim = {}
    for o, (t, s) in lignes.items():
        if t in ('SCRIPT', 'COMBAT'):
            lim[o] = (18, 3)
        else:
            ls = largeurs(s)
            lim[o] = (max(ls), len(ls))
    cible = {o + BASE: o for o, (t, s) in lignes.items() if t in ('POINTE', 'AUTRE', 'MENU')}
    refpos = {}
    for i in range(len(d) - 3):
        v = struct.unpack_from('<I', d, i)[0]
        if v in cible:
            refpos[i] = cible[v]
    par = {p: p for p in refpos}

    def chef(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for p in refpos:
        for s in PAS:
            if p + s in refpos and (p + 2 * s in refpos or p - s in refpos):
                par[chef(p)] = chef(p + s)
    groupes = {}
    for p, o in refpos.items():
        groupes.setdefault(chef(p), set()).add(o)
    for g in groupes.values():
        if len(g) < 3:
            continue
        # noms (1 ligne) et descriptions (plusieurs lignes) peuvent partager un champ : les séparer
        for part in ([o for o in g if lim[o][1] == 1], [o for o in g if lim[o][1] > 1]):
            if not part:
                continue
            c = max(lim[o][0] for o in part)
            n = max(lim[o][1] for o in part)
            for o in part:
                lim[o] = (max(c, lim[o][0]), max(n, lim[o][1]))
    return lim


def main():
    d = open(sys.argv[1], 'rb').read()
    out = sys.argv[2] if len(sys.argv) > 2 else 'out/catalogue.tsv'
    lignes = catalogue(d)
    lim = limites(d, lignes)
    with open(out + '.tmp', 'w', encoding='utf-8') as f:
        f.write('# adresse\ttype\tplace (colonnes x lignes)\ttexte anglais\n')
        for o in sorted(lignes):
            typ, t = lignes[o]
            f.write('%06X\t%s\t%dx%d\t%s\n' % (o + BASE, typ, lim[o][0], lim[o][1], S.lisible(t)))
    __import__('os').replace(out + '.tmp', out)
    par = {}
    for typ, t in lignes.values():
        e = par.setdefault(typ, [0, set(), 0])
        e[0] += 1
        e[1].add(t)
    tot_u = set()
    print('%-7s %6s %6s %8s' % ('type', 'nb', 'diff.', 'car.diff'))
    for typ, (n, u, _) in sorted(par.items()):
        print('%-7s %6d %6d %8d' % (typ, n, len(u), sum(len(x) for x in u)))
        tot_u |= u
    print('TOTAL   %6d %6d %8d' % (len(lignes), len(tot_u), sum(len(x) for x in tot_u)))
    print(out)


if __name__ == '__main__':
    main()
