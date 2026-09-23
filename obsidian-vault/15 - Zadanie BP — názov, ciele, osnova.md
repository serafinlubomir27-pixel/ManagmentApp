# 15 — Zadanie BP: názov, ciele, osnova

Podklad k trom veciam, ktoré vedúca práce žiada poslať ako ďalší krok:
**upravený názov, hlavný a dielčie ciele, návrh novej osnovy.**

Toto sú pracovné poznámky, nie hotový text — vyber varianty, preformuluj vlastnými
slovami a pošli ako svoj návrh.

Súvisí s: [[16 - Smernica EkF — formálne požiadavky]] · [[00 - Prehľad projektu]] ·
[[08 - Roadmap v2.0]] · [[12 - v2.0 Web Aplikácia]]

---

## 1. Názov práce

### Čo vedúca vytkla
- Názov `ManagmentApp` má **pravopisnú chybu** (správne `Management`).
- Ak sa aplikácia volá Nodus, starý názov z finálneho názvu úplne vypustiť.
- Súčasný názov sľubuje desktopovú aplikáciu, ale záver popisuje nasadenú webovú platformu.

### Varianty

**A — presne podľa odporúčania vedúcej (najbezpečnejšie)**
> Návrh, implementácia a vyhodnotenie informačného systému pre riadenie projektov s využitím metódy kritickej cesty

**B — to isté + podtitul s názvom produktu**
> Návrh, implementácia a vyhodnotenie informačného systému pre riadenie projektov s využitím metódy kritickej cesty
> *(na príklade systému Nodus)*

**C — kratší, ak by bol A pridlhý pre EDISON**
> Informačný systém pre riadenie projektov s využitím metódy kritickej cesty: návrh, implementácia a vyhodnotenie

**Poznámka:** A je jej vlastná formulácia — poslať ju nazad znamená, že sa k nej
nemá čo vyjadrovať. B navyše rieši, že produkt má meno, bez toho aby ho tlačil
do hlavného názvu. Názov musí sedieť s tým, čo je zadané v **EDISONe** — ak sa
tam mení, treba to riešiť cez katedru.

---

## 2. Vymedzenie predmetu práce

Toto treba vyriešiť **ako prvé**, lebo z toho vychádza všetko ostatné.

Vedúca píše, že v dokumente sa prelína desktopová aplikácia (Python,
CustomTkinter, SQLite) s webovou verziou (React, FastAPI, PostgreSQL) a objavujú
sa verzie 1.0, 1.1, 1.2, 2.0, 3.0 a „fázy".

### Návrh rozhodnutia
**Predmetom práce je súčasný webový informačný systém Nodus.**
Desktopová aplikácia sa spomenie ako **prototyp a prvá vývojová etapa**, z ktorej
riešenie vzniklo — stručne, v jednej podkapitole, nie ako paralelná línia.

Prakticky to znamená:
- „Verzia 1.x" sa stane **prototypom** (jedna podkapitola v Návrhu alebo Metodike)
- „Verzia 2.0 / 3.0 / Fáza 1–3" **zmiznú ako pojmy** — funkcie sa popíšu tematicky
  (CPM, vizualizácie, spolupráca, prílohy, klientsky modul), nie podľa toho,
  kedy vznikli
- Odovzdávaná verzia kódu = jeden konkrétny commit / tag, ktorý sa uvedie v texte

---

## 3. Hlavný cieľ

Vedúca navrhla znenie sama (v češtine). Preklad do slovenčiny, mierne upravený:

> Cieľom bakalárskej práce je na základe analýzy požiadaviek vybraných používateľov
> navrhnúť, implementovať a vyhodnotiť informačný systém podporujúci plánovanie
> a riadenie projektov s využitím metódy kritickej cesty. Súčasťou riešenia je návrh
> dátového modelu a softvérovej architektúry, implementácia výpočtu CPM a vizualizácia
> projektového harmonogramu. Výsledné riešenie bude overené funkčnými, algoritmickými,
> výkonnostnými a používateľskými testami a ekonomicky posúdené z hľadiska nákladov
> a prínosov pre zvolený typ organizácie.

**Dôležité:** cieľ nesmie byť zoznam funkcií aplikácie. Musí obsahovať celý postup
— analýza → návrh → implementácia → overenie.

