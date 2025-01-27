"""
Įrankiai POT, PO, MO vertimo rinkmenų sukūrimui bei atnaujinimui naudojant Python.
ARBA viską būtų galima pasidaryti ir su tam skirtomis programomis pybabel ar msgfmt iš gettext.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import os
import glob
import warnings
import polib
from babel.messages import frontend as babel_frontend


class Pot:
    """
    POT - vertimo šablonas
    """
    def __init__(
            self, app_name: str="messages", languages=None, babel_config: str="locale_utils/babel.cfg", force_regenerate=False
    ):
        """

        :param app_name: programos vardas, naudojamas POT rinkmenos vardui (taip pat PO ir MO rinkmenų vardams).
        :param languages: sąrašas kalbų, kurioms kurti PO pagal POT; numatyta ["en", "lt"].
        :param babel_config: rinkmena, kurioje yra babel konfigūracija; Python programoms jos viduje turi būti įrašyta:
            [python: **.py]
        :param force_regenerate: ar priverstinai atnaujinti POT, net ji jau yra.
        """

        self.app_name = app_name
        self.pot_filename = f"locale/{app_name}.pot"
        self.languages = languages or ["en", "lt"]
        self.babel_config = babel_config
        regenerate = not os.path.exists(self.pot_filename) or force_regenerate
        if regenerate:
            self.pot = None  # Laikina tuščia reikšmė
            self.generate()  # Užpildyti self.pot turinį
        else:
            self.pot = polib.pofile(self.pot_filename)
            print(f"POT sėkmingai nuskaityta iš:", self.pot_filename)
        for lang in self.languages:
            Po(app_name=self.app_name, language=lang, pot=self.pot, force_update=force_regenerate)


    def generate(self):
        """
        Sukurti gettext tipo POT
        """
        create_dir_for_file(self.pot_filename)
        extract_cmd = babel_frontend.extract_messages()
        extract_cmd.input_paths = ['.']
        extract_cmd.output_file = self.pot_filename
        extract_cmd.mapping_file = self.babel_config
        extract_cmd.finalize_options()
        extract_cmd.run()
        print(f"POT sėkmingai sukurta:", self.pot_filename)

        # Įsikelti POT turinį
        create_dir_for_file(self.pot_filename)  # jei nėra, sukurti atitinkamą katalogą
        self.pot = polib.pofile(self.pot_filename)
        self.pot.header.replace(
            "Translations template for PROJECT.",
            f"Translations template for {self.app_name}."
        )
        self.pot.save(self.pot_filename)


    def get(self):
        return self.pot


class Po:
    """
    PO - vertimo rinkmena į konkrečią kalbą
    """
    def __init__(
            self, app_name: str="messages", language: str="lt", pot=None, force_update=False
    ):
        """
        Sukurti polib.POFile objektą
        :param app_name: programos vardas, naudojamas PO ir MO rinkmenų vardams.
        :param language: kalbos kodas, pvz., "lt", "en".
        :param pot: None, kelias iki POT arba polib.POFile objektas.
        :param force_update: ar priverstinai atnaujinti pagal POT, net jei PO jau yra.
        """

        # PO metaduomenys
        self.app_name = app_name
        self.lang = language
        self.path_po = f"locale/{self.lang}/LC_MESSAGES/{self.app_name}.po"
        self.path_mo = f"locale/{self.lang}/LC_MESSAGES/{self.app_name}.mo"

        # POT kaip šablonas
        pot_auto_filename = f"locale/{self.app_name}.pot"
        if pot is None:
            if os.path.exists(pot_auto_filename):
                pot = pot_auto_filename
            else:
                warnings.warn(f"Nėra POT šablono {pot_auto_filename}")
        self.pot = polib.pofile(pot) if isinstance(pot, str) else pot  # Jei POT pateiktas kaip objektas - naudoti jį

        # PO turinio sukūrimas arba atnaujinimas
        if os.path.exists(self.path_po):
            self.po = polib.pofile(self.path_po)
            print(f"PO sėkmingai nuskaityta iš:", self.path_po)
            if force_update:
                self.update()
                self.compile()  # Perkompiliuoti MO
        else:
            self.po = None  # Laikina tuščia reikšmė
            self.create()  # atnaujinti self.po turinį
            self.compile()  # Kompiliuoti MO


    def create(self):
        """
        Sukurti naują PO pagal POT.
        """

        if self.pot is None:
            "Nėra POT šablono!"
            return

        # Nukopijuoti visą turinį iš POT
        self.po = self.pot

        # Atnaujinti metaduomenis
        self.po.fpath = self.path_po
        self.po.header = self.po.header.replace(
            "PROJECT",  # šis raktažodis numatytuoju atveju gali būti dviejose vietose
            f"{self.app_name}"
        )
        self.po.header = self.po.header.replace(
            f"Translations template for {self.app_name}.",
            f"{self.app_name} translations into {self.lang}"
        )
        self.po.metadata['Report-Msgid-Bugs-To'] = f'your@email.{self.lang}'
        self.po.metadata['Last-Translator'] = f'FULL NAME <your@email.{self.lang}>'
        self.po.metadata['PO-Revision-Date'] = self.pot.metadata['POT-Creation-Date']
        self.po.metadata['Language-Team'] = f'{self.lang} <team@email.{self.lang}>'

        # Įrašyti
        create_dir_for_file(self.path_po)  # jei nėra, sukurti atitinkamą katalogą
        self.po.save(self.path_po)
        print("PO sėkmingai įrašyta į:", self.path_po)


    def update(self):
        """
        Atnaujinti PO įrašus POT pagrindu.
        Tie, PO įrašai, kurių POT nebeturi, nukeliami į galą ir užkomentuojami.
        """
        if self.pot is None:
            "Nėra POT šablono!"
            return

        self.po.merge(self.pot)  # Pats pagrindinis PO atnaujinimas pagal POT
        # .merge() f-ja neatnaujina datos pagal POT - atnaujinti atskirai
        self.po.metadata["POT-Creation-Date"] = self.pot.metadata["POT-Creation-Date"]
        self.po.save(self.path_po)  # Įrašyti atnaujintą PO
        print("PO sėkmingai atnaujinta į:", self.path_po)


    def compile(self):
        """
        Sukompiliuoti PO į MO
        """
        if self.po is None:
            print("Negalite kompiliuoti iš tuščio PO:", self.path_po)
            return
        self.po.save_as_mofile(self.path_mo)
        print("PO sėkmingai sukompiliuota į:", self.path_mo)


    def get(self):
        return self.po


def create_dir_for_file(new_file_path):
    """
    Sukurti katalogą naujai rinkmenai, jei katalogo jai nėra.
    :param new_file_path: naujos rinkmenos kelias
    """
    directory = os.path.dirname(new_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def find_all_po(app_name=None):
    """
    Rasti locale/*/LC_MESSAGES/*.po rinkmenas.
    :param app_name: ieškoti tik nurodytos programos PO (numatyta None - ieškoti visų PO)
    :return: Po sąrašas
    """
    print(f"Ieškoma {app_name if app_name else ''} vertimų PO rinkmenų...")
    po_list = []
    po_files = glob.glob('locale/*/LC_MESSAGES/*.po')
    for po_file in po_files:
        po_name = po_file.split(os.sep)[-1][:-3]
        if (
                (app_name is None) or
                (isinstance(app_name, str) and po_name == app_name) or
                (isinstance(app_name, list) and po_name in app_name)
        ):
            po_lang = po_file.split(os.sep)[1]
            po_list.append(Po(app_name=po_name, language=po_lang))
    return po_list


def recompile_all_po(app_name=None):
    """
    Rasti locale/*/LC_MESSAGES/*.po rinkmenas ir jas perkompiliuoti.
    Ši funkcija naudinga, jei Pot klasė buvo kviečiama su force_regenerate=False, naudotojas rankiniu būdu redagavo PO.
    :param app_name: perkompiliuoti tik nurodytos programos PO (numatyta None - perkompiliuoti visus PO)
    """
    po_list = find_all_po(app_name=app_name)
    if po_list:
        print("Vertimų kompiliavimas:")
        for po in po_list:
            try:
                po.compile()
            except Exception as e:
                warnings.warn(f"Klaida kompiliuojant vertimų MO:\n {e}")


if __name__ == '__main__':
    """
    Atnaujinti `pdsa-grapher` POT, PO, perkompiliuoti MO.
    """
    os.chdir('..')
    app = "pdsa-grapher"
    langs = [po_file.split(os.sep)[1] for po_file in glob.glob(f'locale/*/LC_MESSAGES/{app}.po')]
    pot = Pot(app_name=app, languages=langs, force_regenerate=True)



