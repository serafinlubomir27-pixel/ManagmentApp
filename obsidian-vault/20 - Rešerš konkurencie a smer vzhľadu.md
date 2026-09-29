# 20 — Rešerš konkurencie a smer vzhľadu

Podklad pre kapitolu **4.3 Porovnanie existujúcich riešení**. Zisťované prehliadnutím
verejných stránok jednotlivých nástrojov.

> ⚠️ **Snímka k jednému dňu, nie citovateľný zdroj.** Ceny aj rozsah funkcií sa menia.
> Pred vložením do práce treba každý údaj znovu otvoriť na stránke výrobcu a zapísať
> dátum, ku ktorému platil — smernica to v čl. IV vyžaduje a vedúca to výslovne
> žiadala. Ber to ako zoznam, kde hľadať.

Súvisí s: [[18 - Schválené zadanie a pripomienky k osnove]]

---

## Jednotlivé nástroje

### TeamGantt
Cloudová služba, uvádza vyše 2 milióny používateľov.

**Vzhľad:** čistý, svetlý, pastelové farby. Ťažiskom obrazovky je Ganttov diagram
s presúvaním úloh myšou. Rýchly začiatok práce.

**Funkcie:** Gantt, závislosti s posunom a prekryvom, zvýraznenie kritickej cesty,
míľniky, vyťaženosť zdrojov, evidencia času, portfóliový prehľad, porovnanie plánu
so skutočnosťou, správa súborov, komentáre, zdieľanie s klientom, export do PDF,
napojenie na ďalšie služby.

**Čo nemá:** sieťový diagram uzlov, zobrazenie vypočítaných hodnôt ES/EF/LS/LF.
Kritickú cestu iba farebne vyznačí.

### GanttPRO
Cloudová služba, uvádza vyše 1 milióna používateľov.

**Vzhľad:** tmavý bočný panel, farebné pruhy úloh, prepínanie medzi pohľadmi.
Blízke pocitu MS Project, ale v prehliadači.

**Funkcie:** Gantt, nástenka, zoznam, portfólio, závislosti, kritická cesta,
vyťaženosť, náklady na zdroje, záznam času, zostavy, export.

**Čo nemá:** sieťový diagram, vlastný výpočet s rezervami.

### OpenProject
Otvorený zdrojový kód, možnosť vlastnej inštalácie zdarma.

**Vzhľad:** podnikový, hutnejší. Menej pôsobivý, zato veľmi funkčný.

**Funkcie:** Gantt, agilné nástenky, evidencia času, pracovné postupy, plánovač tímu,
produktová mapa, portfóliové riadenie, hierarchia projektov.

**Čo nemá:** výpočet kritickej cesty, sieťový diagram.

### Monday.com
Veľmi rozšírená platforma.

**Vzhľad:** vizuálne najsilnejší z porovnávaných. Má verejný dizajnový systém **Vibe**
so sekciami Accessibility, Colors, Motion, Round Corners, Shadow, Spacing, Typography
a UX Writing Handbook. Odstupy sú pomenované hodnoty (`space-2`, `space-4`…).

**Prečo vyzerá dobre:** nie kvôli farbám, ale preto, že všetko siaha po tých istých
pomenovaných hodnotách. Nič nevyzerá „skoro rovnako".

**Funkcie:** nástenky, Gantt, automatizácie, formuláre, dashboardy, dokumenty,
mobilné aplikácie, obchod s rozšíreniami, viac ako dvesto napojení. **Funkčne
najbohatší z porovnávaných.**

**Čo nemá:** metódu kritickej cesty vôbec. Žiadne ES/EF/LS/LF.

### ProjectLibre
Bezplatná alternatíva k MS Project, desktop aj cloud.

**Vzhľad:** napodobenina MS Project, zastaraná a neintuitívna.

**Funkcie:** otváranie súborov `.mpp`, CPM aj PERT, vyrovnávanie zdrojov.

