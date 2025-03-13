# Pakeitimai
Čia pateikiami tik programos naudotojui matomiausi ir svarbesni keitimai.
Išsamiausią keitimų žurnalą galite peržiūrėti https://github.com/embar-/pdsa-grapher/commits/master/ puslapyje.

## Naujausi
### Naujos savybės
- Viz: galimybė rodyti langelius prie stulpelių jų žymėjimui spalvomis.
- Atrenkant lenteles iš rankiniu būdu suvestųjų, nepaisyti raidžių dydžio ir atsižvelgti pakaitos simbolius kaip „*“ ir „?“.

## v2.0.7 (2025-03-13)
### Pataisymai
- Pataisyti lentelių atranką ties „Informacija apie pasirinktų lentelių stulpelius“.

## v2.0.6 (2025-03-13)
### Pataisymai
- Darbo pradžioje rodyti atskirą pranešimą Grafiko kortelėje, jei automatiškai nubraižyta jokia lentelė.
### Kiti pakeitimai
- Priklausomybių versijų atnaujinimas (pvz., dėl greito DBML nuskaitymo).
- Atšaukti „Viz: atnaujinti matomą sritį lentelės tempimo metu“ (cab276a).

## v2.0.5 (2025-03-12)
### Pataisymai
- Viz: nelūžti pridedant stulpelius pagal ryšius, jei neįkeltas PDSA ir nėra "column" stulpelio (pataisyti ded0f85).
- memory-uploaded-pdsa ir memory-uploaded-refs atminties storage_type="memory" (vietoj storage_type="session") galbūt
  turėtų padėti vengti klaidų dėl atminties apribojimų naršyklės puslapiui.
- Viz: atnaujinti matomą sritį lentelės tempimo metu.
### Naujos savybės
- Rodyti skaičių, kiek brėžinyje atvaizduota lentelių.
- Darbo pradžioje rodyti pranešimą Grafiko kortelėje, jei automatiškai nubraižytos ne visos lentelės.

## v2.0.4 (2025-03-07)
### Pataisymai
- Leisti importuoti XLSX, kuriame pasitaikė tuščias lakštas tarp netuščių lakštų.
- Kartais lietuviškas tekstinis dokumentas (pvz., JSON) su UTF-8 koduote klaidingai aptiktas kaip Windows-1252.
- JSON nuskaitymas su tuščiais stulpeliais.

## v2.0.3 (2025-03-06)
### Pataisymai
- Viz: stulpelių perrikiavimas pagal raktus anksčiau negu "…" žymos pridėjimas 
  (antraip kai ties pirminių raktų stulpeliu visur yra null, toks perrikiavimas gali permesti "…" žymą į pradžią)
- Vengti iškylančio paaiškinimo atsiradimo virš puslapio matomumo ribos. 
- Leisti žymėti iškylančio paaiškinimo antraštę kaip tekstą, nes pertempimas neįgyvendintas.
### Naujos savybės
- Viz: karpyti ilgus lentelių ir stulpelių aprašus grafike - pilnus aprašus matome dukart spragtelėję.
### Kiti pakeitimai
- Pervadinti PDSA skydelį į universalesnį „Duombazės lentelės ir stulpeliai“.

## v2.0.2 (2025-03-04)
### Pataisymai
- Viz: rodyti stulpelius, kurie yra minimi ryšiuose, bet nėra aprašyti PDSA (arba yra nesutapimai).
- Viz: tinkamai sudėlioti rodykles abiejų krypčių ryšiuose.
### Naujos savybės
- Galimybė iškart įkelti kelis dokumentus (pvz., CSV) tarsi skirtingus lakštus.
- Naudotojui leisti rinktis tik netuščius PDSA stulpelius dėl informacijos pačiame grafike.

## v2.0.1 (2025-03-03)
### Pataisymai
- Nelūžti DBML stulpelio tipui esant Enum.
- Nelūžti jau išanalizuotą DBML turinį konvertuojant į polars lentelę gavus netikėtų reikšmių.
- Importuojant JSON ir DBML vis tiek reiktų tikrinti, 
  ar paskutinis kėlimas buvo PDSA lauke net kai ryšiai jau importuoti anksčiau.

## v2.0.0 (2025-02-28)
### Pataisymai
- Rodant kaimynus, rodyti ryšius ir tarp tų kaimynų. Pvz., jei A turi kaimynus B ir C, tai rodyti ryšį tarp B ir C.
- Nelūžti, kai pasirinktame PDSA lakšte nėra duomenų.
### Naujos savybės
- Naujas numatytasis Viz variklis grafikų braižymui (kaip Cytoscape alternatyva).
- Naudojant Viz variklį yra galimybė redaguoti tarpinę Graphviz DOT sintaksę.
- Galimybė naudotojui nurodyti stulpelius užuot reikalavus vadinti standartiniais vardais.
- Galimybė rinktis ryšių lakštą (jei jų > 1).
- Leisti braižyti vien tik pagal ryšių dokumentą arba PDSA; tuomet tik įspėti.
- Galimybė neįtraukti tuščių PDSA lentelių, t.y. kurių metaduomenyse nurodyta, jog jose įrašų (eilučių) nėra.
- Galimybė įkelti JSON ir DBML.
- Galimybė įrašyti nubraižytas lenteles bei pagrindinius duomenis apie jas į JSON.
### Kiti pakeitimai
- Paleidimo scenarijus pervadintas iš `app_tabs.py` į `main.py`.
- Naudoti `polars` vietoj `pandas`.

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
Pakeitimai nuo [Lukas-Vasionis/pdsa-grapher](https://github.com/Lukas-Vasionis/pdsa-grapher) versijos.
### Pataisymai
- Sutvarkyti Dash nulūžimai atidarant programą ([issue#23](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/23)).
- Sutvarkyti Dash nulūžimai keičiant išdėstymą ([issue#15](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/15)).
### Naujos savybės
Pagrindinės naujos galimybės apima:
- Lietuvių ir anglų sąsajos kalbų pasirinkimas, tad nebereikia atskirų šakų skirtingoms kalboms.
- Automatinis lakštų ir stulpelių vardų parinkimas _Rinkmenų įkėlimo_ kortelėje standartinėms PDSA ir ryšių rinkmenoms.
- Automatinis iki 10 lentelių, turinčių daugiausia ryšių su kitomis lentelėmis, parinkimas rodymui.
