"""
Dash komponentai, kurie naudojami utils_tabs_layouts.py funkcijose.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu;
Jei kaip biblioteką naudojate kitoms reikmėms, tuomet reikia įsikelti ir/arba konfigūruoti gettext, pvz.:
from gettext import pgettext, gettext as _
ARBA
from gettext import translation
translation("pdsa-grapher", 'locale', languages=["lt"]).install()
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import warnings
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from locale_utils.translations import pgettext
from . import utils as gu


def div_for_cyto():
    """
    Sukurti Dash objektus naudojimui su Cytoscape grafikos varikliu.
    :return: Dash html.Div()
    """

    div = html.Div(
        id="cyto-div",
        children=[
            get_fig_cytoscape(),
            dbc.DropdownMenu(
                # Rodyti užrašus virš aktyvių ryšių
                id="dropdown-menu-cyto",
                label="☰",
                className="dash-dropdown-menu",
                children=[
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-cyto-active-edge-labels",
                            label=_("Show active edge labels"),
                            value=False,
                        ),
                    ),
                    dbc.DropdownMenuItem(
                        # Nubraižytų lentelių kopijavimas
                        id="cyto-copy",
                        n_clicks=0,
                        children=copy_div_with_label("cyto-clipboard", _("Copy displayed tables")),
                    ),
                ],
                style={"position": "absolute"},
            ),
        ],
        style={"width": "100%", "height": "100%", "position": "absolute"},
    )
    return div


def get_fig_cytoscape(node_elements=None, df_edges=None, layout="cola"):
    """
    Sukuria Dash Cytoscape objektą - tinklo diagramą.

    Args:
        node_elements (list): sąrašas mazgų
        df_edges (pandas.DataFrame, pasirinktinai): tinklo mazgų jungtys, pvz.,
            df_edges =  pd.DataFrame().from_records([{"source_tbl": "VardasX"}, {"target_tbl": "VardasY"}])
            (numatytuoju atveju braižomas tuščias grąfikas - be mazgas)
        layout (str, optional): Cytoscape išdėstymo stilius; galimos reikšmės: "random", "circle",
            "breadthfirst", "cola" (numatyta), "cose", "dagre", "euler", "grid", "spread".

    Returns:
        Cytoscape objektas.
    """

    # Išdėstymų stiliai. Teoriškai turėtų būti palaikoma daugiau nei įvardinta, bet kai kurie neveikė arba nenaudingi:
    # "preset", "concentric", "close-bilkent", "klay"
    allowed_layouts = [
        "random", "circle", "breadthfirst", "cola", "cose", "dagre", "euler", "grid", "spread",
    ]
    if not (layout in allowed_layouts):
        default_layout = "cola"
        msg = _("Unexpected Cytoscape layout: '%s'. Using default '%s'") % (layout, default_layout)
        warnings.warn(msg)
        layout = default_layout
    cyto.load_extra_layouts()

    # Mazgai ir jungtys
    elements = gu.get_fig_cytoscape_elements(node_elements=node_elements, df_edges=df_edges)

    # Siūlomos spalvos: "indigo," "green", "darkgreen", "orange", "brown"
    edge_color_source = "darkgreen"
    edge_color_target = "indigo"

    fig_cyto = cyto.Cytoscape(
        id="cyto-chart",
        # zoom=len(node_elements)*2,
        boxSelectionEnabled=True,
        responsive=True,
        layout={
            "name": layout,
            "clusters": "clusterInfo",
            "animate": False,
            "idealInterClusterEdgeLengthCoefficient": 0.5,
            "fit": True,
        },
        style={"width": "100%", "height": "100%", "position": "absolute"},
        elements=elements,
        stylesheet=[
            # mazgai
            {
                "selector": "node",  # visi mazgai
                "style": {
                    "content": "data(label)",
                    "background-color": "lightblue",  # tik įprasti mazgai
                },
            },
            {
                "selector": "node.neighbor",  # tik kaimyniniai mazgai pasirinkus atitinkamą parinktį
                "style": {
                    "background-color": "lightgray",
                },
            },
            {
                "selector": "node:active, node:selected",  # pele pažymėtieji
                "style": {
                    "background-color": "blue",
                },
            },

            # ryšių linijos (tarp mazgų)
            {
                "selector": "edge",  # visi ryšiai
                "style": {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "font-size": "12px",  # Etikėtės teksto dydis
                    "text-rotation": "autorotate",  # Automatiškai pasukti etiketės tekstą, kad būtų lygiagretus linijai
                    "text-margin-x": "10px",        # Etikėtės teksto postūmis x ašyje
                    "text-margin-y": "-10px",       # Etikėtės teksto postūmis y ašyje
                }
            },
            {
                "selector": "edge:active, edge:selected",  # pele pažymėtieji
                "style": {
                    "label": "data(link_info_str)",
                    "color": "blue",  # etiketės spalva
                },
            },
            {
                "selector": "edge.source-neighbor",  # įeinantys ryšiai
                "style": {
                    "target-arrow-color": edge_color_source,
                    "line-color": edge_color_source,
                    "label": "data(link_info_str)",
                    "color": "#3CB371",  # žalia etiketės spalva
                }
            },
            {
                "selector": "edge.target-neighbor",  # išeinantys ryšiai
                "style": {
                    "target-arrow-color": edge_color_target,
                    "line-color": edge_color_target,
                    "label": "data(link_info_str)",
                    "color": "violet",  # etiketės spalva
                }
            },
        ],
    )

    return fig_cyto


def div_for_viz():
    """
    Sukurti Dash objektus naudojimui su Viz grafikos varikliu.
    :return: Dash html.Div()
    """

    fig = html.Div(
        id="graphviz-div",
        children=[
            html.Div(
                id="graphviz-chart",
                style={
                    "width": "100%",
                    "height": "100%",
                    "position": "absolute",
                    "textAlign": "center",
                    "overflow": "auto",
                },
            ),
            dcc.Textarea(
                id="graphviz-dot",
                value="",
                className="resizable",
                style={
                    "marginTop": 40,
                    "width": 300,
                    "height": 300,
                    "position": "absolute",
                    "fontFamily": "monospace",
                    "display": "none",
                }
            ),

            dbc.DropdownMenu(
                id="dropdown-menu-viz",
                label="☰",
                className="dash-dropdown-menu",
                children=[
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-edit-dot",
                            label=_("DOT syntax"),
                            value=False,
                        ),
                    ),
                    dbc.DropdownMenuItem(  # Susijungiančios pagal ryšių dokumentą
                        html.Span(
                            _("Save SVG"),
                            style={"marginLeft": "25px"},
                        ),
                        id="save-svg",
                        n_clicks=0,
                    ),
                ],
                style={"position": "absolute"},
            ),
            dcc.Download(id="download-svg"),
        ],
        style={"width": "100%", "height": "100%", "position": "absolute"},
    )
    return fig


def pdsa_radio_sheet_components(id_radio_sheet_tbl, id_radio_sheet_col):
    output_elements = [
        html.H6([_("Sheets:")]),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Label([
                            _("PDSA sheet describing"), " ",
                            html.B(pgettext("PDSA sheet describing... (galininkas)", "tables")), ": "
                        ]),
                        dcc.RadioItems(id=id_radio_sheet_tbl, options=[]),
                    ]
                ),
                dbc.Col(
                    children=[
                        dbc.Label([
                            _("PDSA sheet describing"), " ",
                            html.B(pgettext("PDSA sheet describing... (galininkas)", "columns")), ": "
                        ]),
                        dcc.RadioItems(id=id_radio_sheet_col, options=[]),
                    ]
                ),
            ],
        ),
    ]
    return output_elements


def pdsa_dropdown_columns_components(id_sheet_type, id_dropdown_sheet_type):
    dropdown_sheet_type = [
        html.Hr(),
        dbc.Label(
            [
                _("Select columns of PDSA sheet"), " ",
                html.B(id=id_sheet_type, children=[""]),
                " ", _("that you want to see in the grapher"),
            ]
        ),
        dcc.Dropdown(id=id_dropdown_sheet_type, options=[], value=[], multi=True, placeholder=_("Select...")),
    ]

    return dropdown_sheet_type


def table_preview():
    return dash_table.DataTable()


def dropdown_with_label(dropdown_id, label):
    output_element = html.Div(
        children=[
            dbc.Label(html.B(label)),
            dcc.Dropdown(id=dropdown_id, options=[], placeholder=_("Select...")),
        ]
    )
    return output_element


def copy_div_with_label(clipboard_id, label="", target_id=None):
    """
    Teksto kopijavimo mygtukas su užrašu, kurį reaguoja į paspaudimą tarsi į ženkliuko paspaudimą.
    Standartinė dcc.Clipboard f-ja palaiko tik ženkliuko pateikimą, be galimybės pridėti tekstą šalia;
    bet tą ženkliuką spausti būtina, nes programiškai keičiant vien "content" per Dash nepakeičia iškarpinė.
    :param clipboard_id: Naujai kuriamo objekto identifikatorius.
    :param label:  Užrašas šalia kopijavimo ženkliuko.
    :param target_id: Objektą, kurio turinį kopijuoti; jei None, nepamirškite atskirai priskirti
        kopijuotiną tekstą per clipboard_id objekto savybę "content" arba "html_content".
    :return:
    """
    return html.Div([
        # Tik užrašas kopijavimui, vien jo paspaudimas nieko nepadarytų
        html.Span(
            label,
            style={"position": "absolute", "marginLeft": "25px"},
        ),
        # Tik kopijavimo mygtuko paspaudimas atlieka tikrąjį kopijavimo darbą,
        # bet jo reaktyvioji sritis paspaudimui turi užimti visą meniu plotį
        dcc.Clipboard(
            id=clipboard_id,
            target_id=target_id,
            style={
                "position": "relative",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
            },
        ),
    ]),


def graphic_usage_info():
    grafikas_content = dbc.Card(
        dbc.CardBody(
            [
                html.H6(_("Graphic usage instructions"), className="card-title"),
                html.Div(
                    children=[
                        html.P(
                            _("The graph shows the relationships between the selected tables, "
                              "which are described in the references file.")
                        ),
                        html.P(_("The graph is interactive:")),
                        html.P(_("View can be zoomed in/out")),
                        html.P(
                            _("You can drag points individually or multiple at once (press CTRL)")
                        ),
                        html.P(
                            _("In fact, the appearance of a point does not change when it is selected, "
                              "so it may appear that nothing has been selected")
                        ),
                    ],
                    className="card-text",
                ),
            ]
        ),
    )
    grafikas = html.Div(
        [
            dbc.Button(
                _("Graphic instructions"),
                id="tutorial-grafikas-legacy-target",
                color="success",
                n_clicks=0,
                style={"float": "right", "fontSize": "100%"},
            ),
            dbc.Popover(
                grafikas_content,
                target="tutorial-grafikas-legacy-target",
                body=True,
                trigger="legacy",
                style={"fontSize": "80%"},
            ),
        ]
    )
    return grafikas


def filters_usage_info():
    filtrai_content = dbc.Card(
        dbc.CardBody(
            [
                html.H6(_("Filter usage instructions"), className="card-title"),
                html.Br(),
                html.Div(
                    children=[
                        html.P(
                            _("The graph can be displayed by selecting individual tables or by entering "
                              "a list of tables. Information about the tables can also be found here")
                        ),
                        html.P(
                            children=[
                                html.B(_("Layout")),
                                " - ",
                                html.Label(_("Style of the point placement in the graph.")),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Select tables to graph")),
                                " - ",
                                html.Label(
                                    _("Select PDSA tables which relationships you want to display")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Add list of tables")),
                                " - ",
                                html.Label(
                                    _("You can also specify the tables to be displayed in the list; "
                                      "the names of the tables must be separated by commas")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get neighbours")),
                                " - ",
                                html.Label(
                                    _("Supplement the graph with tables that relate directly to the selected tables")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get info about columns of selected tables")),
                                " - ",
                                html.Label(
                                    _("Displays information about the columns of the selected table(s)")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get info on displayed tables")),
                                " - ",
                                html.Label(
                                    _("Displays the information of the tables shown in the graph")
                                ),
                            ]
                        ),
                    ],
                    className="card-text",
                ),
            ]
        ),
    )
    filtrai = html.Div(
        [
            dbc.Button(
                _("Filter Instructions"),
                id="tutorial-filtrai-legacy-target",
                color="success",
                n_clicks=0,
                style={"fontSize": "100%"},
            ),
            dbc.Popover(
                filtrai_content,
                target="tutorial-filtrai-legacy-target",
                body=True,
                trigger="legacy",
                style={"fontSize": "85%"},
            ),
        ]
    )
    return filtrai


def active_element_info(tooltip_id="active-node-info"):
    """
    Informacinis debesėlis
    """
    return dcc.Tooltip(
        id=tooltip_id,
        direction="left",
        zindex=200,
        style={
            "minWidth": "200px",  # riboti plotį
            "position": "absolute",
            "background": "#cff4fc",
            "fontSize": "85%",
            "textWrap": "wrap",
        },
        children=[
            html.Div([
                html.Div(
                    id=f"{tooltip_id}-header",
                    children=[]
                ),
                html.Div(
                    id=f"{tooltip_id}-content",
                    children=[],
                    style={
                        "minWidth": "200px",  # riboti plotį
                        "minHeight": "10px",  # riboti aukštį
                        "maxHeight": "300px",  # riboti aukštį
                        "overflowY": "auto",  # pridėti slinkties juostas, jei netelpa
                        "resize": "both",       # leisti keisti tiek plotį, tiek aukštį
                        "pointerEvents": "auto",  # reaguoti į pelę
                    },
                ),
            ])
        ]
    )
