"""
PDSA grapher Dash app common callbacks in "Graphic" tab.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import pandas as pd
from dash import Output, Input, State, callback, callback_context, dash_table
from grapher_lib import utils as gu

# ========================================
# Interaktyvumai grafiko kortelėje
# ========================================

@callback(
    Output("filter-tbl-in-df", "options"),  # išskleidžiamojo sąrašo pasirinkimai
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
)
def set_dropdown_tables_for_selected_table_cols_info(data_submitted):
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
def set_dropdown_tables_for_graph(
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
    df_edges = pd.DataFrame(data_submitted["edge_data"]["ref_sheet_data"])

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“, „Braižyti visas“ (jei paspaustas)
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    # Pagal naudotojo pasirinkimą arba automatiškai žymėti lenteles piešimui.
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
        preselected_tables = pd.concat([df_edges2["source_tbl"], df_edges2["target_tbl"]]).unique().tolist()
        preselected_tables = sorted(preselected_tables)
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
        return {}

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
    submitted_edge_data = data_submitted["edge_data"]["ref_sheet_data"]

    # Priklausomai nuo langelio „Rodyti kaimynus“/„Get neighbours“
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

        # Pirminė ryšių atranka, kuri reikalinga kaimynų radimui; pvz., A>B, A>C ras ryšį, bet praleis B>C.
        # tik žinodami kaimynus vėliau iš naujo ieškosime ryšių, nes ryšių galėjo būti tarp pačių kaimynų
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

        # Ryšius atsirenkame iš naujo, nes jungčių galėjo būti tarp pačių kaimynų,
        # pvz., jei iš pradžių turėjome A>B ir A>C, tai dabar jau ras ir B>C.
        df_edges = [
            x
            for x in submitted_edge_data
            if  x["source_tbl"] in selected_tables_and_neighbors
            and x["target_tbl"] in selected_tables_and_neighbors
        ]
        df_edges = pd.DataFrame.from_records(df_edges)


    if df_edges.empty:
        df_edges = pd.DataFrame(columns=["source_tbl", "source_col", "target_tbl", "target_col"])
    return {
        "node_elements": selected_tables_and_neighbors,
        "node_neighbors": neighbors,
        "edge_elements": df_edges.to_dict("records"),  # df būtina paversti į žodyno/JSON tipą, antraip Dash nulūš
    }


@callback(
    Output("clipboard-filter-tbl-in-df", "content"),  # tekstas iškarpinei
    State("filter-tbl-in-df", "value"),
    Input("clipboard-filter-tbl-in-df", "n_clicks"),  # kopijavimo mygtuko paspaudimai
)
def copy_selected_tables_to_clipboard(selected_dropdown_tables, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "clipboard-filter-tbl-in-df" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "clipboard-filter-tbl-in-df"
    (vien programinis "clipboard-filter-tbl-in-df":"content" pakeitimas nepadėtų) -
    tik tuomet būtų nukopijuotas sąrašas lentelių, apie kurias naudotojas pasirinko žiūrinėti lentelių stulpelių info.
    :param selected_dropdown_tables: išskleidžiamajame sąraše naudotojo pasirinktos lentelės
    :param n_clicks:  tik kaip paleidiklis, reikšmė nenaudojama
    :return: naudotojo pasirinktų lentelių sąrašas kaip tekstas
    """
    if not selected_dropdown_tables:
        return ""
    return ", ".join(selected_dropdown_tables)


@callback(
    Output("table-selected-tables", "children"),
    Input("memory-submitted-data", "data"),
    Input("filter-tbl-in-df", "value"),
)
def create_dash_table_about_selected_table_cols(data_submitted, selected_dropdown_tables):
    """
    Parodo lentelę su informacija apie stulpelius iš PDSA lakšto „columns“ priklausomai nuo naudotojo pasirinkimo
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param selected_dropdown_tables: išskleidžiamajame sąraše naudotojo pasirinktos lentelės
    :return: dash_table objektas
    """
    if not (data_submitted and selected_dropdown_tables):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["col_sheet_data_orig"]
    df_col = pd.DataFrame.from_records(data_about_nodes)

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Jei prašoma rodyti informaciją apie pasirinktų lentelių stulpelius
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "filter-tbl-in-df.value" in changed_id:
        col = data_submitted["node_data"]["col_sheet_renamed_cols"]["table"]
        if col in df_col:
            df_col = df_col.loc[df_col[col].isin(selected_dropdown_tables), :]

            dash_tbl = dash_table.DataTable(
                data=df_col.to_dict("records"),
                columns=[{"name": i, "id": i} for i in df_col.columns],
                sort_action="native",
                style_table={
                    "overflowX": "auto"  # jei lentelė netelpa, galėti ją slinkti
                },
                page_size=50,
            )
            return dash_tbl
        return dash_table.DataTable()


