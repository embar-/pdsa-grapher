import openpyxl  # būtina
import pandas as pd
import dash_cytoscape as cyto
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
