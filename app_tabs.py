import os
import pandas as pd
import dash
from dash import (
    html, Output, Input, callback, dash_table, callback_context, State,
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
    Output("memory-uploaded-file", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
    Output("pdsa-file-name", "children"),  # pasirinktos rinkmenos PDSA vardas
    Input("upload-data", "contents"),  # kas paduota
    State("upload-data", "filename"),  # pasirinktos(-ų) rinkmenos(-ų) vardas(-ai)
)
def update_pdsa_output(list_of_contents, list_of_names):
    """
    PDSA rinkmenos įkėlimas.
    """
    if list_of_contents is not None:
        parse_output = gu.parse_file(list_of_contents)
        if type(parse_output) == str:
            # Klaida nuskaitant
            return {}, [list_of_names[0], html.Br(), parse_output]
        else:
            return parse_output, list_of_names[0]
    else:
        return {}, ""


# Ryšiai tarp lentelių
@callback(
    Output("memory-uploaded-file-uzklausa", "data"),
    Output("uzklausa-file-name", "children"),
    Input("upload-data-uzklausa", "contents"),
    State("upload-data-uzklausa", "filename"),
)
def update_uzklausa_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        parse_output = gu.parse_file(list_of_contents)
        if type(parse_output) == str:
            # Klaida nuskaitant
            return {}, [list_of_names[0], html.Br(), parse_output]
        else:
            return parse_output, list_of_names[0]
    else:
        return {}, []


# PDSA
@callback(
    Output("radio-sheet-tbl", "options"),
    Output("radio-sheet-tbl", "value"),
    Output("radio-sheet-col", "options"),
    Output("radio-sheet-col", "value"),
    Input("memory-uploaded-file", "data"),  # nuskaitytas pasirinktos PDSA rinkmenos turinys
)
def get_data_about_xlsx(xlsx_data):
    if xlsx_data:
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
    Input("memory-uploaded-file-uzklausa", "data"),
)
def get_dropdowns_and_preview_source_target(uzklausa_data):
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
    Output("memory-pdsa-meta-info", "data"),
    Input("memory-uploaded-file", "data"),
    Input("radio-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),
    config_prevent_initial_callbacks=True,
)
def store_sheet_names_and_columns(xlsx_data, sheet_name_tbl, sheet_name_col):
    xlsx_data["sheet_tbl"] = sheet_name_tbl
    xlsx_data["sheet_col"] = sheet_name_col
    return xlsx_data


# PDSA
@callback(
    Output("id-sheet-tbl", "children"),
    Output("dropdown-sheet-tbl", "options"),
    Output("dropdown-sheet-tbl", "value"),
    Input("memory-pdsa-meta-info", "data"),
)
def create_pdsa_tables_sheet_column_dropdowns(xlsx_data):
    sheet, columns = gu.create_pdsa_sheet_column_dropdowns(xlsx_data, "sheet_tbl")
    return sheet, columns, columns


