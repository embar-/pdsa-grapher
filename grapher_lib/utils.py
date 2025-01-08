"""
Pagalbinės funkcijos.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu.
Jei kaip biblioteką naudojate kitoms reikmėms, tuomet reikia įsikelti ir/arba konfigūruoti gettext, pvz.:
from gettext import gettext as _
ARBA
from gettext import translation
translation("pdsa-grapher", 'locale', languages=["lt"]).install()
"""

import openpyxl  # būtina
import pandas as pd
import dash_cytoscape as cyto
import base64
import io
import warnings


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
    """
    Įkelto dokumento duomenų gavimas.
    :param contents: XLSX turinys kaip base64 duomenys
    :return: nuskaitytos rinkmenos duomenų struktūra kaip žodynas XLSX atveju arba tekstas (string) klaidos atveju.
    Duomenų struktūros kaip žodyno pavyzdys:
        {
            "file_data":
                {"sheet_name_1":
                    {
                        "df_columns": [],
                        "df": []
                    }
                },
        }
    """
    xlsx_parse_output = {"file_data": {}}

    content_string = contents[0].split(",")[1]
    decoded = base64.b64decode(content_string)

    try:
        # Assume that the user uploaded an excel file
        xlsx_file = pd.ExcelFile(io.BytesIO(decoded))
    except Exception as e:
        msg = _("There was an error while processing Excel file")
        warnings.warn(f"{msg}:\n {e}")
        return msg

    # Kiekvieną lakštą nuskaityti atskirai tam, kad būtų galima lengviau aptikti klaidą
    # Pvz., jei įjungtas duomenų filtravimas viename lakšte, jį nuskaitant  išmes klaidą
    # ValueError: Value must be either numerical or a string containing a wildcard
    for sheet_name in xlsx_file.sheet_names:
        try:
            df = pd.read_excel(xlsx_file, sheet_name)
            info_table = {
                "df_columns": list(df.columns),
                "df": df.to_dict("records")
            }
            xlsx_parse_output["file_data"][sheet_name] = info_table
        except Exception as e:
            msg = _("There was an error while processing Excel sheet \"%s\"") % sheet_name
            warnings.warn(f"{msg}\n {e}")
    if xlsx_parse_output["file_data"]:
        return xlsx_parse_output
    else:
        return _("There was an error while processing Excel file")