**Čo nemá:** moderné rozhranie a tímovú spoluprácu v prehliadači.

---

## Porovnanie

| Vlastnosť | TeamGantt | GanttPRO | OpenProject | Monday | ProjectLibre | **Nodus** |
|---|---|---|---|---|---|---|
| Výpočet ES/EF/LS/LF | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Sieťový diagram uzlov | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Zobrazenie časovej rezervy | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Metóda PERT | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Ganttov diagram | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Práca v prehliadači | ✓ | ✓ | ✓ | ✓ | čiastočne | ✓ |
| Komentáre a prílohy | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Vyťaženosť zdrojov | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Evidencia času | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Export výstupov | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Portfóliový prehľad | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Vlastná inštalácia | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ |
| **Automatizácie** | čiastočne | ✗ | ✓ | **✓** | ✗ | **✗** |
| **Napojenie na iné služby** | ✓ | čiastočne | ✓ | **✓** | ✗ | **✗** |
| **Mobilná aplikácia** | ✓ | ✓ | ✓ | **✓** | ✗ | **✗** |
| **Formuláre** | ✗ | ✗ | ✓ | **✓** | ✗ | **✗** |

Posledné štyri riadky sú tam zámerne. Bez nich by tabuľka pôsobila ako reklama —
a presne pred tým vedúca varovala.

### Medzera na trhu
Nástroje s moderným rozhraním a tímovou spoluprácou **nemajú úplný výpočet kritickej
cesty**. Nástroj, ktorý ho má (ProjectLibre), má rozhranie spred dvadsiatich rokov
a spoluprácu v prehliadači neponúka.

**Nodus stojí v tejto medzere.** Argument nie je „máme viac funkcií" — Monday má
výrazne viac. Argument je, že Monday nemá to jedno, o čom je celá práca.

### Nevýhody a obmedzenia Nodusu
- prevádzka na bezplatnej úrovni služby, kde sa server po nečinnosti uspáva
  (prvé načítanie trvá približne pol minúty)
- niekoľko používateľov, žiadna preverená prevádzka vo väčšej organizácii
- chýba správa platformy oddelená od organizácií
- bez mobilnej aplikácie, automatizácií a napojenia na iné služby
- obnova hesla funguje len obmedzene — systém nemá vlastnú overenú doménu
- výpočet rastie kvadraticky; pri rádovo väčších sieťach by si vyžiadal optimalizáciu

---

## Smer vzhľadu

| Námet | Prečo | Stav |
|---|---|---|
| Úvodná obrazovka so súhrnom | Blížiace sa termíny a rizikové projekty naraz | čiastočne (Portfólio) |
| Prázdne stavy s výzvou | Nový používateľ nevidí prázdnu tabuľku, ale čo má urobiť | čiastočne |
| Kostry pri načítaní | Appka pôsobí rýchlejšie, aj keď je rovnako rýchla | nie |
| Export diagramov | Gantt a sieťový diagram do PDF | **hotové** |
| Uvedenie do práce | Krátka prehliadka pri prvom prihlásení | nie |

> **Prvý dojem nepokazí vzhľad, ale čakanie.** Backend sa budí ~34 sekúnd. Žiadna
> zmena farieb to nevykompenzuje — stránku treba otvoriť pred ukážkou, alebo to
> priznať v sprievodnom texte.

---

## Ako to použiť v práci

Do kapitoly 4.3 **nepatrí tento text tak, ako je.** Vedúca chce systematické porovnanie
podľa kritérií z metodiky (kapitola 3.2), kde pri každom nástroji bude uvedený zdroj
a dátum platnosti údajov.

1. Otvoriť stránku každého nástroja a **overiť ceny aj funkcie k dnešnému dňu**
2. Zapísať zdroj a dátum ku každému údaju
3. Vyplniť tabuľku podľa kritérií z kapitoly 3.2
4. Doplniť odsek o medzere na trhu
5. Doplniť nevýhody vlastného riešenia — bez nich to nebude prijaté
