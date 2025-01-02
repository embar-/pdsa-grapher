# import time

import openpyxl  # būtina

# import scipy as sp
import pandas as pd
import plotly.graph_objects as go

# import networkx as nx
import dash_cytoscape as cyto
from pathlib import Path
import base64
import io


def get_fig_cytoscape(
    df=pd.DataFrame().from_records([{"table_x": "NoneX"}, {"table_y": "NoneY"}]),
    layout="cola",
):
    cyto.load_extra_layouts()

    node_elements = df["table_x"].unique().tolist() + df["table_y"].unique().tolist()
    node_elements = [x for x in node_elements if type(x) == str]
    node_elements = [{"data": {"id": x, "label": x}} for x in node_elements]

    df = df.loc[df["table_x"].notna() & df["table_y"].notna(), :]
    edge_elements = [
        {"data": {"source": x, "target": y}}
        for x, y in zip(df["table_x"], df["table_y"])
    ]

    fig_cyto = cyto.Cytoscape(
        id="org-chart",
        # zoom=len(node_elements)*2,
        boxSelectionEnabled=True,
        responsive=True,
        layout={
            "name": layout,
            "clusters": "clusterInfo",
            "animate": False,
            "idealInterClusterEdgeLengthCoefficient": 0.5,
            "fit": True,
        },
        style={"width": "100%", "height": "500pt"},
        elements=node_elements + edge_elements,
        stylesheet=[
            {
                "selector": "label",  # as if selecting 'node' :/
                "style": {
                    "content": "data(label)",  # not to lose label content
                    # 'color': 'black',
                    "line-color": "grey",
                    "background-color": "lightblue",  # applies to node which will remain pink if selected :/
                },
            },
            {"selector": "edge", "style": {"weight": 1}},
        ],
    )

    return fig_cyto


def parse_file(contents):
    content_string = contents[0].split(",")[1]
    decoded = base64.b64decode(content_string)

    try:
        # Assume that the user uploaded an excel file
        xlsx_file = pd.ExcelFile(io.BytesIO(decoded))

        sheets = xlsx_file.sheet_names
        info_tables = [pd.read_excel(xlsx_file, s) for s in sheets]
        info_tables = [
            {"df_columns": list(d.columns), "df": d.to_dict("records")}
            for d in info_tables
        ]
        xlsx_parse_output = dict(zip(sheets, info_tables))
        xlsx_parse_output = {"file_data": xlsx_parse_output}

        #     Gaunama struktūra:
        # xlsx_parse_output = {
        #     "file_data":
        #         {"sheet_name_1":
        #             {
        #                 "df_columns": [],
        #                 "df": []
        #             }
        #         },
        #     "sheet_tbl":"", # šitas key pridedamas callback'uose
        #     "sheet_col":"", # šitas key pridedamas callback'uose
        #     "col_source":"", # šitas key pridedamas callback'uose
        #     "col_target":"", # šitas key pridedamas callback'uose

        # }

    except Exception as e:
        print(e)

        xlsx_parse_output = "There was an error processing this file."

    return xlsx_parse_output


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
