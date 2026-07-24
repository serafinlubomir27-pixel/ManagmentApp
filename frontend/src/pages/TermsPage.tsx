import { Link } from 'react-router-dom'
import LegalShell, { H2, P, UL } from '../components/LegalShell'

export default function TermsPage() {
  return (
    <LegalShell title="Podmienky používania" updated="24. 7. 2026">
      <P>
        Tieto podmienky upravujú používanie služby <strong>Nodus</strong> (ďalej „Služba"),
        ktorú prevádzkuje <strong>[Obchodné meno prevádzkovateľa]</strong>, [sídlo], IČO: [IČO],
        e-mail: [kontaktný e-mail] (ďalej „Prevádzkovateľ"). Registráciou a používaním Služby
        s týmito podmienkami súhlasíš.
      </P>

      <H2>1. Definície</H2>
      <UL items={[
        <><strong>Používateľ</strong> — fyzická osoba, ktorá si vytvorí účet.</>,
        <><strong>Organizácia</strong> — pracovný priestor, ku ktorému patria používatelia, projekty a dáta.</>,
        <><strong>Obsah</strong> — všetky dáta, ktoré do Služby vložíš (projekty, úlohy, klienti, súbory).</>,
      ]} />

      <H2>2. Účet a registrácia</H2>
      <UL items={[
        'Pri registrácii uvádzaš pravdivé a aktuálne údaje.',
        'Zodpovedáš za dôvernosť svojho hesla a za všetku aktivitu pod svojím účtom.',
        'Službu môžu používať osoby staršie ako 16 rokov, resp. s právnou spôsobilosťou uzavrieť zmluvu.',
      ]} />

      <H2>3. Používanie Služby</H2>
      <P>Zaväzuješ sa Službu nepoužívať na protiprávne účely. Zakázané je najmä:</P>
      <UL items={[
        'narúšať bezpečnosť alebo prevádzku Služby, pokúšať sa o neoprávnený prístup,',
        'nahrávať škodlivý kód alebo obsah porušujúci práva tretích osôb,',
        'zdieľať prístupové údaje s neoprávnenými osobami,',
        'automatizovane zaťažovať Službu nad rámec bežného používania.',
      ]} />

      <H2>4. Plány a platby</H2>
      <UL items={[
        'Služba ponúka bezplatný plán a platené plány s rozšírenými limitmi a funkciami.',
        'Ceny a limity platných plánov sú uvedené na stránke s cenníkom.',
        'Prevádzkovateľ môže ceny a rozsah plánov meniť; o zmenách bude informovať vopred.',
      ]} />

      <H2>5. Tvoj obsah</H2>
      <P>
        Obsah, ktorý do Služby vložíš, ostáva <strong>tvojím vlastníctvom</strong>. Udeľuješ
        Prevádzkovateľovi obmedzené právo tvoj obsah spracúvať výlučne v rozsahu potrebnom na
        prevádzku Služby (uloženie, zobrazenie, zálohovanie). Prevádzkovateľ tvoj obsah nepredáva
        ani nepoužíva na iné účely.
      </P>

      <H2>6. Dostupnosť a zodpovednosť</H2>
      <UL items={[
        'Služba je poskytovaná „tak ako je" (as-is), bez záruky nepretržitej dostupnosti.',
        'Prevádzkovateľ nezodpovedá za nepriame škody, ušlý zisk ani stratu dát v rozsahu, ktorý pripúšťa právo.',
        'Odporúčame pravidelný export dôležitých dát (funkcia Export v nastaveniach).',
      ]} />

      <H2>7. Ukončenie</H2>
      <P>
        Účet aj organizáciu môžeš kedykoľvek zmazať v nastaveniach (Nebezpečná zóna) — dáta sa
        nenávratne odstránia. Prevádzkovateľ môže účet pozastaviť pri závažnom porušení týchto podmienok.
      </P>

      <H2>8. Zmeny podmienok</H2>
      <P>Prevádzkovateľ môže tieto podmienky aktualizovať. O podstatných zmenách bude informovať vopred.</P>

      <H2>9. Rozhodné právo</H2>
      <P>
        Tieto podmienky sa riadia právnym poriadkom Slovenskej republiky. Prípadné spory riešia
        príslušné súdy SR.
      </P>

      <H2>10. Kontakt</H2>
      <P>
        Otázky: [kontaktný e-mail]. Pozri aj{' '}
        <Link to="/ochrana-osobnych-udajov" className="text-brand-500 hover:underline">
          Zásady ochrany osobných údajov
        </Link>.
      </P>
    </LegalShell>
  )
}
