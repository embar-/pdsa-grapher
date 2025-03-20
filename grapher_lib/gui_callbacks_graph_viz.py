"""
PDSA grapher Dash app callbacks in "Graphic" tab for Viz engine.
"""
"""
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import Output, Input, State, callback, callback_context, no_update
from grapher_lib import utils as gu

@callback(
    Output("graphviz-dot", "style"),
    Input("checkbox-edit-dot", "value"),
    State("graphviz-dot", "style"),
    config_prevent_initial_callbacks=True,
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
    Input("checkbox-viz-all-columns", "value"),  # parinktis per Viz grafiko kontekstinį meniu stulpelių rodymui
    Input("checkbox-viz-description", "value"),  # parinktis per Viz grafiko kontekstinį meniu aprašų rodymui
    Input("checkbox-viz-show-checkbox", "value"),  # parinktis per Viz grafiko kontekstinį meniu langelių rodymui
    State("memory-viz-clicked-checkbox", "data"),
    config_prevent_initial_callbacks=True,
)
def get_network_viz_chart(
    data_submitted, filtered_elements, engine, layout,
    show_all_columns, show_descriptions, show_checkbox, viz_selection_dict
):
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
    :param show_all_columns: ar rodyti visus lentelės stulpelius (True); ar tik turinčius ryšių (False)
    :param show_descriptions: ar rodyti lentelių ir stulpelių aprašus pačiame grafike
    :param show_checkbox: ar prie stulpelių pridėti žymimuosius langelius
    :param viz_selection_dict: Visų sužymėtų langelių simboliai žodyne,
        kur pirmasis lygis yra lentelės, antrasis – stulpeliai, pvz:
        {
            "Skaitytojas": {"ID": "⬜"},
            "Rezervacija": {"ClientID": "🟩", "BookCopyID": "🟥"}}
        }
    :return:
    """
    if (engine != "Viz") or (not filtered_elements):
        return ""
    # Išsitraukti reikalingus kintamuosius
    df_edges = pl.DataFrame(filtered_elements["edge_elements"], infer_schema_length=None)  # ryšių lentelė
    nodes = filtered_elements["node_elements"]  # mazgai (įskaitant mazgus)
    neighbors = filtered_elements["node_neighbors"]  # kaimyninių mazgų sąrašas
    df_nodes_tbl = pl.DataFrame(data_submitted["node_data"]["tbl_sheet_data"], infer_schema_length=None)
    df_nodes_col = pl.DataFrame(data_submitted["node_data"]["col_sheet_data"], infer_schema_length=None)

    # Atrinkti lenteles
    if "table" in df_nodes_tbl.columns:
        df_tbl = df_nodes_tbl.filter(pl.col("table").is_in(nodes))
    else:  # Veikti net jei PDSA lenteles aprašančiame lakšte "table" stulpelio nebūtų
        df_tbl = pl.DataFrame({"table": {}})  # get_graphviz_dot() sukurs automatiškai pagal ryšius, jei jie yra
    if "table" in df_nodes_col.columns:
        df_col = df_nodes_col.filter(pl.col("table").is_in(nodes))
    else:  # Veikti net jei PDSA stulpelius aprašančiame lakšte "table" stulpelio nebūtų
        df_col = pl.DataFrame({"table": {}})  # get_graphviz_dot() sukurs automatiškai pagal ryšius, jei jie yra
    df_checkbox = gu.convert_nested_dict2df(viz_selection_dict, ["table", "column", "checkbox"])
    if "checkbox" in df_col:
        df_col = df_col.drop("checkbox")  # išmesti seną stulpelį, nes prijungsim naujas reikšmes iš df_checkboxs
    df_col = df_col.join(df_checkbox, on=["table", "column"], how="left")

    # Sukurti DOT sintaksę
    dot = gu.get_graphviz_dot(
        nodes=nodes, neighbors=neighbors, df_tbl=df_tbl, df_col=df_col, df_edges=df_edges,
        layout=layout, show_all_columns=show_all_columns, show_descriptions=show_descriptions,
        show_checkbox=show_checkbox
    )
    return dot


