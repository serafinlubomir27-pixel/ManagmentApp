# 21 — Mail pre garanta odboru (prof. Zapletal)

Žiadosť o posúdenie funkčnosti systému a informácia o stave konzultácií.

Súvisí s: [[18 - Schválené zadanie a pripomienky k osnove]] · [[20 - Rešerš konkurencie a smer vzhľadu]]

---

**Predmet:** Nodus — prosba o vyskúšanie (BP, Informatika v ekonomice)

---

Dobrý deň, pán profesor,

volám sa Ľubomír Serafín a študujem Informatiku v ekonomice. Pod vedením pani
doktorky Chytilovej robím bakalárku — informačný systém na riadenie projektov
s metódou kritickej cesty.

Chcel by som Vás poprosiť, či by ste si to vyskúšali a povedali mi, čo na to hovoríte.

https://managmentapp.surge.sh

Zaregistrovať sa dá priamo tam, stačí e-mail, heslo a názov organizácie. Každý má
vlastný priestor, takže sa k sebe navzájom nedostaneme.

Jedna vec dopredu: prvé načítanie trvá asi pol minúty. Systém beží na bezplatnom
serveri, ktorý sa po čase nečinnosti uspáva. Potom už reaguje normálne. V práci to
uvádzam medzi obmedzeniami riešenia.

Ak by ste chceli vidieť to hlavné — založte projekt, pridajte pár úloh a nastavte
medzi nimi závislosti. Systém dopočíta najskoršie a najneskoršie termíny, odvodí
časové rezervy a označí kritickú cestu. Zobrazí to v Ganttovom aj v sieťovom diagrame
a dá sa to exportovať do PDF.

Práve tento výpočet je jadrom práce. Z nástrojov, ktoré som porovnával, ho rozšírené
cloudové riešenia buď nemajú vôbec, alebo kritickú cestu len zafarbia bez uvedenia
rezerv.

S pani doktorkou máme dohodnutý názov, ciele aj osnovu. Podľa jej pripomienok som
osnovu prepracoval — metodika ide pred analýzu, ubral som podkapitoly a dopísal
metodickú časť. Dbám na to, aby systém v práci vystupoval ako prostriedok riešenia
manažérskeho a rozhodovacieho problému s ekonomickými dôsledkami, nie ako cieľ sám
osebe.

Výpočet mám overený na referenčných príkladoch, ktoré som si prepočítal ručne.
Ďalej ma čaká používateľské testovanie na vzorke 8 až 12 ľudí.

Budem rád za akýkoľvek názor — či to funguje, čo chýba, alebo či je zameranie práce
v poriadku vzhľadom na náš program.

Ďakujem za čas,

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
