from grapher_lib import utils as gu
import pandas as pd
import os
from dash import Dash, dcc, html, Output, Input, callback, dash_table,  callback_context
import dash_bootstrap_components as dbc

pd.set_option('display.max_columns', None)  # or 1000
pd.set_option('display.max_rows', None)  # or 1000
pd.set_option('display.max_colwidth', None)  # or 199
pd.set_option("expand_frame_repr", False)

# cols_edge_atts = ['is_primary', 'is_unique',
#                   'type', 'n_records', 'n_nulls', 'rules', 'prasme']

pdsa = gu.pdsa(file_path="inputs",
               file_name=
               # "dbis_manifestas_JIVEX.xlsx"
               "Druskininku ligonine OpenLims_manifestas.xlsx"
               ,
               tbl_sheet="lentelės",
               col_sheet="stulpeliai")

data_for_graph = gu.get_data_for_network(pdsa)
df = data_for_graph["df_col"]

dict_rename_file_columns = {"col_table": 'field',
                            "col_column": "column"}

df = df.rename(columns=
               {dict_rename_file_columns["col_table"]: 'table',
                dict_rename_file_columns["col_column"]: 'column'})

df = gu.create_edge_df_tbl_tbl(df)

print(f"Shape of dataframe {df.shape}")

list_all_tables = df['table_x'].dropna().unique().tolist() + df['table_y'].dropna().unique().tolist()





app = Dash(__name__)

app.layout = html.Div(
    children=[
        dbc.Row(dbc.Col(html.P("Dash Cytoscape:"), width=12)),
        dbc.Row(
            children=[
                dbc.Col(
                    style={"float": "left", "width": "50%"},
                    children=
                    html.Div(id="my-network",
                             children=gu.get_fig_cytoscape(df.head(200), layout="cola")
                             ),
                    width=6
                ),
                dbc.Col(
                    style={"float": "left", "width": "50%"},
                    children=
                    html.Div(
                        children=[
                            dcc.Dropdown(
                                id="dropdown-tables",
                                options=list_all_tables,
                                value=[],
                                multi=True),
                            dcc.Dropdown(
                                id="dropdown-layouts",
                                options=["random", "preset", "circle", "concentric", "grid", "breadthfirst", "cose",
                                         "close-bilkent", "cola", "euler", "spread", "dagre", "klay"],
                                value='cola',
                            ),
                            dbc.Button(id="button-get-neighbours",
                                       children="Get neighbours",
                                       color="primary", className="me-1"),

                            html.Br(),
                            html.Hr(),
                            html.P("Select table for info (PDSA::table"),
                            dcc.Dropdown(id="filter-tbl-in-df",
                                         options=list_all_tables,
                                         value=[],
                                         multi=True),
                            html.Div(id="table-selected-tables", children=[]),
                            html.Br(),
                            html.Hr(),
                            html.P("Info on tables displayed in network"),
                            dbc.Button(id="button-send-displayed-nodes-to-table",
                                       children="Get info on displayed nodes (tables in network)",
                                       color="primary", className="me-1"),
                            html.Div(id="table-displayed-nodes", children=[]),

                        ]
                    ),
                    width=6
                )
            ]
        )

    ])


@callback(
    Output('my-network', 'children'),
    Input("dropdown-tables", 'value'),
    Input("dropdown-layouts", 'value'),
    Input("button-get-neighbours", 'n_clicks')

)
def get_network(selected_dropdown_tables, layout, n_clicks):

    """
    Tikslas yra atvaizduoti visus nodes, kurie yra pasirinkti iš dropdown menu
    Mygtukas "get neighbours" į grafą prideda visu pasirinktų lentelių kaimynus

    :param selected_dropdown_tables:
    :param layout:
    :param n_clicks:
    :return:
    """
    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    print(f"callback_context.triggered] {callback_context.triggered}")

    # Jei mygtukas "Get neighbours" nenuspaustas:
    if 'button-get-neighbours' not in changed_id:

        # Atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
        df_filtered = df.loc[
                      df['table_x'].isin(selected_dropdown_tables) | df['table_y'].isin(selected_dropdown_tables), :]

        dict_filtered = df_filtered.to_dict("records")

        # Išskaidau table_x ir table_y į listus ir juos visas lenteles kurios nebuvo pasirinktos yra pakeičiamos į None
        dict_filtered_x = [i["table_x"] if i["table_x"] in selected_dropdown_tables else None for i in dict_filtered]
        dict_filtered_y = [i["table_y"] if i["table_y"] in selected_dropdown_tables else None for i in dict_filtered]

        # Sutraukiu atgal į poras (table_x val, table_y val)
        dict_filtered = list(zip(dict_filtered_x, dict_filtered_y))
        # Pašalinu duplikatines poras
        dict_filtered = set(dict_filtered)
        # Gražinu į dict """"

        dict_filtered = [{"table_x": i[0], "table_y": i[1]} for i in dict_filtered]

        df_filtered=pd.DataFrame.from_records(dict_filtered)

        G = gu.get_fig_cytoscape(df_filtered, layout)

    else:

        neighbours = [x for x in list_all_tables if x in selected_dropdown_tables]

        new_selected_dropdown_tables = neighbours + selected_dropdown_tables
        df_filtered = df.loc[
                      df['table_x'].isin(new_selected_dropdown_tables) | df['table_y'].isin(
                          new_selected_dropdown_tables),
                      :]
        G = gu.get_fig_cytoscape(df_filtered, layout)
    return G

# Select common neighbours if >=2 tables are selected in dropdown
# @callback(
#     Output("update-network", 'children'),
#     Input("dropdown", 'value'), prevent_initial_call=True
# )
# def create_graph_from_selected_tbl(selected_dropdown_tables):

@callback(
    Output("table-selected-tables", 'children'),
    Input("filter-tbl-in-df", 'value'), prevent_initial_call=True
)
# Opens dash table based on tables selected in a dropdown
def create_dash_table_from_selected_tbl(selected_dropdown_tables):
    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    df_tbl = data_for_graph["df_col"]
    df_tbl = df_tbl.loc[df_tbl['table'].isin(selected_dropdown_tables), :]
    print(f"df_tbl shape {df_tbl.shape}")
    print(f"df_tbl head \n {df_tbl.head()}")
    dash_tbl = dash_table.DataTable(
        data=df_tbl.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_tbl.columns],
        sort_action='native')
    return dash_tbl


@callback(
    Output("table-displayed-nodes", 'children'),
    Input("button-send-displayed-nodes-to-table", 'n_clicks'),
    Input("my-network", "children")
)
def create_dash_table_of_displayed_neighbours(n_clicks, G):

    if n_clicks is not None:

        displayed_nodes=G['props']['elements']
        displayed_nodes=[x["data"]["id"] for x in displayed_nodes]

        df_tbl = data_for_graph["df_tbl"]
        df_tbl = df_tbl.loc[df_tbl['table'].isin(displayed_nodes), :]

        dash_tbl = dash_table.DataTable(
            data=df_tbl.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_tbl.columns],
            sort_action='native')
        return dash_tbl


if __name__ == '__main__':
    app.run(debug=True)
