"""
PDSA grapher Dash app extra callbacks in "Graph" tab for both Viz and Cytoscape engines.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import os
import polars as pl
from dash import Output, Input, State, callback, callback_context, html, no_update
import json
from io import StringIO
from datetime import datetime
from grapher_lib import utils as gu
from grapher_lib import utils_file_upload as fu


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
        # Įprasto Graphviz atveju dažniausiai tinkamiausias būna "sfdp", kuris
        #  paprastai gražiau išdėsto nei jo pirmtakas "fdp",
        #  bet "sfdp" naudojant per Viz.js gali nerodyti grafikų dėl klaidų
        #  (kartais padeda overlap ar margin parametro pašalinimas), pvz.:
        #    remove_overlap: Graphviz not built with triangulation library.
        #    SVGMatrix.a setter: Value being assigned is not a finite floating-point value.
        #    An error occurred while processing the graph input.
        # Klasikinis "dot" gražiai išsidėsto hierarchiškai pagal kryptį mazgai, bet
        #  "dot" naudojant su Viz.js, linijos gali pernelyg dažnai perkirsti mazgus
        layout_default = "dot"  # arba "fdp"
        cyto_style["display"] = "none"
        viz_style["display"] = "block"
    else:
        # warnings.warn(_("Unexpected engine selected:"), f"'{engine}'")
        return False, False, [], None
    return cyto_style, viz_style, layout_options, layout_default


@callback(
    Output("memory-last-selected-nodes", "data"),
    Input("cyto-chart", "selectedNodeData"),
    Input("viz-clicked-node-store", "data"),
    Input("dropdown-engines", "value"),
    State("memory-last-selected-nodes", "data"),
    prevent_initial_call=True
)
def get_selected_node_ids(cyto_selected_nodes_data, viz_clicked_node_data, engine, selected_nodes_id_old=None):
    """
    Gauti pažymėtų tinklo mazgų identifikatorių sąrašą.
    :param cyto_selected_nodes_data: grafike šiuo metu naudotojo pažymėti tinklo mazgų/lentelių duomenys.
    :param viz_clicked_node_data: žodynas apie paspaustą mazgą Viz SVG elementą:
        {"type": "nodeClicked", "doubleClick": False, "id": "lentelės vardas"}
    :param engine: "Cytoscape" arba "Viz"
    :param selected_nodes_id_old: senas šios f-jos išduotas pažymėtų mazgų sąrašas (tik palyginimui dėl atnaujinimo),
        nepainioti su Viz variklio atveju išduodamu viz_clicked_node_data["selectedNodes"].
    :return: Viz variklio atveju tai bus tik vienas mazgas, o Cyto variklio atveju – gali būti ir keli mazgai.
    """
    selected_nodes_id = []
    if (engine == "Cytoscape") and cyto_selected_nodes_data:
        selected_nodes_id = [node["id"] for node in cyto_selected_nodes_data]
    elif (  # Graphviz/Viz
        (engine == "Viz") and viz_clicked_node_data and (viz_clicked_node_data["type"] == "nodeClicked")
    ):
        last_clicked_node = viz_clicked_node_data["id"]
        # viz_clicked_node_data["selectedNodes"] reikšmė gaunama dar prieš JavaScript lygiu ką tik paspaustajam mazgui
        # priskiriant "node-clicked" arba "node-clicked-twice" klasę (pastaroji atitinka viz_clicked_node_data["doubleClick"]).
        # Tinka ne tik viz_clicked_node_data["doubleClick"]=False, bet ir True, jei prieš tai buvo pažymėti keli,
        # o po to iš jų paspaustas tik vienas, tad į pastarąjį nekreipti dėmesio.
        selected_nodes_id = viz_clicked_node_data["selectedNodes"]  # Anksčiau pažymėti mazgai
        if last_clicked_node:
            if last_clicked_node in selected_nodes_id:
                # laikant Ctrl paspaustas vienas iš jau pažymėtųjų – jis bus atžymėtas
                selected_nodes_id.remove(last_clicked_node)
            else:
                # Paskutinis paspaustas mazgas bus pažymimas
                selected_nodes_id += [viz_clicked_node_data["id"]]
    # Gali keistis eiliškumas pradėjus ir baigus tempti mazgų grupę, bet išvedimas turėtų likti tas pats
    if selected_nodes_id and selected_nodes_id_old and (sorted(selected_nodes_id) == sorted(selected_nodes_id_old)):
        return no_update
    else:
        return selected_nodes_id


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
    State("memory-submitted-data", "data"),
    State("memory-filtered-data", "data"),
    prevent_initial_call=True
)
def display_tap_node_tooltip(
    active_tab, engine,
    cyto_selected_nodes_data, cyto_tap_node,
    viz_clicked_node_data,
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
    :param engine: "Cytoscape" arba "Viz"
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :return:
    """
    if (active_tab != "graph") or (not filtered_elements):
        return False, None, [], []

    node_id = None  # Dukart spragtelėto mazgo ID ir kartu užrašas; bus pakeistas
    bbox = None

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
                "y0": max(node_position["y"], 100),
                "x1": node_position["x"] + 75,
                "y1": max(node_position["y"] + 150, 100)
            }

    elif (  # Ar dukart spragtelėta ant mazgo Viz grafike
        (engine == "Viz") and viz_clicked_node_data and (viz_clicked_node_data["type"] == "nodeClicked") and
        viz_clicked_node_data["doubleClick"] and viz_clicked_node_data["id"]
    ):
        node_id = viz_clicked_node_data["id"]  # Dukart spragtelėto Viz mazgo ID ir kartu užrašas
        node_position = viz_clicked_node_data["nodePosition"]  # Dukart spragtelėto Viz mazgo koordinatės

        # Padėtis nematomo stačiakampio, į kurio krašto vidurį rodo debesėlio rodyklė
        bbox = {
            "x0": node_position["x"],
            "y0": max(node_position["y"], 75),
            "x1": node_position["x"] + node_position["width"] + 5,
            "y1": max(node_position["y"] + node_position["height"], 100)
        }

    if not node_id:
        # Nėra dukart spragtelėto mazgo - jo nerodyti
        return False, bbox, [], []

    # %% Antraštė
    tooltip_header = [html.H6(node_id)]
    data_about_nodes_tbl = data_submitted["node_data"]["tbl_sheet_data"]
    df_tbl = pl.DataFrame(data_about_nodes_tbl, infer_schema_length=None)
    if "table" in df_tbl:
        df_tbl1 = df_tbl.filter(pl.col("table") == node_id).unique()
        df_tbl1 = fu.select_renamed_or_add_columns(df_tbl1, old_columns=None, new_columns=["comment", "n_records"])
        table_n_prefix = "N=" if (df_tbl1["n_records"].dtype not in [pl.Boolean, pl.String]) else ""  # Tik prieš skaičių
        # Paprastai vienai lentelei turėtų būti tik viena eilutė ir neturėtų reikėti FOR ciklo.
        # Jei naudotojas tyčia (skirtingos schemos turi vienodai besivadinančių lentelių)
        # ar per klaidą (sumaišęs lakštus) pasirinko taip, kad lentelė turi kelis aprašymus, juos sujungti tam,
        # kad vizualiai matytųsi, jog kažkas ne taip, juolab kad nebus galimybės atskirti susijusius stulpelius.
        # Kita vertus, gali būti naudojamas vienas ir tas pats lakštas lentelėms ir stulpeliams, tad nepaisyti tuščių
        for df_tbl1_row in df_tbl1.iter_rows(named=True):
            sublabel = []
            table_comment = df_tbl1_row["comment"]
            if table_comment:
                sublabel.append(f"{table_comment}")
            table_records = df_tbl1_row["n_records"]
            if table_records is not None:
                sublabel.append(f"({table_n_prefix}{table_records})")
            tooltip_header.append(html.P(" ".join(sublabel)))

    # %% Turinys
    content = []

    # Turinys: stulpeliai
    data_about_nodes_col = data_submitted["node_data"]["col_sheet_data"]
    df_col = pl.DataFrame(data_about_nodes_col, infer_schema_length=None)
    if all(col in df_col.columns for col in ["table", "column"]):
        df_col = df_col.filter(pl.col("table") == node_id)  # atsirinkti tik šios lentelės stulpelius
        if df_col.height:  # netuščia lentelė
            table_rows = []  # čia kaupsim naujai kuriamus dash objektus apie stulpelius
            for row in df_col.iter_rows(named=True):
                if row["column"] and f'{row["column"]}'.strip():
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
    def get_df_edges_from_dict(edges_dict):
        df = pl.DataFrame(edges_dict, infer_schema_length=None)
        if df.height == 0:  # jei nėra eilučių, nėra ir reikalingų stulpelių struktūros
            df = pl.DataFrame(schema={
                "source_tbl": pl.Utf8, "source_col": pl.Utf8, "target_tbl": pl.Utf8, "target_col": pl.Utf8
            })
        return df
    df_edges = get_df_edges_from_dict(data_submitted["edge_data"]["ref_sheet_data"])
    df_edges_visib = get_df_edges_from_dict(filtered_elements["edge_elements"])

    # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
    # - Pavaizduoti ryšiai
    displayed_nodes = filtered_elements["node_elements"]
    df_visib_edges_source = df_edges_visib.filter(
        (pl.col("target_tbl") == node_id) & pl.col("source_tbl").is_in(displayed_nodes)
    ).unique().sort(by="target_col")
    df_visib_edges_target = df_edges_visib.filter(
        (pl.col("source_tbl") == node_id) & pl.col("target_tbl").is_in(displayed_nodes)
    ).unique().sort(by="source_col")
    # - Nepavaizduoti ryšiai
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


