# Evolution: Eternal Dungeons — notes techniques (ROM, scripts, texte, interface)

Tout ce qui suit a été mesuré sur la ROM européenne (2 Mio, CRC32 `BE47E531`, titre interne
`EVOLUTION US`). Adresses CPU : la cartouche commence en 0x200000 (fichier 0 = CPU 0x200000) ; la 2e
puce de la ROM traduite (fichier 0x200000) est vue en CPU 0x800000.

La ROM européenne est en **anglais seul** (le réglage de langue de la console est ignoré). La version
japonaise (`Shinki Sekai Evolution - Hateshinai Dungeon`, titre `EVOLUTION NP`) est une autre compilation
du même moteur : même script (mêmes groupes, mêmes commandes), table maîtresse en 0x3AB1EC, texte en
**kana seuls** (police : 0x60–0x8D hiragana あ…ん, 0x8E–0xA6 sonorisés, 0xA7–0xAF petits, 0xB0–0xFF
katakana ; 0x2A = ー). La traduction française a été relue contre ce texte.

## Chaîne de construction
`tools/build.py` : ROM européenne → police (accents, icônes PV/PE) → textes remplacés sur place ou
relogés en 2e puce → mots dessinés en tuiles (noms de lieux) → libellés d'écran → (option) menu de
débogage → ROM de **4 Mio** → patch IPS **depuis la ROM européenne**.
⚠ Le bloc fichier 0x1F0000–0x1FFFFF (rempli de FF, identique dans les deux versions) sert probablement
aux sauvegardes : rien n'y est écrit. Tout le neuf va dans la 2e puce.

## Script des scènes
- Interpréteur : lecture d'opcode `ld L,(XIX+)` en 0x20DA37, `cp L,0x52` → **82 commandes**, table de
  sauts 0x20E373 (4 octets par commande). Pointeur de script en RAM 0x5110 / 0x511C / 0x5114.
