"""Contrôle des fichiers de traduction SANS fabriquer la ROM.

    python -I -B tools/controle.py ROM_EN FICHIER [FICHIER…]

Lignes acceptées : `=ADRESSE<TAB>texte` (texte du catalogue à cette adresse), `@ADRESSE<TAB>texte`
(chaîne entière) et, dans les fichiers de travail, `ANGLAIS<TAB>texte` (anglais recopié exactement).
Vérifie : texte connu, caractères affichables, place (18×3 par boîte pour dialogues/combat, colonne
« place » sinon), AUTRE pas plus long que l'anglais, codes {xx} de l'anglais présents dans le français.
Affiche les erreurs ; code de sortie 1 s'il y en a.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build as B   # noqa: E402
import script as S  # noqa: E402


def verifie(fab, lis, fr, occ):
    """lis : anglais lisible ; occ : [(adresse, type, octets anglais)] ; rend le nombre d'erreurs."""
    erreurs = 0
    codes_en = sorted(re.findall(r'\{[0-9A-F ]+\}', lis))
    # codes de mots-tuiles (0x60–0xFF, sauf les marques {64}/{74}) : remplaçables exprès (mots_tuiles)
    # seuls les codes de CONTRÔLE (< 0x10 : noms, nombres, couleurs…) et les marques {64}/{74} sont
    # obligatoires ; un caractère écrit en code ({2F} barre oblique…) ou un mot-tuile ne l'est pas
    codes_en = [c for c in codes_en if int(c[1:3], 16) < 0x10 or c in ('{64}', '{74}')]
    if (len(re.findall(r'\{[6-9A-F][0-9A-F]\}', lis)) >= 4
            and not re.search(r'[A-Z]{4}', re.sub(r'\{[^}]*\}', ' ', lis))):
        codes_en = []   # texte japonais (kana codés) : pas de codes à conserver
    codes_fr = sorted(re.findall(r'\{[0-9A-F ]+\}', fr))
    interdits = {'{%02X}' % c for c in B.ACCENTS.values()}
    mauvais = [c for c in codes_fr if c in interdits and c not in codes_en]
    if mauvais:
        print('CODE INTERDIT %s (devenu une lettre accentuée) : %s' % (mauvais, fr))
        erreurs += 1
    if [c for c in codes_en if c not in codes_fr]:
        print('CODE MANQUANT %s : %s -> %s' % (sorted(set(codes_en) - set(codes_fr)), lis, fr))
        erreurs += 1
    for o, typ, t in occ:
        try:
            boites = [fab.mots.appliquer(b) for b in B.encoder(fr)]
            fab.controle(typ, t, boites, o)
            if typ == 'AUTRE' and (len(boites) > 1 or len(boites[0]) > len(t)):
                raise B.Erreur('%06X AUTRE plus long que l\'anglais (%d > %d octets)'
                               % (o + B.BASE, len(boites[0]), len(t)))
        except B.Erreur as e:
            print('ERREUR', e, '|', fr)
            erreurs += 1
            break
    return erreurs


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    en = open(sys.argv[1], 'rb').read()
    fab = B.Fabrique(en)
    par_lis = {}
    for o, (typ, t) in fab.cat.items():
        par_lis.setdefault(S.lisible(t), []).append((o, typ, t))
        if S.lisible_ancien(t) != S.lisible(t):
            par_lis.setdefault(S.lisible_ancien(t), []).append((o, typ, t))
    erreurs = total = 0
    for chemin in sys.argv[2:]:
        par_texte, par_adr = B.lire_trad(chemin)
        total += len(par_texte) + len(par_adr)
        for lis, fr in par_texte.items():
            occ = par_lis.get(lis)
            if not occ:
                print('INCONNU (anglais pas recopié exactement ?) :', lis)
                erreurs += 1
                continue
            erreurs += verifie(fab, lis, fr, occ)
        for o, fr in par_adr.items():
            if isinstance(fr, tuple):          # =ADRESSE : texte du catalogue
                if o not in fab.cat:
                    print('ADRESSE INCONNUE au catalogue : %06X' % (o + B.BASE))
                    erreurs += 1
                    continue
                typ, t = fab.cat[o]
                erreurs += verifie(fab, S.lisible(t), fr[1], [(o, typ, t)])
            else:                              # @ADRESSE : chaîne entière, sur place
                fin = en.find(b'\x00', o)
                try:
                    b = [fab.mots.appliquer(x) for x in B.encoder(fr)]
                    if len(b) > 1 or len(b[0]) > fin - o:
                        raise B.Erreur('%06X : plus long que l\'anglais (%d > %d octets)'
                                       % (o + B.BASE, len(b[0]), fin - o))
                except B.Erreur as e:
                    print('ERREUR', e, '|', fr)
                    erreurs += 1
    print('%d traductions, %d erreur(s)' % (total, erreurs))
    sys.exit(1 if erreurs else 0)


if __name__ == '__main__':
    main()
