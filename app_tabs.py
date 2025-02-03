"""
PDSA grapher Dash app allows you to display and filter relationships between
tables in your database, as well as display the metadata of those tables.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import os
import pandas as pd
import dash
from dash import (
    dcc, html, Output, Input, callback, dash_table, callback_context, State,
)
import dash_bootstrap_components as dbc
from grapher_lib import utils as gu
from grapher_lib import utils_tabs_layouts as uw
from locale_utils.translations import refresh_gettext_locale
import logging
from flask import Flask


# ========================================
# Pradinė konfigūracija
# ========================================

# Rodyti tik svarbius pranešimus. Neteršti komandų lango gausiais užrašais kaip "GET /_reload-hash HTTP/1.1" 200
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Pandas parinktys
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


# ========================================
# Kalbos
# ========================================

# Kalbas reikia nustatyti prieš pradedant kurti dash programą tam, kad programos užrašus iš karto būtų galima būtų
# iš karto sudėlioti numatytąja norima kalba. Keičiant kalbą visa programos struktūra būtų perkuriama iš naujo.
LANGUAGES = {  # globalus kintamasis, jį naudos update_language()
    "en": "English",
    "lt": "Lietuvių"
}
refresh_gettext_locale()


# ========================================
# Išdėstymas
# ========================================

# Kortelės
def tab_layout():
    """Kortelės: 1) rinkmenų įkėlimui; 2) grafikams"""
    return [
        dbc.Tab(uw.file_uploading_tab_layout(), tab_id="file_upload", label=_("File upload")),
        dbc.Tab(uw.grapher_tab_layout(), tab_id="graph", label=_("Graphic")),
    ]


# Visuma
def app_layout():
    """Visuminis programos išdėstymas, apimantis korteles iš tab_layout() ir kalbos pasirinkimą"""
    return html.Div(
        style={"marginTop": "20px", "marginLeft": "20px", "marginRight": "20px"},
        children=[
            html.Div(id="blank-output", title="Dash"),  # Laikina reikšmė, vėliau keičiama pagal kalbą
            dbc.DropdownMenu(
                label="🌐",
                children=[
                    dbc.DropdownMenuItem(LANGUAGES[lang], id=lang, n_clicks=0)
                    for lang in LANGUAGES
                ],
                id="language-dropdown",
                style={"float": "right"},
                color="secondary"
            ),
            dbc.Tabs(
                children=tab_layout(),  # bus vėl keičiamas per update_language()
                id="tabs-container"
            ),

            # dcc.Store() gali turėti tokias "storage_type" reikšmes:
            # - "memory": dingsta atnaujinus puslapį arba uždarius naršyklę
            # - "session": dingsta uždarius naršyklės kortelę
            # - "local":  išsilaiko iš naujo atidarius puslapį ir net uždarius ir iš naujo atidarius naršyklę
            # Deja, pastararosios dvi ne visada veikia, tad reikia nepersistengti, pvz:
            #   Failed to execute 'setItem' on 'Storage': Setting the value of 'memory-uploaded-pdsa-plus' exceeded the quota.
            #   QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the value of 'memory-submitted-data' exceeded the quota.
            dcc.Store(id="memory-uploaded-pdsa-init", storage_type="session"),  # žodynas su PDSA duomenimis (pradinis)
            dcc.Store(id="memory-uploaded-pdsa-plus", storage_type="memory"),  # žodynas su PDSA duomenimis (papildytas)
            dcc.Store(id="memory-uploaded-refs", storage_type="session"),  # žodynas su ryšių tarp lentelių duomenimis
            dcc.Store(id="memory-submitted-data", storage_type="memory"),  # Rinkmenų kortelėje patvirtinti duomenys
            dcc.Store(id="memory-filtered-data", storage_type="memory"),
        ],
    )


# ========================================
# Interaktyvumai bendrieji, t.y. nepriklausomai nuo kortelės
# ========================================

# Kalba
@callback(
    Output("language-dropdown", "label"),  # užrašas ties kalbos pasirinkimu
    Output("tabs-container", "children"),  # perkurta kortelių struktūra naująja kalba
    Output("blank-output", "title"),  # nematoma, bet jį panaudos dash.clientside_callback() antraštei keisti
    # Reikalingi funkcijos paleidikliai, pati jų reikšmė nenaudojama
    Input("en", "n_clicks"),
    Input("lt", "n_clicks")
)
def update_language(en_clicks, lt_clicks):  # noqa
    """
    Kalbos perjungimas. Perjungiant kalbą programa tarsi paleidžiama iš naujo.
    Ateityje paieškoti būdų pakeisti kalbą neprarandant naudotojo darbo.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        language = "lt"  # numatytoji lietuvių kalba; arba galite naudoti locale.getlocale()[0]
    else:
        language = ctx.triggered[0]["prop_id"].split(".")[0]

    with app.server.test_request_context():
        refresh_gettext_locale(language)
        print(_("Language set to:"), LANGUAGES[language], language)
        return (
            "🌐 " + language.upper(),
            tab_layout(),
            _("PDSA grapher")
        )


# Naršyklės antraštės pakeitimas pasikeitus kalbai
dash.clientside_callback(
    """
    function(title) {
            document.title = title;
    }
    """,
    Output("blank-output", "children"),
    Input("blank-output", "title"),
)


# ========================================
# Interaktyvumai rinkmenų pasirinkimo kortelėje
# ========================================

