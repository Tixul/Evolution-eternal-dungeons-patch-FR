"""Relevé des chaînes HORS script : toute valeur 32 bits (n'importe quel alignement) qui pointe au
début d'une chaîne de texte plausible.  Compare avec tout le texte présent -> orphelins.

    python -I -B tools/pointes.py ROM [--dump FICHIER.txt]

Chaîne plausible : octet précédent = 00 (ou 01 pour les descriptions coupées ?) — on accepte
simplement « jusqu'au 00, caractères 0x01..0x7E + codes à paramètre, >= 2 lettres, <= 200 octets ».
"""
import re
import struct
import sys

sys.path.insert(0, __import__('os').path.dirname(__file__))
import script as S  # noqa: E402

BASE = 0x200000
OK = set(range(0x20, 0x60)) | {0x01, 0x13, 0x5E}


def chaine(d, o):
    """Rend la chaîne (sans le 00) si o commence une chaîne plausible, sinon None."""
    i = o
    while i < len(d) and i - o < 200:
        c = d[i]
        if c == 0:
            s = d[o:i]
            if len(re.findall(rb'[A-Z]', s)) >= 2 and s[:1] not in (b'\x01',):
                return s
            return None
        if c in S.CODE_PARAM:
            i += 1 + S.CODE_PARAM[c]
            continue
        if c in OK or 0x02 <= c <= 0x0F or 0x60 <= c:
            i += 1
            continue
        return None
    return None


def main():
    d = open(sys.argv[1], 'rb').read()
    an = S.Analyse(d)
    an.graines_maitre()
    an.parcourir()
    dans_script = set()
    for a, (op, n) in an.vu.items():
        dans_script.update(range(a - BASE, a - BASE + n))
    refs = {}
    for i in range(len(d) - 3):
        v = struct.unpack_from('<I', d, i)[0]
        o = v - BASE
        if not (0 <= o < len(d)) or o in dans_script:
            continue
        if o in refs:
            refs[o].append(i)
            continue
        if o > 0 and d[o - 1] not in (0x00,):
            continue
        s = chaine(d, o)
        if s is not None:
            refs[o] = [i]
    # tout le texte « visible » de la ROM (repérage large)
    tout = [(m.start(), m.group()) for m in re.finditer(rb'[\x20-\x5f\x01\x13]{4,}', d)]
    tout = [(o, s) for o, s in tout if len(re.findall(rb'[A-Z]{3,}', s)) >= 1
            and len(re.findall(rb'[A-Z ]', s)) / len(s) > 0.8]
    couvert = set(dans_script)
    for o in refs:
        couvert.update(range(o, o + len(chaine(d, o)) + 1))
    orph = [(o, s) for o, s in tout if not any(x in couvert for x in range(o, o + len(s)))]
    zones = {}
    for o in refs:
        zones.setdefault(o >> 16, 0)
        zones[o >> 16] += 1
    print('chaînes pointées hors script', len(refs),
          'caractères', sum(len(chaine(d, o)) for o in refs))
    print('par 64 Kio :', ' '.join('%X0000:%d' % kv for kv in sorted(zones.items())))
    print('orphelins (texte sans pointeur repéré)', len(orph), 'caractères', sum(len(s) for _, s in orph))
    if '--dump' in sys.argv:
        out = sys.argv[sys.argv.index('--dump') + 1]
        with open(out, 'w', encoding='utf-8') as f:
            for o in sorted(refs):
                f.write('%06X <-%s %s\n' % (o + BASE, ','.join('%06X' % (r + BASE) for r in refs[o][:3]),
                                          S.lisible(chaine(d, o))))
            f.write('\n=== ORPHELINS\n')
            for o, s in orph:
                f.write('%06X %s\n' % (o + BASE, S.lisible(s)))
        print(out)


if __name__ == '__main__':
    main()
