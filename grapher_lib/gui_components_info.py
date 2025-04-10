"""
Dash iškylančiuose languose rodomi komponentai, kurie naudojami utils_tabs_layouts.py funkcijose.

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

from dash import dcc, html
import dash_bootstrap_components as dbc


def graph_usage_info():
    grafikas_content = dbc.Card(
        dbc.CardBody(
            [
                html.H6(_("Graph usage instructions"), className="card-title"),
                html.Div(
                    children=[
                        html.P(
                            _("The graph shows the relationships between the selected tables, "
                              "which are described in the references file.")
                        ),
                        html.P(_("The graph is interactive:")),
                        html.Ul(
                            children=[
                                html.Li(_("You can drag points.")),
                                html.Li(_("View can be zoomed in/out and panned.")),
                            ],
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
                _("Graph instructions"),
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
                style={"fontSize": "90%"},
                placement="left-start",
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
                                html.B(_("Graph engine")), ", ", html.B(_("Layout")), " - ",
                                html.Label(_("Style of the point placement in the graph.")),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Select tables to graph")), " - ",
                                html.Label(
                                    _("Select PDSA tables which relationships you want to display")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Add list of tables")), " - ",
                                html.Label(
                                    _("You can also specify the tables to be displayed in the list; "
                                      "the names of the tables must be separated by commas")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get neighbours")), " - ",
                                html.Label(
                                    _("Supplement the graph with tables that relate directly to the selected tables")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get info about columns of selected tables")), " - ",
                                html.Label(
                                    _("Displays information about the columns of the selected table(s)")
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B(_("Get info on displayed tables")), " - ",
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
                style={"fontSize": "90%"},
                placement="left-start",
            ),
        ]
    )
    return filtrai


def active_element_info(tooltip_id="active-node-info"):
    """
    Informacinis debesėlis apie grafiko objektą
    """
    return dcc.Tooltip(
        id=tooltip_id,
        direction="right",
        zindex=200,
        style={
            "minWidth": "200px",  # riboti plotį
            "position": "absolute",
            "background": "#cff4fc",
            "fontSize": "85%",
            "textWrap": "wrap",
            "pointerEvents": "auto",  # reaguoti į pelę
        },
        loading_text="...",
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
                        "maxHeight": "300px", # riboti aukštį
                        "overflowY": "auto",  # pridėti slinkties juostas, jei netelpa
                        "resize": "both",     # leisti keisti tiek plotį, tiek aukštį
                    },
                ),
            ])
        ]
    )


def graph_info():
    """
    Informacinis debesėlis bendrai apie atranką grafikui
    """
    return html.Div(
        dcc.Tooltip(
            id="graph-info",
            children=[],
            show=False,
            bbox={},  # kad vėliau rodytų, būtina nurodyti bent tuščią, None netinka
            direction="left",
            zindex=200,
            loading_text="...",
            style={
                "minWidth": "200px",
                "maxWidth": "600px",
                "minHeight": "10px",
                "maxHeight": "300px", # riboti aukštį
                "background": "#cff4fc",
                "fontSize": "85%",
                "textWrap": "wrap",
                "overflowY": "auto",  # pridėti slinkties juostas, jei netelpa
                "resize": "both",     # leisti keisti tiek plotį, tiek aukštį
                "pointerEvents": "auto",  # reaguoti į pelę
            }
        ),
        style={"position": "absolute", "top": "50%", "left": "100%"}  # grafiko dešinėje šalia atrankos skydelio
    )
