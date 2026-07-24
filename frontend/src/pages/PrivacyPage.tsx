import { Link } from 'react-router-dom'
import LegalShell, { H2, P, UL } from '../components/LegalShell'

export default function PrivacyPage() {
  return (
    <LegalShell title="Zásady ochrany osobných údajov" updated="24. 7. 2026">
      <P>
        Tieto zásady popisujú, ako služba <strong>Nodus</strong> spracúva osobné údaje v súlade
        s Nariadením (EÚ) 2016/679 (<strong>GDPR</strong>) a zákonom č. 18/2018 Z. z.
      </P>

      <H2>1. Prevádzkovateľ</H2>
      <P>
        <strong>[Obchodné meno]</strong>, [sídlo], IČO: [IČO], e-mail: [kontaktný e-mail].
        Kontakt vo veciach ochrany údajov: [e-mail pre GDPR].
      </P>

      <H2>2. Aké údaje spracúvame</H2>
      <UL items={[
        <><strong>Registračné</strong>: e-mail, meno, názov organizácie, zašifrované heslo.</>,
        <><strong>Obsahové</strong>: dáta, ktoré vložíš (projekty, úlohy, členovia tímu, klienti, súbory).</>,
        <><strong>Technické</strong>: IP adresa, logy prístupu, základné údaje o prehliadači (na bezpečnosť a prevádzku).</>,
      ]} />

      <H2>3. Účel a právny základ</H2>
      <UL items={[
        'Poskytovanie Služby a správa účtu — plnenie zmluvy (čl. 6 ods. 1 písm. b GDPR).',
        'Bezpečnosť, prevencia zneužitia, prevádzkové logy — oprávnený záujem (písm. f).',
        'Zasielanie prevádzkových e-mailov (reset hesla, pozvánky) — plnenie zmluvy.',
        'Prípadné marketingové e-maily — len na základe súhlasu (písm. a), ktorý možno kedykoľvek odvolať.',
      ]} />

      <H2>4. Postavenie pri dátach zákazníka (dôležité)</H2>
      <P>
        Ak ako zákazník ukladáš do Nodusu osobné údaje <strong>tretích osôb</strong> (napr. členov
        tímu alebo klientov v klientskom module), si vo vzťahu k nim <strong>prevádzkovateľom</strong> ty
        a Nodus je <strong>sprostredkovateľ</strong> (processor), ktorý údaje spracúva podľa tvojich
        pokynov. Odporúčame uzavrieť Zmluvu o spracúvaní osobných údajov — kontaktuj nás na [e-mail pre GDPR].
      </P>

      <H2>5. Príjemcovia a sub-sprostredkovatelia</H2>
      <P>Na prevádzku využívame dôveryhodných poskytovateľov (hosting v EÚ, kde je to možné):</P>
      <UL items={[
        'Supabase — databáza (PostgreSQL).',
        'Render — hosting aplikačného servera.',
        'Vercel — hosting webového rozhrania.',
        'Resend — odosielanie transakčných e-mailov (ak je aktívne).',
      ]} />

      <H2>6. Doba uchovávania</H2>
      <P>
        Údaje uchovávame po dobu existencie účtu. Po zmazaní účtu/organizácie sa dáta nenávratne
        odstránia (okrem prípadov, keď zákon vyžaduje ich uchovanie — napr. účtovné doklady).
      </P>

      <H2>7. Tvoje práva</H2>
      <UL items={[
        <><strong>Prístup a prenositeľnosť</strong> — v nastaveniach je funkcia <em>Export dát</em> (JSON).</>,
        <><strong>Výmaz</strong> — v nastaveniach môžeš nenávratne zmazať účet/organizáciu.</>,
        <><strong>Oprava</strong> — údaje si upravíš v profile a nastaveniach.</>,
        <><strong>Námietka a obmedzenie</strong> spracúvania — kontaktuj nás.</>,
      ]} />
      <P>
        Máš tiež právo podať sťažnosť dozornému orgánu:{' '}
        <strong>Úrad na ochranu osobných údajov SR</strong> (dataprotection.gov.sk).
      </P>

      <H2>8. Cookies a lokálne úložisko</H2>
      <P>
        Nodus nepoužíva sledovacie (reklamné) cookies. V prehliadači ukladáme len nevyhnutné údaje
        potrebné na prihlásenie (prihlasovací token v <code>localStorage</code>).
      </P>

      <H2>9. Bezpečnosť</H2>
      <P>
        Heslá ukladáme výhradne ako bcrypt hash, komunikácia prebieha cez HTTPS, dáta organizácií
        sú navzájom izolované (multi-tenancy) a databáza má zapnutú ochranu na úrovni riadkov (RLS).
      </P>

      <H2>10. Kontakt</H2>
      <P>
        Vo veciach ochrany údajov nás kontaktuj na [e-mail pre GDPR]. Pozri aj{' '}
        <Link to="/podmienky" className="text-brand-500 hover:underline">Podmienky používania</Link>.
      </P>
    </LegalShell>
  )
}
