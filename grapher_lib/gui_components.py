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
from grapher_lib import utils as gu


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
                        # Nubraižytų lentelių kopijavimas
                        id="cyto-copy",
                        n_clicks=0,
                        children=copy_div_with_label("cyto-clipboard", _("Copy displayed tables")),
                        style={
                            "width": "250px",  # kadangi neprisitaiko pagal copy_div_with_label() plotį, reikia nurodyti tiksliai},
                        }
                    ),
                    html.Hr(),
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-cyto-active-edge-labels",
                            label=_("Show active edge labels"),
                            value=False,
                        ),
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
                    "width": 500,
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
                        # Nubraižytų lentelių kopijavimas
                        id="viz-copy",
                        n_clicks=0,
                        children=copy_div_with_label("viz-clipboard", _("Copy displayed tables")),
                        style={
                            "width": "250px",  # kadangi neprisitaiko pagal copy_div_with_label() plotį, reikia nurodyti tiksliai},
                        }
                    ),
                    html.Hr(),
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-viz-all-columns",
                            label=_("Show all columns"),
                            value=False,
                        ),
                    ),
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-viz-description",
                            label=_("Show descriptions in graph"),
                            value=True,
                        ),
                    ),
                    dbc.DropdownMenuItem(
                        dbc.Checkbox(
                            id="checkbox-edit-dot",
                            label=_("Show Graphviz DOT syntax"),
                            value=False,
                        ),
                    ),
                    dbc.DropdownMenuItem(  # Susijungiančios pagal ryšių dokumentą
                        id="save-svg",
                        n_clicks=0,
                        children=html.Span(
                            _("Save SVG"),
                            style={"marginLeft": "25px"},
                        ),
                    ),
                ],
                style={"position": "absolute"},
            ),
            dcc.Download(id="download-svg"),
        ],
        style={"width": "100%", "height": "100%", "position": "absolute"},
    )
    return fig


def upload_data(upload_id, upload_label_id, upload_label=None):
    """
    Rinkmenos įkėlimo laukelis
    :param upload_id: pagrindinio objekto identifikatorius, t.y. dcc.Upload() "id"
    :param upload_label_id: užrašo objekto identifikatorius, t.y. html.A() "id"
    :param upload_label: užrašas, t.y. html.A() "children"
    :return: dcc.Upload()
    """
    return dcc.Upload(
        id=upload_id,
        children=html.Div([
            html.A(
                id=upload_label_id,
                children=upload_label or _("Drag and Drop"),
            ),
        ]),
        style={
            "minHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "display": "flex",
            "alignItems": "center",  # vertikalus lygiavimas
            "justifyContent": "center",  # teksto pačio stačiakampio lygiavimas centre
            "textAlign": "center",  # teksto stačiakampio viduje lygiavimas centre
            "margin": "10px",
        },
        multiple=True,  # iš tiesų neįkeliam kelių, bet dėl sintaksės suderinamumo paliekam po senovei
    )


def refs_sheet_selection_components(id_radio_sheet_refs):
    """
    Ryšių lakštų pasirinkimas
    :param id_radio_sheet_refs: Ryšių lentelių lakšto pasirinkimo objekto id
    :return: Dash objektų sąrašas, kuris gali būti naudojamas kaip Dash objekto "children"
    """
    return [
        html.H6([_("Select references sheet:")]),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dcc.RadioItems(id=id_radio_sheet_refs, options=[]),
                    ]
                ),
            ],
        ),
    ]


def pdsa_sheet_selection_components(id_radio_sheet_tbl, id_radio_sheet_col):
    """
    PDSA lakštų pasirinkimas
    :param id_radio_sheet_tbl: PDSA lentelių lakšto pasirinkimo objekto id
    :param id_radio_sheet_col: PDSA stulpelių lakšto pasirinkimo objekto id
    :return: Dash objektų sąrašas, kuris gali būti naudojamas kaip Dash objekto "children"
    """
    return [
        html.H6([_("Select PDSA sheets:")]),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Label([
                            _("Sheet describing"), " ",
                            html.B(pgettext("PDSA sheet describing...", "tables")), ": "
                        ]),
                        dcc.RadioItems(id=id_radio_sheet_tbl, options=[]),
                    ]
                ),
                dbc.Col(
                    children=[
                        dbc.Label([
                            _("Sheet describing"), " ",
                            html.B(pgettext("PDSA sheet describing...", "columns")), ": "
                        ]),
                        dcc.RadioItems(id=id_radio_sheet_col, options=[]),
                    ]
                ),
            ],
        ),
    ]


def pdsa_columns_selection_header(sheet_type_id, sheet_type_label):
    """
    Antraštė PDSA stulpelių pasirinkimui.

    :param sheet_type_id: objekto identifikatorius, pagal kurio vaiką keičiamas pasirinkto lakšto užrašas.
    :param sheet_type_label: pusjuodžiu šriftu rašomas lakšto tipas, kuris nesikeičia.
    :return: html.H6()
    """
    return html.H6([
        pgettext("From PDSA sheet ... select columns that contain", "From PDSA sheet describing"), " ",
        html.B(sheet_type_label),
        " (", html.B(id=sheet_type_id, children=[""]), ")",
        pgettext("From PDSA sheet ... select columns that contain", "select columns that contain")
    ])


def pdsa_dropdown_columns_components(id_dropdown_sheet_type):
    dropdown_sheet_type = [
        html.Br(),
        html.H6(_("Select which columns you want to see information for below the graph:")),
        dcc.Dropdown(id=id_dropdown_sheet_type, options=[], value=[], multi=True, placeholder=_("Select...")),
    ]

    return dropdown_sheet_type


def table_preview():
    return dash_table.DataTable()


def dropdown_with_label(dropdown_id, label):
    output_element = html.Div(
        children=[
            dbc.Label(label),
            dcc.Dropdown(id=dropdown_id, options=[], placeholder=_("Select...")),
        ],
        style={"marginTop": "5px"}
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
    return html.Div(
        children=[
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
        ],
    ),