Formulácia je jej vlastná, takže ju netreba prepisovať od základu. Ak chceš niečo
pridať, tak nanajvýš spresnenie cieľovej organizácie (napr. „malé firmy a
samostatne zárobkovo činné osoby").

---

## 4. Dielčie ciele

Vedúca dala osem. Nižšie sú doplnené o to, čo k nim reálne v projekte existuje —
pomôže to pri písaní a ukáže, kde sú diery.

| # | Dielčí cieľ | Podklad, ktorý už existuje | Čo chýba |
|---|---|---|---|
| 1 | Analyzovať proces projektového plánovania a potreby cieľových používateľov | kap. 3.1 + **konzultácie s bývalým zamestnávateľom** (viď nižšie) | zdokumentovať konzultácie; prípadne doplniť ďalších respondentov |
| 2 | Porovnať existujúce aplikácie podľa vopred stanovených kritérií | rešerš konkurencie (TeamGantt, GanttPRO, OpenProject, Monday, ProjectLibre) | **kritériá, zdroje, dátumy platnosti cien** |
| 3 | Formulovať funkčné a nefunkčné požiadavky | kap. 3.2, 3.3 | previazanie s výsledkami z cieľa 1 |
| 4 | Navrhnúť architektúru, databázu a používateľské roly | [[01 - Architektúra]], [[03 - Databáza & Repo]] | **UML a ER diagramy** |
| 5 | Implementovať CPM a ďalšie kľúčové funkcie systému | [[02 - CPM Engine]] | — (hotové) |
| 6 | Overiť správnosť výpočtov | `tests/test_cpm_engine.py` | **referenčné príklady** (vetvenie, viac kritických ciest, izolované úlohy, cyklus) |
| 7 | Vyhodnotiť funkčnosť, výkon a použiteľnosť | 140 automatizovaných testov | **výkonnostné meranie + používateľské testovanie** |
| 8 | Posúdiť ekonomické náklady a prínosy | kap. 7 súčasného textu | **vlastný modelový príklad (TCO / ROI / bod zvratu)** |

---

## 4b. Zber požiadaviek — konzultácie s praxou

Téma vznikla z konzultácií s **bývalým nadriadeným z obdobia práce vo finančníctve**;
od neho pochádza pôvodné zadanie. To je **reálny zber požiadaviek od odborníka
z praxe**, nie len vlastná skúsenosť — a je to podstatne silnejší podklad, než
vedúca predpokladala.

Vysvetľuje to aj, prečo systém obsahuje klientsky modul pre finančných poradcov —
nie je to vymyslená funkcia, ale požiadavka zo skutočného prostredia.

### Čo treba doplniť, aby to bolo doložiteľné
V metodike (kap. 4.2) a v analýze (kap. 3.2) uviesť:
- **rolu a odbornosť** konzultovanej osoby *(napr. „vedúci tímu finančných poradcov")*
- **obdobie a formu** konzultácií
- **okruhy**, ktoré sa preberali
- **ktoré konkrétne požiadavky** z nich vzišli — ideálne tabuľka
  *požiadavka → zdroj → premietnutie do systému*
- **obmedzenie**: ide o jedného respondenta z jednej domény, nie o reprezentatívny
  prieskum trhu — to treba otvorene priznať

### ⚠️ Administratívna povinnosť
Ak sa firma v práci **menuje** alebo sa opisujú jej interné procesy, smernica
vyžaduje **Prohlášení zástupce spolupracující právnické či fyzické osoby**
(Príloha č. 1 smernice, s podpisom a pečiatkou).
Detaily: [[16 - Smernica EkF — formálne požiadavky#8. ⚠️ Spolupráca s firmou — Príloha č. 1]]

Alternatíva bez podpisu — firmu neidentifikovať a popísať všeobecne. Rozhodnutie
patrí vedúcej, preto sa to oplatí spýtať v tej istej správe.

---

## 5. Návrh novej osnovy

Vedúca navrhla deväť kapitol. Tu je jej kostra naplnená obsahom a s mapovaním
na súčasný text — je vidieť, čo sa presúva, čo prepisuje a čo treba napísať nanovo.

Legenda: **[P]** presunúť · **[U]** upraviť · **[N]** napísať nanovo

### 1. Úvod
- 1.1 Motivácia a kontext problému — **[P]** z 1.1
- 1.2 Cieľ práce a dielčie ciele — **[U]** z 1.2 (nové znenie)
- 1.3 Štruktúra práce — **[U]** z 1.3

### 2. Teoretické východiská
- 2.1 Projektové riadenie a plánovanie — **[N]**
- 2.2 Metóda kritickej cesty (CPM) — **[U]** z 2.1, doplniť odborné zdroje
- 2.3 Metóda PERT a neistota odhadov — **[U]** z 5.11
- 2.4 Ganttov a sieťový diagram — **[U]** z 2.2
- 2.5 Riadenie zdrojov — **[N]**
- 2.6 Informačné systémy a softvérová architektúra — **[N]**

> Vedúca: teória nemá byť len vysvetlením funkcií aplikácie, ale východiskom,
> z ktorého vychádza návrh vlastného riešenia.

### 3. Analýza súčasného stavu a požiadaviek
- 3.1 Cieľové skupiny a používateľské roly — **[P]** z 3.1
- 3.2 Zber požiadaviek — **[N]** (rozhovory, alebo **priznať**, že vychádzajú z vlastnej skúsenosti)
- 3.3 Kritériá hodnotenia existujúcich nástrojov — **[N]**
- 3.4 Porovnanie existujúcich riešení — **[U]** z 2.3, prerobiť systematicky
- 3.5 Funkčné požiadavky — **[P]** z 3.2
- 3.6 Nefunkčné požiadavky — **[P]** z 3.3

> Pri každom nástroji uviesť **zdroj a dátum**, ku ktorému údaje platili.
> Pri vlastnom systéme uviesť aj **nevýhody a obmedzenia** — inak to pôsobí
> ako marketingová prezentácia.

### 4. Metodika riešenia a vyhodnotenia — **[N] CELÁ KAPITOLA**
Najväčšia diera. V súčasnom texte neexistuje vôbec.
- 4.1 Postup riešenia
- 4.2 Metóda zberu požiadaviek
- 4.3 Kritériá výberu porovnávaných nástrojov
- 4.4 Zvolený postup vývoja (iteratívny, prototyp → produkčný systém)
- 4.5 Metóda návrhu dátového modelu a architektúry
- 4.6 Metodika testovania a vyhodnotenia
- 4.7 Metodika ekonomického posúdenia
- 4.8 Použitie nástrojov generatívnej AI *(viď časť 7 nižšie)*

> Čitateľ musí pochopiť nielen **čo** si vytvoril, ale aj **prečo** práve takto
> a ako sa dá doložiť, že to funguje.

### 5. Návrh informačného systému
- 5.1 Prototyp — desktopová aplikácia ako prvá etapa — **[U]**, skrátiť
- 5.2 Architektúra systému — **[P]** z 4.1
- 5.3 Dátový model (ER diagram) — **[U]** z 4.2 + **[N]** diagram
- 5.4 Používateľské roly a oprávnenia — **[U]** z 4.1
- 5.5 Návrh CPM modulu — **[P]** z 4.5
- 5.6 Návrh používateľského rozhrania — **[P]** z 4.3, 4.4

### 6. Implementácia
Tu zaniká chronologický denník verzií — **členiť tematicky**:
- 6.1 Technológie a vývojové prostredie — **[U]** z 2.4 + 5.1
- 6.2 Dátová vrstva a Repository Pattern — **[P]** z 5.3
- 6.3 CPM Engine — **[P]** z 5.4
- 6.4 PERT a odhad rizika — **[P]** z 5.11
- 6.5 REST API a autentifikácia — **[N]**
- 6.6 Používateľské rozhranie — **[U]** z 5.5
- 6.7 Vizualizácie (Gantt, sieťový diagram) — **[U]** z 5.6, 5.14
- 6.8 Spolupráca (komentáre, prílohy, notifikácie) — **[U]** z 5.13
- 6.9 Riadenie zdrojov a evidencia času — **[U]** z 5.12
- 6.10 Klientsky modul — **[U]** z 5.15
- 6.11 Export výstupov (PDF, Excel, CSV) — **[U]** z 5.7
- 6.12 Bezpečnosť — **[N]** *(viď časť 6 nižšie)*
- 6.13 Nasadenie — **[U]** z 5.9, 5.10

### 7. Testovanie a vyhodnotenie
- 7.1 Testovacia stratégia — **[U]** z 6.1
- 7.2 Testovacie prostredie a dáta — **[N]**
- 7.3 Overenie CPM na referenčných príkladoch — **[N]**
- 7.4 Funkčné testy — **[U]** z 6.1
- 7.5 Výkonnostné testy — **[N]**
- 7.6 Používateľské testovanie — **[N]**
- 7.7 Dokumentácia chýb a opráv — **[P]** z 6.2
- 7.8 Vyhodnotenie splnenia požiadaviek — **[P]** z 6.3

### 8. Ekonomické hodnotenie
- 8.1 Nákladová štruktúra riešenia — **[N]**
- 8.2 Modelový príklad: malá firma — **[N]**
- 8.3 TCO, ROI a bod zvratu vo viacerých scenároch — **[N]**
- 8.4 Cenotvorba a obchodný model — **[U]** z 7.4, výrazne skrátiť
- 8.5 Obmedzenia ekonomického posúdenia — **[N]**

> Vedúca odporúča **vlastný modelový príklad namiesto prognóz globálneho trhu**.
> Súčasné kapitoly 7.1, 7.3, 7.5, 7.6 treba väčšinou **vypustiť alebo zásadne
> skrátiť** — obsahujú tvrdenia o trhu, ktoré nemajú dohľadateľný zdroj.

### 9. Záver
- 9.1 Zhrnutie dosiahnutých výsledkov — **[U]** z 8.1
- 9.2 Splnenie cieľov práce — **[N]**
- 9.3 Obmedzenia riešenia — **[U]** z 8.2
- 9.4 Možnosti ďalšieho rozvoja — **[U]** z 8.2

### Prílohy
- A — Štruktúra projektu — **[P]**
- B — Inštalačný manuál — **[P]**
- C — Referenčné príklady CPM a ich overenie — **[N]**
- D — Scenár a výsledky používateľského testovania — **[N]**
- E — Snímky obrazoviek výsledného systému — **[N]**
- Zoznam skratiek, tabuliek a obrázkov — **[N]**

---

## 5b. Ekonomická kapitola — čo zostáva a čo ide preč

Vedúca ocenila, že ekonomická stránka v práci je (*„je pro náš studijní program
důležitá"*), ale vytkla, že *„místy působí jako obchodní prezentace produktu"*.

Jej kľúčová veta: **„Místo rozsáhlých obecných prognóz trhu bych doporučila
vytvořit vlastní modelový ekonomický příklad."**

### Rozhodnutie o súčasných podkapitolách

| Súčasná podkapitola | Osud | Prečo |
|---|---|---|
| 7.1 Analýza globálneho trhu softvéru | **PREČ** | Obecná prognóza trhu; presne to, čo má nahradiť vlastný model |
| 7.2 Konkurenčná analýza a pozicionovanie | **PRESUNÚŤ → kap. 3.4** | Patrí do analýzy súčasného stavu, nie do ekonomického hodnotenia |
| 7.3 Ekonomický dopad CPM na podniky | **SKRÁTIŤ** | Môže zostať ako teoretické východisko, ale **každé číslo musí mať dohľadateľný zdroj** — inak von |
| 7.4 Cenotvorba a SaaS model | **ZOSTÁVA, skrátiť** | Relevantné pre nákladovú stránku; bez marketingového tónu |
| 7.5 Cieľový trh a príležitosť (SR/CZ) | **PREČ** | Trhová prognóza bez doložiteľných dát |
| 7.6 Finančné projekcie a rentabilita | **PREČ → nahradiť** | Nahradí ho vlastný modelový výpočet (TCO/ROI/bod zvratu) |

### Čo napísať nanovo

**8.1 Nákladová štruktúra riešenia** — reálne položky, ktoré vieš doložiť:
- vývoj / obstaranie
- cloudové služby *(hosting backendu, databáza — vieš doložiť cenníkom)*
- prevádzka a údržba
- zaškolenie používateľov

**8.2 Modelový príklad: malá firma**
Definovať konkrétny scenár — počet zamestnancov, počet projektov, hodinová sadzba.
Porovnať **súčasný spôsob plánovania** (tabuľky, e-mail) proti **zavedeniu Nodusu**.
Proti nákladom postaviť **odhadovanú úsporu pracovného času**.

**8.3 TCO, ROI a bod zvratu vo viacerých scenároch**
Minimálne tri: pesimistický / realistický / optimistický. Výpočty musia byť
usporiadané tak, aby ich vedel ktokoľvek prepočítať — smernica to vyžaduje
doslovne (čl. II, ods. 9).

**8.5 Obmedzenia ekonomického posúdenia**
Úspora času je **odhad**, nie meranie. Model vychádza z jedného typu organizácie.
Toto priznať — vedúca explicitne žiadala uvádzať aj nevýhody a obmedzenia.

### Pravidlo pre celú kapitolu
> Každé číslo v texte musí byť buď **(a)** dohľadateľné v citovanom zdroji,
> alebo **(b)** vlastný výpočet s uvedenými vstupmi a postupom.
> Nič medzi tým.

Vedúca konkrétne našla, že *jedna položka literatúry je použitá pre viacero
rôznych tvrdení, ktoré príslušný zdroj nemusí obsahovať*. Pri prepisovaní treba
prejsť citácie jednu po druhej a overiť, že zdroj naozaj obsahuje to tvrdenie.

---

## 6. Čo je v kóde už lepšie, než hovorí text

Niektoré výhrady vedúcej sa týkajú stavu, ktorý je medzitým opravený. Text
zaostáva za kódom — pri prepisovaní to treba zosúladiť.

| Výhrada | Skutočný stav |
|---|---|
| „Samotný SHA-256 bez soli nie je vhodný" | **Opravené.** `logic/passwords.py` používa **bcrypt** (salted) s transparentnou migráciou starých hashov pri prihlásení. V kap. 6.12 vysvetliť *prečo* bcrypt. |
| „Všetkých 64 automatizovaných testov prebehlo úspešne" | Aktuálne **140 testov**. Číslo v texte aktualizovať a uviesť konkrétnu verziu. |
| Default účet `admin/admin123` | V produkčnej schéme `supabase_schema.sql` **odstránený**; v lokálnom SQLite seede sa prepíše cez `SEED_ADMIN_PASSWORD`. **Tabuľku s heslami z textu vypustiť.** |
| Chýbajúci export | **Doplnený** — PDF, Excel aj CSV (kap. 6.11). |

Naopak, tieto výhrady platia a treba ich riešiť v texte:
- MiFID II — checklist **nezaisťuje** regulatórnu zhodu, len podporuje plnenie
  niektorých povinností. Preformulovať a podložiť zdrojmi, doplniť GDPR.
- Citácie — jedna položka literatúry je použitá pre viacero rôznych tvrdení.
- Literatúra je vzhľadom na šírku témy krátka.

---

## 7. Použitie generatívnej AI — čo popísať

Vedúca to **nezakazuje** („což je v pořádku"), ale chce presný popis činností
a spôsob kontroly výstupov. Odporúča zachovať históriu commitov.

> **Pozor:** smernica predpisuje konkrétnu formu deklarácie — vrátane **verzie
> nástroja, dátumu a znenia promptu**, samostatnej **prílohy** a odkazu na ňu
> **v úvode** práce. Presné znenie:
> [[16 - Smernica EkF — formálne požiadavky#4. Deklarácia použitia AI (čl. III) — presné znenie]]
>
> Formálne úpravy (gramatika, štylistika, preklad) sa deklarovať nemusia.
> Nepriznané použitie, ktoré nahrádza vlastnú tvorivú činnosť, sa posudzuje
> ako **plagiátorstvo**.

### Rozhodnutie o rozsahu deklarácie

Súčasný `docs/bakalarska-praca.html` je **pracovný koncept, ktorý sa odovzdávať
nebude** — finálny text vznikne nanovo podľa novej osnovy. Deklaruje sa to, čo je
v **odovzdanej** práci, nie to, čo bolo v zahodenom koncepte. Deklarácia sa teda
sústredí na **pomoc pri tvorbe softvéru**.

### Kde presne vedie čiara

Rozhoduje **pôvod obsahu v odovzdanom texte**, nie to, v ktorom súbore vznikol.

| Situácia | Deklarovať? |
|---|---|
| Kód, testy, komentáre, refaktoring | **áno** — to je jadro deklarácie |
| Koncept HTML, ktorý sa zahodí a nič z neho neprejde | nie |
| Gramatika, štylistika, preklad | nie *(výslovná výnimka, čl. III ods. 4)* |
| **Poznámky v Obsidiane → text práce** | **áno, ak z nich obsah prejde** |
| Rešerš konkurencie → analýza v kap. 3 | **áno** — podklad má pôvod v AI |
| Osnova, formulácia cieľov | **áno, ak sa prevezmú** |

Posledné tri riadky sú tie, na ktoré sa ľahko zabudne. Poznámky 15 a 16 v tomto
trezore sú výstup AI. Ak sa z nich niečo dostane do textu — aj preformulované —
patrí to do deklarácie. Nie je to problém: priznané použitie je v poriadku,
**nepriznané je plagiátorstvo** (čl. III ods. 5).

Praktický test pred odovzdaním: *„Vedel by som pri tomto odseku povedať, odkiaľ
pochádza a prečo tam je?"* Ak áno pri všetkom, deklarácia je úplná.

### Rozdelenie práce

| Oblasť | Podiel |
|---|---|
| Voľba témy a zadanie | konzultácie s praxou *(viď časť 4b)* |
| Architektúra, dátový model, návrh CPM | vlastné rozhodnutia |
| Overenie správnosti výpočtov | vlastné |
| Generovanie kódu, refaktoring, komentáre | s pomocou Claude Code |
| Automatizované testy | s pomocou Claude Code, kontrola spustením |
| Technické poznámky v trezore | s pomocou Claude Code |
| Rešerš konkurencie *(podklad)* | s pomocou Claude Code |
| **Spracovanie rešerše do analýzy** | **vlastné** |
| **Text bakalárskej práce** | **vlastný** |
| Zodpovednosť za správnosť | autor práce |

**Konkrétny príklad kontroly výstupov**, ktorý sa hodí do kapitoly 4.8:
Pri rozširovaní systému sa našla chyba v migračnej rutine `database/setup.py` —
rozhodovala o formáte hesla podľa dĺžky reťazca (64 znakov = hash). Bcrypt hash
má 60 znakov, takže ho považovala za čistý text a prepísala na `sha256(hash)`,
čím sa účet stal neprístupným. Chybu neodhalilo generovanie kódu, ale až
**overenie správania po reštarte aplikácie**; oprava je doložená commitom
`7e25309` a dvoma regresnými testami. Presne toto je doklad, že výstupy sa
kontrolujú a za správnosť zodpovedá autor.

---

## 8. Návrh, čo poslať vedúcej

1. Zvolený názov (jedna varianta, nie zoznam)
2. Hlavný cieľ — jeden odsek
3. Dielčie ciele — osem bodov
4. Osnova — deväť kapitol s podkapitolami (bez značiek [P]/[U]/[N], tie sú pracovné)
5. Krátka poznámka o vymedzení: predmetom je webový systém Nodus, desktopová
   aplikácia je prototyp a prvá etapa
6. Poznámka o zbere požiadaviek: téma a pôvodné zadanie vzišli z konzultácií
   s bývalým nadriadeným z finančného poradenstva
7. Štyri otázky, na ktoré potrebuješ odpoveď:
   - **Treba zmeniť zadanie v EDISONe?** Smernica žiada, aby odovzdaná osnova
     zodpovedala schválenému zadaniu — pri novej osnove aj názve to znamená
     administratívnu zmenu (čl. VI, ods. 1)
   - **Kde je aktuálna fakultná šablóna?** V texte smernice sa spomína ako jej
     príloha, ale v PDF nie je
   - **Treba Prílohu č. 1** (súhlas zástupcu spolupracujúcej osoby), keď sa
     požiadavky preberali s bývalým zamestnávateľom — alebo firmu radšej
     neidentifikovať?
   - **Koľko používateľov** stačí na používateľské testovanie?

> Nepísať zatiaľ žiadne kapitoly. Vedúca výslovne chce najprv skontrolovať
> vymedzenie práce, až potom sa majú prepisovať jednotlivé kapitoly.
