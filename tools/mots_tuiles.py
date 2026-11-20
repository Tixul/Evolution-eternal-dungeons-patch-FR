"""Mots dessinés en tuiles (police étroite, tuiles 0x60–0xFF du bloc police 0x13FFF / 0x20550).

    python -I -B tools/mots_tuiles.py ROM [--planche SORTIE.png]

1. Extrait l'alphabet étroit des mots anglais connus (découpage par colonnes vides, 7 lignes d'encre,
   ligne 0 libre = place pour un accent).
2. Compose les mots français (MOTS_FR), mesure leur largeur, les range dans les tuiles du « pool »
   (tuiles appelées UNIQUEMENT par des chaînes de texte, réattribuables) et fabrique la table de
   remplacement des suites de codes : utilisée par build.py (fonction appliquer_mots).
3. Les mots dessinés par le CODE (catégories de pièces : HAND, BLADE…) sont redessinés SUR PLACE
   (mêmes tuiles) : SUR_PLACE.
"""
import os
import re
import sys

POLICES = (0x13FFF, 0x20550)

# mots anglais connus : suite de tuiles -> texte (sert à extraire l'alphabet)
CONNUS = {
    (0x60, 0x61, 0x62, 0x63, 0x64, 0x65): 'WAREHOUSE',
    (0x66, 0x67, 0x68, 0x69): 'STORAGE',
    (0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F): 'HEADQUATERS',
    (0x70, 0x71, 0x72, 0x73, 0x74, 0x75): 'DEEPEST AREA',
    (0x76, 0x77, 0x78, 0x79): 'SOCIETY',
    (0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F): 'COMMUNICATE',
    (0x80, 0x81, 0x82, 0x63, 0x64, 0x65): "MAG'S HOUSE",
    (0x80, 0x81, 0x82, 0x9D, 0x9E, 0x9F): "MAG'S ROOM",
    (0x83, 0x84, 0x85, 0x63, 0x64, 0x65): 'MOBILEHOUSE',
    (0x86, 0x87, 0x88, 0x89, 0x8A): 'AIR FIELD',
    (0x8B, 0x8C, 0x8D, 0x8E, 0x8F): 'COMBINE',
    (0x90, 0x91, 0x92, 0x93, 0x94): 'SEA OTTER',
    (0x95, 0x96, 0x97, 0x98, 0x99): 'ITEM SHOP',
    (0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F): 'LIVING ROOM',
    (0xA0, 0xA1, 0xA2, 0xA3, 0x9E, 0x9F): 'ENGINE ROOM',
    (0xA4, 0xA5, 0xA6, 0xA7, 0x9E, 0x9F): "LINEAR'S ROOM",
    (0xA8, 0xA9, 0xAA, 0xAB, 0x98, 0x99): 'UPGRADE SHOP',
    (0xAC, 0xAD, 0xAE, 0x9D, 0x9E, 0x9F): 'RADAR ROOM',
    (0xB0, 0xB1, 0xB2, 0xB3, 0xB4): 'RODRIGEZ',
    (0xB5, 0xB6, 0xB7, 0xB8, 0xB9): 'LEONARD',
    (0xBA, 0xBB, 0xBC, 0xBD, 0xBE): 'DESCENT',
    (0xC0, 0xC1, 0xC2): 'PARTS',
    (0xE4, 0xE5, 0xE6, 0x9D, 0x9E, 0x9F): 'EXHIBIT ROOM',
    (0xE7, 0xE8, 0xE9, 0xEA, 0xEB): 'BRAINWASH',
    (0xF0, 0xF1, 0xF2): 'SMALL',
    (0xF3, 0xF4, 0xF5): 'HEAVY',
    (0xF6, 0xF7, 0xF8, 0xF9, 0xFA): 'BARBARA',
    (0xFB, 0xFC, 0xFD, 0xFE): 'FORMATION',
}


def tuile(rom, base, c):
    """8 lignes de 8 valeurs 0..3 (0x13FFF : encre 1, fond 3)."""
    out = []
    for y in range(8):
        w = rom[base + c * 16 + y * 2] | rom[base + c * 16 + y * 2 + 1] << 8
        out.append([(w >> (14 - 2 * x)) & 3 for x in range(8)])
    return out


def bande(rom, codes):
    rows = [[] for _ in range(8)]
    for c in codes:
        t = tuile(rom, POLICES[0], c)
        for y in range(8):
            rows[y] += t[y]
    return rows


