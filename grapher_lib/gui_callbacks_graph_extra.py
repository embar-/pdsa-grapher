"""
PDSA grapher Dash app extra callbacks in "Graphic" tab for both Viz and Cytoscape engines.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import Output, Input, State, callback, html, no_update


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
    Output("filter-tbl-in-df", "value"),
    Input("cyto-chart", "selectedNodeData"),
    Input("viz-clicked-node-store", "data"),
    Input("dropdown-engines", "value"),
    State("filter-tbl-in-df", "value"),
    State("checkbox-get-selected-nodes-info-to-table", "value"),
)
def get_selected_node_data(
    cyto_selected_nodes_data, viz_clicked_node_data, engine, selected_dropdown_tables, append_recently_selected
):
    """
    Paspaudus tinklo mazgą, jį įtraukti į pasirinktųjų sąrašą informacijos apie PDSA stulpelius rodymui
    :param cyto_selected_nodes_data: grafike šiuo metu naudotojo pažymėti tinklo mazgų/lentelių duomenys.
    :param viz_clicked_node_data: žodynas apie paspaustą mazgą Viz SVG elementą:
        {"type": "nodeClicked", "doubleClick": False, "id": "lentelės vardas"}
    :param engine: "Cytoscape" arba "Viz"
    :param selected_dropdown_tables: šiuo metu išskleidžiamajame sąraše esantys grafiko mazgai/lentelės
    :param append_recently_selected: jei True - pažymėtuosius prideda prie pasirinkimų išskleidžiamajame meniu.
    :return: papildytas mazgų/lentelių sąrašas
    """
    if not append_recently_selected:
        return selected_dropdown_tables
    selected_nodes_id = []
    if (engine == "Cytoscape") and cyto_selected_nodes_data:
        selected_nodes_id = [node["id"] for node in cyto_selected_nodes_data]
    elif (  # Graphviz/Viz
        (engine == "Viz") and viz_clicked_node_data and (viz_clicked_node_data["type"] == "nodeClicked") and
        (not viz_clicked_node_data["doubleClick"]) and viz_clicked_node_data["id"]
    ):
        selected_nodes_id = [viz_clicked_node_data["id"]]
    return sorted(list(set(selected_dropdown_tables + selected_nodes_id)))


@callback(
    Output("active-node-info", "show"),
    Output("active-node-info", "bbox"),
    Output("active-node-info-header", "children"),
    Output("active-node-info-content", "children"),
    Input("tabs-container", "active_tab"),
    Input("dropdown-engines", "value"),
    Input("cyto-chart", "selectedNodeData"),
    Input("cyto-chart", "tapNode"),
    Input("viz-clicked-node-store", "data"),
    Input("checkbox-viz-all-columns", "value"),
    State("memory-submitted-data", "data"),
    State("memory-filtered-data", "data"),
)
def display_tap_node_tooltip(
    active_tab, engine,
    cyto_selected_nodes_data, cyto_tap_node,
    viz_clicked_node_data, viz_hide_columns,
    data_submitted, filtered_elements,
):
    """
    Iškylančiame debesėlyje parodo informaciją apie mazgą
    :param active_tab: aktyvi kortelė ("file_upload" arba "graph")
    :param cyto_selected_nodes_data: pažymėtųjų mazgų duomenys
    :param cyto_tap_node: paskutinis spragtelėtas mazgas
    :param viz_clicked_node_data: žodynas apie paspaustą mazgą Viz SVG elementą, pvz. {
        "type": "nodeClicked",
        "doubleClick": True,
        "id": "lentelės vardas",
        "nodePosition": {"x": 500, "y": 300, "width": 200, "height": 300}
    }
    :param viz_hide_columns: ar rodyti lentelės stulpelius
    :param engine: "Cytoscape" arba "Viz"
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :return:
    """
    if (active_tab != "graph") or (not filtered_elements):
        return False, None, [], []

    node_id = None  # Dukart spragtelėto mazgo ID ir kartu užrašas; bus pakeistas
    bbox = None
    shows_columns_info = True

    if (engine == "Cytoscape") and cyto_selected_nodes_data:
        # Ar spragtelėta ant mazgo Cyto grafike
        selected_nodes_id = [node["id"] for node in cyto_selected_nodes_data]
        if cyto_tap_node and cyto_tap_node["selected"] and [cyto_tap_node["data"]["id"]] == selected_nodes_id:
            # tap_node grąžina paskutinį buvusį paspaustą mazgą, net jei jis jau atžymėtas, tad tikrinti ir selected_node;
            # bet tap_node ir selected_node gali nesutapti apvedant (ne spragtelint); veikti tik jei abu sutampa.
            node_id = cyto_tap_node["data"]["label"]  # Dukart spragtelėto Cytoscape mazgo ID ir kartu užrašas
            node_position = cyto_tap_node["renderedPosition"]  # Dukart spragtelėto Cytoscape mazgo koordinatės

            # Padėtis nematomo stačiakampio, į kurio krašto vidurį rodo debesėlio rodyklė
            bbox = {
                "x0": node_position["x"] - 25,
                "y0": node_position["y"],
                "x1": node_position["x"] + 25,
                "y1": node_position["y"] + 150
            }

    elif (  # Ar dukart spragtelėta ant mazgo Viz grafike
        (engine == "Viz") and viz_clicked_node_data and (viz_clicked_node_data["type"] == "nodeClicked") and
        viz_clicked_node_data["doubleClick"] and viz_clicked_node_data["id"]
    ):
        shows_columns_info = not viz_hide_columns
        node_id = viz_clicked_node_data["id"]  # Dukart spragtelėto Viz mazgo ID ir kartu užrašas
        node_position = viz_clicked_node_data["nodePosition"]  # Dukart spragtelėto Viz mazgo koordinatės

        # Padėtis nematomo stačiakampio, į kurio krašto vidurį rodo debesėlio rodyklė
        bbox = {
            "x0": node_position["x"],
            "y0": node_position["y"],
            "x1": node_position["x"] + node_position["width"],
            "y1": node_position["y"] + node_position["height"]
        }

    if not node_id:
        # Nėra dukart spragtelėto mazgo - jo nerodyti
        return False, bbox, [], []

    # %% Antraštė
    tooltip_header = [html.H6(node_id)]
    data_about_nodes_tbl = data_submitted["node_data"]["tbl_sheet_data"]
    df_tbl = pl.DataFrame(data_about_nodes_tbl, infer_schema_length=None)
    if "table" in df_tbl:
        df_tbl1 = df_tbl.filter(pl.col("table") == node_id)
        sublabel = []
        if "comment" in df_tbl1.columns:
            table_comment = df_tbl1["comment"]
            if (not table_comment.is_empty()) and table_comment[0]:
                sublabel.append(f"{table_comment[0]}")
        if "n_records" in df_tbl1.columns:
            table_records = df_tbl1["n_records"]
            if (not table_records.is_empty()) and (table_records[0] is not None):
                sublabel.append(f"(N={table_records[0]})")
        tooltip_header.append(html.P(" ".join(sublabel)))

    # %% Turinys
    content = []

    # Turinys: stulpeliai
    if shows_columns_info:
        data_about_nodes_col = data_submitted["node_data"]["col_sheet_data"]
        df_col = pl.DataFrame(data_about_nodes_col, infer_schema_length=None)
        if all(col in df_col.columns for col in ["table", "column"]):
            df_col = df_col.filter(pl.col("table") == node_id)  # atsirinkti tik šios lentelės stulpelius
            if df_col.height:  # netuščia lentelė
                table_rows = []  # čia kaupsim naujai kuriamus dash objektus apie stulpelius
                for row in df_col.iter_rows(named=True):
                    table_row = ["- ", html.B(row["column"])]
                    if ("is_primary" in row) and row["is_primary"]:
                        table_row.append(" 🔑")  # pirminis raktas
                    if "comment" in row:  # tikrinti, nes gali būti ne tik tekstinis, bet ir skaičių stulpelis
                        if row["comment"] and f'{row["comment"]}'.strip():
                            table_row.extend([" – ", f'{row["comment"]}'])  # paaiškinimas įprastuose PDSA
                    table_rows.append(html.Tr([html.Td(table_row)]))
                content.append(
                        html.Table(
                        children=[
                            html.Thead(html.Tr([html.Th(html.U(_("Columns:")))])),
                            html.Tbody(table_rows)
                        ]
                    )
                )

    # Turinys: ryšiai
    displayed_nodes = filtered_elements["node_elements"]
    # displayed_tables_x = {x["source"] for x in cyto_tap_node["edgesData"]}
    # displayed_tables_y = {y["target"] for y in cyto_tap_node["edgesData"]}
    df_edges = pl.DataFrame(data_submitted["edge_data"]["ref_sheet_data"], infer_schema_length=None)

    # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
    df_visib_edges_source = df_edges.filter(
        (pl.col("target_tbl") == node_id) & pl.col("source_tbl").is_in(displayed_nodes)
    ).unique().sort(by="target_col")
    df_visib_edges_target = df_edges.filter(
        (pl.col("source_tbl") == node_id) & pl.col("target_tbl").is_in(displayed_nodes)
    ).unique().sort(by="source_col")
    df_invis_edges_source = df_edges.filter(
        (pl.col("target_tbl") == node_id) & ~pl.col("source_tbl").is_in(displayed_nodes)
    ).unique().sort(by="target_col")
    df_invis_edges_target = df_edges.filter(
        (pl.col("source_tbl") == node_id) & ~pl.col("target_tbl").is_in(displayed_nodes)
    ).unique().sort(by="source_col")

    if df_visib_edges_source.height or df_visib_edges_target.height:
        if content:
            content.append(html.Hr())  # tarpas tarp sąrašų

        # Pavaizduotų ryšių sąrašas
        invis_edges = []
        for row in df_visib_edges_source.iter_rows(named=True):
            source = ["_:", row["target_col"]] if row["target_col"] else ["_"]
            target = [html.B(row["source_tbl"]), ":", row["source_col"]] if row["source_col"] else [row["source_tbl"]]
            invis_edges.append(source + [html.B(" <- ")] + target)
        for row in df_visib_edges_target.iter_rows(named=True):
            source = ["_:", row["source_col"]] if row["source_col"] else ["_"]
            target = [html.B(row["target_tbl"]), ":", row["target_col"]] if row["target_col"] else [row["target_tbl"]]
            invis_edges.append(source + [html.B(" -> ")] + target)

        # HTML lentelė
        content.extend([
            html.Table(
                children=[
                    html.Thead(html.Tr([html.Th(html.U(_("Displayed relations:")))])),
                    html.Tbody(
                        children=[
                            html.Tr([html.Td(edge)])
                            for edge in invis_edges
                        ]
                    )
                ]
            ),
        ])

    if df_invis_edges_source.height or df_invis_edges_target.height:
        if df_visib_edges_source.height or df_visib_edges_target.height:
            content.append(html.Hr())  # tarpas tarp sąrašų

        # Nepavaizduotų ryšių sąrašas
        invis_edges = []
        for row in df_invis_edges_source.iter_rows(named=True):
            source = ["_:", row["target_col"]] if row["target_col"] else ["_"]
            target = [html.B(row["source_tbl"]), ":", row["source_col"]] if row["source_col"] else [row["source_tbl"]]
            invis_edges.append(source + [html.B(" <- ")] + target)
        for row in df_invis_edges_target.iter_rows(named=True):
            source = ["_:", row["source_col"]] if row["source_col"] else ["_"]
            target = [html.B(row["target_tbl"]), ":", row["target_col"]] if row["target_col"] else [row["target_tbl"]]
            invis_edges.append(source + [html.B(" -> ")] + target)
        # HTML lentelė
        content.extend([
            html.Table(
                children=[
                    html.Thead(html.Tr([html.Th(html.U(_("Not displayed relations:")))])),
                    html.Tbody(
                        children=[
                            html.Tr([html.Td(edge)])
                            for edge in invis_edges
                        ]
                    )
                ]
            ),
        ])

    if content:
        tooltip_header.append(html.Hr())

    return True, bbox, tooltip_header, content
