"""Libellés des écrans de statut / équipement / boutique : remplacés SUR PLACE, octet pour octet.

Ces chaînes (fichier 0x10900..0x12200) sont collées à des codes de mise en page ({02 xx} colonne,
{0F a b} nombre) et à des données : elles ne sont ni dans le catalogue ni déplaçables. Chaque entrée :
(adresse CPU du morceau, anglais, français) ; l'anglais est cherché à partir de l'adresse (n-ième
occurrence dans l'ordre de la liste), le français (≤ anglais) est complété d'espaces, ou du code 03
(« rien ») pour une phrase sur plusieurs lignes.
"""
BASE = 0x200000

LIBELLES = [
    # statut (0x210946..)
    (0x210946, 'HP:', 'PV:'), (0x210957, 'FP:', 'PE:'), (0x210968, 'TP:', 'PT:'),
    (0x210973, 'LV  :', 'NV  :'), (0x21098E, 'NEXT:', 'SUIV:'), (0x21098E, 'STR:', 'FOR:'),
    (0x2109C8, 'SPD:', 'VTS:'), (0x2109D4, 'LUK:', 'CHA:'),
    # équipement
    (0x210BF9, 'HP:', 'PV:'), (0x210C0A, 'FP:', 'PE:'), (0x210C1B, 'TP:', 'PT:'),
    (0x210C26, 'WEAPON', 'ARME'), (0x210C38, 'HEAD', 'TÊTE'), (0x210C47, 'BODY', 'HAUT'),
    (0x210C56, 'FOOT', 'PIED'), (0x210C65, 'ACCESSORY', 'ACCESS.'),
    (0x210C81, 'HP:', 'PV:'), (0x210C92, 'FP:', 'PE:'), (0x210CA3, 'TP:', 'PT:'),
    (0x210CB5, 'SLOT1', 'EMPL1'), (0x210CCA, 'SLOT2', 'EMPL2'), (0x210CDF, 'SLOT3', 'EMPL3'),
    (0x210CF4, 'SLOT4', 'EMPL4'), (0x210D09, 'SLOT5', 'EMPL5'),
    (0x210D20, 'HP:', 'PV:'), (0x210D31, 'FP:', 'PE:'), (0x210D42, 'TP:', 'PT:'),
    (0x210D4D, 'SKILL1', 'TECHN1'), (0x210D5F, 'SKILL2', 'TECHN2'), (0x210D70, 'SKILL3', 'TECHN3'),
    (0x210D81, 'SKILL4', 'TECHN4'), (0x210D92, 'SKILL5', 'TECHN5'),
    (0x210DA7, 'STR:', 'FOR:'), (0x210DD5, 'SPD:', 'VTS:'), (0x210DD5, 'LUK:', 'CHA:'),
    (0x210FC5, 'TP', 'PT'), (0x210FCD, 'FP', 'PE'),
    # réglages, objets, argent
    (0x211134, 'WHEN FINISHED WITH/ALL THE SETTINGS)/PRESS  BUTTON B.',
     'QUAND TOUT EST/RÉGLÉ, APPUYEZ/SUR LE BOUTON B.'),
    (0x211194, 'ITEM', 'OBJ.'), (0x2111A7, 'ITEM-1', 'OBJ.-1'), (0x2111AE, 'ITEM-2', 'OBJ.-2'),
    (0x2111C2, 'ITEM-1', 'OBJ.-1'), (0x2111C2, 'ITEM-2', 'OBJ.-2'), (0x2111E8, 'ITEM-2', 'OBJ.-2'),
    (0x211377, 'MONEY', 'FONDS'), (0x211377, 'DEBT', 'DÛ'), (0x211377, 'AMOUNT', 'SOMME'),
    (0x211450, 'MONEY', 'FONDS'),
    (0x211745, 'ADD A SLOT', '+1 EMPLAC.'),
    (0x2118A9, 'I NEED', 'PRIX:'),   # la suite (« AND/[UPGRADE KIT]. ») est traduite par le catalogue
    (0x211992, 'WEAPON', 'ARME'), (0x211992, 'HEAD', 'TÊTE'), (0x211992, 'BODY', 'HAUT'),
    (0x211992, 'FOOT', 'PIED'), (0x211992, 'ACCESSORY', 'ACCESS.'), (0x211992, 'APPRAISAL', 'EXPERTISE'),
    (0x211992, 'BATTLE', 'COMBAT'), (0x211992, 'OTHERS', 'AUTRES'),
]


def appliquer(r, en, encoder, lisible_en, deja=frozenset()):
    """r : ROM de sortie (bytearray), en : ROM anglaise, encoder : build.encoder,
    lisible_en : fonction texte lisible -> octets anglais (pour les codes {xx} de l'anglais),
    deja : octets (fichier) déjà réécrits par une traduction du catalogue -> libellé ignoré."""
    curseur, faits = {}, 0
    for adr, ang, fr in LIBELLES:
        o = adr - BASE
        a = lisible_en(ang)
        depart = curseur.get((adr, ang), o)
        i = en.find(a, depart, o + 0x60)
        if i < 0:
            raise ValueError('%06X : « %s » introuvable' % (adr, ang))
        curseur[(adr, ang)] = i + len(a)
        b = encoder(fr)[0]
        if len(b) > len(a):
            raise ValueError('%06X : « %s » plus long que « %s »' % (adr, fr, ang))
        if any(x in deja for x in range(i, i + len(a))):
            continue      # déjà traduit par une entrée du catalogue (ex. AUTRE « /ACCESSORY/ »)
        bourre = b'\x03' if 0x01 in a else b' '
        r[i:i + len(a)] = b + bourre * (len(a) - len(b))
        faits += 1
    return faits
