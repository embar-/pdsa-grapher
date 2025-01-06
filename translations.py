"""
Dinamiškas programos vertimų, esančių MO rinkmenose, pasiekimas naudojant gettext sintaksę.
Vertimai gaunami kviečiant funkcijas „_()“ ir, jei reikia atsižvelgti į kontekstą, su „pgettext()“.
"""

from gettext import translation


def set_gettext_locale(lang="lt"):
    # gettex naudojamos kalbos atnaujinimas, kuris diegiamas globaliai naudojimui su _()
    lang_trans = translation("pdsa-grapher", 'locale', languages=[lang])
    lang_trans.install()
    return lang_trans


# Apsirašyti savo pgettext vietoj gettext.pgettext, nes jo neatnaujina gettext .install()
def pgettext(context, message):
    """
    Pranešimo vertimas atsižvelgiant į pranešimo kontekstas. Daro tą patį kaip gettext.pgettext,
    tačiau pastarasis netinka tuomet, kai keičiame kalbas programos viduje.
    :param context: prašimo kontekstas
    :param message: pranešimas
    :return: išverstas tekstas
    """
    return _(f"{context}\x04{message}")
