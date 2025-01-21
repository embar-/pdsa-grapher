"""
Dash komponentai, kurie naudojami utils_tabs_layouts.py funkcijose.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu;
Jei kaip biblioteką naudojate kitoms reikmėms, tuomet reikia įsikelti ir/arba konfigūruoti gettext, pvz.:
from gettext import pgettext, gettext as _
ARBA
from gettext import translation
translation("pdsa-grapher", 'locale', languages=["lt"]).install()
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from locale_utils.translations import pgettext


def pdsa_radio_components(id_radio_sheet_tbl, id_radio_sheet_col):
    output_elements = [
        html.H6([_("Sheets:")]),
        html.Div(
            children=[
                dbc.Label(
                    [
                        _("PDSA sheet describing"), " ",
                        html.B(pgettext("PDSA sheet describing... (galininkas)", "tables")), ": "
                    ]
                ),
                dcc.RadioItems(id=id_radio_sheet_tbl, options=[]),
            ]
        ),
        html.Div(
            children=[
                dbc.Label(
                    [
                        _("PDSA sheet describing"), " ",
                        html.B(pgettext("PDSA sheet describing... (galininkas)", "columns")), ": "
                    ]
                ),
                dcc.RadioItems(id=id_radio_sheet_col, options=[]),
            ]
        ),
    ]
    return output_elements


def pdsa_dropdown_columns_componenets(id_sheet_type, id_dropdown_sheet_type):
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


def uzklausa_select_source_target(id_radio_uzklausa_col, tbl_type):
    output_element = html.Div(
        children=[
            dbc.Label(
                [_("Select column that represents tables of"), " ", html.B(tbl_type)]
            ),
            dcc.Dropdown(id=id_radio_uzklausa_col, options=[], placeholder=_("Select...")),
        ]
    )
    return output_element


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
                style={"float": "right", 'font-size': '100%'},
            ),
            dbc.Popover(
                grafikas_content,
                target="tutorial-grafikas-legacy-target",
                body=True,
                trigger="legacy",
                style={'font-size': '80%'},
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
                html.P(
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
                style={'font-size': '100%'},
            ),
            dbc.Popover(
                filtrai_content,
                target="tutorial-filtrai-legacy-target",
                body=True,
                trigger="legacy",
                style={'font-size': '85%'},
            ),
        ]
    )
    return filtrai


def active_node_info():
    """
    Informacinis debesėlis
    """
    return dcc.Tooltip(
        id="active-node-info",
        direction="left",
        zindex=200,
        style={
            "position": "absolute",
            "background": "#cff4fc",
            "font-size": "85%",
        },
        children=[
            html.Div([
                html.Div(
                    id="active-node-info-header",
                    children=[]
                ),
                html.Div(
                    id="active-node-info-content",
                    children=[],
                    style={
                        "minWidth": "50px",  # riboti aukštį
                        "minHeight": "10px",  # riboti plotį
                        "maxHeight": "300px",  # riboti plotį
                        "overflowY": "auto",  # pridėti slinkties juostas, jei netelpa
                        "resize": "both",       # leisti keisti tiek plotį, tiek aukštį
                        "pointer-events": "auto",  # reaguoti į pelę
                    },
                ),
            ])
        ]
    )
