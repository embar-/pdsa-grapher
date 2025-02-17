"""
PDSA grapher Dash app allows you to display and filter relationships between
tables in your database, as well as display the metadata of those tables.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import os
import pandas as pd
from flask import Flask
import dash
from dash import dcc, html, Output, Input, callback
import dash_bootstrap_components as dbc
import logging
from locale_utils.translations import refresh_gettext_locale
from grapher_lib.gui_layout_file_upload import file_uploading_tab_layout  # GUI elementų kūrimas rinkmenų įkėlimo kortelėje
from grapher_lib.gui_layout_graph import graph_tab_layout  # GUI elementų kūrimas grafiko kortelėje
from grapher_lib.gui_callbacks_file_upload import (   # noqa. Rinkmenų įkėlimo kortelei
    set_pdsa_memory, set_pdsa_sheet_radios,  # PDSA lakštų pasirinkimas
    set_pdsa_tables_sheet_names, set_pdsa_columns_sheet_names,  # pasirinktų PDSA lakštų užrašai
    create_pdsa_tables_sheet_column_dropdowns_for_graph, create_pdsa_columns_sheet_column_dropdowns_for_graph,  # PDSA stulpeliai grafikams
    create_pdsa_tables_sheet_column_dropdowns_for_info, create_pdsa_columns_sheet_column_dropdowns_for_info,  # PDSA stulpeliai informacijoje po grafiku
    create_preview_of_pdsa_tbl_sheet, create_preview_of_pdsa_col_sheet,  # PDSA peržiūra
    set_refs_memory, set_refs_sheet_radios, create_refs_dropdowns_and_preview,  # Ryšiai
    summarize_submission  # Tikrinimas ir pateikimas į Grafiko kortelę
)
from grapher_lib.gui_callbacks_graph import (  # noqa
    set_dropdown_tables_for_graph, get_filtered_data_for_network,  # Duomenys braižymui
    create_dash_table_about_displayed_tables,  # Info apie nubraižytas lenteles
    set_dropdown_tables_for_selected_table_cols_info, create_dash_table_about_selected_table_cols,  # Info apie stulpelius
    copy_selected_tables_to_clipboard,  # Galimybė kopijuoti rodomus mazgus
    change_engine,  # Perjungimas tarp Cytoscape ir Viz grafikos išdėstymo variklio
    change_pdsa_tables_info_visibility, change_pdsa_columns_info_visibility  # info po grafiku matomumas
)
from grapher_lib.gui_callbacks_graph_cyto import (  # noqa
    update_cytoscape_layout, get_network_cytoscape_chart,  # Braižymui naudojant Cytoscape variklį
    get_selected_node_data, display_tap_node_tooltip, display_tap_edge_tooltip,  # Info apie spragtelėtą objektą
    copy_cyto_displayed_nodes_to_clipboard  # Galimybė kopijuoti rodomus mazgus
)
from grapher_lib.gui_callbacks_graph_viz import (  # noqa
    change_dot_editor_visibility, get_network_viz_chart,  # Braižymui naudojant Viz variklį
    copy_viz_displayed_nodes_to_clipboard  # Galimybė kopijuoti rodomus mazgus
)


# ========================================
# Pradinė konfigūracija
# ========================================

# Rodyti tik svarbius pranešimus. Neteršti komandų lango gausiais užrašais kaip "GET /_reload-hash HTTP/1.1" 200
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Pandas parinktys
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


# ========================================
# Kalbos
# ========================================

# Kalbas reikia nustatyti prieš pradedant kurti dash programą tam, kad programos užrašus iš karto būtų galima būtų
# iš karto sudėlioti numatytąja norima kalba. Keičiant kalbą visa programos struktūra būtų perkuriama iš naujo.
LANGUAGES = {  # globalus kintamasis, jį naudos update_language()
    "en": "English",
    "lt": "Lietuvių"
}
refresh_gettext_locale()


# ========================================
# Išdėstymas
# ========================================

# Kortelės
def tab_layout():
    """Kortelės: 1) rinkmenų įkėlimui; 2) grafikams"""
    return [
        dbc.Tab(file_uploading_tab_layout(), tab_id="file_upload", label=_("File upload")),
        dbc.Tab(graph_tab_layout(), tab_id="graph", label=_("Graphic")),
    ]


# Visuma
def app_layout():
    """Visuminis programos išdėstymas, apimantis korteles iš tab_layout() ir kalbos pasirinkimą"""
    return html.Div(
        style={"marginTop": "20px", "marginLeft": "20px", "marginRight": "20px"},
        children=[
            html.Div(id="blank-output", title="Dash"),  # Laikina reikšmė, vėliau keičiama pagal kalbą
            dbc.DropdownMenu(
                label="🌐",
                children=[
                    dbc.DropdownMenuItem(LANGUAGES[lang], id=lang, n_clicks=0)
                    for lang in LANGUAGES
                ],
                id="language-dropdown",
                style={"float": "right"},
                color="secondary"
            ),
            dbc.Tabs(
                children=tab_layout(),  # bus vėl keičiamas per update_language()
                id="tabs-container"
            ),

            # dcc.Store() gali turėti tokias "storage_type" reikšmes:
            # - "memory": dingsta atnaujinus puslapį arba uždarius naršyklę
            # - "session": dingsta uždarius naršyklės kortelę
            # - "local":  išsilaiko iš naujo atidarius puslapį ir net uždarius ir iš naujo atidarius naršyklę
            # Deja, pastarosios dvi ne visada veikia, tad reikia nepersistengti, pvz:
            #   Failed to execute 'setItem' on 'Storage': Setting the value of 'memory-uploaded-pdsa' exceeded the quota.
            #   QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the value of 'memory-submitted-data' exceeded the quota.
            dcc.Store(id="memory-uploaded-pdsa", storage_type="session"),  # žodynas su PDSA duomenimis
            dcc.Store(id="memory-uploaded-refs", storage_type="session"),  # žodynas su ryšių tarp lentelių duomenimis
            dcc.Store(id="memory-submitted-data", storage_type="memory"),  # Rinkmenų kortelėje patvirtinti duomenys
            dcc.Store(id="memory-filtered-data", storage_type="memory"),   # Grafiko piešimui atrinkti duomenys
        ],
    )


# ========================================
# Interaktyvumai bendrieji, t.y. nepriklausomai nuo kortelės
# ========================================

# Kalba
@callback(
    Output("language-dropdown", "label"),  # užrašas ties kalbos pasirinkimu
    Output("tabs-container", "children"),  # perkurta kortelių struktūra naująja kalba
    Output("blank-output", "title"),  # nematoma, bet jį panaudos dash.clientside_callback() antraštei keisti
    # Reikalingi funkcijos paleidikliai, pati jų reikšmė nenaudojama
    Input("en", "n_clicks"),
    Input("lt", "n_clicks")
)
def update_language(en_clicks, lt_clicks):  # noqa
    """
    Kalbos perjungimas. Perjungiant kalbą programa tarsi paleidžiama iš naujo.
    Ateityje paieškoti būdų pakeisti kalbą neprarandant naudotojo darbo.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        language = "lt"  # numatytoji lietuvių kalba; arba galite naudoti locale.getlocale()[0]
    else:
        language = ctx.triggered[0]["prop_id"].split(".")[0]

    with app.server.test_request_context():
        refresh_gettext_locale(language)
        print(_("Language set to:"), LANGUAGES[language], language)
        return (
            "🌐 " + language.upper(),
            tab_layout(),
            _("PDSA grapher")
        )


