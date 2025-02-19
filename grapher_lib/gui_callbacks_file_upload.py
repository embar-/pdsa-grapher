"""
PDSA grapher Dash app callbacks in "File upload" tab.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import (
    Output, Input, State, callback, callback_context, dash_table, html, no_update
)
from grapher_lib import utils as gu
from locale_utils.translations import pgettext


# ========================================
# Interaktyvumai rinkmenų pasirinkimo kortelėje
# ========================================

# PDSA
@callback(
    Output("memory-uploaded-pdsa", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    Output("upload-data-pdsa-label", "children"),  # užrašas apie pasirinktą PDSA rinkmeną
    Input("upload-data-pdsa", "contents"),  # pasirinktos(-ų) PDSA rinkmenos(-ų) turinys
    State("upload-data-pdsa", "filename"),  # pasirinktos(-ų) PDSA rinkmenos(-ų) vardas(-ai)
    State("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis
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
            return (
                {},
                html.Div(
                    children=[html.B(list_of_names[0]), html.Br(), parse_output],
                    style={"color": "red"},
                ),
            )
        else:
            # Sėkmingai įkelti nauji duomenys
            return parse_output, html.B(list_of_names[0])
    elif isinstance(pdsa_dict, dict) and pdsa_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        return pdsa_dict, _("Previously uploaded data")
    else:
        return {}, no_update


# Ryšiai tarp lentelių
@callback(
    Output("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Output("upload-data-refs-label", "children"),  # užrašas apie pasirinktą ryšių rinkmeną
    Input("upload-data-refs", "contents"),  # pasirinktos(-ų) ryšių rinkmenos(-ų) turinys
    State("upload-data-refs", "filename"),  # pasirinktos(-ų) ryšių rinkmenos(-ų) vardas(-ai)
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
            return (
                {},
                html.Div(
                    children=[html.B(list_of_names[0]), html.Br(), parse_output],
                    style={"color": "red"},
                ),
            )
        else:
            # Sėkmingai į įkelti nauji duomenys
            return parse_output, html.B(list_of_names[0])
    elif isinstance(refs_dict, dict) and refs_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        return refs_dict, _("Previously uploaded data")
    else:
        # nieko naujo neįkelta, nėra senų; greičiausiai darbo pradžia
        return {}, no_update

# PDSA
@callback(
    Output("radio-sheet-tbl", "options"),  # Visi PDSA lakštai
    Output("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    Output("radio-sheet-col", "options"),  # Visi PDSA lakštai
    Output("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    Input("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis
    config_prevent_initial_callbacks=True,
)
def set_pdsa_sheet_radios(pdsa_dict):
    """
    Galimų lakštų pasirinkimų sukūrimas pagal įkeltą PDSA dokumentą.
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    """
    if isinstance(pdsa_dict, dict) and "file_data" in pdsa_dict:
        sheets = list(pdsa_dict["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheets]

        # Automatiškai žymėti numatytuosius lakštus, jei jie yra
        preselect_tbl_sheet = "tables" if "tables" in sheets else (sheets[0] if len(sheets) == 1 else None)
        preselect_col_sheet = "columns" if "columns" in sheets else (sheets[0] if len(sheets) == 1 else None)

        return sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        return [], None, [], None


# Ryšiai
@callback(
    Output("refs-sheet-selection", "style"),  # ryšių lakšto pasirinkimo blokas
    Output("radio-sheet-refs", "options"),  # Visi ryšių lakštai
    Output("radio-sheet-refs", "value"),  # Pasirinktas ryšių lakštas
    Input("memory-uploaded-refs", "data"),  # nuskaitytas pasirinktos ryšių rinkmenos turinys
    State("refs-sheet-selection", "style"),
    config_prevent_initial_callbacks=True,
)
def set_refs_sheet_radios(refs_dict, div_style):
    """
    Galimų lakštų pasirinkimų sukūrimas pagal įkeltą ryšių dokumentą.
    :param refs_dict: žodynas su ryšių tarp lentelių duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param div_style: HTML DIV, kuriame yra ryšių lakštai, stilius
    """
    if isinstance(refs_dict, dict) and "file_data" in refs_dict:
        sheets = list(refs_dict["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheets]
        preselect_refs_sheet = sheets[0] if (len(sheets) == 1) else None
        visibility = len(sheets) > 1
        div_style = gu.change_style_display_value(visibility, div_style)
        return div_style, sheet_options, preselect_refs_sheet
    else:
        div_style = gu.change_style_display_value(False, div_style)
        return div_style, [], None


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
    :param sheet_name: PDSA lentelių lakšto vardas
    :param div_style: HTML DIV, kuriame yra lentelių lakšto stulpeliai, stilius
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
    :param sheet_name: PDSA stulpelių lakšto vardas
    :param div_style: HTML DIV, kuriame yra stulpelių lakšto stulpeliai, stilius
    """
    return sheet_name or "", gu.change_style_display_value(sheet_name, div_style)


