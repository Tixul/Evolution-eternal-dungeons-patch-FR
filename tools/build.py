"""Fabrique la ROM traduite d'Evolution: Eternal Dungeons (Europe) et le patch IPS.

    python tools/build.py --rom ROM_EN.ngc --lang fr [--debug] [--ips]
        -> out/fr.ngc (ou out/fr_debug.ngc) et, avec --ips, le patch .ips à côté
    python tools/build.py ROM_EN.ngc SORTIE.ngc --tout-en-saut
        test : sans traduction, fait passer TOUTES les boîtes par un saut (le jeu doit être identique)

- La ROM d'entrée est vérifiée (CRC32 BE47E531, 2 097 152 octets) ; la sortie fait 4 Mio : puce 1 = ROM
  d'origine modifiée, puce 2 (fichier 0x200000 = CPU 0x800000) = tout le neuf.
- Traduction : tous les `lang/<code>/*.txt`. Lignes `=ADRESSE<TAB>texte` (texte du catalogue à cette
  adresse, voir tools/extraire.py) ou `@ADRESSE<TAB>texte` (chaîne entière jusqu'au 00, réécrite sur
  place) ; `#` = commentaire. Texte : minuscules acceptées (mises en majuscules), accents É È Ê À Ç Ù Î
  Ô Û Â, `/` = ligne suivante, `|` = boîte suivante (dialogues et combat seulement), `{xx}` = code brut
  (ex. `{0B}` nom inséré, `{04}` nombre), ponctuation , ; … ' « » ! ? . : - + %.
- Placement : sur place si ça tient (fin bourrée avec le code 03 = rien) ; sinon
  dialogues : `01 texte 00` -> `04 adr` vers `01 … 00 02 01 … 00 04 retour` (script des scènes) ;
  combat : `0A texte 00` -> `01 adr` vers `0A … 00 0B 0A … 00 01 retour` (script de combat) ;
  chaînes pointées : copie sur la puce 2 et réécriture des pointeurs 32 bits.
- Aussi : police (accents), icônes PV/PE, mots dessinés en tuiles (mots_tuiles.py), libellés d'écran
  (libelles.py) ; --debug ajoute l'option DEBUG au menu de commandes (drapeau 0xC7).
Détails : FORMAT.md.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import extraire as E   # noqa: E402
import script as S     # noqa: E402
import mots_tuiles as MT  # noqa: E402
import libelles as LB     # noqa: E402

BASE = 0x200000
PUCE2 = 0x200000
PUCE2_CPU = 0x800000
POLICES = (0x13FFF, 0x20550)   # fichier : tuile 0 des DEUX copies de la police (16 o/tuile)
LARGEUR, LIGNES = 18, 3

# code -> (accent, lettre de base). Dessin : accent sur les lignes 0-1, lettre sur 2-7.
ACCENTS = {'É': 0x23, 'È': 0x2C, 'Ê': 0x3C, 'À': 0x3E, 'Ç': 0x40,
           'Ù': 0x5C, 'Î': 0x5F, 'Ô': 0x3D, 'Û': 0x2A, 'Â': 0x26}
LETTRE6 = {
    'E': ["11111113", "13333333", "11111133", "13333333", "13333333", "11111113"],
    'A': ["33313333", "33131333", "31333133", "31111133", "13333313", "13333313"],
    'C': ["33111133", "31333313", "13333333", "13333333", "31333313", "33111133"],
    'I': ["31111133", "33313333", "33313333", "33313333", "33313333", "31111133"],
    'O': ["33111333", "31333133", "13333313", "13333313", "31333133", "33111333"],
    'U': ["13333313", "13333313", "13333313", "13333313", "13333313", "31111133"],
}
AIGU = ["33333133", "33331333"]
GRAVE = ["33133333", "33313333"]
CIRC = ["33313333", "33131333"]


def dessins():
    g = {
        'É': AIGU + LETTRE6['E'], 'È': GRAVE + LETTRE6['E'], 'Ê': CIRC + LETTRE6['E'],
        'À': GRAVE + LETTRE6['A'], 'Â': CIRC + LETTRE6['A'], 'Ù': GRAVE + LETTRE6['U'],
        'Û': CIRC + LETTRE6['U'], 'Î': CIRC + LETTRE6['I'], 'Ô': CIRC + LETTRE6['O'],
        'Ç': LETTRE6['C'] + ["33313333", "33113333"],
    }
    # icônes du HUD (2 lettres de 3 px) : 0x1C « HP » -> « PV », 0x1D « FP » -> « PE »
    P = ["113", "131", "131", "131", "113", "133", "133"]
    V = ["131", "131", "131", "131", "313", "313", "313"]
    E = ["111", "133", "133", "113", "133", "133", "111"]
    icones = {0x1C: ["33333333"] + [p + "3" + v + "3" for p, v in zip(P, V)],
              0x1D: ["33333333"] + [p + "3" + e + "3" for p, e in zip(P, E)]}
    out = {}
    for code, rows in icones.items():
        b = bytearray()
        for r in rows:
            w = 0
            for x, c in enumerate(r):
                w |= int(c) << (14 - 2 * x)
            b += struct.pack('<H', w)
        out[code] = bytes(b)
    for ch, rows in g.items():
        b = bytearray()
        for r in rows:
            w = 0
            for x, c in enumerate(r):
                w |= int(c) << (14 - 2 * x)
            b += struct.pack('<H', w)
        out[ACCENTS[ch]] = bytes(b)
    return out


PONCT = {',': 0x29, ';': 0x28, '…': 0x5E, "'": 0x13, '’': 0x13, '«': 0x5B, '»': 0x5D,
         '“': 0x5B, '”': 0x5D, '[': 0x5B, ']': 0x5D}
SIMPLES = set(b' !.?:-+%0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
REPLI = {'Ë': 'E', 'Ï': 'I', 'Ü': 'U', 'Œ': 'OE', 'Æ': 'AE', 'Ÿ': 'Y'}


class Erreur(Exception):
    pass


def encoder(fr):
    """Français naturel -> liste de boîtes (bytes), séparées par '|'. Lignes séparées par 0x01."""
    boites = []
    for boite in fr.split('|'):
        b = bytearray()
        i = 0
        s = boite.replace('...', '…')
        while i < len(s):
            c = s[i]
            if c == '{':
                j = s.index('}', i)
                b += bytes(int(x, 16) for x in s[i + 1:j].split())
                i = j + 1
                continue
            if c == '/':
                b.append(0x01)
            elif c in PONCT:
                b.append(PONCT[c])
            else:
                u = c.upper()
                u = REPLI.get(u, u)
                if u in ACCENTS:
                    b.append(ACCENTS[u])
                elif all(ord(x) < 128 and ord(x) in SIMPLES for x in u):
                    b += u.encode()
                else:
                    raise Erreur('caractère non affichable %r dans %r' % (c, fr))
            i += 1
        boites.append(bytes(b))
    return boites


def lignes_de(b):
    return E.largeurs(b)


class Fabrique:
    def __init__(self, en):
        if len(en) != 0x200000:
            raise Erreur('ROM anglaise attendue (2 Mio)')
        self.en = en
        self.r = bytearray(en) + bytearray(b'\xff' * 0x200000)
        self.libre = PUCE2
        self.cat = E.catalogue(en)
        self.lim = E.limites(en, self.cat)
        self.mots = MT.Plan(en)
        self.stats = {'sur place': 0, 'saut': 0, 'déplacée': 0}
        self._refs = None
        self.ecrit = set()         # octets (fichier) déjà réécrits : détecte les chevauchements

    def place(self, data):
        o = self.libre
        if o + len(data) > len(self.r):
            raise Erreur('puce 2 pleine')
        self.r[o:o + len(data)] = data
        self.libre += len(data)
        return o - PUCE2 + PUCE2_CPU

    def refs(self):
        if self._refs is None:
            cibles = {o + BASE for o, (t, _) in self.cat.items() if t in ('MENU', 'POINTE', 'AUTRE')}
            self._refs = {}
            for i in range(len(self.en) - 3):
                v = struct.unpack_from('<I', self.en, i)[0]
                if v in cibles:
                    self._refs.setdefault(v - BASE, []).append(i)
        return self._refs

    def police(self):
        for base in POLICES:
            for code, t in dessins().items():
                self.r[base + code * 16:base + code * 16 + 16] = t
        self.mots.ecrire(self.r)    # mots dessinés en tuiles (noms de lieux), voir mots_tuiles.py

    def controle(self, typ, en, boites, o):
        if typ in ('SCRIPT', 'COMBAT'):
            for b in boites:
                ls = lignes_de(b)
                if len(ls) > LIGNES or max(ls) > LARGEUR:
                    raise Erreur('%06X boîte trop grande (%d lignes, %d col.) : %r'
                                 % (o + BASE, len(ls), max(ls), b))
        else:
            if len(boites) > 1:
                raise Erreur('%06X : « | » interdit pour le type %s' % (o + BASE, typ))
            ls0 = lignes_de(en)
            mx, nl = self.lim.get(o, (max(ls0), len(ls0)))
            ls = lignes_de(boites[0])
            if max(ls) > max(mx, 1) or len(ls) > nl:
                raise Erreur('%06X %s : %s dépasse la place permise (%d col., %d lignes)'
                             % (o + BASE, typ, ls, mx, nl))

    def appliquer(self, o, typ, en, boites, force_saut=False):
        """o = fichier, début du texte anglais (après l'opcode pour SCRIPT/ECRAN/COMBAT)."""
        fin = o + len(en)          # position du 00
        zone = set(range(o - (1 if typ in ('SCRIPT', 'ECRAN', 'COMBAT') else 0), fin + 1))
        if zone & self.ecrit:
            raise Erreur('%06X : chevauche un texte déjà remplacé (catalogue à corriger)' % (o + BASE))
        self.ecrit |= zone
        if not force_saut and len(boites) == 1 and len(boites[0]) <= len(en):
            b = boites[0]
            self.r[o:fin] = b + b'\x03' * (len(en) - len(b))
            self.stats['sur place'] += 1
            return
        if typ in ('SCRIPT', 'ECRAN', 'COMBAT'):
            op = self.en[o - 1]
            a = o - 1
            if fin + 1 - a < 5:
                raise Erreur('%06X : texte d\'origine trop court pour un saut' % (o + BASE))
            saut = 0x04 if typ != 'COMBAT' else 0x01
            attente = b'\x02' if typ != 'COMBAT' else b'\x0b'
            bloc = bytearray()
            for k, b in enumerate(boites):
                if k:
                    bloc += attente
                bloc += bytes([op]) + b + b'\x00'
            bloc += bytes([saut]) + struct.pack('<I', fin + 1 + BASE)
            cible = self.place(bytes(bloc))
            self.r[a:a + 5] = bytes([saut]) + struct.pack('<I', cible)
            self.stats['saut'] += 1
            return
        if typ == 'AUTRE':
            raise Erreur('%06X AUTRE : plus long que l\'anglais, à traiter à la main' % (o + BASE))
        refs = self.refs().get(o, [])
        if not refs:
            raise Erreur('%06X : aucun pointeur trouvé pour déplacer la chaîne' % (o + BASE))
        cible = self.place(boites[0] + b'\x00')
        for i in refs:
            self.r[i:i + 4] = struct.pack('<I', cible)
        self.stats['déplacée'] += 1


def lire_trad(chemin):
    par_texte, par_adr = {}, {}
    with open(chemin, encoding='utf-8') as f:
        for n, l in enumerate(f, 1):
            l = l.rstrip('\n')
            if not l.strip() or l.startswith('#'):
                continue
            if '\t' not in l:
                raise Erreur('%s:%d : il manque la tabulation' % (chemin, n))
            en, fr = l.split('\t', 1)
            if en.startswith('@'):          # chaîne ENTIÈRE à cette adresse (jusqu'au 00)
                par_adr[int(en[1:], 16) - BASE] = fr
            elif en.startswith('='):        # texte du CATALOGUE à cette adresse (tel qu'il le délimite)
                par_adr[int(en[1:], 16) - BASE] = ('=', fr)
            else:
                par_texte[en] = fr
    return par_texte, par_adr


CRC_EN = 0xBE47E531      # ROM attendue : Evolution - Eternal Dungeons (Europe), 2 097 152 octets


def main():
    args = sys.argv[1:]
    if '--rom' in args:   # mode « kit » : --rom ROM_EN --lang CODE [--debug] [--ips]
        import glob
        import zlib
        en = open(args[args.index('--rom') + 1], 'rb').read()
        if len(en) != 0x200000 or zlib.crc32(en) != CRC_EN:
            raise SystemExit('ROM refusée : il faut « Evolution - Eternal Dungeons (Europe) » non modifiée '
                             '(2 097 152 octets, CRC32 BE47E531).')
        code = args[args.index('--lang') + 1] if '--lang' in args else 'fr'
        racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        lang = os.path.join(racine, 'lang', code)
        os.makedirs(os.path.join(racine, 'out'), exist_ok=True)
        sortie = os.path.join(racine, 'out', code + ('_debug' if '--debug' in args else '') + '.ngc')
        args = list(args) + ['--fichiers'] + sorted(glob.glob(os.path.join(lang, '*.txt')))
    else:
        en = open(args[0], 'rb').read()
        sortie = args[1]
    fab = Fabrique(en)
    fab.police()
    erreurs = []
    if '--tout-en-saut' in args:
        for o, (typ, t) in sorted(fab.cat.items()):
            if typ in ('SCRIPT', 'COMBAT') and len(t) + 2 >= 5:
                try:
                    fab.appliquer(o, typ, t, [t], force_saut=True)
                except Erreur as e:
                    erreurs.append(str(e))
    else:
        if '--fichiers' in args:
            fichiers = args[args.index('--fichiers') + 1:]
        elif '--trad' in args:
            fichiers = [args[args.index('--trad') + 1]]
        else:
            raise SystemExit(__doc__)
        par_texte, par_adr = {}, {}
        for fichier in fichiers:
            t, a = lire_trad(fichier)
            par_texte.update(t)
            par_adr.update(a)
        print('traductions lues :', len(par_texte) + len(par_adr), 'dans', len(fichiers), 'fichier(s)')
        for o in par_adr:          # adresse donnée à la main, hors catalogue : sur place seulement
            if isinstance(par_adr[o], tuple):
                if o not in fab.cat:
                    erreurs.append('%06X : « = » mais pas de texte au catalogue à cette adresse' % (o + BASE))
                continue
            if o not in fab.cat or fab.cat[o][0] == 'AUTRE':
                fin = en.index(b'\x00', o)          # chaîne ENTIÈRE (un AUTRE peut n'en être que le début)
                fab.cat[o] = ('AUTRE', en[o:fin])
        for o, (typ, t) in sorted(fab.cat.items()):
            fr = par_adr.get(o)
            if isinstance(fr, tuple):
                fr = fr[1]
            if fr is None:
                fr = par_texte.get(S.lisible(t))
                if fr is None:
                    fr = par_texte.get(S.lisible_ancien(t))   # clé d'avant le format {2F}
            if fr is None:
                if fab.mots.appliquer(t) == t:
                    continue
                boites = [fab.mots.appliquer(t)]   # pas de traduction, mais des mots-tuiles à changer
            try:
                if fr is not None:
                    boites = [fab.mots.appliquer(b) for b in encoder(fr)]
                if typ == 'MENU' and len(boites) == 1 and 0x01 not in boites[0]:
                    # un menu n'efface pas sa case : compléter par des espaces jusqu'à la largeur anglaise
                    manque = max(lignes_de(t)) - max(lignes_de(boites[0]))
                    if manque > 0:
                        boites = [boites[0] + b' ' * manque]
                fab.controle(typ, t, boites, o)
                fab.appliquer(o, typ, t, boites)
            except Erreur as e:
                erreurs.append(str(e))
    for e in erreurs[:40]:
        print('ERREUR', e)
    print('erreurs', len(erreurs), fab.stats, 'puce 2 utilisée 0x%X octets' % (fab.libre - PUCE2))
    if erreurs and '--tolerant' not in args:
        print('ROM NON écrite (erreurs)')
        sys.exit(1)
    if '--tout-en-saut' not in args:
        def lisible_vers_octets(s):
            out, i = bytearray(), 0
            while i < len(s):
                if s[i] == '{':
                    j = s.index('}', i)
                    out += bytes(int(x, 16) for x in s[i + 1:j].split())
                    i = j + 1
                    continue
                out.append(0x01 if s[i] == '/' else ord(s[i]))
                i += 1
            return bytes(out)
        print('libellés d\'écran remplacés :', LB.appliquer(fab.r, en, encoder, lisible_vers_octets, fab.ecrit))
        # mots-tuiles dans les chaînes appelées par le CODE (en-têtes de lieux : 0x21143F « ITEM SHOP »…),
        # hors catalogue : remplacés sur place (le français est complété à la longueur anglaise).
        # Exclu : la table de comptage 0x221A00–0x221E80 (données, pas du texte).
        n = 0
        for old, new in fab.mots.remplace.items():
            i = en.find(old, 0x08000, 0x20000)
            while i != -1:
                if not (0x21A00 <= i < 0x21E80) and not any(x in fab.ecrit for x in range(i, i + len(old))):
                    fab.r[i:i + len(old)] = new
                    n += 1
                i = en.find(old, i + 1, 0x20000)
        print('mots-tuiles remplacés dans les chaînes du code :', n)
    if '--debug' in args:
        # ROM DE TEST : option DEBUG du menu de commandes (drapeau 0xC7 = bit 0x80 de 0x4818, testé
        # par la commande de script 0A). Le test 0x20DABB `call 0x209CA3` est détourné vers une
        # routine qui force le bit puis refait le test (idée : The Cutting Room Floor, routine
        # déplacée sur la puce 2 car 0x1FFC00 est peut-être la zone des sauvegardes).
        assert fab.r[0xDABB:0xDABF] == bytes.fromhex('1da39c20'), 'octets inattendus en 0x20DABB'
        routine = bytes.fromhex('c118483e80') + bytes.fromhex('1da39c20') + bytes.fromhex('1bbfda20')
        cible = fab.place(routine)
        fab.r[0xDABB:0xDABF] = b'\x1b' + cible.to_bytes(3, 'little')
        print('DEBUG activé : routine en %06X' % cible)
    with open(sortie + '.tmp', 'wb') as f:
        f.write(fab.r)
    os.replace(sortie + '.tmp', sortie)
    print(sortie)
    if '--ips' in args:
        import ips
        p = ips.fabrique(en, bytes(fab.r))
        if ips.applique(en, p) != bytes(fab.r):
            raise SystemExit('patch IPS incorrect')
        with open(sortie[:-4] + '.ips.tmp', 'wb') as f:
            f.write(p)
        os.replace(sortie[:-4] + '.ips.tmp', sortie[:-4] + '.ips')
        print(sortie[:-4] + '.ips', len(p), 'octets, vérifié')


if __name__ == '__main__':
    main()
