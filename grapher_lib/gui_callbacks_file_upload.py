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
    Output("uzklausa-file-name", "children"),
    Input("upload-data-uzklausa", "contents"),
    State("upload-data-uzklausa", "filename"),
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
    Input("memory-uploaded-pdsa-init", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
)
def set_pdsa_sheet_radios(pdsa_data):
    """
    Galimų naudotojui pasirinkimų sukūrimas pagal įkeltą PDSA dokumentą.
    :param pdsa_data: nuskaitytas pasirinktos PDSA rinkmenos turinys
    """
    if isinstance(pdsa_data, dict) and "file_data" in pdsa_data:
        sheet_names = list(pdsa_data["file_data"].keys())
        sheet_options = [{"label": x, "value": x} for x in sheet_names]

        # Automatiškai žymėti numatytuosius lakštus, jei jie yra
        preselect_tbl_sheet = "tables" if ("tables" in sheet_names) else None
        preselect_col_sheet = "columns" if ("columns" in sheet_names) else None

        return sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        return [], None, [], None


# PDSA
@callback(
    Output("memory-uploaded-pdsa-plus", "data"),  # žodynas su PDSA duomenimis, papildytas
    Input("memory-uploaded-pdsa-init", "data"),  # žodynas su PDSA duomenimis, pradinis
    Input("radio-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),
    config_prevent_initial_callbacks=True,
)
def store_pdsa_sheet_names_and_columns(pdsa_dict, sheet_name_tbl, sheet_name_col):
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

        df = refs_data["file_data"][sheet_name]["df"][0:10]

        children_df_tbl = dash_table.DataTable(
            df,
            [{"name": i, "id": i} for i in refs_columns],
            style_table={"overflowX": "scroll"},
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
                "tbl_sheet_data": [],  # PDSA lakšto, aprašančio lenteles, turinys
                "col_sheet_data": [],  # PDSA lakšto, aprašančio stulpelius, turinys
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
            "tbl_sheet_data": df_tbl.to_dict("records"),  # PDSA lakšto, aprašančio lenteles, turinys
            "col_sheet_data": df_col.to_dict("records"),  # PDSA lakšto, aprašančio stulpelius, turinys
            "sheet_tbl": sheet_tbl,  # PDSA lakšto, aprašančio lenteles, pavadinimas
            "sheet_col": sheet_col,  # PDSA lakšto, aprašančio stulpelius, pavadinimas
            "list_tbl_tables": pdsa_tbl_tables,  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
            "list_col_tables": pdsa_col_tables or [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
            "list_all_tables": pdsa_all_tables,  # visos iš PDSA kartu
        },
        # Ryšių duomenys
        "edge_data": {
            "ref_sheet_data": df_edges.to_dict("records"),
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