@callback(
    Output("graph-info", "show"),
    State("graph-info", "show"),
    Input("graph-info", "children"),
    Input("viz-clicked-node-store", "data"),
    Input("cyto-chart", "selectedNodeData"),
    Input("cyto-chart", "tapNode"),
    Input("cyto-chart", "selectedEdgeData"),
    Input("cyto-chart", "tapEdge"),
    Input("dropdown-tables", "value"),
    Input("input-list-tables", "value"),
    Input("checkbox-get-neighbours", "value"),
    Input("dropdown-neighbors", "value"),
    Input("checkbox-tables-no-records", "value"),
    Input("dropdown-tables", "options"),  # galimos pasirinkti braižymui lentelės
    prevent_initial_call=True
)
def change_graph_tooltip_visibility(
    graph_info_visibility, graph_info, viz_clicked_node_data, *args # noqa
):
    """
    Rodyti užrašą darbo pradžioje, jei ne visos lentelės matomos arba nėra ką pasirinkti,
    slėpti bet ką pakeitus atrankoje arba paspaudus mazgą grafike.
    """
    if not graph_info:
        # Užrašas tuščias – nebūtų ką rodyti, tad slėpti
        return False
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if changed_id in ["graph-info.children", "dropdown-tables.options"]:
        # Įkelti nauji duomenys
        return True
    return False