# PDSA
@callback(
    Output("memory-uploaded-pdsa-init", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    Output("pdsa-file-name", "children"),  # pasirinktos PDSA rinkmenos vardas
    Input("upload-data", "contents"),  # kas paduota
    State("upload-data", "filename"),  # pasirinktos(-ų) rinkmenos(-ų) vardas(-ai)
    State("memory-uploaded-pdsa-init", "data"),  # žodynas su pdsa duomenimis
)
def update_pdsa_memory(uploaded_content, list_of_names, pdsa_dict):
    """
    PDSA rinkmenos įkėlimas.
    Teoriškai galima paduoti kelis, bet praktiškai visada imama pirmoji rinkmena.
    :param uploaded_content: įkeltų XLSX arba CSV rinkmenų turinys sąrašo pavidalu, kur
        vienas elementas – vienos rinkmenos base64 turinys.
    :param list_of_names: įkeltų XLSX arba CSV rinkmenų vardų sąrašas.
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :return: naujas refs_dict
    """
    if uploaded_content is not None:
        parse_output = gu.parse_file(uploaded_content)
        if type(parse_output) == str:
            # Klaida nuskaitant
            return {}, [list_of_names[0], html.Br(), parse_output]
        else:
            # Sėkmingai į įkelti nauji duomenys
            return parse_output, list_of_names[0]
    elif isinstance(pdsa_dict, dict) and pdsa_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        return pdsa_dict, ""
    else:
        return {}, ""


# Ryšiai tarp lentelių
@callback(
    Output("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Output("uzklausa-file-name", "children"),
    Input("upload-data-uzklausa", "contents"),
    State("upload-data-uzklausa", "filename"),
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
)
def update_refs_memory(uploaded_content, list_of_names, refs_dict):
    """
    Ryšių (pvz., sql_2_references.xlsx) rinkmenos įkėlimas.
    Teoriškai galima paduoti kelis, bet praktiškai visada imama pirmoji rinkmena.
    :param uploaded_content: įkeltų XLSX arba CSV rinkmenų turinys sąrašo pavidalu, kur
        vienas elementas – vienos rinkmenos base64 turinys.
    :param list_of_names: įkeltų XLSX arba CSV rinkmenų vardų sąrašas.
    :param refs_dict: žodynas su ryšių tarp lentelių duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :return: naujas refs_dict
    """
    if uploaded_content is not None:
        parse_output = gu.parse_file(uploaded_content)
        if isinstance(parse_output, str):
            # Klaida nuskaitant
            return {}, [list_of_names[0], html.Br(), parse_output]
        else:
            # Sėkmingai į įkelti nauji duomenys
            return parse_output, list_of_names[0]
    elif isinstance(refs_dict, dict) and refs_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        return refs_dict, ""
    else:
        # nieko naujo neįkelta, nėra senų; greičiausiai darbo pradžia
        return {}, ""


# PDSA
@callback(
    Output("radio-sheet-tbl", "options"),
    Output("radio-sheet-tbl", "value"),
    Output("radio-sheet-col", "options"),
    Output("radio-sheet-col", "value"),
    Input("memory-uploaded-pdsa-init", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
)
def get_data_about_xlsx(xlsx_data):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą PDSA dokumentą.
    :param xlsx_data: nuskaitytas pasirinktos PDSA rinkmenos turinys
    """
    if isinstance(xlsx_data, dict) and "file_data" in xlsx_data:
        sheet_names = list(xlsx_data["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheet_names]

        # Automatiškai žymėti numatytuosius lakštus, jei jie yra
        preselect_tbl_sheet = "tables" if ("tables" in sheet_names) else None
        preselect_col_sheet = "columns" if ("columns" in sheet_names) else None

        return sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        return [], None, [], None


# Ryšiai tarp lentelių
@callback(
    Output("ref-source-tables", "options"),
    Output("ref-source-tables", "value"),
    Output("ref-source-columns", "options"),
    Output("ref-source-columns", "value"),
    Output("ref-target-tables", "options"),
    Output("ref-target-tables", "value"),
    Output("ref-target-columns", "options"),
    Output("ref-target-columns", "value"),
    Output("uzklausa-tbl-preview", "children"),
    Input("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
)
def get_dropdowns_and_preview_source_target(uzklausa_data):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą ryšių dokumentą.
    :param uzklausa_data: nuskaitytas pasirinktos ryšių XLSX ar CSV rinkmenos turinys
    :return:
    """
    # Jei uzklausa_data yra None arba tuščias - dar neįkelta; jei string – įkėlimo klaida
    if (
            isinstance(uzklausa_data, dict) and
            ("file_data" in uzklausa_data)
    ):
        sheet_name = list(uzklausa_data["file_data"].keys())[0]
        uzklausa_columns = uzklausa_data["file_data"][sheet_name]["df_columns"]
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios IŠORINIUS raktus
        preselected_source_tables = next(
            (
                col for col in
                ["TABLE_NAME", "table_name", "table", "Iš_lentelės", "Iš lentelės"]
                if col in uzklausa_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip IŠORINIAI raktai
        preselected_source_columns = next(
            (
                col for col in
                ["COLUMN_NAME", "column_name", "column", "Iš_stulpelio", "Iš stulpelio"]
                if col in uzklausa_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios PIRMINIUS raktus
        preselected_target_tables = next(
            (
                col for col in
                ["REFERENCED_TABLE_NAME", "referenced_table_name", "referenced_table", "Į_lentelę", "Į lentelę"]
                if col in uzklausa_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip PIRMINIAI raktai
        preselected_target_columns = next(
            (
                col for col in
                ["REFERENCED_COLUMN_NAME", "referenced_column_name", "referenced_column", "Į_stulpelį", "Į stulpelį"]
                if col in uzklausa_columns
             ), None
        )

        df = uzklausa_data["file_data"][sheet_name]["df"][0:10]

        children_df_tbl = dash_table.DataTable(
            df,
            [{"name": i, "id": i} for i in uzklausa_columns],
            style_table={"overflowX": "scroll"},
        )

        return (
            uzklausa_columns, preselected_source_tables,
            uzklausa_columns, preselected_source_columns,
            uzklausa_columns, preselected_target_tables,
            uzklausa_columns, preselected_target_columns,
            children_df_tbl
        )
    else:
        return [], None, [], None, [], None, [], None, dash_table.DataTable(style_table={"overflowX": "scroll"})

# PDSA
@callback(
    Output("memory-uploaded-pdsa-plus", "data"),  # žodynas su PDSA duomenimis, papildytas
    Input("memory-uploaded-pdsa-init", "data"),  # žodynas su PDSA duomenimis, pradinis
    Input("radio-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),
    config_prevent_initial_callbacks=True,
)
def store_sheet_names_and_columns(pdsa_dict, sheet_name_tbl, sheet_name_col):
    """
    Papildyti žodyną su PDSA duomenimis naudotojo (ar sistemos) pa(si)rinktais lakštų vardais
    :param pdsa_dict: žodynas su PDSA duomenimis, pradinis (be lakštų vardų)
    :param sheet_name_tbl: PDSA lentelių lakštas
    :param sheet_name_col: PDSA stulpelių lakštas
    :return:
    """
    pdsa_dict["sheet_tbl"] = sheet_name_tbl
    pdsa_dict["sheet_col"] = sheet_name_col
    return pdsa_dict


# PDSA
@callback(
    Output("id-sheet-tbl", "children"),
    Output("dropdown-sheet-tbl", "options"),
    Output("dropdown-sheet-tbl", "value"),
    Input("memory-uploaded-pdsa-plus", "data"),  # žodynas su PDSA duomenimis, papildytas
)
def create_pdsa_tables_sheet_column_dropdowns(pdsa_dict):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius norite pasilikti švieslentėje
    """
    sheet, columns = gu.create_pdsa_sheet_column_dropdowns(pdsa_dict, "sheet_tbl")
    return sheet, columns, columns


# PDSA
@callback(
    Output("id-sheet-col", "children"),
    Output("dropdown-sheet-col", "options"),
    Output("dropdown-sheet-col", "value"),
    Input("memory-uploaded-pdsa-plus", "data"),
)
def create_pdsa_columns_sheet_column_dropdowns(pdsa_dict):
    """
    Sukurti pasirinkimus, kuriuos PDSA stulpelių lakšto stulpelius norite pasilikti švieslentėje
    """
    sheet, columns = gu.create_pdsa_sheet_column_dropdowns(pdsa_dict, "sheet_col")
    return sheet, columns, columns


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Input("memory-uploaded-pdsa-plus", "data"),
    Input("dropdown-sheet-tbl", "value"),
)
def create_preview_of_pdsa_tbl_sheet(xlsx_data, sheet_tbl_selection):
    """
    PDSA lakšto apie lenteles peržiūra
    """
    if not xlsx_data or not sheet_tbl_selection:
        return dash_table.DataTable()
    sheet_tbl = xlsx_data["sheet_tbl"]
    df_tbl = xlsx_data["file_data"][sheet_tbl]["df"][0:10]
    children_df_tbl = dash_table.DataTable(
        df_tbl,
        [{"name": i, "id": i} for i in sheet_tbl_selection],
        style_table={"overflowX": "scroll"},
    )
    return children_df_tbl


# PDSA
@callback(
    Output("sheet-col-preview", "children"),
    Input("memory-uploaded-pdsa-plus", "data"),
    Input("dropdown-sheet-col", "value"),
)
def create_preview_of_pdsa_col_sheet(xlsx_data, sheet_col_selection):
    """
    PDSA lakšto apie stulpelius peržiūra
    """
    if not xlsx_data or not sheet_col_selection:
        return dash_table.DataTable()
    sheet_col = xlsx_data["sheet_col"]
    df_col = xlsx_data["file_data"][sheet_col]["df"][0:10]
    children_df_col = dash_table.DataTable(
        df_col,
        [{"name": i, "id": i} for i in sheet_col_selection],
        style_table={"overflowX": "scroll"},
    )
    return children_df_col


# PDSA ir ryšiai tarp lentelių
@callback(
    Output("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Output("button-submit", "color"),  # pateikimo mygtuko spalva
    Output("submit-error-message", "children"),  # pateikimo klaidos paaiškinimas
    Output("submit-warning-message", "children"),  # pateikimo įspėjimo paaiškinimas
    Output("tabs-container", "active_tab"),  # aktyvios kortelės identifikatorius (perjungimui, jei reikia)
    State("memory-uploaded-pdsa-plus", "data"),  # žodynas su PDSA duomenimis, papildytas
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Input("dropdown-sheet-tbl", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("ref-source-tables", "value"),
    Input("ref-source-columns", "value"),
    Input("ref-target-tables", "value"),
    Input("ref-target-columns", "value"),
    State("tabs-container", "active_tab"),
    Input("button-submit", "n_clicks"),  # tik kaip f-jos paleidiklis paspaudžiant Pateikti
)
def summarize_submission(
    pdsa_file_data,
    refs_file_data,
    dropdown_sheet_tbl,
    dropdown_sheet_col,
    ref_source_tbl,
    ref_source_col,
    ref_target_tbl,
    ref_target_col,
    active_tab,
    submit_clicks,  # noqa
):
    """
    Suformuoti visuminę naudingų duomenų struktūrą, jei turime visus reikalingus PDSA ir ryšių duomenis.
    :param pdsa_file_data: žodynas su PDSA duomenimis:
        "file_data" - žodynas su visu PDSA turiniu;
        "sheet_tbl" - PDSA lakšto, aprašančio lenteles, pavadinimas
        "sheet_col" - PDSA lakšto, aprašančio stulpelius, pavadinimas
    :param refs_file_data: žodynas su ryšių tarp lentelių duomenimis:
        "file_data" - žodynas su visu dokumento turiniu;
    :param dropdown_sheet_tbl: sąrašas stulpelių, kurie yra pdsa_info["sheet_tbl"] (lentelių) lakšte
    :param dropdown_sheet_col: sąrašas stulpelių, kurie yra pdsa_info["sheet_col"] (stulpelių) lakšte
    :param ref_source_tbl: vardas stulpelio, kuriame surašytos ryšio pradžių („IŠ“) lentelės (su išoriniu raktu)
    :param ref_source_col: vardas stulpelio, kuriame surašyti ryšio pradžių („IŠ“) stulpeliai (su išoriniu raktu)
    :param ref_target_tbl: vardas stulpelio, kuriame surašytos ryšio galų („Į“) lentelės (su pirminiu raktu)
    :param ref_target_col: vardas stulpelio, kuriame surašyti ryšio galų („Į“) stulpeliai (su pirminiu raktu)
    :param submit_clicks: mygtuko „Pateikti“ paspaudimų skaičius, bet pati reikšmė nenaudojama
    :param active_tab: aktyvi kortelė "file_upload" arba "graph"
    :return: visų pagrindinių duomenų struktūra, pateikimo mygtuko spalva, paaiškinimai naudotojui, aktyvi kortelė.

    visų naudingų duomenų struktūros pavyzdys:
        data_final = {
            "node_data": {  # Mazgų duomenys iš PDSA
                 "tbl_sheet_data": {  # PDSA lakšto, aprašančio lenteles, turinys
                     "df_columns": [],
                     "df": [],
                },
                 "col_sheet_data": {
                     "df_columns": [],
                     "df": [],
                },
                "sheet_tbl": "",  # PDSA lakšto, aprašančio lenteles, pavadinimas
                "sheet_col": "",  # PDSA lakšto, aprašančio stulpelius, pavadinimas
                "list_tbl_tables": [],  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
                "list_col_tables": [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
                "list_all_tables": [],  # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
            },
            "edge_data":{  # Ryšiai
                "ref_sheet_data": {
                    "df_columns": [],
                    "df": [],
                },
                "ref_source_tbl":"",  # vardas stulpelio, kuriame surašytos ryšio pradžių („IŠ“) lentelės (su išoriniu raktu)
                "ref_source_col": "",  # vardas stulpelio, kuriame surašyti ryšio pradžių („IŠ“) stulpeliai (su išoriniu raktu)
                "ref_target_tbl":"",  # vardas stulpelio, kuriame surašytos ryšio galų („Į“) lentelės (su pirminiu raktu)
                "ref_target_col": "",  # vardas stulpelio, kuriame surašyti ryšio galų („Į“) stulpeliai (su pirminiu raktu)
                "list_all_tables": [],  # tos lentelės, kurios panaudotos ryšiuose
            }}
    """

    # Tikrinimai
    err_msg = []  # Klaidų sąrašas, rodomas po „Pateikimo“ mygtuku raudonai
    wrn_msg = []  # Įspėjimų sąrašas, rodomas po „Pateikimo“ mygtuku rudai
    if (pdsa_file_data is None) or None in (pdsa_file_data["sheet_tbl"], pdsa_file_data["sheet_col"]):
        err_msg.append(html.P(_("Please select PDSA document and its sheets!")))
    if not refs_file_data:
        err_msg.append(html.P(_("Please select references document!")))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"

    if None in (dropdown_sheet_tbl, dropdown_sheet_col):
        err_msg.append(html.P(_("Invalid choices!")))
    if None in (ref_source_tbl, ref_target_tbl):
        err_msg.append(html.P(_("Please select references columns that contain tables!")))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"

    # Surinktą informaciją transformuoju ir paruošiu graferiui
    sheet_tbl = pdsa_file_data["sheet_tbl"]
    sheet_col = pdsa_file_data["sheet_col"]
    if sheet_tbl == sheet_col:
        err_msg.append(html.P(_("Please select different PDSA sheets for tables and columns!")))
        return {}, "secondary", err_msg, wrn_msg, "file_upload"

    # PDSA lakšto (sheet_tbl), aprašančio lenteles, turinys
    df_tbl = pdsa_file_data["file_data"][sheet_tbl]["df"]
    df_tbl = pd.DataFrame.from_records(df_tbl)
    if (
        "lenteles_paaiskinimas"
        in pdsa_file_data["file_data"][sheet_tbl]["df_columns"]
    ):
        df_tbl = df_tbl.sort_values(by="lenteles_paaiskinimas")
    dropdown_sheet_tbl = [x for x in dropdown_sheet_tbl if x in df_tbl]  # paprastai to nereikia, bet apsidrausti, jei kartais būtų paimta iš sesijos atminties
    df_tbl = df_tbl.loc[:, dropdown_sheet_tbl]
    # PDSA lakšte (sheet_tbl) privalomi ir rekomenduojami stulpeliai
    if "table" not in df_tbl.columns:
        # Nėra "table" stulpelio, kuris yra privalomas
        err_msg.append(html.P(
            _("PDSA sheet '%s' must have column '%s'!") % (sheet_tbl, "table")
        ))
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    if "comment" not in df_tbl.columns:
        wrn_msg.append(html.P(
            _("In the PDSA sheet '%s', expected to find column '%s', but it's not a problem.") % (sheet_tbl, "comment")
        ))

    # PDSA lakšto (sheet_col), aprašančio stulpelius, turinys
    df_col = pdsa_file_data["file_data"][sheet_col]["df"]
    df_col = pd.DataFrame.from_records(df_col)
    df_col = df_col.dropna(how="all")
    dropdown_sheet_col = [x for x in dropdown_sheet_col if x in df_col]  # paprastai to nereikia, bet apsidrausti, jei kartais būtų paimta iš sesijos atminties
    df_col = df_col.loc[:, dropdown_sheet_col]
    if "table" not in df_col.columns:
        pdsa_col_tables = None
        wrn_msg.append(html.P(
            _("In the PDSA sheet '%s', expected to find column '%s', but it's not a problem.") % (sheet_col, "table")
        ))
    else:
        pdsa_col_tables = df_col["table"].dropna().drop_duplicates().sort_values().tolist()
    for col in ["column", "comment"]:
        if col not in df_col.columns:
            wrn_msg.append(html.P(
                _("In the PDSA sheet '%s', expected to find column '%s', but it's not a problem.") % (sheet_col, col)
            ))

    # Sukurti ryšių pd.DataFrame tinklo piešimui
    sheet_uzklausa = list(refs_file_data["file_data"].keys())[0]  # ryšių lakšto pavadinimas
    df_edges = refs_file_data["file_data"][sheet_uzklausa]["df"]
    df_edges = pd.DataFrame.from_records(df_edges)
    if None in [ref_source_col, ref_target_col]:
        # ref_source_col ir ref_target_col stulpeliai nėra privalomi, tad kurti tuščią, jei jų nėra
        df_edges[" "] = None
    df_edges = df_edges.loc[
       :, [ref_source_tbl, ref_source_col or " ", ref_target_tbl, ref_target_col or " "]
    ]
    if df_edges.empty:
        wrn_msg.append(html.P(_("There are no relationships between different tables!")))
    # Pervadinti stulpelius į toliau viduje sistemiškai naudojamus
    df_edges.columns = ["source_tbl", "source_col", "target_tbl", "target_col"]
    # Išmesti lentelių nuorodas į save (bet iš tiesų pasitaiko nuorodų į kitą tos pačios lentelės stulpelį)
    df_edges = df_edges.loc[df_edges["source_tbl"] != df_edges["target_tbl"], :]

    # Visų lentelių, esančių lentelių aprašo lakšte, sąrašas
    pdsa_tbl_tables = df_tbl["table"].dropna().tolist()
    pdsa_tbl_tables = sorted(list(set(pdsa_tbl_tables)))
    if not pdsa_tbl_tables:
        warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (sheet_tbl, "table")
        wrn_msg.append(html.P(warning_str))

    # Sutikrinimas tarp sheet_tbl ir sheet_col „table“ stulpelių
    if pdsa_col_tables is not None:
        tables_diff = list(set(pdsa_tbl_tables) - (set(pdsa_col_tables) & set(pdsa_tbl_tables)))
        if tables_diff:
            # Smulkesniuose stulpelių aprašymuose kai kuriuose PDSA būna daugiau lentelių -
            # paprastai tai rodiniai (views) ir į šį įspėjimą galima nekreipti dėmesio
            warning_str = _(
                "PDSA sheet '%s' column '%s' has some tables (%d in total) not present in sheet '%s' column '%s', but it's not a problem:"
            )
            warning_str = warning_str % (sheet_tbl, "table", len(tables_diff), sheet_col, "table")
            warning_str += " " + ", ".join(tables_diff) + "."
            wrn_msg.append(html.P(warning_str))

    # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
    pdsa_all_tables = sorted(list(set(pdsa_col_tables or []) | set(pdsa_tbl_tables)))

    # Visų unikalių lentelių, turinčių ryšių, sąrašas
    edge_tables = sorted(list(set(
        df_edges["source_tbl"].dropna().tolist() +
        df_edges["target_tbl"].dropna().tolist()
    )))
    edge_tables_extra = list(set(edge_tables) - set(pdsa_all_tables))
    if edge_tables_extra:
        warning_str = _("References contain some tables (%d) that are not present in the defined tables:")
        warning_str = warning_str % len(edge_tables_extra)
        warning_str += " " + ", ".join(edge_tables_extra) + "."
        wrn_msg.append(html.P(warning_str))
        ## Lentelės, tik esančios PDSA dokumente:
        # df_edges = df_edges.loc[
        #            df_edges["source_tbl"].isin(pdsa_all_tables) & df_edges["target_tbl"].isin(pdsa_all_tables), :
        #            ]
    # Paprastai neturėtų būti pasikartojančių ryšių, nebent nebuvo nurodyti ryšių stulpeliai apie DB lentelės stulpelius
    df_edges = df_edges.drop_duplicates()

    # %% VISĄ SURINKTĄ INFORMACIJĄ SUKELIU Į VIENĄ STRUKTŪRĄ
    data_final = {
        # Mazgų duomenys iš PDSA
        "node_data": {
            "tbl_sheet_data": {  # PDSA lakšto, aprašančio lenteles,
                "df_columns": list(df_tbl.columns),
                "df": df_tbl.to_dict("records"),
            },
            "col_sheet_data": {
                "df_columns": list(df_col.columns),
                "df": df_col.to_dict("records"),
            },
            "sheet_tbl": sheet_tbl,  # PDSA lakšto, aprašančio lenteles, pavadinimas
            "sheet_col": sheet_col,  # PDSA lakšto, aprašančio stulpelius, pavadinimas
            "list_tbl_tables": pdsa_tbl_tables,  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
            "list_col_tables": pdsa_col_tables or [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
            "list_all_tables": pdsa_all_tables,  # visos iš PDSA kartu
        },
        # Ryšių duomenys
        "edge_data": {
            "ref_sheet_data": {
                "df_columns": list(df_edges.columns),
                "df": df_edges.to_dict("records"),
            },
            "ref_source_tbl": ref_source_tbl,  # stulpelis, kuriame pradžių („IŠ“) lentelės
            "ref_source_col": ref_source_col,  # stulpelis, kuriame pradžių („IŠ“) stulpeliai
            "ref_target_tbl": ref_target_tbl,  # stulpelis, kuriame galų („Į“) lentelės
            "ref_target_col": ref_target_col,  # stulpelis, kuriame galų („Į“) stulpeliai
            "list_all_tables": edge_tables,  # lentelės, kurios panaudotos ryšiuose
        }
    }

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“, „Braižyti visas“ (jei paspaustas)
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    if "button-submit" in changed_id:  # Paspaustas „Pateikti“ mygtukas
        # Perduoti duomenis naudojimui grafiko kortelėje ir į ją pereiti
        active_tab = "graph"
    else:
        # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje.
        # active_tab gali neturėti reikšmės darbo pradžioje ar pakeitus kalbą. Tai padeda išlaikyti kortelę
        active_tab = active_tab or "file_upload"  # jei nėra, pereiti į rinkmenų įkėlimą;
    return data_final, "primary", err_msg, wrn_msg, active_tab


# ========================================
# Interaktyvumai grafiko kortelėje
# ========================================

@callback(
    Output("filter-tbl-in-df", "options"),  # išskleidžiamojo sąrašo pasirinkimai
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
)
def get_dropdown_tables_info_col_display_options(data_submitted):
    """
    Informacija apie pasirinktų lentelių stulpelius - išskleidžiamasis sąrašas
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :return: visų galimų lentelių sąrašas
    """
    if data_submitted:
        # Lentelės iš PDSA, gali apimti rodinius ir nebūtinai turinčios ryšių
        return data_submitted["node_data"]["list_all_tables"]
    else:
        return []


@callback(
    Output("dropdown-tables", "options"),  # galimos pasirinkti braižymui lentelės
    Output("dropdown-tables", "value"),  # automatiškai braižymui parinktos lentelės (iki 10)
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    # tik kaip paleidikliai įkeliant lenteles:
    Input("draw-tables-refs", "n_clicks"),  # Susijungiančios pagal ryšių dokumentą
    Input("draw-tables-pdsa", "n_clicks"),  # Pagal PDSA lentelių lakštą
    Input("draw-tables-all", "n_clicks"),  # Visos visos
    Input("draw-tables-auto", "n_clicks"),  # Automatiškai parinkti
)
def set_dropdown_tables(
    data_submitted,
    *args,  # noqa
):
    """
    Nustatyti galimus pasirinkimus braižytinoms lentelėms.
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data"), žr. f-ją `summarize_submission`
    :return: "dropdown-tables" galimų pasirinkimų sąrašas ir iš anksto parinktos reikšmės
    """
    # Tikrinimas
    if not data_submitted:
        return [], []

    # Galimos lentelės
    tables_pdsa_real = data_submitted["node_data"]["list_tbl_tables"]  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
    tables_pdsa = data_submitted["node_data"]["list_all_tables"]  # lyginant su pdsa_tbl_tables, papildomai gali turėti rodinių (views) lenteles
    tables_refs = data_submitted["edge_data"]["list_all_tables"]  # lentelės, kurios panaudotos ryšiuose
    # Visų visų lentelių sąrašas - tiek iš PDSA, tiek iš ryšių dokumento
    tables_all = sorted(list(set(tables_pdsa) | set(tables_refs)))

    # Ryšiai
    df_edges = pd.DataFrame(data_submitted["edge_data"]["ref_sheet_data"]["df"])

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“, „Braižyti visas“ (jei paspaustas)
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    # Pagal naudotojo pasirinkkimą arba automatiškai žymėti lenteles piešimui.
    # Atsižvelgimas į naudotojo pasirinkimus turi būti išdėstytas aukščiau nei automatiniai
    if "draw-tables-all" in changed_id:
        # visos visos lentelės
        preselected_tables = tables_all
    elif "draw-tables-pdsa" in changed_id:
        # braižyti visas, apibrėžtas lentelių lakšte (gali neįtraukti rodinių)
        preselected_tables = tables_pdsa_real
    elif (
        ("draw-tables-refs" in changed_id) or
        (len(tables_refs) <= 10)  # jei iš viso ryšius turinčių lentelių iki 10
    ):
        # susijungiančios lentelės. Netinka imti tiesiog `tables_refs`, nes tarp jų gai būti nuorodos į save
        df_edges2 = df_edges[df_edges["source_tbl"] != df_edges["target_tbl"]]
        preselected_tables = pd.concat([df_edges2["source_tbl"], df_edges2["target_tbl"]]).to_list()
    elif len(tables_pdsa_real) <= 10:  # jei iš viso PDSA lentelių iki 10
        # braižyti visas, apibrėžtas lentelių lakšte (gali neįtraukti rodinių)
        preselected_tables = tables_pdsa_real
    elif df_edges.empty:
        # Paprastai neturėtų taip būti
        preselected_tables = []
    else:
        # iki 10 populiariausių lentelių tarpusavio ryšiuose; nebūtinai tarpusavyje susijungiančios
        # ryšių su lentele dažnis mažėjančia tvarka
        table_links_n = pd.concat([df_edges["source_tbl"], df_edges["target_tbl"]]).value_counts()
        if table_links_n.iloc[9] < table_links_n.iloc[10]:
            preselected_tables = table_links_n.index[:10].to_list()
        else:
            table_links_n_threshold = table_links_n.iloc[9] + 1
            preselected_tables = table_links_n[table_links_n >= table_links_n_threshold].index.to_list()
        # Pašalinti mazgus, kurie neturi tarpusavio ryšių su parinktaisiais
        preselected_tables = gu.remove_orphaned_nodes_from_sublist(preselected_tables, df_edges)
        if not preselected_tables:  # jei netyčia nei vienas tarpusavyje nesijungia, imti du su daugiausia kt. ryšių
            preselected_tables = table_links_n.index[:2].to_list()

    # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje
    return tables_all, preselected_tables


@callback(
    Output("memory-filtered-data", "data"),
    Input("tabs-container", "active_tab"),
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Input("dropdown-tables", "value"),
    Input("input-list-tables", "value"),
    Input("checkbox-get-neighbours", "value"),
    Input("dropdown-neighbors", "value"),
)
def get_filtered_data_for_network(
    active_tab, data_submitted, selected_dropdown_tables, input_list_tables, get_neighbours, neighbours_type
):
    """
    Gauna visas pasirinktas lenteles kaip tinklo mazgus su jungtimis ir įrašo į atmintį.
    :param active_tab: aktyvi kortelė ("file_upload" arba "graph")
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param selected_dropdown_tables: išskleidžiamajame sąraše pasirinktos braižytinos lentelės
    :param input_list_tables: tekstiniame lauke surašytos papildomos braižytinos lentelės
    :param get_neighbours: ar rodyti kaimynus
    :param neighbours_type: kaimynystės tipas: "all" (visi), "source" (iš), "target" (į)
    """
    if (
            not data_submitted  # apskritai nėra įkeltų duomenų
            or active_tab != "graph"  # esame kitoje nei grafiko kortelėje
            or (not selected_dropdown_tables and not input_list_tables)  # įkelti, bet nepasirinkti
    ):
        return []

    # Visos galimos lentelės
    tables_pdsa = data_submitted["node_data"]["list_all_tables"]
    tables_refs = data_submitted["edge_data"]["list_all_tables"]
    tables_all = list(set(tables_pdsa) | set(tables_refs))

    # Imti lenteles, kurias pasirinko išskleidžiamame meniu
    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Prijungti lenteles, kurias įraše sąraše tekstiniu pavidalu
    if input_list_tables is not None:
        input_list_tables = [x.strip() for x in input_list_tables.split(",") if x.strip() in tables_all]
        selected_tables = list(set(selected_dropdown_tables + input_list_tables))
    else:
        selected_tables = selected_dropdown_tables

    # Ryšiai
    submitted_edge_data = data_submitted["edge_data"]["ref_sheet_data"]["df"]

    if not get_neighbours:
        # Langelis „Rodyti kaimynus“/„Get neighbours“ nenuspaustas, tad
        # atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
        neighbors = []
        selected_tables_and_neighbors = selected_tables
        df_edges = [
            x
            for x in submitted_edge_data
            if x["source_tbl"] in selected_tables
            and x["target_tbl"] in selected_tables
        ]
        df_edges = pd.DataFrame.from_records(df_edges)

    else:
        # Langelis „Rodyti kaimynus“/„Get neighbours“ nuspaustas,
        if neighbours_type == "source":
            # turime target, bet papildomai rodyti source
            df_edges = [
                x
                for x in submitted_edge_data
                if x["target_tbl"] in selected_tables
            ]
        elif neighbours_type == "target":
            # turime source, bet papildomai rodyti target
            df_edges = [
                x
                for x in submitted_edge_data
                if x["source_tbl"] in selected_tables
            ]
        else:  # visi kaimynai
            df_edges = [
                x
                for x in submitted_edge_data
                if x["source_tbl"] in selected_tables
                or x["target_tbl"] in selected_tables
            ]
        df_edges = pd.DataFrame.from_records(df_edges)
        if df_edges.empty:
            neighbors = []
            selected_tables_and_neighbors = selected_tables
        else:
            selected_tables_and_neighbors = list(set(
                    selected_tables +
                    df_edges["source_tbl"].unique().tolist() +
                    df_edges["target_tbl"].unique().tolist()
            ))
            neighbors = list(set(selected_tables_and_neighbors) - set(selected_tables))

    if df_edges.empty:
        df_edges = pd.DataFrame(columns=["source_tbl", "source_col", "target_tbl", "target_col"])
    return {
        "node_elements": selected_tables_and_neighbors,
        "node_neighbors": neighbors,
        "edge_elements": df_edges.to_dict("records"),  # df būtina paversti į žodyno/JSON tipą, antraip Dash nulūš
    }


@callback(
    Output("cyto-chart", "elements"),
    Input("memory-filtered-data", "data"),
    Input("cyto-chart", "tapNodeData"),
    Input("cyto-chart", "selectedNodeData"),
    State("cyto-chart", "elements"),
)
def get_cytoscape_network_chart(filtered_elements, tap_node_data, selected_nodes_data, current_elements):
    """
    Atvaizduoja visas pasirinktas lenteles kaip tinklo mazgus.
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param tap_node_data: paskutinio spragtelėto mazgo duomenys
    :param selected_nodes_data: pažymėtų (pvz., apvestų) mazgų duomenys
    :param current_elements: dabartiniai Cytoscape elementai (mazgai ir ryšiai tarp jų)
    :return:
    """
    if not filtered_elements:
        return {}

    # Išsitraukti reikalingus kintamuosius
    df_edges = pd.DataFrame(filtered_elements["edge_elements"])  # ryšių lentelė
    nodes = filtered_elements["node_elements"]  # mazgai (įskaitant mazgus)
    neighbors = filtered_elements["node_neighbors"]  # kaimyninių mazgų sąrašas

    # Sukurti Cytoscape elementus
    new_elements = gu.get_fig_cytoscape_elements(
        nodes, df_edges, node_neighbors=neighbors
    )

    if selected_nodes_data and tap_node_data:
        tap_node_id = tap_node_data["id"]
        selected_nodes_id = [node["id"] for node in selected_nodes_data]
        if [tap_node_id] == selected_nodes_id:
            for element in new_elements:
                if "source" in element["data"]:
                    if element["data"]["source"] == tap_node_id:
                        element["classes"] = "source-neighbor"
                    elif element["data"]["target"] == tap_node_id:
                        element["classes"] = "target-neighbor"

    # Apjungti senus elementus su naujais - taip išvengsima mazgų perpiešimo iš naujo,
    # jų padėtys liks senos - mes to ir norime (ypač jei naudotojas ranka pertempė mazgus)
    updated_elements = []
    current_elements_map = {element["data"]["id"]: element for element in current_elements}
    for element in new_elements:
        elem_id = element["data"].get("id")
        if elem_id in current_elements_map:
            current_element = current_elements_map[elem_id]
            current_element["classes"] = element.get("classes", "")
            updated_elements.append(current_element)
        else:
            updated_elements.append(element)
    return updated_elements


@callback(
    Output("table-selected-tables", "children"),
    Input("memory-submitted-data", "data"),
    Input("filter-tbl-in-df", "value"),
)
def create_dash_table_from_selected_tbl(data_submitted, selected_dropdown_tables):
    """
    Parodo lentelę su informacija apie stulpelius iš PDSA  lakšto „columns“ priklausomai nuo naudotojo pasirinkimo
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param selected_dropdown_tables: išskleidžiamajame sąraše naudotojo pasirinktos lentelės
    :return: dash_table objektas
    """
    if not (data_submitted and selected_dropdown_tables):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["col_sheet_data"]["df"]
    df_col = pd.DataFrame.from_records(data_about_nodes)

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Jei prašoma rodyti informaciją apie pasirinktų lentelių stulpelius
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "filter-tbl-in-df.value" in changed_id:
        if "table" in df_col:
            df_col = df_col.loc[df_col["table"].isin(selected_dropdown_tables), :]

            dash_tbl = dash_table.DataTable(
                data=df_col.to_dict("records"),
                columns=[{"name": i, "id": i} for i in df_col.columns],
                sort_action="native",
                style_table={
                    'overflowX': 'auto'  # jei lentelė netelpa, galėti ją slinkti
                }
            )
            return dash_tbl
        return dash_table.DataTable()


@callback(
    Output("table-displayed-nodes", "children"),
    Input("memory-submitted-data", "data"),
    Input("checkbox-get-displayed-nodes-info-to-table", "value"),
    Input("cyto-chart", "elements"),
)
def create_dash_table_of_displayed_neighbours(data_submitted, get_displayed_nodes_info, elements):
    """
    Informacija apie grafike rodomas lenteles iš PDSA lakšto „tables“

    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param get_displayed_nodes_info: ar pateikti nubraižytų lentelių informaciją
    :param elements: grafiko duomenys
    :return: dash_table objektas
    """

    if (not data_submitted) or (not elements):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["tbl_sheet_data"]["df"]
    df_tbl = pd.DataFrame.from_records(data_about_nodes)
    if get_displayed_nodes_info and ("table" in df_tbl):
        # tinklo mazgai turi raktą "id" ir "label", bet jungimo linijos jų neturi (jos turi tik "source" ir "target")
        displayed_nodes = [x["data"]["id"] for x in elements if "id" in x["data"]]
        df_tbl = df_tbl.loc[df_tbl["table"].isin(displayed_nodes), :]

        dash_tbl = dash_table.DataTable(
            data=df_tbl.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_tbl.columns],
            sort_action="native",
        )
        return dash_tbl
    else:
        return dash_table.DataTable()


@callback(
    Output("cyto-chart", "layout"),
    Input("dropdown-layouts", "value"),
    State("cyto-chart", "layout"),
)
def update_cytoscape_layout(new_layout_name="cola", layout_dict=None):
    """
    Cytoscape grafiko išdėstymo parinkčių atnaujinimas.
    :param new_layout_name: naujas išdėstymo vardas
    :param layout_dict: cytoscape išdėstymo parinkčių žodynas
    :return:
    """
    if layout_dict is None:
        layout_dict = {"fit": True, "name": "cola"}
    if new_layout_name is not None:
        layout_dict["name"] = new_layout_name
    return layout_dict


@callback(
    Output("filter-tbl-in-df", "value"),
    Input("cyto-chart", "selectedNodeData"),
    State("filter-tbl-in-df", "value"),
    State("checkbox-get-selected-nodes-info-to-table", "value")
)
def get_selected_node_data(selected_nodes_data, selected_dropdown_tables, append_recently_selected):
    """
    Paspaudus tinklo mazgą, jį įtraukti į pasirinktųjų sąrašą informacijos apie PDSA stulpelius rodymui
    :param selected_dropdown_tables: šiuo metu išskleidžiamajame sąraše esantys grafiko mazgai/lentelės
    :param selected_nodes_data: grafike šiuo metu naudotojo pažymėti tinklo mazgų/lentelių duomenys.
    :param append_recently_selected: jei True - pažymėtuosius prideda prie pasirinkimų išskleidžiamajame meniu.
    :return: papildytas mazgų/lentelių sąrašas
    """
    if selected_nodes_data:
        selected_nodes_id = [node['id'] for node in selected_nodes_data]
        if append_recently_selected:
            return sorted(list(set(selected_dropdown_tables + selected_nodes_id)))
    return selected_dropdown_tables


@callback(
    Output("active-node-info", "show"),
    Output("active-node-info", "bbox"),
    Output("active-node-info-header", "children"),
    Output("active-node-info-content", "children"),
    Input("cyto-chart", "selectedNodeData"),
    Input("cyto-chart", "tapNode"),
    State("memory-submitted-data", "data"),
)
def display_tap_node_tooltip(selected_nodes_data, tap_node, data_submitted):
    """
    Iškylančiame debesėlyje parodo informaciją apie mazgą
    :param selected_nodes_data: pažymėtųjų mazgų duomenys
    :param tap_node: paskutinis spragtelėtas mazgas
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :return:
    """

    if selected_nodes_data:
        selected_nodes_id = [node["id"] for node in selected_nodes_data]
        if tap_node and tap_node["selected"] and [tap_node["data"]["id"]] == selected_nodes_id:
            # tap_node grąžina paskutinį buvusį paspaustą mazgą, net jei jis jau atžymėtas, tad tikrinti ir selected_node;
            # bet tap_node ir selected_node gali nesutapti apvedant (ne spragtelint); veikti tik jei abu sutampa.

            # %% Padėtis nematomo stačiakampio, į kurio krašto vidurį rodo debesėlio rodyklė
            node_position = tap_node['renderedPosition']
            bbox={
                "x0": node_position['x'] - 25,
                "y0": node_position['y'],
                "x1": node_position['x'] + 25,
                "y1": node_position['y'] + 150
            }

            # %% Antraštė
            node_label = tap_node["data"]["label"]
            tooltip_header = [html.H6(node_label)]
            data_about_nodes_tbl = data_submitted["node_data"]["tbl_sheet_data"]["df"]
            df_tbl = pd.DataFrame.from_records(data_about_nodes_tbl)
            if "table" in df_tbl:
                for comment_col in ["comment", "description"]:
                    if comment_col in df_tbl.columns:
                        table_comment = df_tbl[df_tbl["table"] == node_label][comment_col]
                        if not table_comment.empty:
                            tooltip_header.append(html.P(table_comment.iloc[0]))

            # %% Turinys
            content = []

            # Turinys: ryšiai
            submitted_edge_data = data_submitted["edge_data"]["ref_sheet_data"]["df"]
            displayed_tables_x = {x["source"] for x in tap_node["edgesData"]}
            displayed_tables_y = {y["target"] for y in tap_node["edgesData"]}
            # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
            dict_filtered = [
                x
                for x in submitted_edge_data
                if (x["source_tbl"] == node_label and x["target_tbl"] not in displayed_tables_y) or
                   (x["target_tbl"] == node_label and x["source_tbl"] not in displayed_tables_x)
            ]
            # tik unikalūs
            dict_filtered = [dict(t) for t in {tuple(d.items()) for d in dict_filtered}]
            if dict_filtered:
                # HTML lentelė
                content.extend([
                    html.Table(
                        children=[
                            html.Thead(html.Tr([html.Th(html.U(_("Not displayed relations:")))])),
                            html.Tbody(
                                children=[
                                    html.Tr([html.Td([row["source_tbl"], html.B(" -> "), row["target_tbl"]])])
                                    for row in dict_filtered
                                ]
                            )
                        ]
                    ),
                ])

            # Turinys: stulpeliai
            data_about_nodes_col = data_submitted["node_data"]["col_sheet_data"]["df"]
            df_col = pd.DataFrame.from_records(data_about_nodes_col)
            if all(col in df_col for col in ["table", "column"]):
                df_col = df_col[df_col["table"] == node_label]  # atsirinkti tik šios lentelės stulpelius
                if not df_col.empty:
                    table_rows = []  # čia kaupsim naujai kuriamus dash objektus apie stulpelius
                    for idx, row in df_col.iterrows():
                        table_row = ["- ", html.B(row["column"])]
                        if ("is_primary" in row) and pd.notna(row["is_primary"]) and row["is_primary"]:
                            table_row.append(" 🔑")  # pirminis raktas
                        for comment_col in ["comment", "description"]:
                            if (comment_col in row) and pd.notna(row[comment_col]) and row[comment_col].strip():
                                table_row.extend([" – ", row[comment_col]])  # paaiškinimas įprastuose PDSA
                                break
                        table_rows.append(html.Tr([html.Td(table_row)]))
                    if content and table_rows:
                        content.append(html.Hr())
                    content.append(
                            html.Table(
                            children=[
                                html.Thead(html.Tr([html.Th(html.U(_("Columns:")))])),
                                html.Tbody(table_rows)
                            ]
                        )
                    )

            if content:
                tooltip_header.append(html.Hr())

            return True, bbox, tooltip_header, content

    return False, None, [], []


@callback(
    Output("active-edge-info", "show"),
    Output("active-edge-info", "bbox"),
    Output("active-edge-info-header", "children"),
    Output("active-edge-info-content", "children"),
    Input("cyto-chart", "selectedEdgeData"),
    Input("cyto-chart", "tapEdge"),
    # State("memory-submitted-data", "data"),
)
def display_tap_edge_tooltip(selected_edges_data, tap_edge):
    """
    Iškylančiame debesėlyje parodo informaciją apie jungtį
    :param selected_edges_data: pažymėtųjų jungčių duomenys
    :param tap_edge: paskutinė spragtelėta jungtis
    :return:
    """

    if selected_edges_data:
        selected_edges_id = [edge["id"] for edge in selected_edges_data]
        # Rodyti info debesėlį tik jei pažymėta viena jungtis
        if (len(selected_edges_id) == 1) and tap_edge:

            # Padėtis nematomo stačiakampio, į kurio krašto vidurį rodo debesėlio rodyklė
            edge_position = tap_edge["midpoint"]
            bbox={
                "x0": edge_position["x"] - 25,
                "y0": edge_position["y"],
                "x1": edge_position["x"] + 25,
                "y1": edge_position["y"] + 150
            }

            # Antraštė
            tooltip_header = [
                html.H6(tap_edge["data"]["source"] + " -> " + tap_edge["data"]["target"]),
            ]

            # Turinys
            table_rows = []
            for link in tap_edge["data"]["link_info"]:
                if link:
                    table_rows.append(html.Tr([html.Td(link)]))
            if table_rows:
                content = html.Table(
                    children=[
                        html.Thead(html.Tr([html.Th(html.U(_("Column references:")))])),
                        html.Tbody(table_rows)
                    ]
                )
                tooltip_header.append(html.Hr())
            else:
                content = []

            return True, bbox, tooltip_header, content
    return False, None, [], []


# ========================================
# Savarankiška Dash programa
# ========================================

server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    routes_pathname_prefix='/pdsa_grapher/',
    requests_pathname_prefix='/pdsa_grapher/',
    update_title=None  # noqa
)
app.layout = app_layout


if __name__ == "__main__":
    """
    Paleisti Docker programą tarsi vietiniame kompiuteryje arba tarsi serveryje automatiškai
    """

    # Aptikti, ar esame Docker konteineryje
    cgroup_path = "/proc/self/cgroup"
    is_docker = (
        os.path.exists("/.dockerenv") or
        (os.path.isfile(cgroup_path) and any("docker" in line for line in open(cgroup_path)))
    )

    if is_docker:
        # Esame Docker konteineryje
        print("Executing App from Docker image")
        app.run_server(port=8080, debug=False)
    else:
        # Paprastas kompiuteris
        app.run(debug=False)
