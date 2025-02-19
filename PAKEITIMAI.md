# Pakeitimai
Čia pateikiami tik programos naudotojui matomiausi ir svarbesni keitimai.
Išsamiausią keitimų žurnalą galite peržiūrėti https://github.com/embar-/pdsa-grapher/commits/master/ puslapyje.

## Naujausi
### Pataisymai
- Rodant kaimynus, rodyti ryšius ir tarp tų kaimynų. Pvz., jei A turi kaimynus B ir C, tai rodyti ryšį tarp B ir C.
- Nelūžti, kai pasirinktame PDSA lakšte nėra duomenų.

### Naujos savybės
- Papildomas pasirinktinis Viz variklis grafikų braižymui (kaip Cytoscape alternatyva).
- Galimybė naudotojui nurodyti stulpelius užuot reikalavus vadinti standartiniais vardais.
- Galimybė rinktis ryšių lakštą (jei jų > 1).
- Leisti braižyti vien tik pagal ryšių dokumentą, neįkėlus PDSA; tuomet tik įspėti.
- Galimybė neįtraukti PDSA lentelių, kurių metaduomenyse nurodyta, jog jose įrašų (eilučių) nėra.

### Kiti pakeitimai
- Paleidimo scenarijus pervadintas iš `app_tabs.py` į `main.py`.
- XLSX ir CSV nuskaitymui naudoti `polars` vietoj `pandas`.

## v1.3 (2025-02-10)
### Pataisymai
- _Rinkmenų įkėlimo_ kortelėje tikrinti, ar įkeliama lentelė turi privalumus stulpelius kaip `table` 
  ([issue#13](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/13)).
- Keičiant kalbą ar iš naujo atidarant puslapį, nepradingsta įkelti PDSA ir ryšių duomenys.

### Naujos savybės
- Galimybė pasirinkti rodytinų kaimynų tipą: įeinančius, išeinančius ar visus ryšius 
  ([issue#14](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/14)).
- Nuo aktyvaus pažymėto mazgo įeinančius ir išeinančius ryšius vaizduoti skirtingomis linijų spalvomis.
- Leisti pasirinkti lenteles, net jos pamirštos aprašyti PDSA dokumente, bet buvo ryšių dokumente.
- Įspėjimai ir klaidos rodomi naršyklės lange po „Pateikti“ mygtuku, paaiškinantys, 
  kodėl naudotojas negali pateikti duomenų grafikui.
- Galimybė rodyti užrašus virš aktyvių ryšių (žymimasis langelis per ☰ meniu).
- Galimybė kopijuoti nubraižytas lenteles (pasirinkimas per ☰ meniu).
- Galimybė kopijuoti sąrašą lentelių, apie kurias naudotojas pasirinko žiūrinėti stulpelių info.
- Nauji pavyzdiniai duomenys, kurie įvairiapusiškiau leidžia įvertinti įrankio galimybes.

## v1.2 (2025-01-29)
### Pataisymai
- Lentelės be ryšių nėra matomos ([issue#21](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/21)).
- Perkompiliuoti vertimų MO ir tuomet, kai jie senesni už PO.
- Vengti nulūžimų pašalinus visus mazgus (lenteles).

### Naujos savybės
- Mygtukas visų lentelių nubraižymui iš karto ([issue#17](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/17)).
- Prašant rodyti kaimynus, juos rodyti kita mazgo spalva.
- Spustelėjus mazgą, rodoma išsami informacija apie jį, įskaitant ryšius su nerodomomis lentelėmis.
- Spustelėjus jungtį rodyti stulpelius, kurie jungia lenteles.
- Galimybė „Rinkmenų įkėlimo“ kortelėje nurodyti, kad turime ryšių stulpelius.
- Galimybė įkelti ryšius kaip CSV rinkmeną, ne tik XLSX ([issue#18](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/18)).
- Atnaujintas išdėstymas _Grafiko_ kortelėje su galimybe keisti skydelių dydį.
- Rodyti ryšių kryptis - pridėti linijoms rodykles priklausomai nuo to, ar tai ryšių pradžia, ar galas.

## v1.0 (2025-01-09)
### Pataisymai
- Sutvarkyti Dash nulūžimai atidarant programą ([issue#23](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/23)).
- Sutvarkyti Dash nulūžimai keičiant išdėstymą ([issue#15](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/15)).

### Naujos savybės
Pagrindinės naujos galimybės apima:
- Lietuvių ir anglų sąsajos kalbų pasirinkimas, tad nebereikia atskirų šakų skirtingoms kalboms.
- Automatinis lakštų ir stulpelių vardų parinkimas _Rinkmenų įkėlimo_ kortelėje standartinėms PDSA ir ryšių rinkmenoms.
- Automatinis iki 10 lentelių, turinčių daugiausia ryšių su kitomis lentelėmis, parinkimas rodymui.
