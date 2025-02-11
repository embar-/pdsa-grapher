"""
PDSA grapher Dash app callbacks in "Graphic" tab for Cytoscape engine.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import pandas as pd
from dash import html, Output, Input, callback, State
from grapher_lib import utils as gu


@callback(
    Output("cyto-chart", "layout"),
    Input("dropdown-layouts", "value"),
    State("dropdown-engines", "value"),
    State("cyto-chart", "layout"),
)
def update_cytoscape_layout(new_layout_name="cola", engine="Cytoscape", layout_dict=None):
    """
    Cytoscape grafiko išdėstymo parinkčių atnaujinimas.
    :param new_layout_name: naujas išdėstymo vardas
    :param engine: grafiko braižymo variklis "Cytoscape" arba "Viz"
    :param layout_dict: cytoscape išdėstymo parinkčių žodynas
    :return:
    """
    if engine == "Cytoscape":
        if layout_dict is None:
            layout_dict = {"fit": True, "name": "cola"}
        if new_layout_name is not None:
            layout_dict["name"] = new_layout_name
    return layout_dict


@callback(
    Output("cyto-chart", "elements"),
    Input("memory-filtered-data", "data"),
    Input("cyto-chart", "style"),
    Input("cyto-chart", "tapNodeData"),
    Input("cyto-chart", "selectedNodeData"),
    Input("checkbox-cyto-active-edge-labels", "value"),  # žymimasis langelis per ☰ meniu
    State("cyto-chart", "elements"),
    State("dropdown-engines", "value"),
)
def get_network_cytoscape_chart(
        filtered_elements, cyto_style, tap_node_data, selected_nodes_data, edge_labels, current_elements, engine
):
    """
    Atvaizduoja visas pasirinktas lenteles kaip tinklo mazgus.
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param cyto_style: Cytoscape grafiko stilius (svarbu, kad būtų "display" savybė)
    :param tap_node_data: paskutinio spragtelėto mazgo duomenys
    :param selected_nodes_data: pažymėtų (pvz., apvestų) mazgų duomenys
    :param edge_labels: True/False: ar rodyti užrašus virš aktyvių ryšių, t.y. jei jungtis pažymėta
        pele tiesiogiai arba mazgą spragtelėjus pasižymi jo jungtis pažymima netiesiogiai
    :param current_elements: dabartiniai Cytoscape elementai (mazgai ir ryšiai tarp jų)
    :param engine: grafiko braižymo variklis "Cytoscape" arba "Viz"
    :return:
    """
    if (engine != "Cytoscape") or (cyto_style["display"] == "none") or (not filtered_elements):
        return {}

    # Išsitraukti reikalingus kintamuosius
    df_edges = pd.DataFrame(filtered_elements["edge_elements"])  # ryšių lentelė
    nodes = filtered_elements["node_elements"]  # mazgai (įskaitant mazgus)
    neighbors = filtered_elements["node_neighbors"]  # kaimyninių mazgų sąrašas

    # Sukurti Cytoscape elementus
    new_elements = gu.get_fig_cytoscape_elements(
        nodes, df_edges, node_neighbors=neighbors, set_link_info_str=edge_labels
    )

    if selected_nodes_data and tap_node_data:
        tap_node_id = tap_node_data["id"]
        selected_nodes_id = [node["id"] for node in selected_nodes_data]
        if [tap_node_id] == selected_nodes_id:
            for element in new_elements:
                if "source" in element["data"]:  # jei jungtis
                    if element["data"]["source"] == tap_node_id:  # liečia paspaustą mazgą, kuris yra jungties pradžia
                        element["classes"] = "source-neighbor"  # keis linijos spalvą pagal "source-neighbor" klasę
                    elif element["data"]["target"] == tap_node_id:  # liečia paspaustą mazgą, kuris yra jungties galas
                        element["classes"] = "target-neighbor"  # keis linijos spalvą pagal "target-neighbor" klasę

    # Apjungti senus elementus su naujais - taip išvengsima mazgų perpiešimo iš naujo,
    # jų padėtys liks senos - mes to ir norime (ypač jei naudotojas ranka pertempė mazgus)
    updated_elements = []
    current_elements_map = {element["data"]["id"]: element for element in current_elements}
    for element in new_elements:
        elem_id = element["data"].get("id")
        if elem_id in current_elements_map:
            current_element = current_elements_map[elem_id]
            current_element["classes"] = element.get("classes", "")
            if "link_info_str" in element["data"]:
                current_element["data"]["link_info_str"] = element["data"]["link_info_str"] if edge_labels else ""
            updated_elements.append(current_element)
        else:
            if (not edge_labels) and ("link_info_str" in element["data"]):
                element["data"]["link_info_str"] = ""
            updated_elements.append(element)

    return updated_elements


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
                        break

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
                            if comment_col in row:
                                if pd.notna(row[comment_col]) and row[comment_col].strip():
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


@callback(
    Output("cyto-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("cyto-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
)
def copy_cyto_displayed_nodes_to_clipboard(filtered_elements, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "cyto-clipboard" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "cyto-clipboard"
    (vien programinis "cyto-clipboard":"content" pakeitimas nepadėtų).
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param n_clicks:  tik kaip paleidiklis, reikšmė nenaudojama
    :return: matomų lentelių sąrašas kaip tekstas
    """
    if not filtered_elements:
        return ""
    displayed_nodes = filtered_elements["node_elements"]
    return ", ".join(displayed_nodes)
