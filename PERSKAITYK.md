# PDSA graferis

**Paskirtis:**
Ši programa leidžia rodyti ir atrinkti duomenų bazės lentelių ryšius, taip pat rodyti tų lentelių metaduomenis.

**Technologijos**:
Python 3, Plotly Dash.

![graferis 1.3 2025-02-10](sample_data/biblioteka_cyto.gif)

## Turinys
- [Pradinio kodo katalogo struktūra](#pradinio-kodo-katalogo-struktūra)
- [Įvedimui reikalingos rinkmenos](#įvedimui-reikalingos-rinkmenos)
- [Diegimas ir paleidimas](#diegimas-ir-paleidimas)
  - [1 būdas: įprastas Python](#1-būdas-įprastas-python)
  - [2 būdas: Docker programa iš vietinio kodo](#2-būdas-docker-programa-iš-vietinio-kodo)
  - [3 būdas: Docker atvaizdis iš „Docker Hub“](#3-būdas-docker-atvaizdis-iš-docker-hub)
- [Naudojimas](#naudojimas)
  - [Rinkmenų įkėlimas](#rinkmenų-įkėlimas)
  - [Grafikas](#grafikas)
- [Atšakos atnaujinimai](#atšakos-atnaujinimai)
- [Žinomi trūkumai ir pageidavimai](#žinomi-trūkumai-ir-pageidavimai)
- [Licencija](#licenzija)


## Pradinio kodo katalogo struktūra
Projekto rinkmenos išdėliotos šiuose kataloguose:


| Katalogas       | Aprašymas                                                                   |
|-----------------|-----------------------------------------------------------------------------|
| `assets/`       | Dash priedai                                                                |
| `grapher_lib/`  | Pagalbinių funkcijų biblioteka                                              |
| `locale/`       | Gettext lokalizacijos rinkmenos                                             |
| `locale_utils/` | Įrankiai Gettext lokalizacijai nustatyti ir `locale/` rinkmenoms atnaujinti |
| `sample_data/`  | Pavyzdinės PDSA, ryšių ir kt. susijusios rinkmenos                          |

Pagrindiniame kataloge rasite pagrindinę Python rinkmeną `main.py`, Docker rinkmenas ir kitas bendrąsias rinkmenas.

Rinkmenos yra UTF-8 koduote.

## Įvedimui reikalingos rinkmenos
- Pirminių duomenų struktūros aprašo (PDSA) XLSX rinkmena, kurioje yra informacija apie mazgus (lenteles).
  Programa tikisi, kad šioje rinkmenoje bus bent du lakštai:
  - Lakštas, aprašantis lenteles:
    - lentelių pavadinimai `table` stulpelyje (privaloma),
    - aprašymai (tikimasi `comment` stulpelyje, neprivaloma)
    - ir kt.
  - Lakštas, aprašantis lentelių stulpelius:
    - lentelių pavadinimai `table` stulpelyje (privaloma),
    - stulpelių pavadinimai (tikimasi `column` stulpelyje),
    - aprašymai (tikimasi `comment` stulpelyje, neprivaloma),
    - pirminio rakto nurodymas (tikimasi `is_primary` stulpelyje, neprivaloma),
    - duomenų tipai, null kiekis ir kt.

- Ryšių XLSX arba CSV rinkmena, kurioje yra informacija apie jungtis (susiejimus tarp lentelių).
  Programai reikia stulpelių, kuriuose yra ryšių pradžių lentelės ir galų lentelių vardai;
  stulpeliai, kuriuose yra informacija apie ryšių pradžių stulpelius ir galų stulpelius, nėra privalomi, bet rekomenduojami.


## Diegimas ir paleidimas
Pasirinkite vieną būdą, kaip įdiegti priklausomybes ir paleisti programą: arba įprastu Python, arba Docker.

### 1 būdas: įprastas Python
1. Atverkite terminalo programą ir įeikite į pradinio kodo katalogą.
2. Įdiekite reikalingas bibliotekas, pvz., paleisdami:
  `pip install -r requirements.txt`
3. Paleiskite programą:
  `python main.py`
4. Atverkite nuorodą, kuri pasirodys terminale, kuri paprastai būna http://127.0.0.1:8050/pdsa_grapher/

**Pastaba:** programa išbandyta su Python 3.10 ir 3.12 versijomis.

### 2 būdas: Docker programa iš vietinio kodo
1. Įsitikinkite, kad jūsų kompiuteryje paleista Docker tarnyba.
2. Atverkite terminalo programą ir įeikite į pradinio kodo katalogą
   (įsitikinkite, kad ten yra `docker-compose.yml`).
3. Įvykdykite komandą Docker konteinerio sukūrimui ir paleidimui:
   `docker-compose up`
4. Atverkite naršyklę ir eikite į http://localhost:8080/pdsa_grapher/

### 3 būdas: Docker atvaizdis iš „Docker Hub“
Programą galite paleisti kaip [mindaubar/grapher-app](https://hub.docker.com/r/mindaubar/grapher-app) atvaizdį:
1. Įsitikinkite, kad jūsų kompiuteryje paleista Docker tarnyba.
2. Atverkite terminalo programą.
3. Įvykdykite komandą Docker konteinerio parsisiuntimui ir jo paleidimui
  (paslauga veikia 80 prievade, todėl reikia susieti prievadus):
  `docker run -p 8080:80 mindaubar/grapher-app:latest`
4. Atverkite naršyklę ir eikite į http://localhost:8080/pdsa_grapher/

**Pastaba:** „Docker Hub“ atvaizdis gali būti neatnaujintas.


## Naudojimas
Darbą pradedame `Rinkmenų įkėlimo` kortelėje, vėliau tęsiame `Grafiko` kortelėje. 

### Rinkmenų įkėlimas
- Atvėrę nuorodą, įkelkite reikiamas PDSA ir ryšių rinkmenas į atitinkamus laukus.
- Nurodykite, kuriuose lakštuose ir stulpeliuose yra sudėta informacija apie duombazę:
  - Kairėje pusėje ties _PDSA_ pasirinkite, kuris lakštas turi informaciją apie lenteles ir stulpelius.
    Tada pasirinkite stulpelius, kuriuos norėsite matyti šalia grafiko.
  - Dešinėje pusėje ties _ryšiais_ nurodykite, kurie stulpeliai turi ryšių pradžias ir galus.
- Paspauskite mygtuką **Pateikti** parinkčių apdorojimui ir perdavimui į _Grafiko_ kortelę. 

### Grafikas
_Grafiko_ kortelėje atvaizduojama jūsų pateikta informacija apie duombazę.
  Puslapio išdėstymas:
- Dešinėje pusėje galite atsirinkti, ką ir kaip rodyti:
  - Viršutinėje juostoje rasite naudojimo instrukcijas.
  - Pasirinkite norimą išdėstymą - tinklo atvaizdavimo mazgų parinktis.
  - Pasirinkite lenteles, kurias norite braižyti, arba įrašykite lentelių sąrašą (atskiriant kableliais).
  - Žymimasis langelis „Rodyti kaimynus“ leidžia rodyti visas lenteles, kurios jungiasi su jūsų jau pasirinktomis.
- Kairėje pusėje rodomas lentelių tinklas.
- Apatinė dalis rodo išsamią informaciją:
  - apie pasirinktų lentelių stulpelius,
  - apie rodomas lenteles.

Pastaba: programa išbandyta Firefox, Chrome, Edge naršyklėse.


## Atšakos atnaujinimai
Lyginant su originaliu [Lukas-Vasionis/pdsa-grapher](https://github.com/Lukas-Vasionis/pdsa-grapher) darbu, šioje atšakoje (angl. fork) 
pataisytos kai kurios klaidos ir pridėtos naujos savybės - svarbiosios aprašytos žemiau. 
Keitimai išsamiau aprašyti [PAKEITIMAI.md](PAKEITIMAI.md) rinkmenoje 
ir [GitHub žurnale](https://github.com/embar-/pdsa-grapher/commits/master/) puslapyje.

### Pataisymai
- Sutvarkyti Dash nulūžimai atidarant programą ([issue#23](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/23)).
- Sutvarkyti Dash nulūžimai keičiant išdėstymą ([issue#15](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/15)).
- Vengti nulūžimų pašalinus visus mazgus (lenteles).
- Lentelės be ryšių nėra matomos ([issue#21](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/21)).

### Naujos savybės
Pagrindinės naujos galimybės apima:
- Galimybė įkelti ryšius kaip CSV rinkmeną, ne tik XLSX ([issue#18](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/18)).
- Lietuvių ir anglų sąsajos kalbų pasirinkimas, tad nebereikia atskirų šakų skirtingoms kalboms.
- Automatinis lakštų ir stulpelių vardų parinkimas _Rinkmenų įkėlimo_ kortelėje standartinėms PDSA ir ryšių rinkmenoms.
- Automatinis iki 10 lentelių, turinčių daugiausia ryšių su kitomis lentelėmis, parinkimas rodymui.
- Mygtukas visų lentelių nubraižymui iš karto ([issue#17](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/17)).
- Spustelėjus mazgą, rodoma išsami informacija apie jį, įskaitant ryšius su nerodomomis lentelėmis.
- Galimybė pasirinkti rodytinų kaimynų tipą: įeinančius, išeinančius ar visus ryšius 
  ([issue#14](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/14)).
- Nuo aktyvaus pažymėto mazgo įeinančius ir išeinančius ryšius vaizduoti skirtingomis linijų spalvomis.

## Žinomi trūkumai ir pageidavimai
- <del>Galimybė rodyti stulpelius, kurie jungia lenteles.<del>
- <del>Rodyti ryšių kryptis - pridėti linijoms rodykles priklausomai nuo to, ar tai ryšių pradžia, ar galas.<del>
- <del>_Rinkmenų įkėlimo_ kortelėje tikrinti, ar įkeliama lentelė turi privalumus stulpelius kaip `table` 
  ([issue#13](https://github.com/Lukas-Vasionis/pdsa-grapher/issues/13)).<del> 
- Įkelti programą į serverį, kad galėtų ja naudotis vartotojai, neturintys programavimo žinių.
- Taip pat žr. https://github.com/Lukas-Vasionis/pdsa-grapher/issues

## Licenzija
Projektas platinamas pagal MIT licenziją, žr. `LICENSE` rinkmeną.