def decoupe(rows):
    """Glyphes (listes de colonnes) séparés par des colonnes sans encre (valeur 1) sur les lignes 1..7."""
    larg = len(rows[0])
    encre = [any(rows[y][x] == 1 for y in range(1, 8)) for x in range(larg)]
    glyphes, cur, vides, espaces = [], [], 0, []
    for x in range(larg):
        if encre[x]:
            if not cur and glyphes and vides >= 3:
                espaces.append(len(glyphes))
            cur.append([rows[y][x] for y in range(8)])
            vides = 0
        else:
            if cur:
                glyphes.append(cur)
                cur = []
            vides += 1
    if cur:
        glyphes.append(cur)
    return glyphes, espaces


def alphabet(rom):
    alpha, conflits = {}, []
    for codes, mot in CONNUS.items():
        glyphes, _ = decoupe(bande(rom, codes))
        lettres = [c for c in mot if c != ' ']
        if len(glyphes) != len(lettres):
            conflits.append((mot, len(glyphes), len(lettres)))
            continue
        for c, g in zip(lettres, glyphes):
            alpha.setdefault(c, g)
    return alpha, conflits


ACCENT = {'É': ('E', 'aigu'), 'È': ('E', 'grave'), 'Ê': ('E', 'circ'), 'À': ('A', 'grave'),
          'Ô': ('O', 'circ'), 'Î': ('I', 'circ'), 'Û': ('U', 'circ'), 'Â': ('A', 'circ')}


def glyphe(alpha, ch):
    if ch in alpha:
        return [list(col) for col in alpha[ch]]
    if ch in ACCENT:
        base, kind = ACCENT[ch]
        g = [list(col) for col in alpha[base]]
        w = len(g)
        mid = w // 2
        if kind == 'aigu':
            g[min(w - 1, mid + (1 if w > 3 else 0))][0] = 1
        elif kind == 'grave':
            g[max(0, mid - (1 if w > 3 else 0))][0] = 1
        else:   # circonflexe : 1 pixel centré (ligne 0 seulement disponible)
            g[mid][0] = 1
        return g
    if ch == '.':
        return [[3, 3, 3, 3, 3, 3, 3, 1]]
    raise KeyError('lettre étroite absente : %r' % ch)


def compose(alpha, texte):
    """Colonnes du mot (glyphes séparés d'1 colonne de fond, espace = 3 colonnes)."""
    cols = []
    for ch in texte:
        if ch == ' ':
            cols += [[3] * 8] * 3
            continue
        if cols and cols[-1] != [3] * 8:
            cols.append([3] * 8)
        cols += glyphe(alpha, ch)
    return cols