@callback(
    Output("pdsa-tables-table", "options"),
    Output("pdsa-tables-table", "value"),
    Output("pdsa-tables-comment", "options"),
    Output("pdsa-tables-comment", "value"),
    Output("pdsa-tables-records", "options"),
    Output("pdsa-tables-records", "value"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_tables_sheet_column_dropdowns_for_graph(pdsa_dict, pdsa_tbl_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius rodyti pačiuose grafikuose
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_tbl_sheet: PDSA lentelių lakšto vardas
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet)  # visi stulpeliai
    columns_str = gu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet, string_type=True)  # tekstiniai stulpeliai
    columns_not_str = list(set(columns) - set(columns_str))  # ne tekstiniai stulpeliai
    columns_not_str = columns_not_str or columns

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" (arba "view") dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "table", "view", "field", "Lentelė", "Lentelės Pavadinimas", "Pavadinimas"
        ] if col in columns_str), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių apibūdinimai
    comments_col = next(
        # "comment" dabartiniuose PDSA, "description" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "comment", "description", "Aprašymas", "Komentaras", "Komentarai",
            "Sisteminis komentaras", "lenteles_paaiskinimas"
        ] if col in columns), None
    )
    n_records_col = "n_records" if "n_records" in columns_not_str else None  # "n_records" dabartiniuose PDSA

    return columns_str, tables_col, columns, comments_col, columns_not_str, n_records_col


# PDSA
@callback(
    Output("checkbox-tables-records-nonzero", "style"),
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-records-nonzero", "style"),
    config_prevent_initial_callbacks=True,
)
def change_pdsa_tables_excluding_checkbox_visibility(n_records_col, style):
    """
    Pakeisti PDSA lentelių lakšto lentelių, kuriose eilučių yra 0, neįtraukimo parinkties matomumą.
    :param n_records_col: vardas stulpelio, kuriame surašyti lentelių eilučių skaičiai
    :param style: žymimojo langelio (checkbox) stilius
    """
    return gu.change_style_display_value(n_records_col, style)