@callback(
    Output("download-json", "data"),
    State("memory-submitted-data", "data"),
    State("memory-filtered-data", "data"),
    State("memory-viz-clicked-checkbox", "data"),
    State("dropdown-tables", "options"),  # visos lentelės; bet jei įj. tuščiųjų šalinimas, būtų be jų
    Input("viz-save-json-displayed", "n_clicks"),  # paspaudimas per Cytoscape grafiko ☰ meniu
    Input("viz-save-json-all", "n_clicks"),  # paspaudimas per Cytoscape grafiko ☰ meniu
    Input("cyto-save-json-displayed", "n_clicks"),  # paspaudimas per Viz grafiko ☰ meniu
    Input("cyto-save-json-all", "n_clicks"),  # paspaudimas per Viz grafiko ☰ meniu
    config_prevent_initial_callbacks=True,
)
def save_displayed_nodes_to_json(
        data_submitted, filtered_elements, viz_selection_dict, all_tables=None,
        *args):  # noqa
    """
    Įrašyti nubraižytas lenteles į JSON
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param viz_selection_dict: Visų sužymėtų langelių simboliai žodyne,
        kur pirmasis lygis yra lentelės, antrasis – stulpeliai, pvz:
        {
            "Skaitytojas": {"ID": "⬜"},
            "Rezervacija": {"ClientID": "🟩", "BookCopyID": "🟥"}}
        }
    :param all_tables: visų lentelių sąrašas, reikalingas tik jei f-ja iškviečiama nuspaudus
        "viz-save-json-all" arba "cyto-save-json-all";
        beje, imant all_tables iš "dropdown-tables"."options" ir esant pažymėtai „Neįtraukti lentelių be įrašų“
        parinkčiai, nebūtų įtraukiamos tuščiosios lentelės, tad būtų eksportuojamos ne visos lentelės.
    :return: matomų lentelių sąrašas kaip tekstas
    """
    if (not filtered_elements) or (not data_submitted):
        return no_update

    changed_id = [p["prop_id"] for p in callback_context.triggered][0]  # kas iškvietė šią f-ją
    only_displayed = changed_id.endswith("-displayed.n_clicks")

    tables_data = {}
    columns_data = {}
    refs_data = filtered_elements["edge_elements"] if only_displayed else data_submitted["edge_data"]["ref_sheet_data"]

    displayed_nodes = filtered_elements["node_elements"]  # visos rodomos lentelės (gali įtraukti kaimynus, jei prašoma)
    neighbor_nodes = filtered_elements["node_neighbors"]  # kaimyninės lentelės
    selected_nodes = [table for table in displayed_nodes if table not in neighbor_nodes]  # tikrai pasirinktos lentelės
    exportable_nodes = displayed_nodes if only_displayed else all_tables or []

    # Stulpelių sužymėjimas langeliuose
    df_checkboxes = gu.convert_nested_dict2df(viz_selection_dict, ["table", "column", "checkbox"])
    if df_checkboxes.is_empty():
        df_checkboxes = df_checkboxes[["table", "column"]]  # kad vėliau nepridėtų tuščio papildomo stulpelio

    # Lentelės
    data_about_nodes_tbl = data_submitted["node_data"]["tbl_sheet_data"]
    df_tbl = pl.DataFrame(data_about_nodes_tbl, infer_schema_length=None)
    if "table" in df_tbl:
        df_tbl = df_tbl.filter(pl.col("table").is_in(exportable_nodes))  # atrenkamos tik eksportuojamos lentelės
        df_tbl = df_tbl.with_columns(pl.col("table").is_in(selected_nodes).alias("selected"))  # pasirinkimo žyma
        tables_data = df_tbl.to_dicts()

        # Stulpeliai
        data_about_nodes_col = data_submitted["node_data"]["col_sheet_data"]
        df_col = pl.DataFrame(data_about_nodes_col, infer_schema_length=None)
        if ("table" in df_col) and ("column" in df_col):
            if "checkbox" in df_col:
                df_col = df_col.drop("checkbox")  # išmesti seną stulpelį, nes prijungsim naujas reikšmes iš df_checkboxes
            columns_data = (
                df_col
                .filter(pl.col("table").is_in(exportable_nodes))  # atrenkami tik stulpeliai iš eksportuojamų lentelių
                .join(df_checkboxes, on=["table", "column"], how="left")
                .to_dicts()
            )

    combined_dict = {
        "tables": tables_data,
        "columns": columns_data,
        "refs": refs_data
    }

    if data_submitted["node_data"]["file_name"]:
        filename = data_submitted["node_data"]["file_name"]
    elif data_submitted["edge_data"]["file_name"]:
        filename = data_submitted["edge_data"]["file_name"]
    else:
        filename = "pdsa-grapher"
    filename, ext = os.path.splitext(filename)
    filename += " " + datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".json"

    json_content = json.dumps(combined_dict, indent=4, ensure_ascii=False)
    return dict(content=json_content, filename=filename, type="application/json")


