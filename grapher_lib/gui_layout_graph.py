"""
Graferio grafiko kortelės struktūros kūrimas.

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
from grapher_lib import gui_components as gc
from grapher_lib import gui_components_info as gi
from locale_utils.translations import pgettext


def graph_tab_layout():
    return html.Div(
        style={
            "marginLeft": "10px",
            "marginRight": "10px",
            "marginTop": "10px",  # kad kalbos keitimo mygtukas dešiniame kampe nesukurtų didelės dešinės paraštės
            "marginBottom": "10px",
        },
        children=[
            dbc.Row(
                # className="resizable" tam, kad būtų galima pakeisti grafiko aukštį. Čiupkite už dešiniojo kampo
                className="resizable",
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
                            html.Div(id="my-network", children=[gc.div_for_cyto(), gc.div_for_viz()]),
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
                                            children=[html.Div(gi.filters_usage_info())],
                                            style={"width": "50%"},
                                            width=1.5,
                                        ),
                                        dbc.Col(
                                            children=[html.Div(gi.graphic_usage_info())],
                                            style={"width": "50%"},
                                            width=1.5,
                                        ),
                                    ],
                                ),

                                # Išdėstymo stilius
                                html.Hr(),
                                dbc.Row(
                                    children=[
                                        dbc.Col(
                                            children=[
                                                html.P(_("Graphic engine")),
                                                dcc.Dropdown(
                                                    id="dropdown-engines",
                                                    options=[
                                                        "Cytoscape",
                                                        "Viz",
                                                    ],
                                                    value="Viz",
                                                    clearable=False,  # niekada negali būti tuščia reikšmė
                                                    placeholder=_("Select..."),
                                                ),
                                            ],
                                        ),
                                        dbc.Col(
                                            children=[
                                                html.P(_("Layout")),
                                                dcc.Dropdown(
                                                    id="dropdown-layouts",
                                                    options=[],
                                                    value=None,
                                                    clearable=False,  # niekada negali būti tuščia reikšmė
                                                    placeholder=_("Select..."),
                                                ),
                                            ],
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
                                        children=[
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
                                                        pgettext("Select tables", "Interconnected from refs"),
                                                        id="draw-tables-refs",
                                                        n_clicks=0
                                                    ),
                                                    dbc.DropdownMenuItem(  # Pagal PDSA lentelių lakštą
                                                        pgettext("Select tables", "Interconnected from PDSA"),
                                                        id="draw-tables-common",
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
                                                    # FIXME: mygtuko per didelis šriftas, bet kodas žemiau nepadeda
                                                    # "fontSize": "80% !important",
                                                }
                                            ),
                                        ],
                                        style={
                                            "width": "50%",
                                        },
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
                                            value="",  # Kad nemestų "Warning: A component is changing an uncontrolled input of type text to be controlled."
                                        ),
                                    ],
                                ),
                                html.Br(),

                                # Rodyti kaimynus
                                dbc.Row([
                                    dbc.Col(
                                        children=[
                                            dbc.Checkbox(
                                                id="checkbox-get-neighbours",
                                                label=_("Get neighbours"),
                                                value=False
                                            ),
                                        ],
                                        style={"width": "50%"},
                                    ),
                                    dbc.Col(
                                        children=[
                                            dcc.Dropdown(
                                                id="dropdown-neighbors",
                                                options=[
                                                    {"label": pgettext("neighbors", "all"),
                                                     "value": "all"},
                                                    {"label": pgettext("neighbors", "source"),
                                                     "value": "source"},
                                                    {"label": pgettext("neighbors", "target"),
                                                     "value": "target"},
                                                ],
                                                value="all",
                                                clearable=False,  # niekada negali būti tuščia reikšmė
                                                placeholder=_("Select..."),
                                            ),
                                        ],
                                        style={"width": "50%"},
                                    ),
                                ]),
                                html.Br(),

                                # Neįtraukti lentelių be įrašų
                                html.Div(
                                    children=dbc.Checkbox(
                                        id="checkbox-tables-no-records",
                                        label=_("Don't include tables with no records"),
                                        value=True
                                    ),
                                    style={"marginBottom": "50px"}
                                ),
                                html.Br(),
                            ],
                        ),
                    ),
                ],
            ),

            # Po grafiku. PDSA duomenis atvaizduojančios lentelės.
            dbc.Row(
                id="graph-tab-pdsa-info",
                style={"position": "relative", "height": "20%"},
                children=[
                    html.Hr(),

                    # Informacija apie pasirinktų lentelių stulpelius
                    dbc.Col(
                        id="graph-tab-pdsa-info-columns",
                        className="resizable",
                        style={"resize": "horizontal"},
                        width=8,  # iš 12 pločio vienetų;
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
                                        width=8,  # iš 12 pločio vienetų;
                                        children=[
                                            # Informacija apie pasirinktų lentelių stulpelius - išskleidžiamasis sąrašas
                                            dcc.Dropdown(
                                                id="filter-tbl-in-df",
                                                options=[],
                                                value=[],
                                                multi=True,
                                                placeholder=_("Select..."),
                                            ),
                                        ],
                                    ),
                                    dbc.Col(
                                        dcc.Clipboard(
                                            id="clipboard-filter-tbl-in-df",
                                            style={"fontSize": 16, "cursor": "pointer"}
                                        ),
                                    ),
                                    html.Br(),
                                ],
                            ),
                            dbc.Row(
                                className="resizable",
                                style={"resize": "vertical"},
                                children=[
                                    # Informacija apie pasirinktų lentelių stulpelius - lentelė
                                    html.Div(id="table-selected-tables", children=gc.table_preview()),
                                ],
                            ),
                            html.Br(),
                        ],
                    ),

                    # Info apie nubraižytas lenteles
                    dbc.Col(
                        id="graph-tab-pdsa-info-tables",
                        width=4,  # iš 12 pločio vienetų;
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
                                className="resizable",
                                id="table-displayed-nodes",
                                children=gc.table_preview()
                            ),
                            html.Br(),
                        ],
                    ),

                ],
            ),
            gi.active_element_info("active-node-info"),
            gi.active_element_info("active-edge-info"),
            dcc.Download(id="download-json"),
        ],
    )
