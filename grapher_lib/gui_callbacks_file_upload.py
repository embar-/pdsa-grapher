"""
PDSA grapher Dash app callbacks in "File upload" tab.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import pandas as pd
from dash import (
    html, Output, Input, callback, dash_table, callback_context, State,
)
from grapher_lib import utils as gu
from locale_utils.translations import pgettext


# ========================================
# Interaktyvumai rinkmenų pasirinkimo kortelėje
# ========================================

# PDSA
@callback(
    Output("memory-uploaded-pdsa", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    Output("pdsa-file-name", "children"),  # pasirinktos PDSA rinkmenos vardas
    Input("upload-data", "contents"),  # kas paduota
    State("upload-data", "filename"),  # pasirinktos(-ų) rinkmenos(-ų) vardas(-ai)
    State("memory-uploaded-pdsa", "data"),  # žodynas su pdsa duomenimis
)
def set_pdsa_memory(uploaded_content, list_of_names, pdsa_dict):
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
    Output("refs-file-name", "children"),
    Input("upload-data-refs", "contents"),
    State("upload-data-refs", "filename"),
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
)
def set_refs_memory(uploaded_content, list_of_names, refs_dict):
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
    Input("memory-uploaded-pdsa", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    config_prevent_initial_callbacks=True,
)
def set_pdsa_sheet_radios(pdsa_dict):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą PDSA dokumentą.
    :param pdsa_dict: nuskaitytas pasirinktos PDSA rinkmenos turinys
    """
    if isinstance(pdsa_dict, dict) and "file_data" in pdsa_dict:
        sheet_names = list(pdsa_dict["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheet_names]

        # Automatiškai žymėti numatytuosius lakštus, jei jie yra
        preselect_tbl_sheet = "tables" if ("tables" in sheet_names) else None
        preselect_col_sheet = "columns" if ("columns" in sheet_names) else None

        return sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        return [], None, [], None


# PDSA
@callback(
    Output("pdsa-tables-header-for-cols-selection", "children"),
    Output("pdsa-panel-tables", "style"),
    Input("radio-sheet-tbl", "value"),
    State("pdsa-panel-tables", "style"),
    config_prevent_initial_callbacks=True,
)
def set_pdsa_tables_sheet_names(sheet_name, div_style):
    """
    Pakeisti užrašą, kuris rodomas virš PDSA lentelių lakšto stulpelių pasirinkimo.
    :param sheet_name: PDSA lentelių lakštas
    :param div_style: HTML DIV, kuriame yra lentelių lakšto stulpeliai, stilius
    :return:
    """
    return sheet_name or "", gu.change_style_display_value(sheet_name, div_style)


# PDSA
@callback(
    Output("pdsa-columns-header-for-cols-selection", "children"),
    Output("pdsa-panel-columns", "style"),
    Input("radio-sheet-col", "value"),
    State("pdsa-panel-columns", "style"),
    config_prevent_initial_callbacks=True,
)
def set_pdsa_columns_sheet_names(sheet_name, div_style):
    """
    Pakeisti užrašą, kuris rodomas virš PDSA stulpelių lakšto stulpelių pasirinkimo.
    :param sheet_name: PDSA stulpelių lakštas
    :param div_style: HTML DIV, kuriame yra stulpelių lakšto stulpeliai, stilius
    :return:
    """
    return sheet_name or "", gu.change_style_display_value(sheet_name, div_style)


@callback(
    Output("pdsa-tables-table", "options"),
    Output("pdsa-tables-table", "value"),
    Output("pdsa-tables-comment", "options"),
    Output("pdsa-tables-comment", "value"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_tables_sheet_column_dropdowns(pdsa_dict, pdsa_tbl_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius rodyti pačiuose grafikuose
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet)  # Galimi stulpeliai

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" (arba "view") dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in ["table", "view", "field", "Pavadinimas", "Lentelės Pavadinimas"] if col in columns), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių apibūdinimai
    comments_col = next(
        # "comment" dabartiniuose PDSA, "description" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "comment", "description", "Aprašymas", "Komentaras", "Komentarai",
            "Sisteminis komentaras", "lenteles_paaiskinimas", "n_records"
        ] if col in columns), None
    )

    return columns, tables_col, columns, comments_col


# PDSA
@callback(
    Output("dropdown-sheet-tbl", "options"),
    Output("dropdown-sheet-tbl", "value"),
    Input("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_tables_sheet_column_dropdowns(pdsa_dict, pdsa_tbl_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius norite pasilikti švieslentėje
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet)
    return columns, columns


@callback(
    Output("pdsa-columns-table", "options"),
    Output("pdsa-columns-table", "value"),
    Output("pdsa-columns-column", "options"),
    Output("pdsa-columns-column", "value"),
    Output("pdsa-columns-primary", "options"),
    Output("pdsa-columns-primary", "value"),
    Output("pdsa-columns-comment", "options"),
    Output("pdsa-columns-comment", "value"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_columns_sheet_column_dropdowns(pdsa_dict, pdsa_col_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius rodyti pačiuose grafikuose
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_col_sheet)  # Galimi stulpeliai

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in ["table", "view", "field", "Lentelės Pavadinimas"] if col in columns), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių stulpeliai
    columns_col = next(
        (col for col in ["column", "Pavadinimas"] if col in columns), None
    )
    # PDSA lakšto stulpelis, kuriame nurodyta, at duombazės lentelės stulpelis yra pirminis raktas
    primary_col = next(
        (col for col in ["is_primary", "Ar pirminis raktas"] if col in columns), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių apibūdinimai
    comments_col = next(
        # "comment" dabartiniuose PDSA, "description" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "comment", "description", "Aprašymas", "Komentaras", "Komentarai", "Sisteminis komentaras",
            "column_type", "Duomenų tipas", "Raktažodžiai", "Objektas"
        ] if col in columns), None
    )
    return columns, tables_col, columns, columns_col, columns, primary_col, columns, comments_col


# PDSA
@callback(
    Output("dropdown-sheet-col", "options"),
    Output("dropdown-sheet-col", "value"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_columns_sheet_column_dropdowns(pdsa_dict, pdsa_col_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA stulpelių lakšto stulpelius norite pasilikti švieslentėje
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_col_sheet)
    return columns, columns


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-tbl", "value"),
    Input("dropdown-sheet-tbl", "value"),
    config_prevent_initial_callbacks=True,
)
def create_preview_of_pdsa_tbl_sheet(pdsa_dict, pdsa_tbl_sheet, sheet_tbl_selection):
    """
    PDSA lakšto apie lenteles peržiūra
    """
    if not pdsa_dict or not sheet_tbl_selection:
        return dash_table.DataTable()
    df_tbl = pdsa_dict["file_data"][pdsa_tbl_sheet]["df"]
    children_df_tbl = dash_table.DataTable(
        df_tbl,
        [{"name": i, "id": i} for i in sheet_tbl_selection],
        style_table={"overflowX": "scroll"},
        page_size=5,
    )
    return children_df_tbl


# PDSA
@callback(
    Output("sheet-col-preview", "children"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-col", "value"),
    Input("dropdown-sheet-col", "value"),
    config_prevent_initial_callbacks=True,
)
def create_preview_of_pdsa_col_sheet(pdsa_dict, pdsa_col_sheet, sheet_col_selection):
    """
    PDSA lakšto apie stulpelius peržiūra
    """
    if not pdsa_dict or not sheet_col_selection:
        return dash_table.DataTable()
    df_col = pdsa_dict["file_data"][pdsa_col_sheet]["df"]
    children_df_col = dash_table.DataTable(
        df_col,
        [{"name": i, "id": i} for i in sheet_col_selection],
        style_table={"overflowX": "scroll"},
        page_size=10,
    )
    return children_df_col


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
    Output("refs-tbl-preview", "children"),
    Input("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    config_prevent_initial_callbacks=True,
)
def create_refs_dropdowns_and_preview(refs_data):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą ryšių dokumentą.
    :param refs_data: nuskaitytas pasirinktos ryšių XLSX ar CSV rinkmenos turinys
    :return:
    """
    # Jei refs_data yra None arba tuščias - dar neįkelta; jei string – įkėlimo klaida
    if (
            isinstance(refs_data, dict) and
            ("file_data" in refs_data)
    ):
        sheet_name = list(refs_data["file_data"].keys())[0]
        refs_columns = refs_data["file_data"][sheet_name]["df_columns"]
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios IŠORINIUS raktus
        preselected_source_tables = next(
            (
                col for col in
                ["TABLE_NAME", "table_name", "table", "Iš_lentelės", "Iš lentelės"]
                if col in refs_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip IŠORINIAI raktai
        preselected_source_columns = next(
            (
                col for col in
                ["COLUMN_NAME", "column_name", "column", "Iš_stulpelio", "Iš stulpelio"]
                if col in refs_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios PIRMINIUS raktus
        preselected_target_tables = next(
            (
                col for col in
                ["REFERENCED_TABLE_NAME", "referenced_table_name", "referenced_table", "Į_lentelę", "Į lentelę"]
                if col in refs_columns
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip PIRMINIAI raktai
        preselected_target_columns = next(
            (
                col for col in
                ["REFERENCED_COLUMN_NAME", "referenced_column_name", "referenced_column", "Į_stulpelį", "Į stulpelį"]
                if col in refs_columns
             ), None
        )

        df = refs_data["file_data"][sheet_name]["df"]

        children_df_tbl = dash_table.DataTable(
            df,
            [{"name": i, "id": i} for i in refs_columns],
            style_table={"overflowX": "scroll"},
            page_size=10,
        )

        return (
            refs_columns, preselected_source_tables,
            refs_columns, preselected_source_columns,
            refs_columns, preselected_target_tables,
            refs_columns, preselected_target_columns,
            children_df_tbl
        )
    else:
        return [], None, [], None, [], None, [], None, dash_table.DataTable(style_table={"overflowX": "scroll"})


# PDSA ir ryšiai tarp lentelių
@callback(
    Output("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Output("button-submit", "color"),  # pateikimo mygtuko spalva
    Output("submit-error-message", "children"),  # pateikimo klaidos paaiškinimas
    Output("submit-warning-message", "children"),  # pateikimo įspėjimo paaiškinimas
    Output("tabs-container", "active_tab"),  # aktyvios kortelės identifikatorius (perjungimui, jei reikia)
    State("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis, papildytas
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    Input("pdsa-tables-table", "value"),
    Input("pdsa-tables-comment", "value"),
    Input("dropdown-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    Input("pdsa-columns-table", "value"),
    Input("pdsa-columns-column", "value"),
    Input("pdsa-columns-primary", "value"),
    Input("pdsa-columns-comment", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("ref-source-tables", "value"),
    Input("ref-source-columns", "value"),
    Input("ref-target-tables", "value"),
    Input("ref-target-columns", "value"),
    State("tabs-container", "active_tab"),
    Input("button-submit", "n_clicks"),  # tik kaip f-jos paleidiklis paspaudžiant Pateikti
    config_prevent_initial_callbacks=True,
)
def summarize_submission(
    pdsa_file_data,
    refs_file_data,
    pdsa_tbl_sheet,
    pdsa_tbl_table,
    pdsa_tbl_comment,
    dropdown_sheet_tbl,
    pdsa_col_sheet,
    pdsa_col_table,
    pdsa_col_column,
    pdsa_col_primary,
    pdsa_col_comment,
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
    :param pdsa_tbl_table: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių vardais
    :param pdsa_tbl_comment: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių apibūdinimais
    :param dropdown_sheet_tbl: sąrašas stulpelių, kurie yra pdsa_info["sheet_tbl"] (lentelių) lakšte
    :param pdsa_col_table: PDSA lakšte, aprašančiame stulpelius, stulpelis su lentelių vardais
    :param pdsa_col_column: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių vardais
    :param pdsa_col_primary: PDSA lakšte, aprašančiame stulpelius, stulpelis su požymiu, ar stulpelis yra pirminis raktas
    :param pdsa_col_comment: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių apibūdinimais
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
                "tbl_sheet_data_orig": [],  # PDSA lakšto, aprašančio lenteles, turinys su originaliais stulpeliais
                "col_sheet_data_orig": [],  # PDSA lakšto, aprašančio stulpelius, turinys su originaliais stulpeliais
                "tbl_sheet_data": [],  # PDSA lakšto, aprašančio lenteles, turinys su pervadintais stulpeliais
                "col_sheet_data": [],  # PDSA lakšto, aprašančio stulpelius, turinys su pervadintais stulpeliais
                "tbl_sheet_renamed_cols": {},  # PDSA lakšte, aprašančiame lenteles, stulpelių vidiniai pervadinimai
                "col_sheet_renamed_cols": {},  # PDSA lakšte, aprašančiame stulpelius, stulpelių vidiniai pervadinimai
                "sheet_tbl": "",  # PDSA lakšto, aprašančio lenteles, pavadinimas
                "sheet_col": "",  # PDSA lakšto, aprašančio stulpelius, pavadinimas
                "list_tbl_tables": [],  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
                "list_col_tables": [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
                "list_all_tables": [],  # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
            },
            "edge_data":{  # Ryšiai
                "ref_sheet_data": [],  # Ryšių lakšto turinys
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
    pre_msg = _("Enhance analysis by selecting from the sheet defining the %s (%s), the column describing the %s.")
    if (pdsa_file_data is None) or None in (pdsa_tbl_sheet, pdsa_col_sheet):
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
    if pdsa_tbl_sheet == pdsa_col_sheet:
        wrn_msg.append(html.P(_("PDSA sheets for tables and columns are the same!")))
    print(pdsa_tbl_sheet)
    # PDSA lakšto (pdsa_tbl_sheet), aprašančio lenteles, turinys
    if not pdsa_tbl_table:
        msg = pre_msg % (
            pgettext("PDSA sheet describing...", "tables"), pdsa_tbl_sheet, pgettext("pdsa column for", "tables")
        )
        wrn_msg.append(html.P(msg))
    elif dropdown_sheet_tbl and (pdsa_tbl_table not in dropdown_sheet_tbl):
        dropdown_sheet_tbl = [pdsa_tbl_table] + dropdown_sheet_tbl  # lentelės vardas privalomas
    df_tbl = pdsa_file_data["file_data"][pdsa_tbl_sheet]["df"]
    df_tbl = pd.DataFrame.from_records(df_tbl)
    df_tbl_orig = df_tbl.loc[:, dropdown_sheet_tbl].copy()
    tbl_sheet_renamed_cols = {  # prisiminti būsimus pervadinimus; tačiau dėl galimų dublių ar tuščių, pervadinant bus pateikiamas ne šis žodynas
        "table": pdsa_tbl_table,
        "comment": pdsa_tbl_comment,
    }
    if None in [pdsa_tbl_table, pdsa_tbl_comment]:
        df_tbl[" "] = None  # kurti tuščią stulpelį, jei kai kurie stulpeliai nenurodyti
    df_tbl = df_tbl.loc[:, [pdsa_tbl_table or " ", pdsa_tbl_comment or " "]]
    df_tbl.columns = ["table", "comment"]  # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui

    # PDSA lakšto (pdsa_col_sheet), aprašančio stulpelius, turinys
    df_col = pdsa_file_data["file_data"][pdsa_col_sheet]["df"]
    df_col = pd.DataFrame.from_records(df_col)
    df_col = df_col.dropna(how="all")
    if dropdown_sheet_col:
        # lentelės ir stulpelio vardas privalomi
        if pdsa_col_column and (pdsa_col_column not in dropdown_sheet_col):
            dropdown_sheet_col = [pdsa_col_column] + dropdown_sheet_col
        if pdsa_col_table and (pdsa_col_table not in dropdown_sheet_col):
            dropdown_sheet_col = [pdsa_col_table] + dropdown_sheet_col
    df_col_orig = df_col.loc[:, dropdown_sheet_col].copy()
    col_sheet_renamed_cols = {  # prisiminti būsimus pervadinimus; tačiau dėl galimų dublių ar tuščių, pervadinant bus pateikiamas ne šis žodynas
        "table": pdsa_col_table,
        "column": pdsa_col_column,
        "is_primary": pdsa_col_primary,
        "comment": pdsa_col_comment,
    }
    if None in [pdsa_col_table, pdsa_col_column, pdsa_col_primary, pdsa_col_comment]:
        df_col[" "] = None  # kurti tuščią stulpelį, jei kai kurie stulpeliai nenurodyti
    df_col = df_col.loc[:, [
        pdsa_col_table or " ", pdsa_col_column or " ", pdsa_col_primary or " ", pdsa_col_comment or " "]
    ]
    df_col.columns = ["table", "column", "is_primary", "comment"]  # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui
    if not pdsa_col_table:
        pdsa_col_tables = None
        msg = pre_msg % (
            pgettext("PDSA sheet describing...", "columns"), pdsa_col_sheet, pgettext("pdsa column for", "tables")
        )
        wrn_msg.append(html.P(msg))
    else:
        pdsa_col_tables = df_col["table"].dropna().drop_duplicates().sort_values().tolist()
    if not pdsa_col_column:
        msg = pre_msg % (
            pgettext("PDSA sheet describing...", "columns"), pdsa_col_sheet, pgettext("pdsa column for", "columns")
        )
        wrn_msg.append(html.P(msg))

    # Sukurti ryšių pd.DataFrame tinklo piešimui
    refs_sheet = list(refs_file_data["file_data"].keys())[0]  # ryšių lakšto pavadinimas
    df_edges = refs_file_data["file_data"][refs_sheet]["df"]
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
    if pdsa_tbl_table and (not pdsa_tbl_tables):
        warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (pdsa_tbl_sheet, pdsa_tbl_table)
        wrn_msg.append(html.P(warning_str))

    # Sutikrinimas tarp pdsa_tbl_sheet ir pdsa_col_sheet „table“ stulpelių
    if pdsa_tbl_table and pdsa_col_table and (pdsa_col_tables is not None):
        tables_diff = list(set(pdsa_tbl_tables) - (set(pdsa_col_tables) & set(pdsa_tbl_tables)))
        if tables_diff:
            # Smulkesniuose stulpelių aprašymuose kai kuriuose PDSA būna daugiau lentelių -
            # paprastai tai rodiniai (views) ir į šį įspėjimą galima nekreipti dėmesio
            warning_str = _(
                "PDSA sheet '%s' column '%s' has some tables (%d in total) not present in sheet '%s' column '%s', but it's not a problem:"
            )
            warning_str = warning_str % (pdsa_tbl_sheet, pdsa_tbl_table, len(tables_diff), pdsa_col_sheet, pdsa_col_table)
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
    if pdsa_tbl_table and pdsa_col_table and edge_tables_extra:
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
            "tbl_sheet_data_orig": df_tbl_orig.to_dict("records"),  # PDSA lakšto, aprašančio lenteles, originalus turinys
            "col_sheet_data_orig": df_col_orig.to_dict("records"),  # PDSA lakšto, aprašančio stulpelius, originalus turinys
            "tbl_sheet_data": df_tbl.to_dict("records"),  # PDSA lakšto, aprašančio lenteles, turinys pervadinus stulpelius
            "col_sheet_data": df_col.to_dict("records"),  # PDSA lakšto, aprašančio stulpelius, turinys pervadinus stulpelius
            "tbl_sheet_renamed_cols": tbl_sheet_renamed_cols,  # PDSA lakšte, aprašančiame lenteles, stulpelių vidiniai pervadinimai
            "col_sheet_renamed_cols": col_sheet_renamed_cols,  # PDSA lakšte, aprašančiame stulpelius, stulpelių vidiniai pervadinimai
            "sheet_tbl": pdsa_tbl_sheet,  # PDSA lakšto, aprašančio lenteles, pavadinimas
            "sheet_col": pdsa_col_sheet,  # PDSA lakšto, aprašančio stulpelius, pavadinimas
            "list_tbl_tables": pdsa_tbl_tables,  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
            "list_col_tables": pdsa_col_tables or [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
            "list_all_tables": pdsa_all_tables,  # visos iš PDSA kartu
        },
        # Ryšių duomenys
        "edge_data": {
            "ref_sheet_data": df_edges.to_dict("records"),  # Ryšių lakšto turinys
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
