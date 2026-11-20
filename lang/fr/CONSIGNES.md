# Evolution: Eternal Dungeons — consignes de traduction française

Jeu : RPG de donjons (ESP/Sting, Neo Geo Pocket Color, 2000), adaptation de « Evolution » (Dreamcast).
Ton : aventure légère et comique, ados qui se chamaillent, un majordome stylé, un empire de méchants
d'opérette. Public : joueurs français d'aujourd'hui.

## 1. ADAPTER, pas traduire (règle n° 1)
- Chaque boîte doit avoir du sens SEULE, dite par CE personnage, comme un Français le dirait à l'oral.
- Se demander ce que le personnage VEUT DIRE dans la scène, puis l'écrire naturellement. Pas de calque,
  pas d'ordre des mots « traduit ». Relire en se demandant : « un natif le dirait-il ? », pas seulement
  « c'est correct ».
- Gags / jeux de mots : trouver un équivalent français qui garde la FONCTION de la réplique.
- L'anglais du jeu contient des fautes (DAMEGED, BEATED, SEVING…) : traduire le SENS.

## 2. Contraintes techniques (vérifiées par l'outil : une erreur = ROM refusée)
- Boîte de dialogue (types SCRIPT, COMBAT) : **18 caractères × 3 lignes maximum**.
  `/` = ligne suivante. `|` = **boîte suivante** (autant qu'il faut : on peut ALLONGER, mieux vaut
  2 boîtes naturelles qu'une boîte télégraphique).
- Autres types (POINTE, MENU, ECRAN, AUTRE) : respecter la colonne « place » (colonnes × lignes),
  **pas de `|`**. Les AUTRE doivent en plus tenir dans le même nombre d'octets que l'anglais
  (en pratique : pas plus long que l'anglais).
- Les descriptions d'objets se terminent souvent par `/` (ligne vide finale) : le garder.
- Majuscules seules à l'écran (écrire en minuscules est accepté, l'outil met en majuscules).
- Accents disponibles : **É È Ê À Ç Ù Î Ô Û Â** (les autres : Ë→E, Ï→I, Œ→OE).
- Ponctuation : `. , ; : ! ? - + %` · apostrophe `'` · points de suspension `…` (ou `...`) ·
  guillemets `[` `]` (affichés « “ ” », c'est la convention du jeu pour les noms d'objets).
  Pas de parenthèses, pas de `/` littéral (s'il le faut : `{2F}`).
- **Pas d'espace avant ! ? : ;** (place).
- Codes `{xx}` : à RECOPIER tels quels, place libre dans la phrase (l'ordre des mots français est
  libre). `{04}`..`{07}` = nombre, `{08}`..`{0B}` = nom inséré (perso, monstre, objet),
  `{0C xx}` vitesse, `{0D xx}` couleur, `{02 xx}` colonne. Un nom inséré compte 0 pour l'outil :
  laisser de la marge sur sa ligne (un nom fait jusqu'à ~13 caractères).
- Dans l'anglais lisible : `)` = virgule, `(` = point-virgule, `^` = « … », `'` = apostrophe.

## 3. Personnages et registre
- **MAG** (Mag Launcher) : héros, jeune aventurier, fils d'un aventurier célèbre, couvert de dettes.
  Parle familier, vif, râleur, au grand cœur.
- **LINEAR** (Linear Cannon) : fille mystérieuse et très silencieuse qui vit chez Mag (« … »).
- **GRE** (Gre Nade) : vieux majordome de Mag, très poli, **vouvoie** Mag et l'appelle
  « MAÎTRE MAG » (MASTER MAG). Pédagogue, un peu solennel.
- **CHAIN** (Chain Gun) : aventurière de la SOCIETY, sûre d'elle, rivale moqueuse de Mag.
- **PEPPER** (Pepper Box), **NINA**, **EUGENE** (prince du 8e Empire, grandiloquent), mamie
  **BARBARA**, **BRUTO** et **VICKY**… : à déduire du contexte.
- **PORTRAITS ET VOIX** (établis d'après le japonais original ; numéro = visage affiché par la commande
  de script `11 xx`, voir FORMAT.md) :
  - 01–09 = Mag (06 rire gêné, 08 troublé, 09 sérieux) ; 0B/0C/0E = Linear (3F : Linear OU Chain selon la scène, lire le japonais) (rares mots, « … ») ;
    10–14 = **Chain** (アタイ/オマエ : brutale, « FERME-LA! ») ; 15–19 = Gre (solennel : « MONSIEUR
    VOTRE PÈRE… », « C'EST FORT JUSTE ») ; 1A–1E et 41 = **Pepper** (charmeuse, « MON CHOU » sur les
    répliques à ♥) ; 1F–23, 42–45, 48 = Eugene ; 33 = serveuse du bar ; 32 = patron du bar ;
    34 = vieil aventurier conseiller (ワシ/じゃ : tutoie Mag, « PETIT », « VIEUX BRISCARD » ; ses
    conseils sont souvent marqués portrait 00).
  - 35 = **NINA**, réceptionniste de la SOCIETY (わたし, わよ/わね) : tutoie Mag, maternelle et taquine,
    rit « HI HI », le trouve lent à la détente, admire Gre et Pepper, lit des romans d'espionnage,
    refuse d'être appelée « vétérane ». Lignes de missions / présentation des ruines en portrait 00 =
    Nina aussi. Pepper finit parfois par « BYE-BYE! » (バーイ).
  - 36 = **jeune archiviste** de la SOCIETY (ボク, 23 ans et y tient) : tic « MÉMO, MÉMO… » (note tout,
    oublie tout), amoureux de Nina (bégaie quand on en parle), surnom d'enfance [PÉPÉ], tutoie Mag.
  - 37 = **LE CONSERVATEUR**, vieux savant (ワシ/じゃよ) : tutoie Mag (« MON CHER MAG »), « LA JEUNE
    CHAIN », rit « HA HA HA ». 38 = **étudiant** à mi-temps (おれ, vise une grande école) : vouvoie
    Pepper, tutoie Chain. 19 = Gre ému (« SNIF… », « VOTRE VIEUX GRE »).
  - 30 = femme de marin, fleur bleue (« MON CHÉRI ») ; 49 = jeune mère qui parle bébé à son enfant
    (mots enfantins, sans zozoter) ; 2F = marin, son mari, fils de l'armateur, familier avec Mag ;
    27 = un proche de mamie Barbara (pas elle), tutoie Mag. Le garde du corps (25) vouvoie aussi Chain
    (« LA DEMOISELLE SORT? »). Gre parle de la mère de Mag : « MADAME VOTRE MÈRE ».
  - 28 = **mamie BARBARA** (あたし/じゃ) : « MON PETIT MAG », rit « HO HO HO » ; 27 = sa parente (ton
    maternel, « HI HI », Mag l'appelle « M'DAME ») ; 29 = docker du port, populaire (« J'SUIS », « P'TÊT ») ;
    24 = gamin (オイラ) qui veut épouser Linear, traite Mag de « BON À RIEN », « GROS TAS DE DETTES » ;
    31 = ex-journaliste aguicheuse (« QUEL PETIT INNOCENT ») ; 2A = jeune fille rêveuse, veut être star
    (« AAAH… », « NA! »). 02 sert aussi aux textes LUS à voix haute (roman, journal intime).
  - Gre appelle Linear « MADEMOISELLE LINEAR » (リニアさま), « LINEAR » si la place manque ; il parle
    du père de Mag : « MONSIEUR VOTRE PÈRE ».
  - **EUGENE LUITPOLD** (1F–23, 42–45, 48 ; 余, マグくん) : pompeux, condescendant, tutoie Mag ; rires
    クックックッ = « HIHIHI », ふはははは = « MOUAHAHAHA ». 3B/3C/39 = soldats du 8e Empire (3B tutoie
    Mag ; 3C familier puis déférent). 40 = Gre en aparté (pensées). 46/09 = Mag dépité, 0A/3A = Mag au
    réveil ; 0B peut aussi accompagner un récit de Gre (souvenir) : lire le japonais.
  - Gre : « MADEMOISELLE LINEAR », « MADEMOISELLE CHAIN » (de la famille Gun), « FORT BIEN »,
    « HÉLAS », « VOTRE GRE ». Portrait 00 = aussi les voix hors champ.
  - 33 = **serveuse du bar** (あたし, ado pétillante) : tutoie Mag, **VOUVOIE Pepper**. 32 = **patron du
    bar** (わたし, paternel : « FISTON », « LA PETITE LINEAR », philosophe sur l'alcool) : **VOUVOIE Pepper**.
    Pepper (アタシ) : coquette, vaniteuse, boit beaucoup, se donne l'air blasé.
  - 25 = **garde du corps de Chain** (でやんす) : **VOUVOIE** Mag (« M'SIEUR MAG »), finit souvent par
    « …M'VOYEZ », appelle Chain « LA DEMOISELLE ».
  - 26 = **EASTER**, domestique de Chain (っス, おれっち) : **VOUVOIE** Mag (« CAPITAINE MAG ») et Chain,
    élisions populaires (« Z'AVEZ », « Z'ALLEZ », « J'VOUS »), appelle Chain « MAM'ZELLE ».
  - 2B = vieux marchand (じゃよ : « VOIS-TU », « MON GARÇON ») ; 2C = sa petite-fille, **zozote**
    (J→Z : « BONZOUR », « ZE », « Z'AI », « PAPI Y VA… », « TOUTOU ») ; 2D = marchand ami des
    Launcher (familier) ; 2E = tenancier de la BOUTIQUE, ancien ami d'Asrock (père de Mag), bourru.
  - Mots : ADVENTURE MANIAC = DINGUE D'AVENTURE, CAPTAIN MAG = CAPITAINE MAG, GRANDPA = PAPI.
- **Tutoiement** entre jeunes et amis. **Vouvoiement** : Gre envers Mag, personnages très polis,
  inconnus adultes qui s'adressent avec déférence, le prince à ses ennemis s'il est cérémonieux.
- Colonne « portrait » : numéro du visage affiché (00 = aucun / narrateur / choix). Même numéro =
  même personnage (plusieurs numéros par personnage selon l'expression). Ex. 15 = Gre.

## 4. Lexique (à garder identique partout)
| anglais | français |
|---|---|
| SOCIETY | SOCIETY (nom propre de l'organisation ; « LA SOCIETY ») |
| CYFRAME | CYFRAME |
| RUINS | RUINES |
| HP / FP / TP | PV / PE / PT (PE = points d'énergie : coût des attaques spéciales ; PT = points de technique : gagnés en battant des ennemis, dépensés pour apprendre des techniques) |
| LV | NV |
| EXP POINTS | PTS D'EXP |
| ITEM | OBJET |
| SPECIAL (TECHNIQUE) | TECHNIQUE SPÉCIALE / SPÉCIAL |
| PANNAM TOWN | PANNAM |
| 8TH EMPIRE | 8E EMPIRE |
| SEA OTTER (le bateau) | [SEA OTTER] |
| EVOLUTIA | ÉVOLUTIA |
| DUNGEON / FLOOR | DONJON / ÉTAGE |
| COMMISSION (mission de la Society) | MISSION |
| HALL OF FAME | PANTHÉON (DE LA SOCIETY) |
| HEADQUARTERS (Society) | SIÈGE |
| AIR FIELD | AÉRODROME (dialogues) / AÉROPORT (nom de lieu en tuiles, place limitée) |
| [SEA OTTER], AIRPLANE, AEROBOAT (飛行艇, l'engin de Mag) | HYDRAVION |
| RECOVERY PARTS | PIÈCE DE SOIN |
| CYFRAME UPGRADE SHOP | ATELIER DES CYFRAMES |
| EXHIBITION ROOM | SALLE D'EXPO |
| ITEM STORE / ITEM SHOP | BOUTIQUE |
| FREE ADVENTURER | AVENTURIER LIBRE |
| IOU / DEBT | ARDOISE / DETTE |
| STR / VIT / AGI / LUK | FOR / VIT / AGI / CHA |
| STR BOOSTER (etc.) | BOOSTER FOR (etc.) |
| PARTS GET!! / BOOSTER GET!! (collection complète) | TOUTES LES PIÈCES! / TOUS LES BOOSTERS! |
| MASTER MAG (Gre) | MAÎTRE MAG |
| THIS WILL NEVER DO (phrase fétiche de Gre) | CELA NE VA PAS DU TOUT |
| HOUSE OF GUN / LAUNCHER | FAMILLE GUN / LES LAUNCHER |
| rires : HEH (Mag) / HMH (Nina) | HÉ HÉ / HI HI |
| Noms des ruines DEEP, BLIND, DESCENT, HEAVEN, SHADES, SHEOL… | gardés en ANGLAIS (noms propres), entre [ ] comme dans le jeu |
- Noms propres (personnages, lieux, Naolin…) : gardés. Noms d'objets descriptifs : traduits
  (WINGED SHOES → BOTTES AILÉES). Noms d'attaques : traduits avec panache (TAIL FLAP → COUP DE QUEUE).

## 5. Fichiers
Une ligne par texte : `=ADRESSE<TAB>FRANÇAIS` (adresse = 1re colonne de `out/catalogue.tsv`, produit par
`tools/extraire.py` depuis votre ROM, qui donne aussi le type, la place et l'anglais). `#` = commentaire.
Un texte sans ligne garde l'anglais. Textes techniques de test/débogage (VER.ENGLISH, D1ON…) : ne pas
les traduire. Contrôle : `python tools/controle.py ROM lang/fr/*.txt`.