@callback(
    Output("viz-graph-nodes-plain-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("viz-graph-nodes-plain-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_viz_displayed_nodes_to_clipboard(filtered_elements, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "viz-graph-nodes-plain-clipboard" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "viz-graph-nodes-plain-clipboard"
    (vien programinis "viz-graph-nodes-plain-clipboard":"content" pakeitimas nepadėtų).
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


@callback(
    Output("viz-graph-nodes-quoted-clipboard", "content"),  # tekstas iškarpinei
    State("memory-filtered-data", "data"),
    Input("viz-graph-nodes-quoted-clipboard", "n_clicks"),  # paspaudimas per ☰ meniu
    config_prevent_initial_callbacks=True,
)
def copy_viz_displayed_nodes_to_clipboard_quoted(filtered_elements, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "viz-graph-nodes-quoted-clipboard" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "viz-graph-nodes-plain-clipboard"
    (vien programinis "viz-graph-nodes-quoted-clipboard":"content" pakeitimas nepadėtų).
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
    return '"' + f'",\n"'.join(displayed_nodes) + '"'


@callback(
    Output("memory-viz-clicked-checkbox", "data"),
    Input("memory-submitted-data", "data"),
    Input("viz-clicked-checkbox-store", "data"),
    State("memory-viz-clicked-checkbox", "data"),
    prevent_initial_callbacks=True,
)
def remember_viz_clicked_checkbox(data_submitted, viz_last_clicked_checkbox, viz_selection_dict):
    """
    Paskutinio pakeisto žymimojo langelio simbolį įtraukia į visų pakeistųjų žodyną
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param viz_last_clicked_checkbox: Paskutinio paspausto langelio duomenys, pvz:
        {
            "type": "checkboxClicked",
            "id": "Skaitytojas:ID",
            "value": True,
            "symbol": "🟩",
            "parentPosition": {"x": 168.6, "y": 268.6, "width": 275.4, "height": 21.5}
        }
    :param viz_selection_dict: Visų sužymėtų langelių simboliai žodyne,
        kur pirmasis lygis yra lentelės, antrasis – stulpeliai, pvz:
        {
            "Skaitytojas": {"ID": "⬜"},
            "Rezervacija": {"ClientID": "🟩", "BookCopyID": "🟥"}}
        }
    :return:
    """
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]  # Sužinoti, kas iškvietė f-ją
    if (changed_id == "memory-submitted-data.data") and data_submitted:
        # Įkelti nauji duomenys "col_sheet_data"
        if data_submitted["node_data"]["col_sheet_renamed_cols"]["checkbox"]:  # Ar buvo "checkbox" prasmę turintis stulpelis
            return gu.convert_df2nested_dict(
                data_submitted["node_data"]["col_sheet_data"],
                col_names=["table", "column", "checkbox"]
            )
        return {}
    if not viz_selection_dict:
        viz_selection_dict = {}
    if (
        (not viz_last_clicked_checkbox) or (not isinstance(viz_last_clicked_checkbox, dict)) or
        ("id" not in viz_last_clicked_checkbox)
    ):
        # viz_last_clicked_checkbox netinkamas
        return no_update
    id_parts = viz_last_clicked_checkbox["id"].split(":")
    if len(id_parts) != 2:
        return no_update
    table, column = id_parts
    if table not in viz_selection_dict:
        viz_selection_dict[table] = {}
    viz_selection_dict[table][column] = viz_last_clicked_checkbox["symbol"]
    return viz_selection_dict


@callback(
    Output("checkbox-viz-show-checkbox", "value"),
    Input("memory-submitted-data", "data"),
    State("checkbox-viz-show-checkbox", "value"),
    prevent_initial_callbacks=True,
)
def viz_clicked_checkbox_visibility(data_submitted, viz_selection_visibility):
    """
    Jei nėra įjungtas Viz langelių rodymas, įjungti automatiškai esant spalvotų langelių duomenims.
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param viz_selection_visibility: ar per Viz grafiko ☰ meniu įjungtas langelių rodymas
    """
    if viz_selection_visibility:
        return True
    if data_submitted:
        checkbox_col = data_submitted["node_data"]["col_sheet_renamed_cols"]["checkbox"]
        if checkbox_col:  # Ar buvo "checkbox" prasmę turintis stulpelis
            df = pl.DataFrame(data_submitted["node_data"]["col_sheet_data"], infer_schema_length=None)
            df = df.filter(
                pl.when(
                    pl.col(checkbox_col).is_null() |
                    pl.col(checkbox_col).cast(pl.Utf8).str.to_lowercase().is_in(
                        ["false", "no", "ne", "0", "", "⬜", "🔲", "☐"]
                    )
                )
                .then(pl.lit(False))
                .otherwise(pl.lit(True))
            )
            return not df.is_empty()
    return False
