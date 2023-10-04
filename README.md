# Reikalingi failai (inputs):
* PDSA failas
* Užklausos failas, kuriame aprašyti lentelių ryšiai

# Naudojimas
Programuotojams:
* Susiinstaliuoti bibliotekas
* Paleisti app_tabs.py script'ą
* Paleist scriptą: terminale turėtų atsirasti nuoroda - ją atidaryti su savo naršykle (testuota ant Chrome)

Visiems:
* Failų įkelimas
  * Atsidariusiame puslapyje įkelti du failus - PDSA ir Užklausos. Pažymėti kurie sheet'ai ir stulepliai ką atitinka
  * Kairėje, PDSA skyltyje, pasirinkti, kuriuos stulpelius norit atvaizduoti iš sheet'o aprašančio lenteles ir sheet'o aprašančio stulpelius.
  * **Būtinai paspauskit** `Submit`

* Atvaizdavimas
  * Viršuje paspauskite tab'ą Grapher - jame bus atvaziduojama jūsų informacija iš PDSA ir Užklausos failų, pagal jūsų parinktis.
  * Puslapio išdėstymas:
    *   Kairėje pusėje atvaizduojamos lentelių jungtys
    *   Dešinėje pasirenkama ką ir kaip atviazduoti.
    *   Viršuje rasite instrukcijas kaip naudotis šiomis skiltimis
      
# Reikalingi update:
* <del>Kadangi norim duot šį scriptą naudoti PDSA vadybininkams, jam reikia sukurti GUI</del>
* Sukurti galimybę grafoje atvaizduoti stulpelius, kurie jungia lenteles
* Grafą paversti į "directed graph". Kitaip tariant, pridėti rodykles, nurodančias kas jungtyje yra source ir target
* Uždėt apribojimą ant stuleplių pasirinkimo tab'e "failų įkelimas". Čia, būtina palikti stulpelius "table" ir "column", nes jie yra naudojami grapher tab'o filtruose. Jei šie stulpeliai yra pašalinami tab'e "failų įkelimas", "grapher" tab'e lentelių informacijos nebeatvaizduosi.  
* Deploy'int programa, informacijos vadibininkams prieinamu budu