- **Table maîtresse 0x3ABB18** : 11 groupes → listes de scripts (66 points d'entrée). Le code lance un
  script par `(0x3ABB18)[groupe][n]` ; la commande `03 g n` fait de même.
- Paramètres (octets) : 0 pour 02 09 10 14 15 1C 1D 1F 23 24–30 33 34 3E 3F 40 42 4C 4D 4E 4F 50 51 ;
  1 pour 08 0A 0B 0E 0F 11 12 13 16 17 1A 20 21 38 39 3C 3D ; 2 pour 37 ; 4 pour 35 41 ; 6 pour 3A 3B ;
  31/32 : 1 (rend la main, reprend après) ; 4D/4E : lance un combat puis reprend après.
- Sauts : `04 adr32` absolu · `05 adr32` appel / `06` retour (une seule case) · `0C`/`0D adr32` si drapeau
  0x5126 = 0 / ≠ 0 · `36 adr32` · `07 n` + n adresses (au hasard) · `1B` option de menu · `22` calculé.
- Texte : `01 chaîne 00` (dans la boîte) · `43`..`4B` chaîne à position fixe (générique) ·
  `18 adr32` → nom du lieu · `19` = menu : 12 octets d'en-tête + entrées (adr32 texte, adr32 script, u32),
  terminées par u32 0 · `11 xx` = portrait xx (table 0x26D2B4) · `02` = attendre un bouton.
- Drapeaux : `0A n` / `0B n` testent `(0x4800 + n>>3) & masque[n&7]` (routine 0x209CA3).

## Script de combat
Second interpréteur : boucle 0x21BB33, `cp L,0x68` → 104 commandes, table 0x21BB56. Seule la commande
**0A** écrit du texte (`0A chaîne 00`, puis `0B` = attendre) ; **01 adr32** = saut absolu. Zones :
0x220000.. (états) et 0x384000..0x3ABB17 (effets).

## Codes du texte (routine d'écriture 0x2097E0)
Code ≥ 0x10 = numéro de tuile posé tel quel (aucun contrôle de colonne ni de ligne). 0x00–0x0F :
`0` fin · `1` ligne suivante · `2 xx` colonne · `3` rien · `4..7` nombre (RAM 0x51E8..0x51F4) ·
`8..B` chaîne insérée (pointeurs RAM 0x51D8..0x51E4 : noms) · `C xx` vitesse · `D xx` couleur ·
`E xx` · `F a b` (2 octets). Signes détournés de la police : 0x29 = virgule, 0x28 = point-virgule,
0x5E = …, 0x5B/0x5D = guillemets, 0x13 = apostrophe. Dans l'ancien moteur de combat (0x217xxx), les
minuscules `t` / `d` sont des marques (cible / nombre).

## Allonger le texte sans reconstruire les scripts
- Si le français tient : écrit sur place, fin bourrée avec le code 03 (« rien »).
- Sinon, dialogue : `01 texte 00` (≥ 5 octets) → `04 adr` vers un bloc en 2e puce
  `01 … 00 02 01 … 00 04 retour` ; combat : `0A texte 00` → `01 adr` vers `0A … 00 0B 0A … 00 01 retour`.
  On peut ainsi ajouter autant de boîtes que nécessaire. Validé : toutes les boîtes du jeu passées par
  ce saut avec l'anglais d'origine donnent un jeu identique au pixel près.
- Chaînes pointées (objets, capacités, monstres, menus) : copiées en 2e puce, pointeurs 32 bits réécrits.
- `tools/extraire.py` fait le catalogue de tout le texte (parcours complet des deux scripts + chaînes
  pointées) et calcule la place permise : les chaînes pointées sont regroupées par champ de table
  (pointeurs à pas fixe) ; noms d'objets 16 colonnes, de capacités 13, descriptions 18 × 4.

## Police et graphismes
- Police 8×8 (encre 1, fond 3), 256 tuiles non compressées, **deux copies** (fichier 0x13FFF et
  0x20550) : 0x00–0x5F caractères, 0x60–0xFF mots dessinés en police étroite (2 lettres par tuile).
- Accents ajoutés à la place de signes inutilisés : É 0x23 · È 0x2C · Ê 0x3C · À 0x3E · Ç 0x40 · Ù 0x5C ·
  Î 0x5F · Ô 0x3D · Û 0x2A · Â 0x26 (lettre sur 6 lignes, accent sur 2). Icônes 0x1C « HP » → « PV »,
  0x1D « FP » → « PE ».
- Mots en tuiles (`tools/mots_tuiles.py`) : alphabet étroit extrait des mots anglais (7 lignes d'encre,
  accent d'un pixel sur la ligne 0) ; noms de lieux redessinés dans les tuiles réattribuables et suites de
  codes remplacées dans les chaînes (complétées d'espaces : l'affichage n'efface pas). Les en-têtes de
  lieux sont aussi des chaînes appelées par le code (ex. 0x21143F « ITEM SHOP ») : remplacées sur place.
- Libellés des écrans de statut / équipement / boutique (`tools/libelles.py`) : chaînes de mise en page
  collées à des codes et à des données (0x210946..0x211992), remplacées octet pour octet.

## Boîtes et menus
- Boîte de dialogue : **18 colonnes × 3 lignes**. Un nom inséré peut faire jusqu'à ~13 caractères.
- Un menu n'efface pas sa case : un texte plus court que l'anglais est complété d'espaces.

## Menu de débogage
Option DEBUG du menu de commandes (OPTION dans un menu de lieu, si 0x5124 ≠ 0) : le script du menu
(groupe 10, 0x3E74FC) retire l'option 8 tant que le drapeau **0xC7** (octet 0x4818, bit 0x80) est à 0 ;
DEBUG mène au groupe 0, entrée 4 (« VER.ENGLISH. 03/15 00:00 », OPEN TOWN DGN CLEAR SHIPEV JUKE KIT
STAFF FLAG). `build.py --debug` détourne le test 0x20DABB `call 0x209CA3` vers une petite routine en
2e puce : `or (0x4818),0x80 ; call 0x209CA3 ; jp 0x20DABF`.
