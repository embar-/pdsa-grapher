"""
PDSA grapher Dash app callbacks in "File upload" tab for PDSA and refences upload, sheets and columns selection.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

from dash import (
    Output, Input, State, callback, callback_context, dash_table, html, no_update
)
from grapher_lib import utils as gu
from grapher_lib import utils_file_upload as fu


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
    config_prevent_initial_callbacks=True,
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
        parse_output = fu.parse_file(uploaded_content, list_of_names)
        list_of_names_str = "; ".join(list_of_names)
        if type(parse_output) == str:
            # Klaida nuskaitant
            return (
                {},
                html.Div(
                    children=[html.B(list_of_names_str), html.Br(), parse_output],
                    style={"color": "red"},
                ),
            )
        else:
            # Sėkmingai įkelti nauji duomenys
            parse_output["file_name"] = list_of_names_str
            return parse_output, html.B(list_of_names_str)
    elif isinstance(pdsa_dict, dict) and pdsa_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        file_name = pdsa_dict["file_name"] if "file_name" in pdsa_dict else None
        return pdsa_dict, html.B(file_name) if file_name else _("Previously uploaded data")
    else:
        return {}, no_update


# Ryšiai tarp lentelių
@callback(
    Output("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Output("upload-data-refs-label", "children"),  # užrašas apie pasirinktą ryšių rinkmeną
    Input("upload-data-refs", "contents"),  # pasirinktos(-ų) ryšių rinkmenos(-ų) turinys
    State("upload-data-refs", "filename"),  # pasirinktos(-ų) ryšių rinkmenos(-ų) vardas(-ai)
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Input("memory-uploaded-pdsa", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    config_prevent_initial_callbacks=True,
)
def set_refs_memory(uploaded_content, list_of_names, refs_dict, pdsa_dict):
    """
    Ryšių (pvz., sql_2_references.xlsx) rinkmenos įkėlimas.
    Teoriškai galima paduoti kelis, bet praktiškai visada imama pirmoji rinkmena.
    :param uploaded_content: įkeltų XLSX arba CSV rinkmenų turinys sąrašo pavidalu, kur
        vienas elementas – vienos rinkmenos base64 turinys.
    :param list_of_names: įkeltų XLSX arba CSV rinkmenų vardų sąrašas.
    :param refs_dict: (nebūtinas) žodynas su ryšių tarp lentelių duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_dict: (nebūtinas) žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}},
        kuris gali būti naudojamas jei nėra kitų duomenų, o PDSA turi "refs" lakštą, kas leidžia vienu įkėlimu
        importuoti JSON arba DBML (nereikia pakartotinai to paties dokumento įkelti ryšiams).
    :return: naujas refs_dict
    """
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]  # Sužinoti, kuris mygtukas buvo paspaustas
    if (changed_id == "upload-data-refs.contents") and (uploaded_content is not None):
        # Įkelti nauji ryšių duomenys
        parse_output = fu.parse_file(uploaded_content, list_of_names)
        list_of_names_str = "; ".join(list_of_names)
        if isinstance(parse_output, str):
            # Klaida nuskaitant
            return (
                {},
                html.Div(
                    children=[html.B(list_of_names_str), html.Br(), parse_output],
                    style={"color": "red"},
                ),
            )
        else:
            # Sėkmingai į įkelti nauji duomenys
            parse_output["file_name"] = list_of_names_str
            return parse_output, html.B(list_of_names_str)
    elif (
            isinstance(pdsa_dict, dict) and ("file_data" in pdsa_dict) and ("refs" in pdsa_dict["file_data"]) and
            ("df" in pdsa_dict["file_data"]["refs"]) and (pdsa_dict["file_data"]["refs"]["df"])
        ):
        # Galimai naudotojas kaip PDSA įkėlė JSON arba DBML
        file_name = pdsa_dict["file_name"] if "file_name" in pdsa_dict else None
        refs_dict = {"file_name": file_name, "file_data": {"refs": pdsa_dict["file_data"]["refs"]}}
        return refs_dict, html.B(file_name) if file_name else _("Previously uploaded data")
    elif isinstance(refs_dict, dict) and refs_dict:
        # Panaudoti iš atminties; atmintyje galėjo likti, jei naudotojas pakeitė kalbą arbą iš naujo atidarė puslapį
        file_name = refs_dict["file_name"] if "file_name" in refs_dict else None
        return refs_dict, html.B(file_name) if file_name else _("Previously uploaded data")
    else:
        # nieko naujo neįkelta, nėra senų; greičiausiai darbo pradžia
        return {}, no_update

# PDSA
@callback(
    Output("pdsa-sheets-selection", "style"),  # PDSA lakšto pasirinkimo blokas
    Output("radio-sheet-tbl", "options"),  # Visi PDSA lakštai
    Output("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    Output("radio-sheet-col", "options"),  # Visi PDSA lakštai
    Output("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    Input("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis
    State("pdsa-sheets-selection", "style"),
    config_prevent_initial_callbacks=True,
)
def set_pdsa_sheet_radios(pdsa_dict, div_style):
    """
    Galimų lakštų pasirinkimų sukūrimas pagal įkeltą PDSA dokumentą.
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param div_style: HTML DIV, kuriame yra PDSA lakštai, stilius
    """
    if isinstance(pdsa_dict, dict) and "file_data" in pdsa_dict:
        sheets = list(pdsa_dict["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheets]

        # Automatiškai žymėti numatytuosius lakštus, jei jie yra
        preselect_tbl_sheet = "tables" if "tables" in sheets else (sheets[0] if len(sheets) == 1 else None)
        preselect_col_sheet = "columns" if "columns" in sheets else (sheets[0] if len(sheets) == 1 else None)

        # Nerodyti lakštų pasirinkimo, jei importuota iš JSON arba DBML
        visibility = set(sheets) != {"tables", "columns", "refs"}
        div_style = gu.change_style_display_value(visibility, div_style)

        return div_style, sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        div_style = gu.change_style_display_value(True, div_style)
        return div_style, [], None, [], None


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
        if len(sheets) == 1:
            preselect_refs_sheet = sheets[0]
        else:
            preselect_refs_sheet = next(
                (sheet for sheet in [
                    "refs", "references", "sql_2_references", "sql_2_references(in)", "SQL lentelių ryšiai", "sql_2"
                ] if sheet in sheets), None
            )
        visibility = (len(sheets) > 1) and set(sheets) != {"tables", "columns", "refs"}
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
    columns = fu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet, not_null_type=True)  # netušti stulpeliai
    columns_str = fu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet, string_type=True)  # tekstiniai stulpeliai
    columns_not_str = list(set(columns) - set(columns_str))  # ne tekstiniai stulpeliai
    columns_not_str = columns_not_str or columns

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" (arba "view") dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "table", "table_name", "view", "field", "Lentelė", "Lentelės Pavadinimas", "Pavadinimas"
        ] if col in columns_str), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių apibūdinimai
    comments_col = next(
        # "comment" dabartiniuose PDSA, "description" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "comment", "description", "note", "Lentelės aprašymas", "Aprašymas", "Komentaras", "Komentarai",
            "Sisteminis komentaras", "lenteles_paaiskinimas"
        ] if col in columns), None
    )
    n_records_col = "n_records" if "n_records" in columns_not_str else None  # "n_records" dabartiniuose PDSA

    return columns_str, tables_col, columns, comments_col, columns_not_str, n_records_col


# PDSA
@callback(
    Output("checkbox-tables-no-records", "style"),
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-no-records", "style"),
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
    columns = fu.get_sheet_columns(pdsa_dict, pdsa_tbl_sheet)
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
    State("pdsa-tables-table", "value"),
    config_prevent_initial_callbacks=True,
)
def create_pdsa_columns_sheet_column_dropdowns_for_graph(pdsa_dict, pdsa_col_sheet, tbl_tables_col):
    """
    Sukurti pasirinkimus, kuriuos PDSA lentelių lakšto stulpelius rodyti pačiuose grafikuose
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_col_sheet: PDSA stulpelių lakšto vardas
    :param tbl_tables_col: PDSA lentelių lakšte parinkto lentelių stulpelio vardas
    """
    columns = fu.get_sheet_columns(pdsa_dict, pdsa_col_sheet, not_null_type=True)  # netušti stulpeliai
    columns_str = fu.get_sheet_columns(pdsa_dict, pdsa_col_sheet, string_type=True)  # tekstiniai stulpeliai

    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių vardai
    tables_col = next(
        # "table" dabartiniuose PDSA, "field" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            tbl_tables_col, "table", "table_name", "view", "field", "Lentelė", "Lentelės Pavadinimas"
        ] if col in columns_str), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės lentelių stulpeliai
    columns_col = next(
        (col for col in ["column", "colname", "column_name", "Stulpelis", "Pavadinimas"] if col in columns_str), None
    )
    # PDSA lakšto stulpelis, kuriame nurodyta, ar duombazės lentelės stulpelis yra pirminis raktas
    primary_col = next(
        (col for col in ["is_primary", "Ar pirminis raktas"] if col in columns), None
    )
    # PDSA lakšto stulpelis, kuriame surašyti duombazės stulpelių apibūdinimai
    comments_col = next(
        # "comment" dabartiniuose PDSA, "description" matyt istoriškai senuose (pagal seną graferį)
        (col for col in [
            "comment", "description", "note", "Stulpelio aprašymas", "Aprašymas",
            "Komentaras", "Komentarai", "Sisteminis komentaras",
            "column_type", "type", "dtype", "Duomenų tipas", "Raktažodžiai", "Objektas"
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
    columns = fu.get_sheet_columns(pdsa_dict, pdsa_col_sheet)
    return columns, columns


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Input("memory-uploaded-pdsa", "data"),
    Input("radio-sheet-tbl", "value"),
    Input("dropdown-sheet-tbl", "value"),
    config_prevent_initial_callbacks=True,
)
def create_preview_of_pdsa_tbl_sheet(
    pdsa_dict, pdsa_tbl_sheet, sheet_tbl_selection
):
    """
    PDSA lakšto apie lenteles peržiūra
    :param pdsa_dict: žodynas su pdsa duomenimis {"file_data": {lakštas: {"df: df, ""df_columns": []}}}
    :param pdsa_tbl_sheet: PDSA lentelių lakšto vardas
    :param sheet_tbl_selection: pasirinktieji PDSA lentelių lakšto stulpeliai išplėstinei informacijai
    """
    if (
        (not pdsa_dict) or (not sheet_tbl_selection) or ("file_data" not in pdsa_dict) or
        (pdsa_tbl_sheet not in pdsa_dict["file_data"]) or ("df" not in pdsa_dict["file_data"][pdsa_tbl_sheet])
    ):
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
    columns = fu.get_sheet_columns(refs_data, refs_sheet)  # visi stulpeliai
    columns_str = fu.get_sheet_columns(refs_data, refs_sheet, string_type=True)  # tekstiniai stulpeliai
    if columns_str:
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios IŠORINIUS raktus
        preselected_source_tables = next(
            (
                col for col in
                ["TABLE_NAME", "table_name", "table", "Iš_lentelės", "Iš lentelės", "source_tbl"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip IŠORINIAI raktai
        preselected_source_columns = next(
            (
                col for col in
                ["COLUMN_NAME", "column_name", "column", "Iš_stulpelio", "Iš stulpelio", "source_col"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra LENTELĖS, naudojančios PIRMINIUS raktus
        preselected_target_tables = next(
            (
                col for col in
                ["REFERENCED_TABLE_NAME", "referenced_table_name", "referenced_table", "ref_table",
                 "Į_lentelę", "Į lentelę", "target_tbl"]
                if col in columns_str
             ), None
        )
        # Numatytieji vardai stulpelių, kuriuose yra STULPELIAI kaip PIRMINIAI raktai
        preselected_target_columns = next(
            (
                col for col in
                ["REFERENCED_COLUMN_NAME", "referenced_column_name", "referenced_column", "ref_column",
                 "Į_stulpelį", "Į stulpelį", "target_col"]
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
