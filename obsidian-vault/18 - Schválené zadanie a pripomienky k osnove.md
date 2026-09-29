# 18 — Schválené zadanie a druhé kolo pripomienok

Odpoveď vedúcej (Lucie Chytilová) na návrh zadania. **Názov, ciele aj vymedzenie
schválené — možno vložiť do EDISONu v rámci Seminára A.**

Súvisí s: [[17 - Správa vedúcej — návrh zadania]] · [[16 - Smernica EkF — formálne požiadavky]]

---

## Schválené

**Názov** — bez pridania „Nodus", takto je všeobecnejší a lepšie vystihuje odborný problém:

> Návrh, implementace a vyhodnocení informačního systému pro řízení projektů
> s využitím metody kritické cesty

**Hlavný cieľ aj dielčie ciele** — formulované podstatne lepšie, ciele logicky nadväzujú.

**Vymedzenie** — desktopová aplikácia len stručne ako prototyp, ťažisko na webovom Nodus.

---

## Zmeny v osnove

### 1. Metodika ide PRED analýzu
Najprv vysvetliť, *ako* budú požiadavky získané, podľa akých kritérií sa porovnajú
nástroje a ako bude prebiehať testovanie — až potom prezentovať výsledky analýzy.

Nové poradie: Úvod → Teória → **Metodika** → **Analýza** → Návrh → Implementácia →
Testovanie → Ekonomika → Záver.

### 2. Výrazne obmedziť počet podkapitol
> *„Zejména kapitola Implementace je nyní členěna až příliš podrobně a začíná znovu
> připomínat technickou dokumentaci aplikace."*

Nie je nutná samostatná podkapitola ku každému modulu. Podrobne popísať len to, čo
priamo súvisí s cieľom práce — architektúru, dátový model, implementáciu CPM,
kľúčové funkcie a relevantné bezpečnostné prvky. Export, nasadenie a špecializované
moduly zlúčiť do väčších celkov.

**Urobené:** 55 podkapitol → 34. Implementácia z 13 na 5.

### 3. Modul pre finančných poradcov
Nie samostatná podkapitola — len **aplikačný príklad** využitia systému. Nemá
odvádzať pozornosť od hlavnej témy.

### 4. PERT
Ponechať **len ak bude implementovaný, využívaný a aj overovaný**. Hlavnou témou je
kritická cesta, netreba rozsah umelo rozširovať.

**Rozhodnutie: ponechať a overiť.** Overenie na 6 referenčných príkladoch je hotové
(`scripts/verify_pert_reference.py`), 6/6 prešlo.

### 5. Ekonomické hodnotenie
Držať ako **modelové posúdenie pre zvolený typ organizácie** — náklady, očakávané
prínosy, pár scenárov. **Cenový model a bod zvratu zaradiť len pri rozumne
podložených predpokladoch.**

### 6. Rozsah celkovo
> *„Není nutné prokazovat úplně všechno, co systém umí."*

---

## Odpovede na otázky

| Otázka | Odpoveď |
|---|---|
| **Firma** | **Neidentifikovať.** Popísať všeobecne, uviesť že požiadavky vychádzajú z konzultácie s jedným odborníkom → obmedzenie práce. Písomný súhlas len ak sa použijú interné údaje, cituje konkrétna osoba alebo sa firma priamo identifikuje. |
| **Používateľské testovanie** | **8–12 používateľov** z cieľovej skupiny, zamerané na použiteľnosť. Konkrétne úlohy, sledovať úspešnosť a problémy, potom krátky štruktúrovaný dotazník — napr. **SUS** + vlastné otázky + otvorená otázka na problémy a návrhy. |
| **Bezpečnosť** | Po popísaných úpravách dáva zmysel. |
| **MiFID II** | Opatrnejšia formulácia správna — systém môže podporovať procesy alebo kontrolu požiadaviek, ale zo samotnej funkcionality sa nedá deklarovať zaistenie súladu. **GDPR a uchovávanie dokumentov stručne doplniť.** |
| **EDISON** | Áno, možno vložiť názov a vymedzenie v rámci Seminára A. Osnova sa počas spracovania môže ešte mierne meniť. |