# PDSA
@callback(
    Output("id-sheet-col", "children"),
    Output("dropdown-sheet-col", "options"),
    Output("dropdown-sheet-col", "value"),
    Input("memory-pdsa-meta-info", "data"),
)
def create_pdsa_columns_sheet_column_dropdowns(xlsx_data):
    sheet, columns = gu.create_pdsa_sheet_column_dropdowns(xlsx_data, "sheet_col")
    return sheet, columns, columns


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Input("memory-pdsa-meta-info", "data"),
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
    Input("memory-pdsa-meta-info", "data"),
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
    Output("dropdown-tables", "options"),  # galimos pasirinkti braižymui lentelės
    Output("dropdown-tables", "value"),  # automatiškai braižymui parinktos lentelės (iki 10)
    Output("tabs-container", "active_tab"),  # aktyvios kortelės identifikatorius (perjungimui, jei reikia)
    Output("button-submit", "color"),
    State("memory-pdsa-meta-info", "data"),
    State("memory-uploaded-file-uzklausa", "data"),
    Input("dropdown-sheet-tbl", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("ref-source-tables", "value"),
    Input("ref-target-tables", "value"),
    Input("button-submit", "n_clicks"),  # tik kaip funkcijos paleidiklis paspaudžiant mygtuką
)
def summarize_submission(
    pdsa_info,
    uzklausa_info,
    dropdown_sheet_tbl,
    dropdown_sheet_col,
    ref_source_tbl,
    ref_target_tbl,
    n_clicks,  # noqa
):
    """
    Suformuoti visuminę naudingų duomenų struktūrą, jei turime visus reikalingus PDSA ir ryšių duomenis.
    :param pdsa_info: žodynas su PDSA duomenimis:
        "file_data" - žodynas su visu PDSA turiniu;
        "sheet_tbl" - PDSA lakšto, aprašančio lenteles, pavadinimas
        "sheet_col" - PDSA lakšto, aprašančio stulpelius, pavadinimas
    :param uzklausa_info: žodynas su ryšių tarp lentelių duomenimis:
        "file_data" - žodynas su visu dokumento turiniu;
    :param dropdown_sheet_tbl: sąrašas stulpelių, kurie yra pdsa_info["sheet_tbl"] (lentelių) lakšte
    :param dropdown_sheet_col: sąrašas stulpelių, kurie yra pdsa_info["sheet_col"] (stulpelių) lakšte
    :param ref_source_tbl: vardas stulpelio, kuriame surašytos ryšio pradžių („IŠ“) lentelės (su išoriniu raktu)
    :param ref_target_tbl: vardas stulpelio, kuriame surašytos ryšio galų („Į“) lentelės (su pirminiu raktu)
    :param n_clicks: mygtuko paspaudimų skaičius, bet pati reikšmė nenaudojama
    :return: visų pagrindinių duomenų struktūra, braižytinos lentelės, aktyvi kortelė.


    visų naudingų duomenų struktūros pavyzdys:
        data_final = {
            "node_data": {  # PDSA
                "file_data":
                    {"sheet_name_1":
                        {"df_columns": [],
                         "df": [] },

                    },
                "sheet_tbl": "",  # pridedamas interaktyvume (callback'uose)
                "sheet_col": "",  # pridedamas interaktyvume (callback'uose)
            },
            "edge_data":{  # Ryšiai
                "file_data":
                    {"sheet_name_1":
                        {
                            "df_columns": [],
                            "df": []
                        }
                    },
                "col_source":"",  # pridedamas interaktyvume (callback'uose)
                "col_target":"",  # pridedamas interaktyvume (callback'uose)
                "list_all_tables":"",  # pridedamas interaktyvume (callback'uose)
            }}
    """
    if None not in (pdsa_info, uzklausa_info, ref_source_tbl, ref_target_tbl):
        # Papildau ryšių duomenis source/target stulpelių pavadinimais
        uzklausa_info["col_source"] = ref_source_tbl
        uzklausa_info["col_target"] = ref_target_tbl

        # Surinktą informaciją transformuoju ir paruošiu graferiui
        sheet_tbl = pdsa_info["sheet_tbl"]
        sheet_col = pdsa_info["sheet_col"]
        if None in (sheet_tbl, sheet_col):
            return {}, [], [], "file_upload", "secondary"

        # PDSA lakšto (sheet_tbl), aprašančio lenteles, turinys
        df_tbl = pdsa_info["file_data"][sheet_tbl]["df"]
        df_tbl = pd.DataFrame.from_records(df_tbl)

        if (
            "lenteles_paaiskinimas"
            in pdsa_info["file_data"][sheet_tbl]["df_columns"]
        ):
            df_tbl = df_tbl.sort_values(by="lenteles_paaiskinimas")

        df_tbl = df_tbl.loc[:, dropdown_sheet_tbl]

        # PDSA lakšto (sheet_col), aprašančio stulpelius, turinys
        df_col = pdsa_info["file_data"][sheet_col]["df"]
        df_col = pd.DataFrame.from_records(df_col)

        df_col = df_col.dropna(how="all")
        df_col = df_col.loc[:, dropdown_sheet_col]

        # Sukurti ryšių pd.DataFrame tinklo piešimui
        sheet_uzklausa = list(uzklausa_info["file_data"].keys())[0]  # ryšių lakšto pavadinimas

        df_edges = uzklausa_info["file_data"][sheet_uzklausa]["df"]
        df_edges = pd.DataFrame.from_records(df_edges)

        df_edges = df_edges.loc[:, [ref_source_tbl, ref_target_tbl]]

        df_edges.columns = ["table_x", "table_y"]  # pervadinti stulpelius į toliau viduje sistemiškai naudojamus
        df_edges = df_edges.loc[df_edges["table_x"] != df_edges["table_y"], :]  # išmesti nuorodas į save

        # Visų unikalių lentelių, turinčių ryšių, sąrašas
        list_all_tables = (
            df_edges["table_x"].dropna().tolist()
            + df_edges["table_y"].dropna().tolist()
        )
        list_all_tables = sorted(list(set(list_all_tables)))

        if not list_all_tables:
            # Visos lentelės rodo į save – nieko negalės piešti.
            # Ateityje atskirti visas ir galimas piešti ryšiams lenteles.
            return {}, [], [], "file_upload", "secondary"

        # %% VISĄ SURINKTĄ INFORMACIJĄ SUKELIU Į VIENĄ STRUKTŪRĄ: {k:v}
        data_final = {}

        pdsa_info["file_data"][sheet_tbl]["df"] = df_tbl.to_dict("records")
        pdsa_info["file_data"][sheet_col]["df"] = df_col.to_dict("records")

        uzklausa_info["file_data"][sheet_uzklausa]["df"] = df_edges.to_dict(
            "records"
        )
        uzklausa_info["file_data"]["list_all_tables"] = list_all_tables

        data_final["node_data"] = pdsa_info
        data_final["edge_data"] = uzklausa_info
        data_final["edge_data"]["list_all_tables"] = list_all_tables

        # Automatiškai žymėti lenteles piešimui
        if len(list_all_tables) <= 10:
            # visos ryšių turinčios lentelės, jei jų iki 10
            preselected_tables = list_all_tables  # braižyti visas
        else:
            # iki 10 populiariausių lentelių tarpusavio ryšiuose; nebūtinai tarpusavyje susijungiančios
            # ryšių su lentele dažnis mažėjančia tvarka
            table_links_n = pd.concat([df_edges['table_x'], df_edges['table_y']]).value_counts()
            if table_links_n.iloc[9] < table_links_n.iloc[10]:
                preselected_tables = table_links_n.index[:10].to_list()
            else:
                table_links_n_threshold = table_links_n.iloc[9] + 1
                preselected_tables = table_links_n[table_links_n >= table_links_n_threshold].index.to_list()
            # Pašalinti mazgus, kurie neturi tarpusavio ryšių su parinktaisiais
            preselected_tables = gu.remove_orphaned_nodes_from_sublist(preselected_tables, df_edges)
            if not preselected_tables:  # jei netyčia nei vienas tarpusavyje nesijungia, imti du su daugiausia kt. ryšių
                preselected_tables = table_links_n.index[:2].to_list()

        changed_id = [p["prop_id"] for p in callback_context.triggered][0]
        if "button-submit" in changed_id:
            # Perduoti duomenis naudojimui grafiko kortelėje ir į ją pereiti
            return data_final, list_all_tables, preselected_tables, "graph", "primary"
        else:
            # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje
            return data_final, list_all_tables, preselected_tables, "file_upload", "primary"
    return {}, [], [], "file_upload", "secondary"



