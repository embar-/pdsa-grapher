import os

import numpy as np
import openpyxl
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import scipy as sp
import dash_cytoscape as cyto
from pathlib import Path

# utils are done
# this is app_tab_remote
class pdsa:
    def __init__(self, file_path, file_name, tbl_sheet, col_sheet, keep_cols_df_tbl, keep_cols_df_col):
        self.file_path = Path(fr"{file_path}")
        self.file_name = file_name
        self.tbl_sheet = tbl_sheet
        self.col_sheet = col_sheet
        self.keep_cols_df_tbl = keep_cols_df_tbl
        self.keep_cols_df_col = keep_cols_df_col


class uzklausa:
    def __init__(self, file_path, file_name, tbl_x_series, tbl_y_series, edge_data=None):
        self.file_path = Path(fr"{file_path}")
        self.file_name = file_name
        self.tbl_x_series = tbl_x_series
        self.tbl_y_series = tbl_y_series
        self.edge_data = edge_data

    def get_edge_dataframe_for_network(self):

        '''
            Sukuria pd.Dataframe apie lentelių ryšius "edges" iš uzklausos failo sheet.
            Tam, kad greičiau atsidarytų, pirmą kartą atidaromas xlsx failas ir norimas sheet
            įrašomas į tsv. Sekančius kartus failas atidaromas iš tsv


            :return: pd.DataFrame

        '''
        # Creating tsv name
        tsv_edge_file_name = self.file_name.rsplit(".", 1)[0] + ".tsv"

        # Try load tsv
        try:
            df_edges = pd.read_csv(f"inputs/temp/{tsv_edge_file_name}", sep='\t')

            print("Loading from tsv")

        # Otherwise make tsv
        except Exception as e:
            print(e)
            print("Loading from xlsx and saving into tsv")

            # Check if Excel is saved as real xlsx and nor Strict Open XML
            try:
                df_edges = pd.read_excel(f"{self.file_path}/{self.file_name}")
            except ValueError as ve:
                print(ve)
                print("Failas išsaugotas kaip Strict Open XML ir turi xlsx extention'ą. Save As į tikrą XLSX")
                exit()

            # From xlsx make tsv
            df_edges = df_edges.loc[:, [self.tbl_x_series, self.tbl_y_series]]
            df_edges.columns = ["table_x", "table_y"]
            # (a bit of cleaning...)
            df_edges = df_edges.loc[df_edges["table_x"] != df_edges["table_y"], :]

            df_edges.to_csv(f"inputs/temp/{tsv_edge_file_name}", sep='\t', index=False)
        # Set df_edges as edge_data property
        self.edge_data = df_edges
        return df_edges


def get_data_about_tbls_n_cols(pdsa):
    '''
    Sukuria pd.Dataframe iš PDSA failo sheet.
    Tam kad greičiau atsidarytų, pirmą kartą atidaromas xlsx failas ir norimas sheet
    įrašomas į tsv. Sekančius kartus failas atidaromas iš tsv

    :param pdsa: pdsa failo objektas, kuris aprašo jo lokaciją ir sheet iš kurio norim paimt lentelę
    :return: pd.DataFrame

    '''

    tsv_col_file_name = pdsa.file_name.replace(".xlsx", f"_{pdsa.col_sheet}.tsv")
    tsv_tbl_file_name = pdsa.file_name.replace(".xlsx", f"_{pdsa.tbl_sheet}.tsv")
    try:
        df_col = pd.read_csv(f"inputs/temp/{tsv_col_file_name}", sep='\t')
        df_tbl = pd.read_csv(f"inputs/temp/{tsv_tbl_file_name}", sep='\t')

        print("Loading from tsv")
    except Exception as e:
        print(e)

        """
        Iš tbl_sheet išsitraukiu lenteles, kurios turi aprašymus
        (atsikratau tų, kurios jų neturi. Kaip sakė Aliona Milentjeva:
        lentelės be aprašymų neturi duomenų)
        """

        df_tbl = pd.read_excel(f"{pdsa.file_path}/{pdsa.file_name}", sheet_name=pdsa.tbl_sheet)

        # list_tbl = df_tbl.loc[df_tbl['lenteles_paaiskinimas'].notna(), "table"].tolist()
        list_required_cols_df_tbl = pdsa.keep_cols_df_tbl
        df_tbl = df_tbl.loc[:, list_required_cols_df_tbl]
        # df_tbl = df_tbl.loc[df_tbl["table"].isin(list_tbl),:]
        if "lenteles_paaiskinimas" in df_tbl.columns:
            df_tbl = df_tbl.sort_values(by="lenteles_paaiskinimas")

        # Iš column sheet pasilieku tik tas lenteles, kurios table sheet'e turėjo paaiškinimus
        # Išsaugau tsv, kad greičiau atidarytų
        df_col = pd.read_excel(f"{pdsa.file_path}/{pdsa.file_name}", sheet_name=pdsa.col_sheet)
        list_required_cols_df_cols = pdsa.keep_cols_df_col

        df_col = df_col.loc[:, list_required_cols_df_cols]
        # df_col = df_col.loc[df_col["table"].isin(list_tbl)]

        df_col.to_csv(f"inputs/temp/{tsv_col_file_name}", sep='\t', index=False)
        df_tbl.to_csv(f"inputs/temp/{tsv_tbl_file_name}", sep='\t', index=False)
        # df.to_csv(f"inputs/temp/{pdsa.file_name}.tsv", sep='\t')

    return {"df_tbl": df_tbl, "df_col": df_col}


