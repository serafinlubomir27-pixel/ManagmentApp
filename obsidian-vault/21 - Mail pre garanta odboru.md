# 21 — Mail pre garanta odboru (prof. Zapletal)

Žiadosť o posúdenie funkčnosti systému a informácia o stave konzultácií.

Súvisí s: [[18 - Schválené zadanie a pripomienky k osnove]] · [[20 - Rešerš konkurencie a smer vzhľadu]]

---

**Predmet:** Nodus — žiadosť o posúdenie funkčnosti (BP, Informatika v ekonomice)

---

Dobrý deň, pán profesor,

som študent bakalárskeho programu Informatika v ekonomice a v rámci záverečnej práce
vyvíjam informačný systém na riadenie projektov s využitím metódy kritickej cesty.
Vedúcou práce je pani doktorka Chytilová.

Rád by som Vás poprosil o posúdenie funkčnosti systému a o Váš názor, keby ste si
našli chvíľu.

**Odkaz:** https://managmentapp.surge.sh

Registrácia je otvorená, stačí zadať e-mail, heslo a názov organizácie. Vytvorí sa
samostatný priestor, takže sa nedostanete k cudzím údajom ani nikto k Vašim.

**Prosím o strpenie pri prvom načítaní.** Systém beží na bezplatnej úrovni cloudovej
služby, ktorá server po dobe nečinnosti uspáva — prvá požiadavka preto trvá približne
pol minúty, ďalšie už reagujú okamžite. Je to obmedzenie prevádzky, ktoré v práci
uvádzam medzi limitmi riešenia.

**Čo si môžete vyskúšať**

Po založení projektu a niekoľkých úloh stačí medzi nimi nastaviť závislosti. Systém
sám vypočíta najskoršie a najneskoršie možné začiatky a konce, odvodí časové rezervy
a označí kritickú cestu. Výsledok je zobrazený v Ganttovom aj v sieťovom diagrame
a dá sa exportovať do PDF, Excelu alebo CSV.

Práve tento výpočet považujem za jadro práce. Z nástrojov, ktoré som porovnával,
ho rozšírené cloudové riešenia neponúkajú vôbec alebo len ako farebné zvýraznenie
bez uvedenia rezerv.

**Stav konzultácií s vedúcou práce**

S pani doktorkou Chytilovou máme dohodnuté vymedzenie práce. Schválený je názov
„Návrh, implementace a vyhodnocení informačního systému pro řízení projektů
s využitím metody kritické cesty", hlavný cieľ aj dielčie ciele a osnova.

Na jej pripomienky som osnovu prepracoval — metodiku som zaradil pred analýzu,
výrazne som znížil počet podkapitol a doplnil chýbajúcu metodickú časť. Podľa jej
odporúčania kladiem dôraz na to, aby bol informačný systém prezentovaný ako
prostriedok riešenia manažérskeho a rozhodovacieho problému, ktorý má ekonomické
dôsledky, nie ako cieľ práce sám osebe.

Správnosť výpočtu je overená na referenčných príkladoch s hodnotami odvodenými ručne,
nezávisle od implementácie. V ďalšom kroku ma čaká používateľské testovanie, pre ktoré
mi pani doktorka odporučila vzorku 8 až 12 používateľov a dotazník System Usability
Scale.

Budem vďačný za akúkoľvek spätnú väzbu — či už k funkčnosti, k tomu, čo v systéme
chýba, alebo k samotnému zameraniu práce vzhľadom na náš študijný program.

Ďakujem za Váš čas a prajem pekný deň,

Ľubomír Serafín

---

## Pred odoslaním

- [ ] **Otvoriť odkaz pár minút pred odoslaním** — backend sa zobudí a prvý dojem
      nepokazí čakanie
- [ ] **Zmeniť heslo účtu `admin`** — `admin123` je stále funkčné
      (`$env:ADMIN_USERNAME='admin'; $env:ADMIN_PASSWORD='…'; py scripts/create_admin.py`)
- [ ] Doplniť správne oslovenie s titulom
- [ ] Prejsť vlastnými slovami

## Čo v maili zámerne nie je

**Prihlasovacie údaje.** Nech si založí vlastný účet — uvidí tým aj registráciu
a nedostane sa k tvojim dátam.

**Tlačidlo Export funguje**, takže sa mu netreba vyhýbať. Backend aj rozhranie
sú zosúladené, overené 17 kontrolami.

**Zoznam všetkého, čo systém vie.** Mail ukazuje jednu vec, ktorá ho odlišuje, nie
katalóg funkcií. Garant odboru ocení zameranie viac než rozsah.
