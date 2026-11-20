"""Analyseur du script d'événements d'Evolution (E).

    python -I -B tools/script.py ROM [--dump FICHIER.txt]

Parcourt TOUT le script en suivant le flot à partir de la table maîtresse 0x3ABB18
(11 groupes -> pointeurs de scripts), comme l'interpréteur 0x20DA37 (82 commandes, table 0x20E373).
Sort : couverture, textes (commande 01, 43..4B, chaînes pointées par 18 et par les menus 19),
erreurs (opcode >= 0x52, saut hors ROM).  Détail des commandes : FORMAT.md.
"""
import struct
import sys

BASE = 0x200000
MAITRE = 0x3ABB18
NB_GROUPES = 11

# taille des paramètres des commandes simples (octets), sans texte ni pointeur
FIXE = {0x02: 0, 0x08: 1, 0x09: 0, 0x0A: 1, 0x0B: 1, 0x0E: 1, 0x0F: 1, 0x10: 0,
        0x11: 1, 0x12: 1, 0x13: 1, 0x14: 0, 0x15: 0, 0x16: 1, 0x17: 1, 0x1A: 1,
        0x1C: 0, 0x1D: 0, 0x1F: 0, 0x20: 1, 0x21: 1, 0x23: 0, 0x37: 2, 0x38: 1,
        0x39: 1, 0x3C: 1, 0x3D: 1, 0x3E: 0, 0x3F: 0, 0x40: 0, 0x41: 4, 0x42: 0,
        0x4C: 0, 0x4D: 0, 0x4E: 0, 0x4F: 0, 0x50: 0, 0x51: 0, 0x33: 0, 0x34: 0, 0x35: 4,
        0x3A: 6, 0x3B: 6}
for _o in range(0x24, 0x31):
    FIXE[_o] = 0
FIN = {0x00, 0x04, 0x03, 0x06, 0x07, 0x1B, 0x1E, 0x22}   # pas de suite directe
CODE_PARAM = {0x02: 1, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x0F: 2}   # codes de texte avec paramètre


class Rom:
    def __init__(self, data):
        self.d = data

    def u8(self, a):
        return self.d[a - BASE]

    def u16(self, a):
        return struct.unpack_from('<H', self.d, a - BASE)[0]

    def u32(self, a):
        return struct.unpack_from('<I', self.d, a - BASE)[0]

    def ok(self, a):
        return BASE <= a < BASE + len(self.d)


def lire_texte(rom, a):
    """Chaîne de texte jusqu'à 00 (codes à paramètre sautés). Rend (fin_exclue, octets)."""
    debut = a
    while True:
        c = rom.u8(a)
        a += 1
        if c == 0:
            return a, rom.d[debut - BASE:a - 1 - BASE]
        if c in CODE_PARAM:
            a += CODE_PARAM[c]


