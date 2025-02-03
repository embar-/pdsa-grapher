"""
Graferio kortelių struktūros kūrimas.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu.
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

import dash_bootstrap_components as dbc
from dash import dcc, html
from . import my_components as mc
from locale_utils.translations import pgettext


def file_uploading_tab_layout():
    return html.Div(
        [
            dbc.Row(
                style={"marginTop": "20px"},
                children=[
                    dbc.Col(
                        width={"size": 6},
                        id="pdsa-panel",
                        children=[
                            html.Div(
                                style={"marginLeft": "20px", "marginRight": "10px"},
                                children=[
                                    html.H5(
                                        _("PDSA"),
                                        style={"textAlign": "center"},
                                    ),
                                    html.Div(
                                        id="pdsa-selections",
                                        children=[
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    [
                                                        _("Drag and Drop") + " ",
                                                        html.A(pgettext("Drag and Drop", "PDSA File")),
                                                    ]
                                                ),
                                                style={
                                                    "height": "60px",
                                                    "lineHeight": "60px",
                                                    "borderWidth": "1px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "5px",
                                                    "textAlign": "center",
                                                    "margin": "10px",
                                                },
                                                # Allow multiple files to be uploaded
                                                multiple=True,
                                            )
                                        ],
                                    ),
                                    html.H6(
                                        children=[
                                            _("File name: "),
                                            html.B(
                                                id="pdsa-file-name",
                                                children=[],
                                                style={'fontSize': '90%'},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="info-uploaded-pdsa",
                                        children=mc.pdsa_radio_components(
                                            "radio-sheet-tbl",
                                            "radio-sheet-col",
                                        ),
                                    ),
                                    html.Div(
                                        id="column-selection-sheet-tbl",
                                        children=mc.pdsa_dropdown_columns_componenets(
                                            "id-sheet-tbl", "dropdown-sheet-tbl"
                                        ),
                                    ),
                                    html.Div(
                                        id="sheet-tbl-preview",
                                        children=mc.table_preview(),
                                    ),
                                    html.Div(
                                        id="column-selection-sheet-col",
                                        children=mc.pdsa_dropdown_columns_componenets(
                                            "id-sheet-col", "dropdown-sheet-col"
                                        ),
                                    ),
                                    html.Div(
                                        id="sheet-col-preview",
                                        children=mc.table_preview(),
                                    ),
                                ],
                            )
                        ],
                    ),
                    dbc.Col(
                        width={"size": 6},
                        id="uzklausa-panel",
                        children=[
                            html.Div(
                                style={"marginLeft": "10px", "marginRight": "20px"},
                                children=[
                                    html.H5(
                                        _("References"),
                                        style={"textAlign": "center"},
                                    ),
                                    html.Div(
                                        id="uzklausa-selections",
                                        children=[
                                            dcc.Upload(
                                                id="upload-data-uzklausa",
                                                children=html.Div(
                                                    [
                                                        _("Drag and Drop"), " ",
                                                        html.A(
                                                            pgettext("Drag and Drop", "References File")
                                                        ),
                                                    ]
                                                ),
                                                style={
                                                    "height": "60px",
                                                    "lineHeight": "60px",
                                                    "borderWidth": "1px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "5px",
                                                    "textAlign": "center",
                                                    "margin": "10px",
                                                },
                                                # Allow multiple files to be uploaded
                                                multiple=True,
                                            ),
                                        ],
                                    ),
                                    html.H6(
                                        children=[
                                            _("File name: "),
                                            html.B(
                                                id="uzklausa-file-name",
                                                children=[],
                                                style={'fontSize': '90%'},
                                            ),
                                        ]
                                    ),
                                    html.H6(
                                        children=[_("Select columns that contain:")],
                                    ),
                                    dbc.Row(
                                        children=[
                                            dbc.Col(
                                                children=mc.uzklausa_select_source_target(
                                                    "ref-source-tables",
                                                    pgettext("source tables", "references")
                                                ),
                                            ),
                                            dbc.Col(
                                                children=mc.uzklausa_select_source_target(
                                                    "ref-source-columns",
                                                    pgettext("source columns", "references")
                                                ),
                                            )
                                        ],
                                    ),
                                    dbc.Row(
                                        children=[
                                            dbc.Col(
                                                children=mc.uzklausa_select_source_target(
                                                    "ref-target-tables",
                                                    pgettext("target tables", "references")
                                                ),
                                            ),
                                            dbc.Col(
                                                children=mc.uzklausa_select_source_target(
                                                    "ref-target-columns",
                                                    pgettext("target columns", "references")
                                                ),
                                            )
                                        ],
                                    ),
                                    html.Br(),
                                    html.Div(
                                        id="uzklausa-tbl-preview",
                                        children=mc.table_preview(),
                                    ),
                                    html.Div(
                                        style={"marginTop": "20px"},
                                        children=[
                                            dbc.Button(
                                                id="button-submit",
                                                children=html.B(_("Submit")),
                                                color="secondary",
                                            ),
                                            html.Div(
                                                id="submit-error-message",
                                                children=[],
                                                style={"color": "red"},
                                            ),
                                            html.Div(
                                                id="submit-warning-message",
                                                children=[],
                                                style={"color": "brown"},
                                            ),
                                        ],
                                        className="d-grid gap-2",
                                    ),
                                ],
                            )
                        ],
                    ),
                ]
            ),
        ]
    )

def grapher_tab_layout():
    return html.Div(
        style={
            "marginLeft": "10px",
            "marginRight": "10px",
            "marginTop": "10px",  # kad kalbos keitimo mygtukas dešiniame kampe nesukurtų didelės dešinės paraštės
            "marginBottom": "10px",
        },
        children=[
            dbc.Row(
                # className="resizable-row" tam, kad būtų galima pakeisti grafiko aukštį. Čiupkite už dešiniojo kampo
                className="resizable-row",
                children=[

                    # Pats grafikas
                    dbc.Col(
                        width=9,  # iš 12 pločio vienetų;
                        style={
                            "width": "74%",
                            "position": "relative",
                            "marginRight": "1%",
                        },
                        children=[
                            html.Div(id="my-network", children=mc.get_fig_cytoscape()),
                        ],
                    ),

                    # Atrankos pasirinkimai
                    dbc.Col(
                        width=3,  # iš 12 pločio vienetų;
                        style={
                            "width": "25%",
                            "position": "relative",
                        },
                        children=html.Div(
                            children=[
                                dbc.Row(
                                    style={
                                        "marginTop": "20px",
                                        "marginBottom": "20px",
                                    },
                                    # Paaiškinimų mygtukai
                                    children=[
                                        dbc.Col(
                                            children=[html.Div(mc.filters_usage_info())],
                                            style={"width": "50%"},
                                            width=1.5,
                                        ),
                                        dbc.Col(
                                            children=[html.Div(mc.graphic_usage_info())],
                                            style={"width": "50%"},
                                            width=1.5,
                                        ),
                                    ],
                                ),

                                # Braižytinos lentelės
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col(
                                        children=[
                                            html.P(_("Select tables to graph")),
                                        ],
                                        style={"width": "50%"},
                                    ),
                                    dbc.Col(
                                        dbc.DropdownMenu(
                                            id="dropdown-draw-tables",
                                            label=_("Select"),
                                            className="dash-dropdown-menu",
                                            children=[
                                                dbc.DropdownMenuItem(  # Susijungiančios pagal ryšių dokumentą
                                                    pgettext("Select tables", "Automatically"),
                                                    id="draw-tables-auto",
                                                    n_clicks=0
                                                ),
                                                dbc.DropdownMenuItem(  # Susijungiančios pagal ryšių dokumentą
                                                    pgettext("Select tables", "Interconnected"),
                                                    id="draw-tables-refs",
                                                    n_clicks=0
                                                ),
                                                dbc.DropdownMenuItem(  # Pagal PDSA lentelių lakštą
                                                    pgettext("Select tables", "Defined in PDSA"),
                                                    id="draw-tables-pdsa",
                                                    n_clicks=0
                                                ),
                                                dbc.DropdownMenuItem(  # Visos visos
                                                    pgettext("Select tables", "All"),
                                                    id="draw-tables-all",
                                                    n_clicks=0
                                                ),
                                            ],
                                            style={
                                                "float": "right",
                                                "width": "50%",
                                                "fontSize": "80%  !important",  # Nepadeda :/
                                                "marginRight": "20px",
                                            },
                                        ),
                                    ),
                                ]),
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            id="dropdown-tables",
                                            options=[],
                                            value=[],
                                            multi=True,
                                            placeholder=_("Select..."),
                                        ),
                                    ],
                                ),
                                # Rodytinų lentelių papildomas sąrašas (atskirtas kableliu)
                                html.Div(
                                    children=[
                                        html.Br(),
                                        html.P(
                                            _("Add list of tables to graph (comma separated)")
                                        ),
                                        dcc.Input(
                                            id="input-list-tables",
                                            style={"width": "100%"},
                                            placeholder=_("table1,table2,table3..."),
                                        ),
                                    ],
                                ),
                                html.Br(),
                                dbc.Checkbox(
                                    id="checkbox-get-neighbours",
                                    label=_("Get neighbours"),
                                    value=False
                                ),

                                # Išdėstymo stilius
                                html.Hr(),
                                html.Div(
                                    children=[
                                        html.P(_("Layout")),
                                        dcc.Dropdown(
                                            id="dropdown-layouts",
                                            options=[
                                                "random",
                                                "breadthfirst",
                                                "circle",
                                                "cola",
                                                "cose",
                                                "dagre",
                                                "euler",
                                                "grid",
                                                "spread",
                                            ],
                                            value="cola",
                                            clearable=False,  # niekada negali būti tuščia reikšmė
                                            placeholder=_("Select..."),
                                        ),
                                    ],
                                ),
                                html.Br(),
                            ],
                        ),
                    ),
                ],
            ),

            # Po grafiku. PDSA duomenis atvaizduojančios lentelės.
            dbc.Row(
                style={"position": "relative", "height": "20%"},
                children=[
                    html.Hr(),

                    # Informacija apie pasirinktų lentelių stulpelius
                    dbc.Col(
                        className="resizable-col",
                        style={"resize": "horizontal"},
                        width=9,  # iš 12 pločio vienetų;
                        children=[
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        width=2,  # iš 12 pločio vienetų;
                                        children=[
                                            # Informacija apie pasirinktų lentelių stulpelius - žymimasis langelis
                                            dbc.Checkbox(
                                                id="checkbox-get-selected-nodes-info-to-table",
                                                label=_("Get info about columns of selected tables"),
                                                value=True
                                            ),
                                        ],
                                    ),
                                    dbc.Col(
                                        width=7,  # iš 12 pločio vienetų;
                                        children=[
                                            # Informacija apie pasirinktų lentelių stulpelius - išskleidžiamasis sąrašas
                                            dcc.Dropdown(
                                                id="filter-tbl-in-df",
                                                options=[],
                                                value=[],
                                                multi=True,
                                                placeholder=_("Select..."),
                                                style={"width": "90%"},
                                            ),
                                        ],
                                    ),
                                    html.Br(),
                                ],
                            ),
                            dbc.Row(
                                className="resizable-row",
                                style={"resize": "vertical"},
                                children=[
                                    # Informacija apie pasirinktų lentelių stulpelius - lentelė
                                    html.Div(id="table-selected-tables", children=mc.table_preview()),
                                ],
                            ),
                            html.Br(),
                        ],
                    ),

                    # Info apie nubraižytas lenteles
                    dbc.Col(
                        width=3,  # iš 12 pločio vienetų;
                        children=[
                            dbc.Row(
                                children=[
                                    # Info apie nubraižytas lenteles - žymimasis langelis
                                    dbc.Checkbox(
                                        id="checkbox-get-displayed-nodes-info-to-table",
                                        label=_("Get info on displayed tables"),
                                        value=True
                                    ),
                                ],
                            ),
                            # Info apie nubraižytas lenteles - pačios lentelės
                            dbc.Row(
                                className="resizable-row",
                                id="table-displayed-nodes",
                                children=mc.table_preview()
                            ),
                            html.Br(),
                        ],
                    ),

                ],
            ),
            mc.active_element_info("active-node-info"),
            mc.active_element_info("active-edge-info"),
        ],
    )
