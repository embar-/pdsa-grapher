"""
Graferio rinkmenų įkėlimo kortelės struktūros kūrimas.

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
                                                style={"fontSize": "90%"},
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
                                                style={"fontSize": "90%"},
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
