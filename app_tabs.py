import os
import pandas as pd
import dash
from dash import (
    Dash, dcc, html, Output, Input, callback, dash_table, callback_context, State,
)
import dash_bootstrap_components as dbc
from grapher_lib import utils as gu
from grapher_lib import utils_tabs_layouts as uw
from locale_utils.translations import set_gettext_locale


# ========================================
# Pradinė konfigūracija
# ========================================

# Pandas parinktys
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# Dash app
external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
)

# Kalbos
LANGUAGES = {
    "en": "English",
    "lt": "Lietuvių"
}
if (
        (not os.path.exists("locale/lt/LC_MESSAGES/pdsa-grapher.mo")) or
        (not os.path.exists("locale/en/LC_MESSAGES/pdsa-grapher.mo"))
):
    # Pradiniame kode paprastai kompiliuotieji MO nėra pateikiami - jie pateikiami platinamoje programoje.
    # Jei jų nebuvo - pirmą kartą paleidžiant programą vertimai sukompiliuosimi automatiškai
    from locale_utils import translation_files_update as tu # tyčia importuoti tik pagal poreikį, o ne viršuje visada
    if (
        os.path.exists("locale/lt/LC_MESSAGES/pdsa-grapher.po") and
        os.path.exists("locale/en/LC_MESSAGES/pdsa-grapher.po")
    ):
        # Vertimų MO nėra, bet yra PO - užtenka tik perkompiliuoti MO (POT ir PO nėra atnaujinami).
        # Tai jei pravers, jei naudotojas rankiniu būdu redagavo PO vertimų rinkmenas (ir ištrynė MO perkompiliavimui)
        tu.recompile_all_po(app_name="pdsa-grapher")
    else:
        # Sukurti visas reikalingas POT, PO, MO vertimų rinkmenas iš naujo
        tu.Pot(app_name="pdsa-grapher", languages=["lt", "en"], force_regenerate=True)


# Išdėstymas
def tab_layout():
    """Kortelės: 1) rinkmenų įkėlimui; 2) grafikams"""
    return [
        dbc.Tab(uw.file_uploading_tab_layout(), tab_id="file_upload", label=_("File upload")),
        dbc.Tab(uw.grapher_tab_layout(), tab_id="graph", label=_("Graphic")),
    ]


def app_layout():
    return html.Div(
        style={"margin-top": "20px", "margin-left": "20px", "margin-right": "20px"},
        children=[
            dbc.Tab([
                    dbc.DropdownMenu(
                        label="🌐",
                        children=[
                            dbc.DropdownMenuItem("EN", id="en", n_clicks=0),
                            dbc.DropdownMenuItem("LT", id="lt", n_clicks=0)
                        ],
                        id="language-dropdown",
                        style={"float": "right"}
                    ),
            ]),
            dbc.Tabs(
                children=tab_layout(),
                id="tabs-container"
            ),
        ],
    )


# ========================================
# Interaktyvumai
# ========================================

