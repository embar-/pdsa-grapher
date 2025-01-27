"""
Dinamiškas programos vertimų, esančių MO rinkmenose, pasiekimas naudojant gettext sintaksę.
Vertimai gaunami kviečiant funkcijas „_()“ ir, jei reikia atsižvelgti į kontekstą, su „pgettext()“.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import os
from gettext import translation


def refresh_gettext_locale(lang: str="lt"):
    """
    gettex vertimo rinkmenų patikrinimas ir kalbos nustatymų atnaujinimas globaliam naudojimui su _()
    :param lang: pasirinktos kalbos kodas
    """
    update_locate_files_if_needed([lang])
    set_gettext_locale(lang)


def set_gettext_locale(lang: str="lt"):
    """
    gettex naudojamos kalbos atnaujinimas, kuris diegiamas globaliai naudojimui su _()
    :param lang: pasirinktos kalbos kodas
    :return: GNUTranslations objektas
    """
    lang_trans = translation("pdsa-grapher", 'locale', languages=[lang])
    lang_trans.install()
    return lang_trans


# Apsirašyti savo pgettext vietoj gettext.pgettext, nes jo neatnaujina gettext .install()
def pgettext(context: str, message: str) -> str:
    """
    Pranešimo vertimas atsižvelgiant į pranešimo kontekstas. Daro tą patį kaip gettext.pgettext,
    tačiau pastarasis netinka tuomet, kai keičiame kalbas programos viduje.
    :param context: prašimo kontekstas
    :param message: pranešimas
    :return: išverstas tekstas
    """
    return _(f"{context}\x04{message}")


def update_locate_files_if_needed(languages=None):
    """
    Patikrinti PO ir MO vertimų rinkmenų buvimą, jei reikia iškviesti jų perkūrimą arba atnaujinimą
    """
    if languages is None:
        languages = ['en', 'lt']
    elif isinstance(languages, str):
        languages = [languages]
    elif isinstance(languages, dict):
        languages = list(languages.keys())

    if all([  # ar turime tiek PO, tiek MO
        os.path.exists(f"locale/{lang}/LC_MESSAGES/pdsa-grapher.{ext}") for lang in languages for ext in ["po", "mo"]
    ]) and all([  # ar MO nepasenę
        os.path.getmtime(f"locale/{lang}/LC_MESSAGES/pdsa-grapher.mo") >=
        os.path.getmtime(f"locale/{lang}/LC_MESSAGES/pdsa-grapher.po") for lang in languages
    ]):
        # Visi MO vertimai yra naujausi, nereikia atnaujinti jokių vertimo rinkmenų
        return

    # Pradiniame kode paprastai kompiliuotieji MO nėra pateikiami - jie pateikiami platinamoje programoje.
    # Jei jų nebuvo arba pasenę - pirmą kartą paleidžiant programą vertimai sukompiliuosimi automatiškai
    from locale_utils import translation_files_update as tu  # importuoti tik pagal poreikį, tad rašau ne viršuje
    if all([
        os.path.exists(f"locale/{lang}/LC_MESSAGES/pdsa-grapher.po") for lang in languages
    ]):
        # Vertimų MO nėra, bet yra PO - užtenka tik perkompiliuoti MO (POT ir PO nėra atnaujinami).
        # Tai jei pravers, jei naudotojas rankiniu būdu redagavo PO vertimų rinkmenas (ir ištrynė MO perkompiliavimui)
        tu.recompile_all_po(app_name="pdsa-grapher")
    else:
        # Sukurti visas reikalingas POT, PO, MO vertimų rinkmenas iš naujo
        tu.Pot(app_name="pdsa-grapher", languages=languages, force_regenerate=True)