class Analyse:
    def __init__(self, data, maitre=MAITRE, nb_groupes=NB_GROUPES):
        self.rom = Rom(data)
        self.maitre, self.nb_groupes = maitre, nb_groupes   # ROM JP : 0x3AB1EC
        self.vu = {}          # adresse de commande -> (opcode, taille)
        self.textes = []      # (adresse_commande, type, adresse_texte, octets)
        self.chaines = {}     # chaînes pointées (18, menus) : adresse -> octets
        self.erreurs = []
        self.graines = []
        self.tables_07 = []

    def graines_maitre(self):
        r = self.rom
        groupes = [r.u32(self.maitre + 4 * i) for i in range(self.nb_groupes)]
        self.taille_groupes = []
        for g in groupes:
            a, borne = g, 1 << 32
            while a < borne and (a == g or a not in groupes):
                v = r.u32(a)
                if not (BASE <= v < BASE + len(r.d)):
                    break
                self.graines.append((v, 'maitre %06X' % a))
                if v > g:
                    borne = min(borne, v)
                a += 4
            self.taille_groupes.append((a - g) // 4)
        return groupes

    def parcourir(self):
        r = self.rom
        pile = list(self.graines)
        while pile:
            a, origine = pile.pop()
            while True:
                if not r.ok(a):
                    self.erreurs.append((a, 'hors ROM depuis ' + origine))
                    break
                if a in self.vu:
                    break
                op = r.u8(a)
                p = a + 1
                suite = True
                if op >= 0x52:
                    self.erreurs.append((a, 'opcode %02X (depuis %s)' % (op, origine)))
                    break
                if op == 0x01 or 0x43 <= op <= 0x4B:
                    fin, t = lire_texte(r, p)
                    self.textes.append((a, op, p, t))
                    p = fin
                elif op in (0x04, 0x05, 0x0C, 0x0D, 0x36):
                    cible = r.u32(p)
                    p += 4
                    pile.append((cible, '%02X@%06X' % (op, a)))
                    suite = op != 0x04
                elif op == 0x03:
                    i, j = r.u8(p), r.u8(p + 1)
                    p += 2
                    pile.append((r.u32(r.u32(self.maitre + 4 * i) + 4 * j), '03@%06X' % a))
                    suite = False
                elif op == 0x07:
                    n = r.u8(p)
                    p += 1
                    for k in range(n):
                        pile.append((r.u32(p + 4 * k), '07@%06X' % a))
                    self.tables_07.append((a, n))
                    p += 4 * n
                    suite = False
                elif op == 0x18:
                    s = r.u32(p)
                    p += 4
                    self.chaines[s] = lire_texte(r, s)[1]
                elif op == 0x19:
                    p += 12
                    while True:
                        t = r.u32(p)
                        if t == 0:
                            p += 4
                            break
                        cible = r.u32(p + 4)
                        self.chaines[t] = lire_texte(r, t)[1]
                        pile.append((cible, '19@%06X' % a))
                        p += 12
                elif op in (0x31, 0x32):
                    p += 1           # rend la main puis reprend juste après
                elif op in FIXE:
                    p += FIXE[op]
                    suite = op not in FIN
                elif op in FIN:
                    suite = False
                else:
                    self.erreurs.append((a, 'opcode %02X non classé' % op))
                    break
                self.vu[a] = (op, p - a)
                if not suite:
                    break
                a = p


def lisible(t, barre_code=True):
    """Format lisible : 0x01 = '/', vrai caractère '/' (0x2F) = '{2F}' (avant le 21/11 : '/' aussi,
    ambigu -> lisible_ancien, encore accepté comme clé de traduction)."""
    out = []
    i = 0
    while i < len(t):
        c = t[i]
        if c == 1:
            out.append('/')
        elif c == 0x2F and barre_code:
            out.append('{2F}')
        elif c == 0x13:
            out.append("'")
        elif 0x20 <= c < 0x60:      # 0x60+ = minuscules-marques / mots en tuiles / kana -> {xx}
            out.append(chr(c))
        else:
            n = CODE_PARAM.get(c, 0)
            out.append('{%02X%s}' % (c, ''.join(' %02X' % x for x in t[i + 1:i + 1 + n])))
            i += n
        i += 1
    return ''.join(out)


def lisible_ancien(t):
    return lisible(t, barre_code=False)


def main():
    data = open(sys.argv[1], 'rb').read()
    an = Analyse(data)
    groupes = an.graines_maitre()
    an.parcourir()
    octets = sum(t for _, t in an.vu.values())
    print('groupes', len(groupes), 'graines', len(an.graines))
    print('commandes', len(an.vu), 'octets de script couverts', octets)
    print('textes 01/43-4B', len(an.textes), 'différents', len({t for *_, t in an.textes}),
          'caractères', sum(len(t) for *_, t in an.textes))
    print('chaînes pointées (18/menus)', len(an.chaines))
    print('erreurs', len(an.erreurs))
    for e in an.erreurs[:30]:
        print('  %06X %s' % e)
    if an.vu:
        lo, hi = min(an.vu), max(an.vu)
        print('étendue %06X..%06X' % (lo, hi))
    if '--dump' in sys.argv:
        out = sys.argv[sys.argv.index('--dump') + 1]
        with open(out, 'w', encoding='utf-8') as f:
            for a, op, pt, t in sorted(an.textes):
                f.write('%06X %02X %s\n' % (a, op, lisible(t)))
            for s, t in sorted(an.chaines.items()):
                f.write('%06X PTR %s\n' % (s, lisible(t)))
        print(out)


if __name__ == '__main__':
    main()