@callback(
    Output("table-displayed-nodes", "children"),
    Input("memory-submitted-data", "data"),
    Input("memory-filtered-data", "data"),
    Input("checkbox-get-displayed-nodes-info-to-table", "value"),
)
def create_dash_table_about_displayed_tables(data_submitted, filtered_elements, get_displayed_nodes_info):
    """
    Informacija apie grafike rodomas lenteles iš PDSA lakšto „tables“

    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param get_displayed_nodes_info: ar pateikti nubraižytų lentelių informaciją
    :return: dash_table objektas
    """

    if (not data_submitted) or (not filtered_elements):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["tbl_sheet_data_orig"]
    df_tbl = pd.DataFrame.from_records(data_about_nodes)
    col = data_submitted["node_data"]["tbl_sheet_renamed_cols"]["table"]
    if get_displayed_nodes_info and (col in df_tbl):
        # tinklo mazgai turi raktą "id" ir "label", bet jungimo linijos jų neturi (jos turi tik "source" ir "target")
        displayed_nodes = filtered_elements["node_elements"]
        df_tbl = df_tbl.loc[df_tbl[col].isin(displayed_nodes), :]

        dash_tbl = dash_table.DataTable(
            data=df_tbl.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_tbl.columns],
            sort_action="native",
            page_size=50,
        )
        return dash_tbl
    else:
        return dash_table.DataTable()


@callback(
    Output("cyto-chart", "style"),
    Output("graphviz-div", "style"),
    Output("dropdown-layouts", "options"),
    Output("dropdown-layouts", "value"),
    Input("dropdown-engines", "value"),
    State("cyto-chart", "style"),
    State("graphviz-div", "style"),
)
def change_engine(engine, cyto_style, viz_style):
    """
    Grafiko braižymo variklio stilių nustatymas.
    :param engine: "Cytoscape" arba "Viz"
    :param cyto_style: Cytoscape grafiko stilius (svarbu, kad būtų "display" savybė)
    :param viz_style: Viz grafiko stilius (svarbu, kad būtų "display" savybė)
    :return: visų naudingų stilių sąrašas atitinkam varikliui ir vienas konkretus stilius
    """
    if engine == "Cytoscape":
        layout_options = ["random", "breadthfirst", "circle", "cola", "cose", "dagre", "euler", "grid", "spread"]
        layout_default = "cola"
        cyto_style["display"] = "block"
        viz_style["display"] = "none"
    elif engine == "Viz":  # Graphviz/Viz
        layout_options = ["circo", "dot", "fdp", "neato", "osage", "sfdp", "twopi"]
        # "sfdp" paprastai gražiau išdėsto nei "fdp", bet gali nerodyti grafikų dėl netikėtų klaidų
        # (kartais padeda overlap ar margin parametro pašalinimas), pvz.:
        #   remove_overlap: Graphviz not built with triangulation library.
        #   SVGMatrix.a setter: Value being assigned is not a finite floating-point value.
        #   An error occurred while processing the graph input.
        layout_default = "fdp"
        cyto_style["display"] = "none"
        viz_style["display"] = "block"
    else:
        # warnings.warn(_("Unexpected engine selected:"), f"'{engine}'")
        return False, False, [], None
    return cyto_style, viz_style, layout_options, layout_default


@callback(
    Output("graph-tab-pdsa-info-tables", "style"),
    Input("pdsa-tables-table", "value"),
    Input("memory-submitted-data", "data"),
    State("graph-tab-pdsa-info-tables", "style"),
)
def change_pdsa_tables_info_visibility(pdsa_tbl_table, data_submitted, div_style):
    """
    Informacijos, pateikiamos lentelėje po grafiku, apie pasirinktų lentelių stulpelius matomumas
    :param pdsa_tbl_table: PDSA lentelių lakšto stulpelis, kuriame nurodyti lentelių vardai
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param div_style: html.Div stiliaus žodynas
    :return: pakeistas "style" žodynas.
    """
    visibility = pdsa_tbl_table and data_submitted["node_data"]["tbl_sheet_data_orig"]
    return gu.change_style_display_value(visibility, div_style)


@callback(
    Output("graph-tab-pdsa-info-columns", "style"),
    Input("pdsa-columns-table", "value"),
    Input("memory-submitted-data", "data"),
    State("graph-tab-pdsa-info-columns", "style"),
)
def change_pdsa_columns_info_visibility(pdsa_col_table, data_submitted, div_style):
    """
    Informacijos, pateikiamos lentelėje po grafiku, apie nubraižytas lenteles matomumas
    :param pdsa_col_table: PDSA stulpelių lakšto stulpelis, kuriame nurodyti lentelių vardai
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param div_style: html.Div stiliaus žodynas
    :return: pakeistas "style" žodynas.
    """
    visibility = pdsa_col_table and data_submitted["node_data"]["col_sheet_data_orig"]
    return gu.change_style_display_value(visibility, div_style)
