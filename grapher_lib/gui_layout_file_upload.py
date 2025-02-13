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
from grapher_lib import gui_components as gc
from locale_utils.translations import pgettext


def file_uploading_tab_layout():

    # PDSA lakšte, aprašančiame duombazės lenteles, galimybė pasirinkti lakšto stulpelius
    pdsa_panel_tables = html.Div(
        id="pdsa-panel-tables",
        children=[
            gc.pdsa_columns_selection_header(
                "pdsa-tables-header-for-cols-selection",
                pgettext("PDSA sheet describing...", "tables")
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-tables-table",
                            pgettext("pdsa column for", "tables")
                        ),
                    ),
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-tables-comment",
                            pgettext("pdsa column for", "comments")
                        ),
                    ),
                ],
            ),
            html.Div(
                id="pdsa-panel-tables-info",
                children=[
                    html.Div(
                        id="column-selection-sheet-tbl",
                        children=gc.pdsa_dropdown_columns_components("dropdown-sheet-tbl"),
                    ),
                    html.Div(
                        id="sheet-tbl-preview",
                        children=gc.table_preview(),
                    ),
                ],
            ),
            html.Br(),
            html.Hr(),
        ],
        style={"display": "none"},  # iš pradžių nematomas, bet pasirinkus lakštą bus matomas
    )

    # PDSA lakšte, aprašančiame duombazės lentelių stulpelius, galimybė pasirinkti lakšto stulpelius
    pdsa_panel_columns = html.Div(
        id="pdsa-panel-columns",
        children=[
            gc.pdsa_columns_selection_header(
                "pdsa-columns-header-for-cols-selection",
                pgettext("PDSA sheet describing...", "columns")
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-columns-table",
                            pgettext("pdsa column for", "tables")
                        ),
                    ),
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-columns-column",
                            pgettext("pdsa column for", "columns")
                        ),
                    ),
                ],
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-columns-primary",
                            pgettext("pdsa column for", "primary")
                        ),
                    ),
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "pdsa-columns-comment",
                            pgettext("pdsa column for", "comments")
                        ),
                    ),
                ],
            ),
            html.Div(
                id="pdsa-panel-columns-info",
                children=[
                    html.Div(
                        id="column-selection-sheet-col",
                        children=gc.pdsa_dropdown_columns_components("dropdown-sheet-col"),
                    ),
                    html.Div(
                        id="sheet-col-preview",
                        children=gc.table_preview(),
                    ),
                ],
            ),
        ],
        style={"display": "none"},  # iš pradžių nematomas, bet pasirinkus lakštą bus matomas
    )

    # Pirminių duomenų struktūros aprašo (PDSA) skydelis
    pdsa_panel = html.Div(
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
                        children=html.Div([
                            _("Drag and Drop") + " ",
                            html.A(pgettext("Drag and Drop", "PDSA File")),
                        ]),
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
                        id="pdsa-file-name",
                        children=[],
                        style={"fontSize": "90%"},
                    ),
                ],
            ),

            # PDSA lakštų pasirinkimas
            html.Div(
                id="pdsa-sheets-selection",
                children=gc.pdsa_radio_sheet_components("radio-sheet-tbl", "radio-sheet-col"),
            ),
            html.Hr(),

            # Galimybė pasirinkti PDSA lakštų stulpelius
            pdsa_panel_tables,
            pdsa_panel_columns,
            html.Br(),
        ],
    )

    # Ryšių skydelis
    refs_panel = html.Div(
        style={"marginLeft": "10px", "marginRight": "20px"},
        children=[
            html.H5(
                _("References"),
                style={"textAlign": "center"},
            ),
            html.Div(
                id="refs-selections",
                children=[
                    dcc.Upload(
                        id="upload-data-refs",
                        children=html.Div([
                            _("Drag and Drop"), " ",
                            html.A(pgettext("Drag and Drop", "References File")),
                        ]),
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
                        id="refs-file-name",
                        children=[],
                        style={"fontSize": "90%"},
                    ),
                ],
            ),
            html.Hr(),
            html.H6(_("Select columns that contain:")),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "ref-source-tables",
                            pgettext("references", "source tables")
                        ),
                    ),
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "ref-source-columns",
                            pgettext("references", "source columns")
                        ),
                    ),
                ],
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "ref-target-tables",
                            pgettext("references", "target tables")
                        ),
                    ),
                    dbc.Col(
                        children=gc.dropdown_with_label(
                            "ref-target-columns",
                            pgettext("references", "target columns")
                        ),
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                id="refs-tbl-preview",
                children=gc.table_preview(),
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

    return html.Div([
        dbc.Row(
            style={"marginTop": "20px"},
            children=[
                dbc.Col(
                    width={"size": 6},
                    id="pdsa-panel",
                    children=pdsa_panel
                ),
                dbc.Col(
                    width={"size": 6},
                    id="refs-panel",
                    children=refs_panel,
                ),
            ],
        ),
    ])
