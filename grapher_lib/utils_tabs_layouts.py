import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback, callback_context

# from . import devs
from . import my_components as mc
from . import utils as gu


class app_layouts:
    file_upload = html.Div([
        dbc.Row(children=[
            dbc.Col(width={"size": 6}, id='pdsa-panel',
                    children=[
                        html.Div(style={"margin-left": "20px", "margin-right": "20px"},
                                 children=[
                                     html.Div(id="pdsa-selections",
                                              children=[
                                                  dcc.Upload(
                                                      id='upload-data',
                                                      children=html.Div([
                                                          'Drag and Drop ',
                                                          html.A('PDSA File')
                                                      ]),
                                                      style={
                                                          # 'width': '100%',
                                                          'height': '60px',
                                                          'lineHeight': '60px',
                                                          'borderWidth': '1px',
                                                          'borderStyle': 'dashed',
                                                          'borderRadius': '5px',
                                                          'textAlign': 'center',
                                                          'margin': '10px'
                                                      },
                                                      # Allow multiple files to be uploaded
                                                      multiple=True
                                                  )
                                              ]),
                                     dcc.Store(id='memory-uploaded-file'),
                                     dcc.Store(id="memory-pdsa-meta-info"),
                                     html.H6(children=["File name: ",
                                                       html.B(id="pdsa-file-name", children=[])]
                                             ),
                                     html.Div(id='info-uploaded-pdsa',
                                              children=mc.pdsa_radio_components("pdsa-sheets", "radio-sheet-tbl",
                                                                                "radio-sheet-col")),

                                     html.Div(id='column-selection-sheet-tbl',
                                              children=mc.pdsa_dropdown_columns_componenets("id-sheet-tbl",
                                                                                            "dropdown-sheet-tbl")),
                                     html.Div(id='sheet-tbl-preview', children=mc.table_preview()),

                                     html.Div(id='column-selection-sheet-col',
                                              children=mc.pdsa_dropdown_columns_componenets("id-sheet-col",
                                                                                            "dropdown-sheet-col")),
                                     html.Div(id='sheet-col-preview', children=mc.table_preview())
                                 ])
                    ]),
            dbc.Col(width={"size": 6}, id="uzklausa-panel",
                    children=[
                        html.Div(style={"margin-left": "10px", "margin-right": "10px"},
                                 children=[
                                     html.Div(id="uzklausa-selections",
                                              children=[
                                                  dcc.Upload(
                                                      id='upload-data-uzklausa',
                                                      children=html.Div([
                                                          'Drag and Drop ',
                                                          html.A('Užklausa File')
                                                      ]),
                                                      style={
                                                          # 'width': '100%',
                                                          'height': '60px',
                                                          'lineHeight': '60px',
                                                          'borderWidth': '1px',
                                                          'borderStyle': 'dashed',
                                                          'borderRadius': '5px',
                                                          'textAlign': 'center',
                                                          'margin': '10px'
                                                      },
                                                      # Allow multiple files to be uploaded
                                                      multiple=True
                                                  ),
                                              ]),
                                     html.H6(children=["File name: ",
                                                       html.B(id="uzklausa-file-name", children=[])]),
                                     html.Div(id='selection-source',
                                              children=mc.uzklausa_select_source_target("id-radio-uzklausa-source",
                                                                                        "source")),
                                     html.Div(id='selection-target',
                                              children=mc.uzklausa_select_source_target("id-radio-uzklausa-target",
                                                                                        "target")),
                                     html.Br(),
                                     html.Div(id='uzklausa-tbl-preview', children=mc.table_preview()),
                                     html.Div(style={"margin-top": "20px"},
                                              children=[dbc.Button(id="button-submit",
                                                                   children=html.B("Submit"), color="secondary")],
                                              className="d-grid gap-2"),
                                     dcc.Store(id='memory-uploaded-file-uzklausa'),
                                 ])
                    ])
        ]),
        # dbc.Row(children=[
        #     dbc.Col(width={"size": 6, "offset": 3}, id='submit-panel',
        #             children=[
        #                 html.Div(style={"margin-top": "20px"},
        #                          children=[dbc.Button(id="button-submit",
        #                                               children=html.B("Submit"), color="secondary")],
        #                          className="d-grid gap-2")
        #             ])
        # ]),
        dcc.Store(id="memory-submitted-data", storage_type="session")
    ])

    grapher = html.Div(
        style={"margin-left": "20px", "margin-right": "20px", "margin-top": "20px", "margin-bottom": "20px"},
        children=[
            dbc.Row(children=
                    [dbc.Col(children=[html.Div(mc.Tutorials.grafikas), html.Hr()], style={"margin-bottom": "20px"},
                             width=6),
                     dbc.Col(children=[html.Div(mc.Tutorials.filtrai), html.Hr()], style={"margin-bottom": "20px"},
                             width=6)]
                    ),
            dbc.Row(
                children=[
                    dbc.Col(
                        style={"float": "left", "width": "50%"},
                        children=[
                            html.Div(id="my-network",
                                     children=gu.get_fig_cytoscape()
                                     )],
                        width=6
                    ),
                    dbc.Col(
                        style={"float": "left", "width": "50%"},
                        children=
                        html.Div(
                            children=[
                                html.Div(children=[
                                    html.P("Select your layout"),
                                    dcc.Dropdown(id="dropdown-layouts",
                                                 options=["random", "preset", "circle",
                                                          "concentric", "grid",
                                                          "breadthfirst", "cose",
                                                          "close-bilkent",
                                                          "cola", "euler", "spread", "dagre",
                                                          "klay"],
                                                 value='cola',
                                                 style={"width": "50%"})],
                                ),
                                html.Br(),
                                html.Hr(),
                                html.Div(children=[
                                    html.P("Select tables to graph"),
                                    dcc.Dropdown(
                                        id="dropdown-tables",
                                        options=[],
                                        value=[],
                                        multi=True)]
                                ),
                                html.Div(children=[
                                    html.Br(),
                                    html.P("Add list of tables to graph (comma separated)"),
                                    dcc.Input(
                                        id="input-list-tables",
                                        style={"width": "100%"},
                                        placeholder="lentele1,letele2,lentele3..."
                                    )
                                ]
                                ),
                                html.Br(),
                                dbc.Button(id="button-get-neighbours",
                                           children="Get neighbours",
                                           color="primary", className="me-1"),
                                html.Br(),
                                html.Hr(),
                                html.P(
                                    "Get info about columns of selected tables (PDSA sheet 'columns')"),
                                dcc.Dropdown(id="filter-tbl-in-df",
                                             options=[],
                                             value=[],
                                             multi=True),
                                html.Div(id="table-selected-tables", children=[]),
                                html.Br(),
                                html.Hr(),
                                html.P(
                                    "Info on tables displayed in network (PDSA sheet 'tables')"),
                                dbc.Button(id="button-send-displayed-nodes-to-table",
                                           children="Get info on displayed tables (tables in network)",
                                           color="primary", className="me-1"),
                                html.Div(id="table-displayed-nodes", children=[]),

                            ]
                        ),
                        width=6
                    )
                ])

        ])