@callback(
    Output("cyto-mouse-nodes-plain-clipboard-dropdown-item", "style"),
    Output("cyto-mouse-nodes-quoted-clipboard-dropdown-item", "style"),
    Output("viz-mouse-nodes-plain-clipboard-dropdown-item", "style"),
    Output("viz-mouse-nodes-quoted-clipboard-dropdown-item", "style"),
    Input("memory-last-selected-nodes", "data"),
    config_prevent_initial_callbacks=True,
)
def change_mouse_selected_nodes_copy_option_visibility(selected_nodes):
    """
    Pakeisti mygtukų, leidžiančių kopijuoti pele pažymėtus mazgus, matomumą: slėpti, jei nėra pasirinktų lentelių.
    :param selected_nodes: pele pažymėtų mazgų sąrašas
    """
    old_style = {"width": "300px"}  # nurodyti tiksliai, nes neprisitaiko pagal copy_div_with_label() plotį
    new_style = gu.change_style_for_activity(selected_nodes, old_style)
    return (new_style, ) * 4


@callback(
    Output("cyto-mouse-nodes-plain-clipboard", "content"),  # tekstas iškarpinei
    Output("viz-mouse-nodes-plain-clipboard", "content"),  # tekstas iškarpinei
    State("memory-last-selected-nodes", "data"),
    Input("cyto-mouse-nodes-plain-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    Input("viz-mouse-nodes-plain-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_mouse_selected_nodes_to_clipboard(selected_nodes, *args):  # noqa
    """
    Nukopijuoti pačiame grafike pele pažymėtas lenteles į iškarpinę (be kabučių).
    Tačiau tam, kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas atitinkamas mygtukas
    (vien programinis "content" pakeitimas nepadėtų).
    :param selected_nodes: pele pažymėtų mazgų sąrašas
    :return: matomų lentelių sąrašas kaip tekstas
    """
    outputs_n = 2  # Vienodų išvedimų skaičius
    if not selected_nodes:
        return ("", ) * outputs_n
    clipboard_content = f",\n".join(selected_nodes)
    return (clipboard_content, ) * outputs_n


@callback(
    Output("cyto-mouse-nodes-quoted-clipboard", "content"),  # tekstas iškarpinei
    Output("viz-mouse-nodes-quoted-clipboard", "content"),  # tekstas iškarpinei
    State("memory-last-selected-nodes", "data"),
    Input("cyto-mouse-nodes-quoted-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    Input("viz-mouse-nodes-quoted-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_mouse_selected_nodes_to_clipboard_quoted(selected_nodes, *args):  # noqa
    """
    Nukopijuoti pačiame grafike pele pažymėtas lenteles į iškarpinę (su kabutėmis).
    Tačiau tam, kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas atitinkamas mygtukas
    (vien programinis "content" pakeitimas nepadėtų).
    :param selected_nodes: pele pažymėtų mazgų sąrašas
    :return: matomų lentelių sąrašas kaip tekstas
    """
    outputs_n = 2  # Vienodų išvedimų skaičius
    if not selected_nodes:
        return ("", ) * outputs_n
    clipboard_content = '"' + f'",\n"'.join(selected_nodes) + '"'
    return (clipboard_content, ) * outputs_n


@callback(
    Output("cyto-graph-nodes-plain-clipboard-dropdown-item", "style"),
    Output("cyto-graph-nodes-quoted-clipboard-dropdown-item", "style"),
    Output("cyto-save-json-displayed", "style"),
    Output("cyto-save-json-all", "style"),
    Output("cyto-graph-nodes-metadata-tab-clipboard-dropdown-item", "style"),
    Output("viz-graph-nodes-plain-clipboard-dropdown-item", "style"),
    Output("viz-graph-nodes-quoted-clipboard-dropdown-item", "style"),
    Output("viz-graph-nodes-metadata-tab-clipboard-dropdown-item", "style"),
    Output("viz-save-json-displayed", "style"),
    Output("viz-save-json-all", "style"),
    Output("viz-save-svg", "style"),
    Output("upload-data-viz-checkbox-dropdown-item", "style"),
    Input("memory-filtered-data", "data"),
    config_prevent_initial_callbacks=True,
)
def change_displayed_nodes_copy_option_visibility(filtered_elements):
    """
    Pakeisti mygtukų, leidžiančių kopijuoti pele pažymėtus mazgus, matomumą: slėpti, jei nėra pasirinktų lentelių.
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    """
    condition = isinstance(filtered_elements, dict) and filtered_elements.get("node_elements")
    old_style = {"width": "300px"}  # nurodyti tiksliai, nes neprisitaiko pagal copy_div_with_label() plotį
    new_style = gu.change_style_for_activity(condition, old_style)
    return (new_style, ) * 12


@callback(
    Output("cyto-graph-nodes-plain-clipboard", "content"),  # tekstas iškarpinei
    Output("viz-graph-nodes-plain-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("cyto-graph-nodes-plain-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    Input("viz-graph-nodes-plain-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_displayed_nodes_to_clipboard(filtered_elements, *args):  # noqa
    """
    Nukopijuoti visas grafike nubraižytas lenteles į iškarpinę (be kabučių).
    Tačiau tam, kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas atitinkamas mygtukas
    (vien programinis "content" pakeitimas nepadėtų).
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :return: matomų lentelių sąrašas kaip tekstas
    """
    outputs_n = 2  # Vienodų išvedimų skaičius
    if not filtered_elements:
        return ("", ) * outputs_n
    displayed_nodes = filtered_elements["node_elements"]
    clipboard_content = f",\n".join(displayed_nodes)
    return (clipboard_content, ) * outputs_n


@callback(
    Output("cyto-graph-nodes-quoted-clipboard", "content"),  # tekstas iškarpinei
    Output("viz-graph-nodes-quoted-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("cyto-graph-nodes-quoted-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    Input("viz-graph-nodes-quoted-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_displayed_nodes_to_clipboard_quoted(filtered_elements, *args):  # noqa
    """
    Nukopijuoti visas grafike nubraižytas lenteles į iškarpinę (su kabutėmis).
    Tačiau tam, kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas atitinkamas mygtukas
    (vien programinis "content" pakeitimas nepadėtų).
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :return: matomų lentelių sąrašas kaip tekstas
    """
    outputs_n = 2  # Vienodų išvedimų skaičius
    if not filtered_elements:
        return ("", ) * outputs_n
    displayed_nodes = filtered_elements["node_elements"]
    clipboard_content = '"' + f'",\n"'.join(displayed_nodes) + '"'
    return (clipboard_content, ) * outputs_n


@callback(
    Output("cyto-graph-nodes-metadata-tab-clipboard", "content"),  # tekstas iškarpinei
    Output("viz-graph-nodes-metadata-tab-clipboard", "content"),  # tekstas iškarpinei
    State("memory-submitted-data", "data"),
    State("memory-filtered-data", "data"),
    Input("cyto-graph-nodes-metadata-tab-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    Input("viz-graph-nodes-metadata-tab-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_displayed_nodes_metadata_to_clipboard_v2(data_submitted, filtered_elements, *args):  # noqa
    """
    Nukopijuoti visų grafike nubraižytų lentelių stulpelių stulpelius su aprašymais į iškarpinę, atskiriant per \t, pvz.:
        ```
        "table"     "table_comment"   "column"      "description"       \n
        "lentelė1"  "Lentelės Nr.1"                                     \n
        "lentelė1"                    "stulpelis1"  "stulpelio1_aprašas"\n
        "lentelė1"                    "stulpelis2"  "stulpelio2_aprašas"\n
        "lentelė2"  "Lentelės Nr.2"                                     \n
        "lentelė2"                    "stulpelis3"  "stulpelio3_aprašas"\n
        ```

    Tačiau tam, kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas atitinkamas mygtukas
    (vien programinis "content" pakeitimas nepadėtų).
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant kaimynus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    """
    outputs_n = 2  # Vienodų išvedimų skaičius
    if not filtered_elements:
        return ("", ) * outputs_n

    # Išsitraukti reikalingus kintamuosius
    df_edges = pl.DataFrame(filtered_elements["edge_elements"], infer_schema_length=None)  # ryšių lentelė
    displayed_nodes = filtered_elements["node_elements"]  # mazgai (įskaitant kaimynus)
    # Stulpelių metaduomenys
    df_nodes_col = pl.DataFrame(data_submitted["node_data"]["col_sheet_data"], infer_schema_length=None)
    if "table" in df_nodes_col.columns:
        df_col = df_nodes_col.filter(pl.col("table").is_in(displayed_nodes))
    else:
        # Veikti net jei PDSA stulpelius aprašančiame lakšte "table" stulpelio nebūtų
        # get_graphviz_dot() sudės "table" reikšmes vėliau automatiškai pagal ryšius, jei jie yra
        df_col = pl.DataFrame({"table": {}}, schema={"table": pl.String})

    # Apjungti PSDA minimus pasirinktos lentelės stulpelius su ryšiuose minimais pasirinktos lentelės stulpeliais
    df_clipboard = pl.DataFrame()  # Praktiškai šis priskyrimas nenaudojamas, bet bent IDE nemėtys įspėjimų
    for index, table in enumerate(displayed_nodes):
        df_hibr1 = gu.merge_pdsa_and_refs_columns(
            df_col, df_edges, table=table, tables_in_context=None, get_all_columns=True
        )
        if index == 0:
            df_clipboard = df_hibr1
        else:
            df_clipboard = pl.concat([df_clipboard, df_hibr1], how="vertical_relaxed")
    if df_clipboard.is_empty():
        return ("",) * outputs_n

    if ("alias" in df_clipboard.columns) and (df_clipboard["alias"].dtype == pl.String):
        clibboard_columns_old = ["table", "column", "alias", "comment"]
        clibboard_columns_new = ["table", "column_orig", "column", "description"]
    else:
        clibboard_columns_old = ["table", "column", "comment"]
        clibboard_columns_new = ["table", "column", "description"]
    df_clipboard = fu.select_renamed_or_add_columns(df_clipboard, clibboard_columns_old, clibboard_columns_new)

    # Iškarpinės turinys
    tsv_memory = StringIO()
    df_clipboard.write_csv(
        tsv_memory, include_header=True, separator="\t", quote_style="non_numeric"
    )
    clipboard_content = tsv_memory.getvalue()
    return (clipboard_content, ) * outputs_n