# PDSA
@callback(
    Output("dropdown-sheet-tbl", "options"),
    Output("dropdown-sheet-tbl", "value"),
    Input("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_tables_sheet_column_dropdowns_for_info(pdsa_dict, pdsa_tbl_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius norite pasilikti švieslentėje
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_tbl_sheet: PDSA lentelių lakšto vardas
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
def create_pdsa_columns_sheet_column_dropdowns_for_graph(pdsa_dict, pdsa_col_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius rodyti pačiuose grafikuose
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_col_sheet: PDSA stulpelių lakšto vardas
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_col_sheet)  # visi stulpeliai
    columns_str = gu.get_sheet_columns(pdsa_dict, pdsa_col_sheet, string_type=True)  # tekstiniai stulpeliai

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in ["table", "view", "field", "Lentelė", "Lentelės Pavadinimas"] if col in columns_str), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių stulpeliai
    columns_col = next(
        (col for col in ["column", "Stulpelis", "Pavadinimas"] if col in columns_str), None
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
    return columns_str, tables_col, columns_str, columns_col, columns, primary_col, columns, comments_col


# PDSA
@callback(
    Output("dropdown-sheet-col", "options"),
    Output("dropdown-sheet-col", "value"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    config_prevent_initial_callbacks=True,
)
def create_pdsa_columns_sheet_column_dropdowns_for_info(pdsa_dict, pdsa_col_sheet):
    """
    Sukurti pasirinkimus, kuriuos PDSA stulpelių lakšto stulpelius norite pasilikti švieslentėje
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_col_sheet: PDSA stulpelių lakšto vardas
    """
    columns = gu.get_sheet_columns(pdsa_dict, pdsa_col_sheet)
    return columns, columns


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-tbl", "value"),
    Input("dropdown-sheet-tbl", "value"),
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-records-nonzero", "value"),
    config_prevent_initial_callbacks=True,
)
def create_preview_of_pdsa_tbl_sheet(
    pdsa_dict, pdsa_tbl_sheet, sheet_tbl_selection, pdsa_tbl_records, pdsa_tbl_exclude_empty
):
    """
    PDSA lakšto apie lenteles peržiūra
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_tbl_sheet: PDSA lentelių lakšto vardas
    :param sheet_tbl_selection: pasirinktieji PDSA lentelių lakšto stulpeliai išplėstinei informacijai
    :param pdsa_tbl_records: PDSA lakšte, aprašančiame lenteles, stulpelis su eilučių (įrašų) skaičiumi
    :param pdsa_tbl_exclude_empty: ar išmesti PDSA lentelių lakšto lenteles, kuriose nėra įrašų
    """
    if not pdsa_dict or not sheet_tbl_selection:
        return dash_table.DataTable()
    df_tbl = pdsa_dict["file_data"][pdsa_tbl_sheet]["df"]
    if pdsa_tbl_records and pdsa_tbl_exclude_empty:
        df_tbl = [r for r in df_tbl if r[pdsa_tbl_records] not in [0, "0"]]
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
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_col_sheet: PDSA stulpelių lakšto vardas
    :param sheet_col_selection: pasirinktieji PDSA stulpelių lakšto stulpeliai išplėstinei informacijai
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
    Input("radio-sheet-refs", "value"),  # Pasirinktas ryšių lakštas
    config_prevent_initial_callbacks=True,
)
def create_refs_dropdowns_and_preview(refs_data, refs_sheet):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą ryšių dokumentą.
    :param refs_data: nuskaitytas pasirinktos ryšių XLSX ar CSV rinkmenos turinys
    :param refs_sheet: pasirinktas ryšių lakštas
    """
    # Jei refs_data yra None arba tuščias - dar neįkelta; jei string – įkėlimo klaida
    columns = gu.get_sheet_columns(refs_data, refs_sheet)  # visi stulpeliai
    columns_str = gu.get_sheet_columns(refs_data, refs_sheet, string_type=True)  # tekstiniai stulpeliai
    if columns_str:
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios IŠORINIUS raktus
        preselected_source_tables = next(
            (
                col for col in
                ["TABLE_NAME", "table_name", "table", "Iš_lentelės", "Iš lentelės"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip IŠORINIAI raktai
        preselected_source_columns = next(
            (
                col for col in
                ["COLUMN_NAME", "column_name", "column", "Iš_stulpelio", "Iš stulpelio"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios PIRMINIUS raktus
        preselected_target_tables = next(
            (
                col for col in
                ["REFERENCED_TABLE_NAME", "referenced_table_name", "referenced_table", "Į_lentelę", "Į lentelę"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip PIRMINIAI raktai
        preselected_target_columns = next(
            (
                col for col in
                ["REFERENCED_COLUMN_NAME", "referenced_column_name", "referenced_column", "Į_stulpelį", "Į stulpelį"]
                if col in columns_str
             ), None
        )

        df = refs_data["file_data"][refs_sheet]["df"]

        children_df_tbl = dash_table.DataTable(
            df,
            [{"name": i, "id": i} for i in columns],
            style_table={"overflowX": "scroll"},
            page_size=10,
        )

        return (
            columns_str, preselected_source_tables,
            columns_str, preselected_source_columns,
            columns_str, preselected_target_tables,
            columns_str, preselected_target_columns,
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
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-records-nonzero", "value"),
    Input("dropdown-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    Input("pdsa-columns-table", "value"),
    Input("pdsa-columns-column", "value"),
    Input("pdsa-columns-primary", "value"),
    Input("pdsa-columns-comment", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("radio-sheet-refs", "value"),  # Pasirinktas ryšių lakštas
    Input("ref-source-tables", "value"),
    Input("ref-source-columns", "value"),
    Input("ref-target-tables", "value"),
    Input("ref-target-columns", "value"),
    State("tabs-container", "active_tab"),
    Input("button-submit", "n_clicks"),  # tik kaip f-jos paleidiklis paspaudžiant Pateikti
    config_prevent_initial_callbacks=True,
)
def summarize_submission(
    pdsa_file_data, refs_file_data,
    pdsa_tbl_sheet,
    pdsa_tbl_table, pdsa_tbl_comment, pdsa_tbl_records, pdsa_tbl_exclude_empty, dropdown_sheet_tbl,
    pdsa_col_sheet,
    pdsa_col_table, pdsa_col_column, pdsa_col_primary, pdsa_col_comment, dropdown_sheet_col,
    refs_sheet,
    ref_source_tbl, ref_source_col,
    ref_target_tbl, ref_target_col,
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
    :param pdsa_tbl_sheet: PDSA lakšto, aprašančio lenteles, vardas
    :param pdsa_tbl_table: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių vardais
    :param pdsa_tbl_comment: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių apibūdinimais
    :param pdsa_tbl_records: PDSA lakšte, aprašančiame lenteles, stulpelis su eilučių (įrašų) skaičiumi
    :param pdsa_tbl_exclude_empty: ar išmesti PDSA lentelių lakšto lenteles, kuriose nėra įrašų
    :param dropdown_sheet_tbl: sąrašas stulpelių, kurie yra pdsa_info["sheet_tbl"] (lentelių) lakšte
    :param pdsa_col_sheet: PDSA lakšto, aprašančio stulpelius, vardas
    :param pdsa_col_table: PDSA lakšte, aprašančiame stulpelius, stulpelis su lentelių vardais
    :param pdsa_col_column: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių vardais
    :param pdsa_col_primary: PDSA lakšte, aprašančiame stulpelius, stulpelis su požymiu, ar stulpelis yra pirminis raktas
    :param pdsa_col_comment: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių apibūdinimais
    :param dropdown_sheet_col: sąrašas stulpelių, kurie yra pdsa_info["sheet_col"] (stulpelių) lakšte
    :param refs_sheet: pasirinktas ryšių lakštas
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
                "ref_sheet_name": "",  # Ryšių lakšto vardas
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
        wrn_msg.append(html.P(_("Please select PDSA document and its sheets!")))
    if not refs_file_data:
        err_msg.append(html.P(_("Please select references document!")))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    if None in (ref_source_tbl, ref_target_tbl):
        err_msg.append(html.P(_("Please select references columns that contain tables!")))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    if pdsa_col_sheet and pdsa_tbl_sheet == pdsa_col_sheet:
        wrn_msg.append(html.P(_("PDSA sheets for tables and columns are the same!")))

    # %% Surinktą informaciją transformuoju ir paruošiu graferiui

    # PDSA lakšto (pdsa_tbl_sheet), aprašančio LENTELES, turinys
    df_tbl = pdsa_file_data["file_data"][pdsa_tbl_sheet]["df"] if pdsa_tbl_sheet else {}
    df_tbl = pl.DataFrame(df_tbl, infer_schema_length=None)
    dropdown_sheet_tbl = dropdown_sheet_tbl or []
    if df_tbl.height == 0:
        if pdsa_tbl_sheet:
            msg = _("PDSA sheet describing %s (%s) has no data.")
            msg = msg % (pgettext("PDSA sheet describing...", "tables"), pdsa_tbl_sheet)
            wrn_msg.append(html.P(msg))
        df_tbl_orig = df_tbl  # Tuščias df
        pdsa_tbl_tables = []
    else:
        if not pdsa_tbl_table:
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "tables"),  # lenteles
                pdsa_tbl_sheet,
                pgettext("pdsa column for", "tables")  # ... nurodysite stulpelį, kuriame yra lentelės.
            )
            wrn_msg.append(html.P(msg))
        elif dropdown_sheet_tbl and (pdsa_tbl_table not in dropdown_sheet_tbl):
            dropdown_sheet_tbl = [pdsa_tbl_table] + dropdown_sheet_tbl  # lentelės vardas privalomas
        df_tbl_orig = df_tbl[dropdown_sheet_tbl].clone()
        # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui
        selected_tbl_columns = [pdsa_tbl_table, pdsa_tbl_comment, pdsa_tbl_records]
        internal_tbl_columns = ["table", "comment", "n_records"]
        df_tbl = gu.select_renamed_or_add_columns(df_tbl, selected_tbl_columns, internal_tbl_columns)
        if pdsa_tbl_records and pdsa_tbl_exclude_empty:
            # Pašalinti lenteles, kuriose eilučių skaičius yra 0 (bet palikti jei jų yra None).
            # Tačiau vėliau gali kilti painiavos vėlesniuose įspėjimuose, pvz., neva nėra apibrėžtų kai kurių lentelių
            n_records_dtype = df_tbl.schema["n_records"]
            numeric_polars_dtypes = [
                pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Int128, pl.Decimal,
                pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64
            ]
            if  n_records_dtype in numeric_polars_dtypes:
                df_tbl = df_tbl.filter(pl.col("n_records") != 0)
                df_tbl_orig = df_tbl_orig.filter(pl.col(pdsa_tbl_records) != 0)
            elif n_records_dtype == pl.Utf8:  # pl.String
                df_tbl = df_tbl.filter(pl.col("n_records") != "0")
                df_tbl_orig = df_tbl_orig.filter(pl.col(pdsa_tbl_records) != "0")
            else:
                msg = _("In the PDSA sheet '%s', the column '%s' has unexpected dtype '%s'!")
                msg = msg % (pdsa_tbl_sheet, pdsa_tbl_records, n_records_dtype)
                wrn_msg.append(html.P(msg))
        pdsa_tbl_tables = df_tbl["table"].drop_nulls().to_list()
        pdsa_tbl_tables = sorted(list(set(pdsa_tbl_tables)))
        if pdsa_tbl_table and (not pdsa_tbl_tables):
            warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (pdsa_tbl_sheet, pdsa_tbl_table)
            wrn_msg.append(html.P(warning_str))
        if not all([isinstance(x, str) for x in pdsa_tbl_tables]):
            error_str = _("In the PDSA sheet '%s', the column '%s' some values are not strings!")
            error_str = error_str  % (pdsa_tbl_sheet, pdsa_tbl_table)
            err_msg.append(html.P(error_str))
            return {}, "secondary", err_msg, wrn_msg, "file_upload"
    # Prisiminti naudotojo pasirinktas lentelių lakšto stulpelių sąsajas; bet tai nereiškia, kad tie stulpeliai iš tiesų yra!
    tbl_sheet_renamed_cols = {
        "table": pdsa_tbl_table,
        "comment": pdsa_tbl_comment,
        "n_records": pdsa_tbl_records
    }

    # PDSA lakšto (pdsa_col_sheet), aprašančio STULPELIUS, turinys
    df_col = pdsa_file_data["file_data"][pdsa_col_sheet]["df"] if pdsa_col_sheet else {}
    df_col = pl.DataFrame(df_col, infer_schema_length=None)
    dropdown_sheet_col = dropdown_sheet_col or []
    if df_col.height == 0:
        if pdsa_col_sheet:
            msg = _("PDSA sheet describing %s (%s) has no data.")
            msg = msg % (pgettext("PDSA sheet describing...", "columns"), pdsa_col_sheet)
            wrn_msg.append(html.P(msg))
        df_col_orig = df_col  # Tuščias df
        pdsa_col_tables = None  # Tyčia ne [], kad būtų galima atskirti vėlesniame etape
    else:
        if dropdown_sheet_col:
            # lentelės ir stulpelio vardas privalomi
            if pdsa_col_column and (pdsa_col_column not in dropdown_sheet_col):
                dropdown_sheet_col = [pdsa_col_column] + dropdown_sheet_col
            if pdsa_col_table and (pdsa_col_table not in dropdown_sheet_col):
                dropdown_sheet_col = [pdsa_col_table] + dropdown_sheet_col
        df_col_orig = df_col[dropdown_sheet_col].clone()
        # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui
        selected_col_columns = [pdsa_col_table, pdsa_col_column, pdsa_col_primary, pdsa_col_comment]
        internal_col_columns = ["table", "column", "is_primary", "comment"]
        df_col = gu.select_renamed_or_add_columns(df_col, selected_col_columns, internal_col_columns)
        if pdsa_col_table:
            pdsa_col_tables = df_col["table"].drop_nulls().unique().sort().to_list()
            if not pdsa_col_tables:
                warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (pdsa_col_sheet, pdsa_col_table)
                wrn_msg.append(html.P(warning_str))
            if not all([isinstance(x, str) for x in pdsa_col_tables]):
                error_str = _("In the PDSA sheet '%s', the column '%s' some values are not strings!")
                error_str = error_str  % (pdsa_col_sheet, pdsa_col_table)
                err_msg.append(html.P(error_str))
                return {}, "secondary", err_msg, wrn_msg, "file_upload"
        else:
            pdsa_col_tables = None
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "columns"),  # stulpelius
                pdsa_col_sheet,
                pgettext("pdsa column for", "tables")  # ... nurodysite stulpelį, kuriame yra lentelės.
            )
            wrn_msg.append(html.P(msg))
        if not pdsa_col_column:
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "columns"),  # stulpelius
                pdsa_col_sheet,
                pgettext("pdsa column for", "columns")  # ... nurodysite stulpelį, kuriame yra stulpeliai.
            )
            wrn_msg.append(html.P(msg))
        elif not all([isinstance(x, str) for x in df_col["column"].drop_nulls().unique().sort().to_list()]):
            error_str = _("In the PDSA sheet '%s', the column '%s' some values are not strings!")
            error_str = error_str % (pdsa_col_sheet, pdsa_col_column)
            err_msg.append(html.P(error_str))
            return {}, "secondary", err_msg, wrn_msg, "file_upload"
    # Prisiminti naudotojo pasirinktas stulpelių lakšto stulpelių sąsajas; bet tai nereiškia, kad tie stulpeliai iš tiesų yra!
    col_sheet_renamed_cols = {
        "table": pdsa_col_table,
        "column": pdsa_col_column,
        "is_primary": pdsa_col_primary,
        "comment": pdsa_col_comment,
    }

    # RYŠIAI
    df_edges = refs_file_data["file_data"][refs_sheet]["df"]
    df_edges = pl.DataFrame(df_edges)
    if df_edges.height == 0:
        wrn_msg.append(html.P(_("There are no relationships between different tables!")))
    selected_refs_columns = [ref_source_tbl, ref_source_col, ref_target_tbl, ref_target_col]
    ref_cols_uniq = list(set(selected_refs_columns))  # unikalūs ryšių lakšto stulpeliai
    ref_cols_uniq = [c for c in ref_cols_uniq if c]  # netušti ryšių lakšto stulpeliai
    for ref_col in ref_cols_uniq:
        if ref_col not in df_edges.columns:
            df_edges[ref_col] = None # Galėjo stulpelis būti, bet čia jo nerasti, nes stulpelyje nebuvo duomenų
        if not all([isinstance(x, str) for x in df_edges[ref_col].drop_nulls().to_list()]):
            error_str = _("In the references sheet '%s', the column '%s' some values are not strings!")
            error_str = error_str % (refs_sheet, ref_col)
            err_msg.append(html.P(error_str))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    # Pervadinti stulpelius į toliau viduje sistemiškai naudojamus
    internal_refs_columns = ["source_tbl", "source_col", "target_tbl", "target_col"]
    df_edges = gu.select_renamed_or_add_columns(df_edges, selected_refs_columns, internal_refs_columns)

    # Sutikrinimas tarp pdsa_tbl_sheet ir pdsa_col_sheet „table“ stulpelių
    if pdsa_tbl_table and pdsa_col_table and (pdsa_col_tables is not None):
        tables_diff = list(set(pdsa_tbl_tables) - (set(pdsa_col_tables) & set(pdsa_tbl_tables)))
        if tables_diff:
            # Smulkesniuose stulpelių aprašymuose kai kuriuose PDSA būna daugiau lentelių -
            # paprastai tai rodiniai (views) ir į šį įspėjimą galima nekreipti dėmesio
            # Be to dalis lentelių galėjo būti pašalinta ties `if pdsa_tbl_records and pdsa_tbl_exclude_empty`
            warning_str = _(
                "PDSA sheet '%s' column '%s' has some tables (%d in total) not present in sheet '%s' column '%s', but it's not a problem:"
            )
            warning_str = warning_str % (pdsa_tbl_sheet, pdsa_tbl_table, len(tables_diff), pdsa_col_sheet, pdsa_col_table)
            warning_str += " " + ", ".join(tables_diff) + "."
            wrn_msg.append(html.P(warning_str))

    # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
    pdsa_all_tables = sorted(list(set(pdsa_col_tables or []) | set(pdsa_tbl_tables)))

    # Visų unikalių lentelių, turinčių ryšių, sąrašas
    edge_source_tbl = df_edges["source_tbl"].drop_nulls().to_list()  # ryšių pradžių lentelės
    edge_target_tbl = df_edges["target_tbl"].drop_nulls().to_list()  # ryšių galų lentelės
    edge_tables = sorted(list(set(edge_source_tbl + edge_target_tbl)))
    edge_tables_extra = list(set(edge_tables) - set(pdsa_all_tables))
    if pdsa_tbl_table and pdsa_col_table and edge_tables_extra:
        # Įspėjimas gali klaidinti, jei dalis lentelių pašalinta ties `if pdsa_tbl_records and pdsa_tbl_exclude_empty`
        warning_str = _("References contain some tables (%d) that are not present in the defined tables:")
        warning_str = warning_str % len(edge_tables_extra)
        warning_str += " " + ", ".join(edge_tables_extra) + "."
        wrn_msg.append(html.P(warning_str))
        ## Lentelės, tik esančios PDSA dokumente:
        # df_edges = df_edges.loc[
        #            df_edges["source_tbl"].isin(pdsa_all_tables) & df_edges["target_tbl"].isin(pdsa_all_tables), :
        #            ]
    # Paprastai neturėtų būti pasikartojančių ryšių, nebent nebuvo nurodyti ryšių stulpeliai apie DB lentelės stulpelius
    df_edges = df_edges.unique()

    # %% VISĄ SURINKTĄ INFORMACIJĄ SUKELIU Į VIENĄ STRUKTŪRĄ
    data_final = {
        # Mazgų duomenys iš PDSA
        "node_data": {
            "tbl_sheet_data_orig": df_tbl_orig.to_dicts(),  # PDSA lakšto, aprašančio lenteles, originalus turinys
            "col_sheet_data_orig": df_col_orig.to_dicts(),  # PDSA lakšto, aprašančio stulpelius, originalus turinys
            "tbl_sheet_data": df_tbl.to_dicts(),  # PDSA lakšto, aprašančio lenteles, turinys pervadinus stulpelius
            "col_sheet_data": df_col.to_dicts(),  # PDSA lakšto, aprašančio stulpelius, turinys pervadinus stulpelius
            "tbl_sheet_renamed_cols": tbl_sheet_renamed_cols,  # PDSA lakšte, aprašančiame lenteles, stulpelių vidiniai pervadinimai
            "col_sheet_renamed_cols": col_sheet_renamed_cols,  # PDSA lakšte, aprašančiame stulpelius, stulpelių vidiniai pervadinimai
            "sheet_tbl": pdsa_tbl_sheet,  # PDSA lakšto, aprašančio lenteles, vardas
            "sheet_col": pdsa_col_sheet,  # PDSA lakšto, aprašančio stulpelius, vardas
            "list_tbl_tables": pdsa_tbl_tables,  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
            "list_col_tables": pdsa_col_tables or [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
            "list_all_tables": pdsa_all_tables,  # visos iš PDSA kartu
        },
        # Ryšių duomenys
        "edge_data": {
            "ref_sheet_data": df_edges.to_dicts(),  # Ryšių lakšto turinys
            "ref_sheet_name": refs_sheet,      # ryšių lakšto vardas
            "ref_source_tbl": ref_source_tbl,  # stulpelis, kuriame pradžių („IŠ“) lentelės
            "ref_source_col": ref_source_col,  # stulpelis, kuriame pradžių („IŠ“) stulpeliai
            "ref_target_tbl": ref_target_tbl,  # stulpelis, kuriame galų („Į“) lentelės
            "ref_target_col": ref_target_col,  # stulpelis, kuriame galų („Į“) stulpeliai
            "list_all_tables": edge_tables,  # lentelės, kurios panaudotos ryšiuose
        }
    }

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    if "button-submit" in changed_id:  # Paspaustas „Pateikti“ mygtukas
        # Perduoti duomenis naudojimui grafiko kortelėje ir į ją pereiti
        active_tab = "graph"
    else:
        # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje.
        # active_tab gali neturėti reikšmės darbo pradžioje ar pakeitus kalbą. Tai padeda išlaikyti kortelę
        active_tab = active_tab or "file_upload"  # jei nėra, pereiti į rinkmenų įkėlimą;
    return data_final, "primary", err_msg, wrn_msg, active_tab