def create_edge_df_tbl_tbl(df, pdsa):
    # Atsirenku tik reikiamus stuleplius
    df = df.loc[:, ["table", "column"]]

    # Self join'as kad rasti kurios lentelės jungiasi galėtų jungtis per bendrus stuleplius
    df = df.merge(df, on="column", how='inner')

    # Pašalinu edge'us kur lentelė jungiasi su savimi
    df = df.loc[df["table_x"] != df["table_y"], ["table_x", "table_y"]]

    # Pašalinu duplikatus kur skiriasi tik jungimosi kryptis A->B == B->A
    df['combine'] = df[['table_x', 'table_y']].values.tolist()
    df['combine'] = df['combine'].apply(lambda x: sorted(x))
    df[['table_x', 'table_y']] = pd.DataFrame(df["combine"].tolist(), index=df.index)

    df = df.loc[:, ['table_x', 'table_y']]
    # print(df.loc[(df["table_x"]=="ATB") & (df["table_y"]=="ATBMOBreakPointSada"),:])

    df = df.drop_duplicates()
    # df.to_csv(f"inputs/temp/{pdsa.file_name}.tsv", sep='\t', index=False)
    return df


def get_fig_cytoscape(df, layout):
    cyto.load_extra_layouts()

    node_elements = df['table_x'].unique().tolist() + df['table_y'].unique().tolist()
    node_elements = [x for x in node_elements if type(x) == str]
    node_elements = [{'data': {'id': x, 'label': x}} for x in node_elements]

    df = df.loc[df["table_x"].notna() & df["table_y"].notna(), :]
    edge_elements = [{'data': {'source': x, 'target': y}} for x, y in zip(df["table_x"], df["table_y"])]

    fig_cyto = cyto.Cytoscape(
        id='org-chart',
        # zoom=len(node_elements)*2,
        boxSelectionEnabled=True,
        responsive=True,
        layout={
            'name': layout,
            'clusters': 'clusterInfo',
            'animate': False,
            'idealInterClusterEdgeLengthCoefficient': 0.5,
            'fit': True},
        style={'width': '100%', "height": "500pt"},
        elements=node_elements + edge_elements,
        stylesheet=[
            {'selector': 'label',  # as if selecting 'node' :/
             'style': {'content': 'data(label)',  # not to lose label content
                       'color': 'black',
                       'line-color': 'grey',

                       'background-color': 'blue'  # applies to node which will remain pink if selected :/
                       }},
            {"selector": "edge",
             "style": {"weight": 1}}
        ]
    )

    # print(f"Amount of nodes: {len(fig_cyto.elements)}")

    return fig_cyto


##################################
# Documentation for cyto
##################################

