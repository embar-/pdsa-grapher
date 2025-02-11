"""
PDSA grapher Dash app callbacks in "Graphic" tab for Viz engine.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import pandas as pd
from dash import Output, Input, State, callback
from grapher_lib import utils as gu

@callback(
    Output("graphviz-dot", "style"),
    Input("checkbox-edit-dot", "value"),
    State("graphviz-dot", "style"),
)
def change_dot_editor_visibility(enable_edit, editor_style):
    """
    Slėpti arba rodyti DOT sintaksės redaktorių.
    :param enable_edit: True (rodyti) arba False (slėpti).
    :param editor_style: redaktoriaus objekto stiliaus struktūra.
    :return: editor_style su pakeista "display" reikšme.
    """
    editor_style["display"] = "block" if enable_edit else "none"
    return editor_style


@callback(
    Output("graphviz-dot", "value"),
    Input("memory-submitted-data", "data"),
    Input("memory-filtered-data", "data"),
    Input("dropdown-engines", "value"),
    Input("dropdown-layouts", "value"),
)
def get_network_viz_chart(data_submitted, filtered_elements, engine, layout):
    """
    Atvaizduoja visas pasirinktas lenteles kaip tinklo mazgus.
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param engine: grafiko braižymo variklis "Cytoscape" arba "Viz"
    :param layout: išdėstymo stilius
    :return:
    """
    if (engine != "Viz") or (not filtered_elements):
        return ""
    # Išsitraukti reikalingus kintamuosius
    df_edges = pd.DataFrame(filtered_elements["edge_elements"])  # ryšių lentelė
    nodes = filtered_elements["node_elements"]  # mazgai (įskaitant mazgus)
    neighbors = filtered_elements["node_neighbors"]  # kaimyninių mazgų sąrašas
    df_nodes_tbl = pd.DataFrame(data_submitted["node_data"]["tbl_sheet_data"]["df"])
    df_nodes_col = pd.DataFrame(data_submitted["node_data"]["col_sheet_data"]["df"])

    # Atrinkti lenteles
    df_tbl = df_nodes_tbl[df_nodes_tbl["table"].isin(nodes)]  # PDSA lentelių lakšte "table" stulpelis privalomas
    if "table" in df_nodes_col.columns:  # Veikti net jei PDSA stulpelius aprašančiame lakšte "table" stulpelio nebūtų
        df_col = df_nodes_col[df_nodes_col["table"].isin(nodes)]
    else:
        df_col = pd.DataFrame({"table": {}})  # get_graphviz_dot() sukurs automatiškai pagal ryšius, jei jie yra

    # Sukurti DOT sintaksę
    dot = gu.get_graphviz_dot(df_tbl, df_col, nodes, neighbors, df_edges, layout)
    return dot


@callback(
    Output("viz-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("viz-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
)
def copy_viz_displayed_nodes_to_clipboard(filtered_elements, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "viz-clipboard" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "viz-clipboard"
    (vien programinis "viz-clipboard":"content" pakeitimas nepadėtų).
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
