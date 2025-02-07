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
    df_tbl = df_nodes_tbl[df_nodes_tbl["table"].isin(nodes)]
    df_col = df_nodes_col[df_nodes_col["table"].isin(nodes)]
    dot = gu.get_graphviz_dot(df_tbl, df_col, nodes, neighbors, df_edges, layout)
    return dot