def en_tuiles(cols, n=None):
    """Colonnes -> liste de tuiles (8×8), complétées de fond jusqu'à n tuiles."""
    k = n if n is not None else -(-len(cols) // 8)
    cols = cols + [[3] * 8] * (8 * k - len(cols))
    return [[[cols[t * 8 + x][y] for x in range(8)] for y in range(8)] for t in range(k)]


def octets(t):
    b = bytearray()
    for row in t:
        w = 0
        for x, v in enumerate(row):
            w |= v << (14 - 2 * x)
        b += w.to_bytes(2, 'little')
    return bytes(b)


# Lettres absentes des mots anglais, dessinées à la main (colonnes de haut en bas, lignes 1..7)
Q_LIGNES = [".##.", "#..#", "#..#", "#..#", "#.##", "#..#", ".###"]


def lettre_main(lignes):
    larg = len(lignes[0])
    return [[3] + [1 if lignes[y][x] == '#' else 3 for y in range(7)] for x in range(larg)]


# Noms de lieux / menus (chaînes MENU) : suite anglaise -> mot français (≤ 6 tuiles = 48 px)
MOTS_FR = {
    (0x60, 0x61, 0x62, 0x63, 0x64, 0x65): 'ENTREPÔT',
    (0x66, 0x67, 0x68, 0x69): 'DÉPÔT',
    (0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F): 'SIÈGE',
    (0x70, 0x71, 0x72, 0x73, 0x74, 0x75): 'TRÉFONDS',
    (0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F): 'LIAISON',
    (0x80, 0x81, 0x82, 0x63, 0x64, 0x65): 'CHEZ MAG',
    (0x80, 0x81, 0x82, 0x9D, 0x9E, 0x9F): 'CH. MAG',
    (0x83, 0x84, 0x85, 0x63, 0x64, 0x65): 'CARAVANE',
    (0x86, 0x87, 0x88, 0x89, 0x8A): 'AÉROPORT',
    (0x8B, 0x8C, 0x8D, 0x8E, 0x8F): 'COMBINER',
    (0x95, 0x96, 0x97, 0x98, 0x99): 'BOUTIQUE',
    (0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F): 'SALON',
    (0xA0, 0xA1, 0xA2, 0xA3, 0x9E, 0x9F): 'MACHINES',
    (0xA4, 0xA5, 0xA6, 0xA7, 0x9E, 0x9F): 'CH. LINEAR',
    (0xA8, 0xA9, 0xAA, 0xAB, 0x98, 0x99): 'ATELIER',
    (0xAC, 0xAD, 0xAE, 0x9D, 0x9E, 0x9F): 'SALLE RADAR',
    (0xE4, 0xE5, 0xE6, 0x9D, 0x9E, 0x9F): 'SALLE EXPO',
}
# Tuiles réutilisables : celles des mots ci-dessus + celles des noms de pièces / soldats / lavage de
# cerveau, que le français écrit en lettres normales (PIECES_TEXTE). Gardées telles quelles : SOCIETY,
# SEA OTTER, RODRIGEZ, LEONARD, DESCENT, BARBARA, FORMATION, PEPPER (EC–EF), BF (redessinée « NV »).
LIBEREES = set(range(0xC0, 0xE4)) - {0xBF} | set(range(0xE7, 0xEC)) | set(range(0xF0, 0xF6))
# « {PIÈCE} {NV} » des noms de pièces -> lettres normales « NV » (fait à la fabrication)
PIECE_NV = (bytes([0xC0, 0xC1, 0xC2, 0x20, 0xBF]), b'NV')


class Plan:
    """Nouveaux dessins de tuiles + table de remplacement des suites de codes."""

    def __init__(self, rom):
        self.alpha, _ = alphabet(rom)
        self.alpha['Q'] = lettre_main(Q_LIGNES)
        pool = set(LIBEREES)
        for seq in MOTS_FR:
            pool |= set(seq)
        self.pool = sorted(pool)
        self.dessins = {}          # code tuile -> 16 octets
        self.remplace = {}         # suite anglaise (bytes) -> suite française (bytes)
        libres = list(self.pool)
        deja = {}                  # dessin -> code (tuiles identiques partagées)
        for seq, mot in MOTS_FR.items():
            cols = compose(self.alpha, mot)
            if len(cols) > 8 * 6:
                raise ValueError('mot trop large : %s (%d px)' % (mot, len(cols)))
            codes = []
            for t in en_tuiles(cols):
                b = octets(t)
                if b not in deja:
                    if not libres:
                        raise ValueError('plus de tuiles libres')
                    c = libres.pop(0)
                    deja[b] = c
                    self.dessins[c] = b
                codes.append(deja[b])
            # compléter par des espaces jusqu'à la longueur anglaise : l'affichage n'efface pas la zone
            codes += [0x20] * (len(seq) - len(codes))
            self.remplace[bytes(seq)] = bytes(codes)
        # BF « LV » -> « NV » sur place (N 4 px + 1 + V 3 px)
        n = self.alpha['N']
        v = [[3] + [1 if r[x] == '#' else 3 for r in ["#.#", "#.#", "#.#", "#.#", "#.#", "#.#", ".#."]]
             for x in range(3)]
        self.dessins[0xBF] = octets(en_tuiles(n + [[3] * 8] + v, 1)[0])
        self.utilisees = len(deja)

    def appliquer(self, b):
        """Remplace, dans une chaîne encodée, les suites de tuiles anglaises par les françaises."""
        b = b.replace(*PIECE_NV)
        for old in sorted(self.remplace, key=len, reverse=True):
            b = b.replace(old, self.remplace[old])
        return b

    def ecrire(self, r):
        for base in POLICES:
            for c, t in self.dessins.items():
                r[base + c * 16:base + c * 16 + 16] = t


def main():
    rom = open(sys.argv[1], 'rb').read()
    alpha, conflits = alphabet(rom)
    print('alphabet :', ''.join(sorted(alpha)), '| largeurs', {c: len(g) for c, g in sorted(alpha.items())})
    print('mots non découpés proprement :', conflits)
    p = Plan(rom)
    print('tuiles réservées', len(p.pool), '| utilisées', p.utilisees)
    if '--planche' in sys.argv:
        from PIL import Image
        out = sys.argv[sys.argv.index('--planche') + 1]
        pal = [255, 170, 85, 0]
        mots = list(MOTS_FR.items())
        im = Image.new('L', (8 * 6 + 4, 12 * len(mots)), 255)
        for k, (seq, mot) in enumerate(mots):
            for j, c in enumerate(p.remplace[bytes(seq)]):
                t = p.dessins[c]
                for y in range(8):
                    w = t[y * 2] | t[y * 2 + 1] << 8
                    for x in range(8):
                        im.putpixel((j * 8 + x, k * 12 + y), pal[(w >> (14 - 2 * x)) & 3])
        im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(out)
        print(out)


if __name__ == '__main__':
    main()