# ========================================
# Interaktyvumai grafiko kortelėje
# ========================================

@callback(
    Output("filter-tbl-in-df", "options"),
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
)
def get_dropdown_tables_info_col_display_options(data_submitted):
    if data_submitted:
        return data_submitted["edge_data"]["list_all_tables"]
    else:
        return []


@callback(
    Output("my-network", "children"),
    Input("tabs-container", "active_tab"),
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Input("dropdown-layouts", "value"),
    Input("dropdown-tables", "value"),
    Input("input-list-tables", "value"),
    Input("checkbox-get-neighbours", "value"),
)
def get_network(
    active_tab, data_submitted, layout, selected_dropdown_tables, input_list_tables, get_neighbours
):
    """
    Atvaizduoja visas pasirinktas lenteles kaip tinklo mazgus.
    :param active_tab: aktyvi kortelė ("file_upload" arba "graph")
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param layout: išdėstymo stilius (pvz., "cola")
    :param selected_dropdown_tables: išskleidžiamajame sąraše pasirinktos braižytinos lentelės
    :param input_list_tables: tekstiniame lauke surašytos papildomos braižytinos lentelės
    :param get_neighbours: ar rodyti kaimynus
    """
    if (
            not data_submitted  # apskritai nėra įkeltų duomenų
            or active_tab != "graph"  # esame kitoje nei grafiko kortelėje
            or (not selected_dropdown_tables and not input_list_tables)  # įkelti, bet nepasirinkti
    ):
        # Tuščias grafikas, bet būtina grąžinti kaip Cytoscape objektą, kad ir be objektų, antraip nulūžta
        return gu.get_fig_cytoscape()

    list_all_tables = data_submitted["edge_data"]["list_all_tables"]

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    if input_list_tables is not None:
        input_list_tables = [x.strip() for x in input_list_tables.split(",")]
        selected_dropdown_tables = list(
            set(selected_dropdown_tables + input_list_tables)
        )

    submitted_edge_data_sheet = list(data_submitted["edge_data"]["file_data"].keys())[0]
    submitted_edge_data = data_submitted["edge_data"]["file_data"][submitted_edge_data_sheet]["df"]

    # Jei langelis „Rodyti kaimynus“/„Get neighbours“ nenuspaustas:
    if not get_neighbours:
        # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
        dict_filtered = [
            x
            for x in submitted_edge_data
            if x["table_x"] in selected_dropdown_tables
            or x["table_y"] in selected_dropdown_tables
        ]

        # Išskaidau table_x ir table_y į sąrašus; visos lentelės, kurios nebuvo pasirinktos, yra pakeičiamos į None
        dict_filtered_x = [
            i["table_x"] if i["table_x"] in selected_dropdown_tables else None
            for i in dict_filtered
        ]
        dict_filtered_y = [
            i["table_y"] if i["table_y"] in selected_dropdown_tables else None
            for i in dict_filtered
        ]

        # Sutraukiu atgal į poras (table_x val, table_y val)
        dict_filtered = list(zip(dict_filtered_x, dict_filtered_y))
        # Pašalinu besikartojančias poras
        dict_filtered = set(dict_filtered)
        # Gražinu į dict
        dict_filtered = [{"table_x": i[0], "table_y": i[1]} for i in dict_filtered]

    else:
        neighbours = [x for x in list_all_tables if x in selected_dropdown_tables]

        new_selected_dropdown_tables = neighbours + selected_dropdown_tables

        dict_filtered = [
            x
            for x in submitted_edge_data
            if x["table_x"] in new_selected_dropdown_tables
            or x["table_y"] in new_selected_dropdown_tables
        ]

    if dict_filtered:
        df_filtered = pd.DataFrame.from_records(dict_filtered)
        df_filtered = df_filtered.drop_duplicates()
        g = gu.get_fig_cytoscape(df=df_filtered, layout=layout)
        return g


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
    sheet_col = data_submitted["node_data"]["sheet_col"]
    data_about_nodes = data_submitted["node_data"]["file_data"][sheet_col]["df"]
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
    Input("my-network", "children"),
)
def create_dash_table_of_displayed_neighbours(data_submitted, get_displayed_nodes_info, g):
    """
    Informacija apie grafike rodomas lenteles iš PDSA lakšto „tables“

    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param get_displayed_nodes_info: ar pateikti nubraižytų lentelių informaciją
    :param g: grafiko duomenys
    :return: dash_table objektas
    """

    if (not data_submitted) or (g is None):
        return dash_table.DataTable()

    sheet_tbl = data_submitted["node_data"]["sheet_tbl"]
    data_about_nodes = data_submitted["node_data"]["file_data"][sheet_tbl]["df"]

    df_tbl = pd.DataFrame.from_records(data_about_nodes)
    if get_displayed_nodes_info and ("table" in df_tbl):
        displayed_nodes = g["props"]["elements"]
        # tinklo mazgai turi raktą "id" ir "label", bet jungimo linijos jų neturi (jos turi tik "source" ir "target")
        displayed_nodes = [x["data"]["id"] for x in displayed_nodes if "id" in x["data"]]
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
    Output("filter-tbl-in-df", "value"),
    Input("org-chart", "selectedNodeData"),
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
    Input('org-chart', 'selectedNodeData'),
    Input("org-chart", 'tapNode'),
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
        selected_nodes_id = [node['id'] for node in selected_nodes_data]
        if tap_node and tap_node["selected"] and [tap_node['data']['id']] == selected_nodes_id:
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
            node_label = tap_node['data']['label']
            tooltip_header = [html.H6(node_label)]
            sheet_tbl = data_submitted["node_data"]["sheet_tbl"]
            data_about_nodes_tbl = data_submitted["node_data"]["file_data"][sheet_tbl]["df"]
            df_tbl = pd.DataFrame.from_records(data_about_nodes_tbl)
            if ("table" in df_tbl) and ("comment" in df_tbl):
                table_comment = df_tbl[df_tbl["table"] == node_label]["comment"]
                if not table_comment.empty:
                    tooltip_header.append(html.P(table_comment.iloc[0]))
                tooltip_header.append(html.Hr())

            # %% Turinys
            content = []

            # Turinys: ryšiai
            submitted_edge_data_sheet = list(data_submitted["edge_data"]["file_data"].keys())[0]
            submitted_edge_data = data_submitted["edge_data"]["file_data"][submitted_edge_data_sheet]["df"]
            displayed_tables_x = {x["source"] for x in tap_node["edgesData"]}
            displayed_tables_y = {y["target"] for y in tap_node["edgesData"]}
            # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
            dict_filtered = [
                x
                for x in submitted_edge_data
                if (x["table_x"] == node_label and x["table_y"] not in displayed_tables_y) or
                   (x["table_y"] == node_label and x["table_x"] not in displayed_tables_x)
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
                                    html.Tr([html.Td([row["table_x"], html.B(" -> "), row["table_y"]])])
                                    for row in dict_filtered
                                ]
                            )
                        ]
                    ),
                    html.Br(),
                ])

            # Turinys: stulpeliai
            sheet_col = data_submitted["node_data"]["sheet_col"]
            data_about_nodes_col = data_submitted["node_data"]["file_data"][sheet_col]["df"]
            df_col = pd.DataFrame.from_records(data_about_nodes_col)
            df_col = df_col[df_col["table"] == node_label]
            if all(col in df_col for col in ["table", "column", "comment"]) and not df_col.empty:
                table_rows = []
                for idx, row in df_col.iterrows():
                    table_row = ["- ", html.B(row["column"])]
                    if ("is_primary" in row) and pd.notna(row["is_primary"]) and row["is_primary"]:
                        table_row.append(" 🔑")  # pirminis raktas
                    if ("comment" in row) and pd.notna(row["comment"]) and row["comment"]:
                        table_row.extend([" – ", row["comment"]])  # paaiškinimas
                    table_rows.append(html.Tr([html.Td(table_row)]))
                content.append(
                        html.Table(
                        children=[
                            html.Thead(html.Tr([html.Th(html.U(_("Columns:")))])),
                            html.Tbody(table_rows)
                        ]
                    )
                )

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
