import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback


def pdsa_radio_components(id_pdsa_sheet, id_radio_sheet_tbl, id_radio_sheet_col):
    output_elements = [
        html.H6(["Aptikti sheet'ai: ", html.B(id=id_pdsa_sheet, children=[])]),
        html.Div(
            children=[
                dbc.Label(
                    ["Nurodykite, kuris PDSA sheet'as aprašo ", html.B("lenteles: ")]
                ),
                dcc.RadioItems(id=id_radio_sheet_tbl, options=[]),
            ]
        ),
        html.Div(
            children=[
                dbc.Label(
                    ["Nurodykite, kuris PDSA sheet'as aprašo ", html.B("stulpelius: ")]
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
                f"Pasirinkite, kuriuos PDSA sheet'o '",
                html.B(id=id_sheet_type, children=["___________"]),
                "' stulpelius norite pasilikti švieslentėje",
            ]
        ),
        dcc.Dropdown(id=id_dropdown_sheet_type, options=[], value=[], multi=True),
    ]

    return dropdown_sheet_type


def table_preview():
    return dash_table.DataTable()


def uzklausa_select_source_target(id_radio_uzklausa_col, tbl_type):
    output_element = html.Div(
        children=[
            dbc.Label(
                ["Pasirinkite stulpelį, kuris reprecentuoja lentelę ", html.B(tbl_type)]
            ),
            dcc.Dropdown(id=id_radio_uzklausa_col, options=[]),
        ]
    )
    return output_element


def uzklausa_select_sheet(id_radio_uzklausa_sheet, tbl_type):
    output_element = html.Div(
        children=[
            dbc.Label(["Pasirinkite sheet'ą, kuris aprašo ", html.B(tbl_type)]),
            dcc.Dropdown(id=id_radio_uzklausa_sheet, options=[]),
        ]
    )
    return output_element


class Tutorials:
    grafikas_content = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Naudojimo Instrukcija", className="card-title"),
                # html.H6("Grafiko skiltis", className="card-subtitle"),
                html.Div(
                    children=[
                        html.P(
                            "Grafike atvaizduojami pasirinktų lentelių ryšiai, kurie yra aprašomi užklausos faile."
                        ),
                        html.P("Grafikas yra interaktyvus: "),
                        html.P("Grafiko vaizdą galima pritraukti/atitraukti"),
                        html.P(
                            "Taškus galima tampyti pavieniui arba kelis (reikia nuspausti CTRL)"
                        ),
                        html.P(
                            "Tiesa, pažymėjus tašką, jo išvaizda nepasikeičiai, tad gali atrodyti, kad niekas nepasižymėjo."
                            "Tai bus pataisyta artimiausiuose atnaujinimuose"
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
                "Grafiko instrukcija",
                id="tutorial-grafikas-legacy-target",
                color="success",
                n_clicks=0,
            ),
            dbc.Popover(
                grafikas_content,
                target="tutorial-grafikas-legacy-target",
                body=True,
                trigger="legacy",
            ),
        ]
    )
    filtrai_content = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Naudojimo Instrukcija", className="card-title"),
                html.H6("Filtrų aprašymai", className="card-subtitle"),
                html.Br(),
                html.P(
                    children=[
                        html.P(
                            "Grafike galima atvaizduoti pasirenkant pavienes lenteles arba įvedant jų sąrašą.Čia taip pat galima rasti informaciją apie lenteles"
                        ),
                        html.P(
                            children=[
                                html.B("Layout - "),
                                html.Label("Grafiko taškų išdėstymo schemos."),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B("Select tables to graph - "),
                                html.Label(
                                    "pasirinkite kurių PDSA lentelių ryšius norite atvaizduoti"
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B("Add list of tables - "),
                                html.Label(
                                    "galima nurodyti atvaizduoti sąrašą lentelių. Sąraše lentelių pavadinimai turi būt atskirti kableliais"
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B("Get neighbours - "),
                                html.P(
                                    "Grafiką papildo lentelėmis, kurios tiesiogiai siejasi su pasirinktomis lentelėmis"
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B("Get info about columns of selected tables - "),
                                html.Label(
                                    "Parodo informaciją apie pasirinktos lentelės(-ių) stulpelius"
                                ),
                            ]
                        ),
                        html.P(
                            children=[
                                html.B("Get info on displayed tables - "),
                                html.Label(
                                    "parodo grafike atvaizduotų lentelių informaciją"
                                ),
                            ]
                        ),
                    ],
                    className="card-text",
                ),
            ]
        ),
        # style={"width": "50%"}
    )
    filtrai = html.Div(
        [
            dbc.Button(
                "Filtrų instrukcija",
                id="tutorial-filtrai-legacy-target",
                color="success",
                n_clicks=0,
            ),
            dbc.Popover(
                filtrai_content,
                target="tutorial-filtrai-legacy-target",
                body=True,
                trigger="legacy",
            ),
        ]
    )
