"""
PDSA grapher Dash app callbacks in "Graphic" tab for Cytoscape engine.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import html, Output, Input, callback, State
from grapher_lib import utils as gu


@callback(
    Output("cyto-chart", "layout"),
    Input("dropdown-layouts", "value"),
    State("dropdown-engines", "value"),
    State("cyto-chart", "layout"),
    config_prevent_initial_callbacks=True,
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
    config_prevent_initial_callbacks=True,
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
    df_edges = pl.DataFrame(filtered_elements["edge_elements"], infer_schema_length=None)  # ryšių lentelė
    nodes = filtered_elements["node_elements"]  # mazgai (įskaitant mazgus)
    neighbors = filtered_elements["node_neighbors"]  # kaimyninių mazgų sąrašas

    # Išmesti lentelių nuorodas į save (bet iš tiesų pasitaiko nuorodų į kitą tos pačios lentelės stulpelį)
    if not df_edges.height == 0:
        df_edges = df_edges.filter(pl.col("source_tbl") != pl.col("target_tbl"))

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
    Output("active-edge-info", "show"),
    Output("active-edge-info", "bbox"),
    Output("active-edge-info-header", "children"),
    Output("active-edge-info-content", "children"),
    Input("cyto-chart", "selectedEdgeData"),
    Input("cyto-chart", "tapEdge"),
    config_prevent_initial_callbacks=True,
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
            """
            Dash 2.18 Cytoscape 1.0.2 netiksliai išduoda jungčių koordinates, 
            tap_edge["midpoint"] neatitinka linijos vidurio,
            tap_edge["sourceEndpoint"] ir tap_edge["targetEndpoint"] irgi netikslūs,
            nors node atveju display_tap_node_tooltip() "active-node-info" veikia gerai
            Pvz.,
            display_tap_node_tooltip() "active-node-info":
                source cyto_tap_node["renderedPosition"] {'x': 412.1098426385264, 'y': 533.1845719380465}
                target cyto_tap_node["renderedPosition"] {'x': 445.29806833026475, 'y': 398.7809456885337}
            display_tap_edge_tooltip() "active-edge-info" atitinkamiems taškams:
                sourceEndpoint {'x': 375.96035635388057, 'y': 462.7152778769273}
                targetEndpoint {'x': 390.1735716164434, 'y': 405.15547670837896}
            """
            # X skaičiuojamas nuo kairiojo krašto, Y nuo viršaus (ne nuo apačios!)
            source_point = tap_edge["sourceEndpoint"]
            target_point = tap_edge["targetEndpoint"]
            bbox={
                "x0": min(source_point["x"], target_point["x"]),
                "y0": max(min(source_point["y"], target_point["y"]), 100),
                "x1": max(source_point["x"], target_point["x"]) + 75,
                "y1": max(max(source_point["y"], target_point["y"]), 100)
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
    config_prevent_initial_callbacks=True,
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
    return f",\n".join(displayed_nodes)
