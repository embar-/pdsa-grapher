"""
Graferio kortelių struktūros kūrimas.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu.
Jei kaip biblioteką naudojate kitoms reikmėms, tuomet reikia įsikelti ir/arba konfigūruoti gettext, pvz.:
from gettext import pgettext, gettext as _
ARBA
from gettext import translation
translation("pdsa-grapher", 'locale', languages=["lt"]).install()
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from . import my_components as mc
from . import utils as gu
from locale_utils.translations import pgettext


def file_uploading_tab_layout():
    return html.Div(
        [
            dbc.Row(
                children=[
                    dbc.Col(
                        width={"size": 6},
                        id="pdsa-panel",
                        children=[
                            html.Div(
                                style={"margin-left": "20px", "margin-right": "20px"},
                                children=[
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
                                                    # 'width': '100%',
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
                                    dcc.Store(id="memory-uploaded-file"),
                                    dcc.Store(id="memory-pdsa-meta-info"),
                                    html.H6(
                                        children=[
                                            _("File name: "),
                                            html.B(
                                                id="pdsa-file-name",
                                                children=[],
                                                style={'font-size': '90%'},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="info-uploaded-pdsa",
                                        children=mc.pdsa_radio_components(
                                            "pdsa-sheets",
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
                                style={"margin-left": "10px", "margin-right": "10px"},
                                children=[
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
                                                style={'font-size': '90%'},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="selection-source",
                                        children=mc.uzklausa_select_source_target(
                                            "id-radio-uzklausa-source",
                                            pgettext("table type for references directions", "source")
                                        ),
                                    ),
                                    html.Div(
                                        id="selection-target",
                                        children=mc.uzklausa_select_source_target(
                                            "id-radio-uzklausa-target",
                                            pgettext("table type for references directions","target")
                                        ),
                                    ),
                                    html.Br(),
                                    html.Div(
                                        id="uzklausa-tbl-preview",
                                        children=mc.table_preview(),
                                    ),
                                    html.Div(
                                        style={"margin-top": "20px"},
                                        children=[
                                            dbc.Button(
                                                id="button-submit",
                                                children=html.B(_("Submit")),
                                                color="secondary",
                                            )
                                        ],
                                        className="d-grid gap-2",
                                    ),
                                    dcc.Store(id="memory-uploaded-file-uzklausa"),
                                ],
                            )
                        ],
                    ),
                ]
            ),
            dcc.Store(id="memory-submitted-data", storage_type="session"),
        ]
    )

def grapher_tab_layout():
    return html.Div(
        style={
            "margin-left": "20px",
            "margin-right": "20px",
            "margin-top": "20px",
            "margin-bottom": "20px",
        },
        children=[
            dbc.Row(
                children=[

                    # Pats grafikas
                    dbc.Col(
                        width=9,  # iš 12 pločio vienetų; t.y. 75%
                        style={"float": "left", "width": "75%"},
                        children=[
                            html.Div(id="my-network", children=gu.get_fig_cytoscape())
                        ],
                    ),

                    dbc.Col(
                        width=3,  # iš 12 pločio vienetų; t.y. 5%
                        style={"float": "left", "width": "25%"},
                        children=html.Div(
                            children=[
                                dbc.Row(
                                    # Paaiškinimų mygtukai
                                    children=[
                                        dbc.Col(
                                            children=[html.Div(mc.filters_usage_info())],
                                            style={"margin-bottom": "20px", "width": "50%"},
                                            width=1.5,
                                        ),
                                        dbc.Col(
                                            children=[html.Div(mc.graphic_usage_info())],
                                            style={"margin-bottom": "20px", "width": "50%"},
                                            width=1.5,
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.Div(
                                    children=[
                                        html.P(_("Select tables to graph")),
                                        dcc.Dropdown(
                                            id="dropdown-tables",
                                            options=[],
                                            value=[],
                                            multi=True,
                                            placeholder=_("Select..."),
                                        ),
                                    ]
                                ),
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
                                    ]
                                ),
                                html.Br(),
                                dbc.Checklist(
                                    id="checkbox-get-neighbours",
                                    options=[{'label': _("Get neighbours"), 'value': True}],
                                    value=False
                                ),
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
                                html.Hr(),
                                html.P(
                                    _("Get info about columns of selected tables")
                                ),
                                dcc.Dropdown(
                                    id="filter-tbl-in-df",
                                    options=[],
                                    value=[],
                                    multi=True,
                                    placeholder=_("Select..."),
                                ),
                                html.Div(id="table-selected-tables", children=[]),
                                html.Hr(),
                                html.P(
                                    _("Get info on displayed tables")
                                ),
                                dbc.Button(
                                    id="button-send-displayed-nodes-to-table",
                                    children=_("Get info on displayed tables"),
                                    color="primary",
                                    className="me-1",
                                ),
                                html.Div(id="table-displayed-nodes", children=[]),
                            ]
                        ),
                    ),
                ]
            ),
        ],
    )