---

## ⚠️ Nezrovnalosť v smernici

Vedúca píše, že formálne náležitosti sa riadia smernicou **EkF_SME_07_004 vo verzii Q**,
dostupnou cez **InNET**.

Ale PDF, ktoré máme, je **verzia U s účinnosťou od 23. 9. 2026** — teda novšia.
Podľa histórie revízií je Q zo 17. 10. 2023 a po nej prišli ešte R, S, T a U.

**Treba overiť na InNETe, ktorá verzia tam naozaj visí.** Medzi verziami sa menili
článok II (rozsah), článok IV (citácie) aj prílohy. To isté platí pre šablónu —
porovnať `Šablona BP_DP_2026.dotx` s tou na InNETe.

---

## Čo sa očakáva na Seminár A

> *„Správně vymezené téma a cíl práce, volba metod a postupů, zpracování
> teoreticko-metodologické části a analýza vstupních požadavků a současného stavu."*

Prakticky to znamená sústrediť sa na **kapitoly 1 až 4**:

1. Úvod
2. Teoretické východiská
3. Metodika riešenia a vyhodnotenia
4. Analýza súčasného stavu a požiadaviek

Kapitoly 5 až 9 (návrh, implementácia, testovanie, ekonomika, záver) počkajú.

---

## Rámec, ktorý treba držať v hlave

> *„Jde o bakalářskou práci na Ekonomické fakultě v programu Informatika v ekonomice.
> Práce by proto měla vhodně propojit informatickou část s analytickým a ekonomickým
> pohledem. Nestačí tedy pouze předvést funkční aplikaci a popsat její kód — důležitá
> je formulace problému, práce s odbornou literaturou, jasná metodika, analýza
> požadavků, zdůvodnění návrhu a následné objektivní vyhodnocení."*

A na záver:

> *„Cílem není co nejpodrobněji zdokumentovat celý systém. Výsledkem má být
> bakalářská práce, ve které na základě jasně popsaného problému a metodiky
> navrhnete řešení, implementujete jeho podstatné části a následně objektivně
> a kriticky vyhodnotíte, zda splňuje stanovené požadavky."*

---

## Tretie kolo — posilnenie ekonomického a manažérskeho kontextu

Vedúca súhlasila s posilnením zamerania, ale **opravila formuláciu problému**:

> *„Jen bych byla opatrná s označením samotné identifikace kritických činností jako
> ekonomického problému. Vnímala bych jej spíše jako problém projektového řízení
> a rozhodování, který má následně ekonomické důsledky — například z hlediska
> termínů, využití zdrojů nebo dodatečných nákladů."*

### Správny reťazec
1. **Problém** je manažérsky a rozhodovací — vedúci projektu nevie určiť, ktoré
   činnosti rozhodujú o termíne
2. **Dôsledky** sú ekonomické — posun termínu, zle vynaložená kapacita, dodatočné
   náklady na zrýchlenie prác
3. **Informačný systém** je prostriedok riešenia, nie cieľ sám osebe

Túto väzbu chce vidieť v úvode, vo formulácii problému **aj pri hodnotení prínosu**.

### Dve obmedzenia
- **Žiadny podnikateľský zámer, trhové prognózy ani príjmové projekcie** — odvádzalo
  by to pozornosť od schváleného cieľa
- Ekonomický kontext musí byť **priamo naviazaný na riešený problém**, nesmie sa stať
  samostatnou všeobecnou teoretickou časťou o malých firmách

### Zapracované
- Kapitola 1.1 prepísaná — vedie od rozhodovacej situácie k jej ekonomickým dôsledkom
- Kapitola 3.4 — prínosy odvodené priamo od dôsledkov z úvodu, s rozlíšením, ktorý
  sa dá kvantifikovať a ktoré len opísať
