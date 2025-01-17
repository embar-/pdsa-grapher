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
# import odfpy  # jei norite nuskaityti LibreOffice ODS
import pandas as pd
import dash_cytoscape as cyto
import base64
import io
import csv
import chardet
import warnings


def get_fig_cytoscape(df=None, layout="cola"):
    """
    Sukuria Dash Cytoscape objektą - tinklo diagramą.

    Args:
        df (pandas.DataFrame, pasirinktinai): tinklo mazgų jungtys, pvz.,
            df =  pd.DataFrame().from_records([{"table_x": "VardasX"}, {"table_y": "VardasY"}])
            (numatytuoju atveju braižomas tuščias grąfikas - be mazgas)
        layout (str, optional): Cytoscape išdėstymo stilius; galimos reikšmės: "random", "circle",
            "breadthfirst", "cola" (numatyta), "cose", "dagre", "euler", "grid", "spread".

    Returns:
        Cytoscape objektas.
    """

    # Jungtys tarp tinklo mazgų
    if df is None:
        df = pd.DataFrame(columns=["table_x", "table_y"])

    # Išdėstymų stiliai. Teoriškai turėtų būti palaikoma daugiau nei įvardinta, bet kai kurie neveikė arba nenaudingi:
    # "preset", "concentric", "close-bilkent", "klay"
    allowed_layouts = [
        "random", "circle", "breadthfirst", "cola", "cose", "dagre", "euler", "grid", "spread",
    ]
    if not (layout in allowed_layouts):
        msg = _("Unexpected Cytoscape layout: %s. Using default 'cola'") % layout
        warnings.warn(msg)
        layout = "cola"

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
        style={"width": "100%", "height": "100%", "position": "absolute"},
        elements=node_elements + edge_elements,
        stylesheet=[
            {
                "selector": "label",  # as if selecting 'node' :/
                "style": {
                    "content": "data(label)",  # not to lose label content
                    "background-color": "lightblue",
                },
            },
            {
                "selector": "node:active, node:selected",
                "style": {
                    "background-color": "blue",
                },
            },
            {
                "selector": "edge",
                "style": {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle'
                }
            },
        ],
    )

    return fig_cyto


def parse_file(contents):
    """
    Įkelto dokumento duomenų gavimas.
    :param contents: XLSX arba CSV turinys kaip base64 duomenys
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
    content_string = contents[0].split(",")[1]
    decoded = base64.b64decode(content_string)

    # Ar tai Excel .xls (\xD0\xCF\x11\xE0) arba .zip/.xlsx/.ods (PK\x03\x04)?
    is_excel = decoded.startswith(b"\xD0\xCF\x11\xE0") or decoded.startswith(b"PK\x03\x04")
    if is_excel:
        return parse_excel(decoded)  # Bandyti nuskaityti tarsi Excel XLS, XLSX arba LibreOffice ODS
    else:
        return parse_csv(decoded)  # Bandyti nuskaityti tarsi CSV


def parse_excel(byte_string):
    """
    Pagalbinė `parse_file` funkcija Excel XLS arba XLSX nuskaitymui.

    :param byte_string: CSV turinys (jau iškoduotas su base64.b64decode)
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """
    xlsx_parse_output = {"file_data": {}}

    try:
        xlsx_file = pd.ExcelFile(io.BytesIO(byte_string))
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
            warnings.warn(f"{msg}:\n {e}")
            return msg
    if xlsx_parse_output["file_data"]:
        return xlsx_parse_output
    else:
        return _("There was an error while processing Excel file")


def parse_csv(byte_string):
    """
    Pagalbinė `parse_file` funkcija CSV nuskaitymui, automatiškai pasirenkant skirtuką ir koduotę.
    Standartinė pandas pd.read_csv() komanda neaptinka koduotės ir skirtukų automatiškai.

    :param byte_string: CSV turinys (jau iškoduotas su base64.b64decode)
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """
    try:
        encoding = chardet.detect(byte_string)['encoding']  # automatiškai nustatyti CSV koduotę
        decoded_string = byte_string.decode(encoding)  # Decode the byte string into a regular string
        dialect = csv.Sniffer().sniff(decoded_string)  # automatiškai nustatyti laukų skirtuką
        if dialect.delimiter in [";", ",", "\t"]:
            df = pd.read_csv(io.StringIO(decoded_string), delimiter=dialect.delimiter)
        else:
            # Kartais blogai aptinka ir vis tiek reikia tikrinti kiekvieną
            df = None
            for delimiter in [";", ",", "\t"]:
                if delimiter in decoded_string:
                    try:
                        df = pd.read_csv(io.StringIO(decoded_string), delimiter=delimiter)
                        break
                    except Exception:
                        pass
            if df is None:
                return _("There was an error while processing file of unknown type")
        info_table = {
            "df_columns": list(df.columns),
            "df": df.to_dict("records")
        }
        csv_parse_output = {"file_data": {"CSV": info_table}}
        return csv_parse_output
    except Exception as e:
        msg = _("There was an error while processing file as CSV")
        warnings.warn(f"{msg}:\n {e}")
        return msg


def remove_orphaned_nodes_from_sublist(nodes_sublist, df_edges):
    """
    Pašalinti mazgus, kurie neturi tarpusavio ryšių su išvardintaisiais
    :param nodes_sublist: pasirinktų mazgų poaibio sąrašas
    :param df_edges: ryšių poros, surašytais pandas.DataFrame su "table_x" ir "table_y" stulpeliuose
    :return: tik tarpusavyje tiesioginių ryšių turinčių mazgų sąrašas
    """
    # Filter df_edges to include only rows where both table_x and table_y are in selected_items
    filtered_edges = df_edges[df_edges['table_x'].isin(nodes_sublist) & df_edges['table_y'].isin(nodes_sublist)]
    # Create a set of inter-related items
    inter_related_items = set(filtered_edges['table_x']).union(set(filtered_edges['table_y']))
    # Filter the selected items to keep only those that are inter-related
    filtered_items = [item for item in nodes_sublist if item in inter_related_items]
    return filtered_items


def create_pdsa_sheet_column_dropdowns(xlsx_data, sheet):
    """
    Iš memory-pdsa-meta-info struktūros pasirinktam lakštui ištraukti jo visus stulpelius.
    :param xlsx_data: žodynas {"file_data": lakštas: {"df_columns": [stulpelių sąrašas]}}
    :param sheet: pasirinkto lakšto kodas ("sheet_tbl" arba "sheet_col")
    :return: lakšto vardas, stulpeliai
    """
    if (
        isinstance(xlsx_data, dict) and
        sheet in xlsx_data.keys() and
        (xlsx_data[sheet] is not None)
    ):
            sheet_col = xlsx_data[sheet]
            sheet_tbl_columns = xlsx_data["file_data"][sheet_col]["df_columns"]
            return sheet_col, sheet_tbl_columns

    return "", []