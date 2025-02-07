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
from . import gui_components as mc
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
                                                    {"label": pgettext("neighbors", "all"), "value": "all"},
                                                    {"label": pgettext("neighbors", "source"), "value": "source"},
                                                    {"label": pgettext("neighbors", "target"), "value": "target"},
                                                ],
                                                value="all",
                                                clearable=False,  # niekada negali būti tuščia reikšmė
                                                placeholder=_("Select..."),
                                            ),
                                        ],
                                        style={"width": "50%"},
                                    ),
                                ]),

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
                        className="resizable",
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
                                className="resizable",
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
                                className="resizable",
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