# def get_fig_cytoscape(df, layout):
#     cyto.load_extra_layouts()
#
#     node_elements = df['table_x'].unique().tolist() + df['table_y'].unique().tolist()
#     node_elements = [x for x in node_elements if type(x) == str]
#     node_elements = [{'data': {'id': x, 'label': x}} for x in node_elements]
#
#     df = df.loc[df["table_x"].notna() & df["table_y"].notna(), :]
#     edge_elements = [{'data': {'source': x, 'target': y}} for x, y in zip(df["table_x"], df["table_y"])]
#
#     fig_cyto = cyto.Cytoscape(
#         id='org-chart',
#         # zoom=len(node_elements)*2,
#         boxSelectionEnabled=True,
#         responsive=True,
#         layout={
#             'name': layout,
#             #     # "padding":100,
#             #     'randomize': True,
#             #     'componentSpacing': 1000, #Atstumas tarp agreguotų node's (lizdų)
#             #     'nodeRepulsion': 100000,
#             #     'edgeElasticity': 100,
#             #     "fit": False,
#             #     "animate":True,
#
#             # 'name' : 'cise',
#
#             # ClusterInfo can be a 2D array contaning node id's or a function that returns cluster ids.
#             # For the 2D array option, the index of the array indicates the cluster ID for all elements in
#             # the collection at that index. Unclustered nodes must NOT be present in this array of clusters.
#             #
#             # For the function, it would be given a Cytoscape node and it is expected to return a cluster id
#             # corresponding to that node. Returning negative numbers, null or undefined is fine for unclustered
#             # nodes.
#             # e.g
#             # Array:                                     OR          function(node){
#             #  [ ['n1','n2','n3'],                                       ...
#             #    ['n5','n6']                                         }
#             #    ['n7', 'n8', 'n9', 'n10'] ]
#             'clusters': 'clusterInfo',
#             'animate': False,
#
#             # number of ticks per frame; higher is faster but more jerky
#             # 'refresh': 10,
#             # true : Fits at end of layout for animate:false or animate:'end'
#             # "fit": True,
#
#             # Padding in rendered co-ordinates around the layout
#             # 'padding': 30,
#
#             # separation amount between nodes in a cluster
#             # note: increasing this amount will also increase the simulation time
#             # 'nodeSeparation': 12.5,
#
#             # Inter-cluster edge length factor
#             # (2.0 means inter-cluster edges should be twice as long as intra-cluster edges)
#             'idealInterClusterEdgeLengthCoefficient': 0.5,
#
#             # Whether to pull on-circle nodes inside of the circle
#             # 'allowNodesInsideCircle': False,
#
#             # Max percentage of the nodes in a circle that can move inside the circle
#             # 'maxRatioOfNodesInsideCircle': 0.1,
#
#             # - Lower values give looser springs
#             # - Higher values give tighter springs
#             # 'springCoeff': 0.45,
#
#             # Node repulsion (non overlapping) multiplier
#             # 'nodeRepulsion': 4500,
#
#             # Gravity force (constant)
#             # 'gravity': 0.25,
#
#             # Gravity range (constant)
#             # 'gravityRange': 3.8,
#         },
#
#         style={'width': '100%', 'height': '2000pt'},
#         elements=node_elements + edge_elements,
#         stylesheet=[
#             {'selector': 'label',  # as if selecting 'node' :/
#              'style': {'content': 'data(label)',  # not to lose label content
#                        'color': 'black',
#                        'line-color': 'grey',
#
#                        'background-color': 'blue'  # applies to node which will remain pink if selected :/
#                        },
#              },
#             {"selector": "edge",
#              "style": {"weight": 1}
#              }
#         ]
#
#     )
#     # print(f"Amount of nodes: {len(fig_cyto.elements)}")
#
#     return fig_cyto


#############################
# Depricated
#############################
def create_edge_df_tbl_col_tbl(df):
    df.loc[:, 'Occur'] = df['column'].apply(lambda x: (df['column'] == x).sum())
    df['index'] = df.index

    df['columns_connecting_tables_1'] = "col1_" + df['index'].astype(str)
    df['columns_connecting_tables_2'] = "col2_" + df['index'].astype(str)

    df.loc[df["Occur"] > 1, 'columns_connecting_tables_1'] = df.loc[df["Occur"] > 1, "column"]
    df.loc[df["Occur"] > 1, 'columns_connecting_tables_2'] = df.loc[df["Occur"] > 1, "column"]

    df_1 = df.loc[:, ["table", "columns_connecting_tables_1"]]
    df_2 = df.loc[:, ["table", "columns_connecting_tables_2"]]

    df = df_1.merge(df_2,
                    left_on="columns_connecting_tables_1",
                    right_on="columns_connecting_tables_2",
                    how='outer')

    df = df.loc[df["table_x"] != df["table_y"], ["table_x", "table_y"]]
    df = df.drop_duplicates()
    return df


def create_edge_tbl(df, columns: list):
    df_network = df.loc[:, columns]
    return df_network

    G = nx.from_pandas_edgelist(edge_tbl,
                                source='table',
                                target='column',
                                edge_attr=['is_primary', 'is_unique', 'type', 'n_records', 'n_nulls', 'rules', 'prasme']
                                )
    return G


def filter_df(df):
    df.loc[:, 'Occur'] = df['column'].apply(lambda x: (df['column'] == x).sum())
    df = df.loc[df["Occur"] > 1, :]

    df = df.loc[(df["is_primary"] == True), :]
    # df = df.loc[df['table'] == "ATBMOBreakPointSada",:]

    return df


def create_fig(G, cols_edge_atts):
    ###################################
    # By: https://plotly.com/python/network-graphs/
    ###################################

    ###################################
    # Creating edges
    ###################################

    edge_x = []
    edge_y = []
    pos = nx.kamada_kawai_layout(G)
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    ###################################
    # Adding collor and text to Nodes
    ###################################

    node_adjacencies = []
    node_text = []
    # for node, adjacencies in enumerate(G.adjacency()):
    #     node_adjacencies.append(len(adjacencies[1]))
    #     node_text.append('# of connections: ' + str(len(adjacencies[1])))

    node_colors = []
    node_text = []
    for node in G.nodes:
        # node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f"# Name: {node}")

    # node_trace.marker.color = node_adjacencies
    node_trace.text = node_text
    ###################################
    # Creating fig
    ###################################

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network graph made with Python',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.write_html("outputs/file.html")