@callback(
    [
        Output("language-dropdown", "label"),
        Output("language-dropdown", "children"),
        Output("tabs-container", "children")
    ],
    [
        Input("en", "n_clicks"),
        Input("lt", "n_clicks")
    ]
)
def update_language(en_clicks, lt_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        language = "lt"  # numatytoji lietuvių kalba; arba galite naudoti locale.getlocale()[0]
    else:
        language = ctx.triggered[0]["prop_id"].split(".")[0]
    print("Pasirinkta kalba:", language)

    with app.server.test_request_context():
        set_gettext_locale(language)
        return (
            "🌐 " + language.upper(),
            [dbc.DropdownMenuItem(name, id=lang, n_clicks=0) for lang, name in LANGUAGES.items()],
            tab_layout()
        )


# PDSA
@callback(
    Output("memory-uploaded-file", "data"),
    Output("pdsa-file-name", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_pdsa_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        parse_output = gu.parse_file(list_of_contents)

        return parse_output, list_of_names[0]
    else:
        return {}, ""


# UŽKLAUSA
@callback(
    Output("memory-uploaded-file-uzklausa", "data"),
    Output("uzklausa-file-name", "children"),
    Input("upload-data-uzklausa", "contents"),
    State("upload-data-uzklausa", "filename"),
)
def update_uzklausa_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        parse_output = gu.parse_file(list_of_contents)

        return parse_output, list_of_names
    else:
        return {}, []


# PDSA
@callback(
    Output("pdsa-sheets", "children"),
    Output("radio-sheet-tbl", "options"),
    Output("radio-sheet-tbl", "value"),
    Output("radio-sheet-col", "options"),
    Output("radio-sheet-col", "value"),
    Input("memory-uploaded-file", "data"),
)
def get_data_about_xlsx(xlsx_data):
    if xlsx_data:
        if type(xlsx_data) == str:
            # If it is string, then xlsx=="There was an error processing this file."
            return xlsx_data, [], None, [], None
        else:
            sheet_names = list(xlsx_data["file_data"].keys())
            sheet_names_detected = ", ".join(sheet_names)
            sheet_options = [{"label": x, "value": x} for x in sheet_names]

            # Automatiškai žymėti numatytuosius lakštus, jei jie yra
            preselect_tbl_sheet = "tables" if ("tables" in sheet_names) else None
            preselect_col_sheet = "columns" if ("columns" in sheet_names) else None

            return sheet_names_detected, sheet_options, preselect_tbl_sheet, sheet_options, preselect_col_sheet
    else:
        return "", [], None, [], None


# UŽKLAUSA
@callback(
    Output("id-radio-uzklausa-source", "options"),
    Output("id-radio-uzklausa-source", "value"),
    Output("id-radio-uzklausa-target", "options"),
    Output("id-radio-uzklausa-target", "value"),
    Output("uzklausa-tbl-preview", "children"),
    Input("memory-uploaded-file-uzklausa", "data"),
)
def get_dropdowns_and_preview_source_target(uzklausa_data):
    if uzklausa_data:
        sheet_name = list(uzklausa_data["file_data"].keys())[0]
        uzklausa_columns = uzklausa_data["file_data"][sheet_name]["df_columns"]
        # Numatytieji automatiškai pažymimi vardai stulpelių, kuriuose yra LENTELĖS, naudojančios išorinius raktus
        preselected_source = next(
            (
                col for col in
                ["TABLE_NAME", "table", "Iš_lentelės", "Iš lentelės"]
                if col in uzklausa_columns
             ), None
        )
        # Numatytieji automatiškai pažymimi vardai stulpelių, kuriuose yra LENTELĖS, naudojančios pirminius raktus
        preselected_target = next(
            (
                col for col in
                ["REFERENCED_TABLE_NAME", "referenced_table", "Į_lentelę", "Į lentelę"]
                if col in uzklausa_columns
             ), None
        )

        df = uzklausa_data["file_data"][sheet_name]["df"][0:10]

        children_df_tbl = dash_table.DataTable(
            df,
            [{"name": i, "id": i} for i in uzklausa_columns],
            style_table={"overflowX": "scroll"},
        )

        return uzklausa_columns, preselected_source, uzklausa_columns, preselected_target, children_df_tbl
    else:
        return [], None, [], None, dash_table.DataTable(style_table={"overflowX": "scroll"})

# PDSA
@callback(
    Output("memory-pdsa-meta-info", "data"),
    Input("memory-uploaded-file", "data"),
    Input("radio-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),
    config_prevent_initial_callbacks=True,
)
def store_sheet_names_and_columns(xlsx_data, sheet_name_tbl, sheet_name_col):
    if None not in [sheet_name_tbl, sheet_name_col]:
        xlsx_data["sheet_tbl"] = sheet_name_tbl
        xlsx_data["sheet_col"] = sheet_name_col

        return xlsx_data


# PDSA
@callback(
    Output("id-sheet-tbl", "children"),
    Output("dropdown-sheet-tbl", "options"),
    Output("dropdown-sheet-tbl", "value"),
    Output("id-sheet-col", "children"),
    Output("dropdown-sheet-col", "options"),
    Output("dropdown-sheet-col", "value"),
    Input("memory-pdsa-meta-info", "data"),
)
def create_column_dropdowns(xlsx_data):
    if xlsx_data is not None:
        if "sheet_tbl" in xlsx_data.keys() and "sheet_col" in xlsx_data.keys():
            sheet_tbl = xlsx_data["sheet_tbl"]
            sheet_col = xlsx_data["sheet_col"]

            sheet_tbl_columns = xlsx_data["file_data"][sheet_tbl]["df_columns"]
            sheet_col_columns = xlsx_data["file_data"][sheet_col]["df_columns"]

            return (
                sheet_tbl,
                sheet_tbl_columns,
                sheet_tbl_columns,
                sheet_col,
                sheet_col_columns,
                sheet_col_columns,
            )

    return "", [], [], "", [], []


# PDSA
@callback(
    Output("sheet-tbl-preview", "children"),
    Output("sheet-col-preview", "children"),
    Input("memory-pdsa-meta-info", "data"),
    Input("dropdown-sheet-tbl", "value"),
    Input("dropdown-sheet-col", "value"),
)
def create_preview_of_pdsa_sheets(xlsx_data, sheet_tbl_selection, sheet_col_selection):
    def check_input_conditions(variable):
        if variable is None:
            variable = []

        conditions = [type(variable) == list, len(variable) > 1]

        return any(conditions)
    
    if not xlsx_data:
        empty_table = dash_table.DataTable(style_table={"overflowX": "scroll"})
        return empty_table, empty_table
    if (
      check_input_conditions(sheet_tbl_selection) and 
      check_input_conditions(sheet_col_selection)
    ):
        sheet_tbl = xlsx_data["sheet_tbl"]
        sheet_col = xlsx_data["sheet_col"]

        df_tbl = xlsx_data["file_data"][sheet_tbl]["df"][0:10]
        df_col = xlsx_data["file_data"][sheet_col]["df"][0:10]

        children_df_tbl = dash_table.DataTable(
            df_tbl,
            [{"name": i, "id": i} for i in sheet_tbl_selection],
            style_table={"overflowX": "scroll"},
        )
        children_df_col = dash_table.DataTable(
            df_col,
            [{"name": i, "id": i} for i in sheet_col_selection],
            style_table={"overflowX": "scroll"},
        )

        return children_df_tbl, children_df_col


@callback(
    Output("memory-submitted-data", "data"),
    Output("dropdown-tables", "value"),
    Output("tabs-container", "active_tab"),
    State("memory-pdsa-meta-info", "data"),
    State("memory-uploaded-file-uzklausa", "data"),
    Input("dropdown-sheet-tbl", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("id-radio-uzklausa-source", "value"),
    Input("id-radio-uzklausa-target", "value"),
    Input("button-submit", "n_clicks"),
)
def summarize_submission(
    pdsa_info,
    uzklausa_info,
    dropdown_sheet_tbl,
    dropdown_sheet_col,
    radio_source,
    radio_target,
    n_clicks,
):
    if None not in (pdsa_info, uzklausa_info, radio_source, radio_target):
        ###########################################################
        # Papildau uzklasos duomenis souuce/target stulpelių pavadinimais
        ###########################################################
        uzklausa_info["col_source"] = radio_source
        uzklausa_info["col_target"] = radio_target

        ###########################################################
        # Surinktą informaciją transformuoju ir paruošiu graferiui
        ###########################################################
        sheet_tbl = pdsa_info["sheet_tbl"]
        sheet_col = pdsa_info["sheet_col"]

        ############################
        # get_data_about_tbls_n_cols
        ############################

        ###########
        # sheet_tbl
        ###########
        df_tbl = pdsa_info["file_data"][sheet_tbl]["df"]
        df_tbl = pd.DataFrame.from_records(df_tbl)

        if (
            "lenteles_paaiskinimas"
            in pdsa_info["file_data"][sheet_tbl]["df_columns"]
        ):
            df_tbl = df_tbl.sort_values(by="lenteles_paaiskinimas")

        df_tbl = df_tbl.loc[:, dropdown_sheet_tbl]

        ###########
        # sheet_col
        ###########
        df_col = pdsa_info["file_data"][sheet_col]["df"]
        df_col = pd.DataFrame.from_records(df_col)

        df_col = df_col.dropna(how="all")
        df_col = df_col.loc[:, dropdown_sheet_col]

        ############################
        # apply_requirements_for_the_app
        ############################
        if "field" in df_tbl.columns:
            df_tbl = df_tbl.rename({"field": "table"}, axis=1)
        if "field" in df_col.columns:
            df_col = df_col.rename({"field": "column"}, axis=1)

        ############################
        # get_edge_dataframe_for_network
        ############################

        sheet_uzklausa = list(uzklausa_info["file_data"].keys())[0]

        col_source = uzklausa_info["col_source"]
        col_target = uzklausa_info["col_target"]

        df_edges = uzklausa_info["file_data"][sheet_uzklausa]["df"]
        df_edges = pd.DataFrame.from_records(df_edges)

        df_edges = df_edges.loc[:, [col_source, col_target]]

        df_edges.columns = ["table_x", "table_y"]
        df_edges = df_edges.loc[df_edges["table_x"] != df_edges["table_y"], :]

        ############################
        # get unique list of tables
        ############################
        list_all_tables = (
            df_edges["table_x"].dropna().tolist()
            + df_edges["table_y"].dropna().tolist()
        )
        list_all_tables = sorted(list(set(list_all_tables)))

        ###########################################################
        # Visą surinktą informaciją sukeliu į vieną struktūrą: {k:v}
        ###########################################################
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
        #     Gaunama struktūra:
        # data_final = {
        #     "node_data": {
        #         "file_data":
        #             {"sheet_name_1":
        #                 {"df_columns": [],
        #                  "df": [] },
        #
        #             },
        #         "sheet_tbl": "",  # šitas key pridedamas callback'uose
        #         "sheet_col": "",  # šitas key pridedamas callback'uose
        #     },
        #     "edge_data":{
        #         "file_data":
        #             {"sheet_name_1":
        #                 {
        #                     "df_columns": [],
        #                     "df": []
        #                 }
        #             },
        #         "col_source":"", # šitas key pridedamas callback'uose
        #         "col_target":"", # šitas key pridedamas callback'uose
        #         "list_all_tables":"", # šitas key pridedamas callback'uose
        #     }}

        # Automatiškai žymėti lenteles piešimui
        if len(list_all_tables) <= 10:
            # visos, jei iki 10
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

        changed_id = [p["prop_id"] for p in callback_context.triggered][0]
        if "button-submit" in changed_id:
            # Perduoti duomenis naudojimui grafiko kortelėje ir į ją pereiti
            return data_final, preselected_tables, "graph"
        else:
            # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje
            return data_final, preselected_tables, "file_upload"
    return {}, [], "file_upload"

##########################################################
##########################################################
##########################################################
# Grapher call backai
##########################################################
##########################################################
##########################################################


@callback(
    Output("dropdown-tables", "options"),
    Input("memory-submitted-data", "data"),
)
def get_dropdown_display_node_tables_options(data_submitted):
    if data_submitted:
        return data_submitted["edge_data"]["list_all_tables"]
    else:
        return []
    

@callback(
    Output("filter-tbl-in-df", "options"),
    Input("memory-submitted-data", "data"),
)
def get_dropdown_tables_info_col_display_options(data_submitted):
    if data_submitted:
        return data_submitted["edge_data"]["list_all_tables"]
    else:
        return []


@callback(
    Output("my-network", "children"),
    Input("memory-submitted-data", "data"),
    Input("dropdown-layouts", "value"),
    Input("dropdown-tables", "value"),
    Input("input-list-tables", "value"),
    Input("checkbox-get-neighbours", "value"),
)
def get_network(
    data_submitted, layout, selected_dropdown_tables, input_list_tables, get_neighbours
):
    """
    Tikslas yra atvaizduoti visus nodes, kurie yra pasirinkti iš dropdown menu
    Mygtukas "get neighbours" į grafą prideda visu pasirinktų lentelių kaimynus

    :param data_submitted:
    :param selected_dropdown_tables:
    :param layout:
    :param input_list_tables:
    :param get_neighbours:
    :return:
    """
    if not data_submitted:
        return
    
    list_all_tables = data_submitted["edge_data"]["list_all_tables"]

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    if input_list_tables is not None:
        input_list_tables = [x.strip() for x in input_list_tables.split(",")]
        selected_dropdown_tables = list(
            set(selected_dropdown_tables + input_list_tables)
        )
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    submitted_edge_data_sheet = list(data_submitted["edge_data"]["file_data"].keys())[0]
    submitted_edge_data = data_submitted["edge_data"]["file_data"][
        submitted_edge_data_sheet
    ]["df"]

    # Jei langelis „Rodyti kaimynus“/„Get neighbours“ nenuspaustas:
    if not get_neighbours:
        # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių

        dict_filtered = [
            x
            for x in submitted_edge_data
            if x["table_x"] in selected_dropdown_tables
            or x["table_y"] in selected_dropdown_tables
        ]

        # Išskaidau table_x ir table_y į listus ir juos visas lenteles kurios nebuvo pasirinktos yra pakeičiamos į None
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
        # Pašalinu duplikatines poras
        dict_filtered = set(dict_filtered)
        # Gražinu į dict """"

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
        g = gu.get_fig_cytoscape(df=df_filtered, layout=layout)
        return g


@callback(
    Output("table-selected-tables", "children"),
    Input("memory-submitted-data", "data"),
    Input("filter-tbl-in-df", "value"),
)
# Shows dash table based on tables selected in a dropdown
def create_dash_table_from_selected_tbl(data_submitted, selected_dropdown_tables):
    if not data_submitted:
        return dash_table.DataTable()
    sheet_col = data_submitted["node_data"]["sheet_col"]
    data_about_nodes = data_submitted["node_data"]["file_data"][sheet_col]["df"]

    data_about_nodes = {
        "df_col": pd.DataFrame.from_records(data_about_nodes)
    }  # Refactorint

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Jei mygtukas "Get neighbours" nenuspaustas:
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "filter-tbl-in-df.value" in changed_id:
        df_col = data_about_nodes["df_col"]
        df_col = df_col.loc[df_col["table"].isin(selected_dropdown_tables), :]

        dash_tbl = dash_table.DataTable(
            data=df_col.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_col.columns],
            sort_action="native",
        )
        return dash_tbl


@callback(
    Output("table-displayed-nodes", "children"),
    Input("memory-submitted-data", "data"),
    Input("button-send-displayed-nodes-to-table", "n_clicks"),
    Input("my-network", "children"),
)
def create_dash_table_of_displayed_neighbours(data_submitted, n_clicks, g):

    if not data_submitted:
        return
    
    sheet_tbl = data_submitted["node_data"]["sheet_tbl"]
    data_about_nodes = data_submitted["node_data"]["file_data"][sheet_tbl]["df"]

    data_about_nodes = pd.DataFrame.from_records(data_about_nodes)
    if n_clicks is not None:
        displayed_nodes = g["props"]["elements"]
        displayed_nodes = [x["data"]["id"] for x in displayed_nodes]

        df_tbl = data_about_nodes
        df_tbl = df_tbl.loc[df_tbl["table"].isin(displayed_nodes), :]

        dash_tbl = dash_table.DataTable(
            data=df_tbl.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_tbl.columns],
            sort_action="native",
        )
        return dash_tbl


# ========================================
# Savarankiška programa
# ========================================
set_gettext_locale()
app.layout = app_layout


if __name__ == "__main__":
    app.run(debug=False)