# Naršyklės antraštės pakeitimas pasikeitus kalbai
dash.clientside_callback(
    """
    function(title) {
            document.title = title;
    }
    """,
    Output("blank-output", "children"),
    Input("blank-output", "title"),
)


# ========================================
# Savarankiška Dash programa
# ========================================

# Viz atvaizdavimo varikliui reikalingi papildomi JavaScript
js_dependencies = {
    "d3.v7.min.js": "https://d3js.org/d3.v7.min.js",
    "viz-standalone.v3.11.0.js": "https://unpkg.com/@viz-js/viz@3.11.0/lib/viz-standalone.js"
}
# Patikrinti vietinių JavaScript buvimą
external_scripts = []
for filename, url in js_dependencies.items():
    if not os.path.exists(os.path.join("assets", filename)):
        external_scripts.append(url)

# Programos paleidimas
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    external_scripts=external_scripts if external_scripts else None,
    routes_pathname_prefix='/pdsa_grapher/',
    requests_pathname_prefix='/pdsa_grapher/',
    update_title=None  # noqa
)
app.layout = app_layout

# Viz atvaizdavimo varikliui: perpiešti sugeneravus naują Graphviz DOT sintaksę
app.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='runRenderFunction'),
    Input("graphviz-dot", "value"),  # Graphviz DOT sintaksė kaip tekstas
)
# Viz atvaizdavimo varikliui: SVG paveikslo parsiuntimas į diską
app.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='saveSVG'),
    Input("save-svg", "n_clicks"),  # išsaugoti grafiką kaip SVG
)


if __name__ == "__main__":
    """
    Paleisti Docker programą tarsi vietiniame kompiuteryje arba tarsi serveryje automatiškai
    """

    # Aptikti, ar esame Docker konteineryje
    cgroup_path = "/proc/self/cgroup"
    is_docker = (
        os.path.exists("/.dockerenv") or
        (os.path.isfile(cgroup_path) and any("docker" in line for line in open(cgroup_path)))
    )

    if is_docker:
        # Esame Docker konteineryje
        print("Executing App from Docker image")
        app.run_server(port=8080, debug=False)
    else:
        # Paprastas kompiuteris
        app.run(debug=False)
