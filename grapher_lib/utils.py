"""
Pagalbinės funkcijos.

Čia naudojama „_“ funkcija vertimams yra apibrėžiama ir globaliai jos kalba keičiama programos lygiu.
Jei kaip biblioteką naudojate kitoms reikmėms, tuomet reikia įsikelti ir/arba konfigūruoti gettext, pvz.:
from gettext import gettext as _
ARBA
from gettext import translation
translation("pdsa-grapher", "locale", languages=["lt"]).install()
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import openpyxl  # noqa: būtina
# import odfpy  # jei norite nuskaityti LibreOffice ODS
import pandas as pd
import base64
import io
import csv
import chardet
import warnings


def get_fig_cytoscape_elements(node_elements=None, df_edges=None, node_neighbors=None):
    """
    Sukuria Dash Cytoscape objektui elementų - mazgų ir jungčių - žodyną.

    Args:
        node_elements (list): sąrašas mazgų
        df_edges (pandas.DataFrame, pasirinktinai): tinklo mazgų jungtys, pvz.,
            df_edges =  pd.DataFrame().from_records([{"source_tbl": "VardasX"}, {"target_tbl": "VardasY"}])
            (numatytuoju atveju braižomas tuščias grąfikas - be mazgas)
        node_neighbors (list): kurie iš node_elements yra kaimynai
    """

    # %% Mazgai (lentelės)
    if node_elements is None:
        node_elements = []
    if node_neighbors is None:
        node_neighbors = []
    node_elements = {x for x in node_elements if type(x) == str}
    node_elements = [
        {"data": {"id": x, "label": x}, "classes": "neighbor" if x in node_neighbors else ""}
        for x in node_elements
    ]

    # %% Jungtys tarp mazgų (ryšiai tarp lentelių)
    # Konvertavimas
    if not isinstance(df_edges, pd.DataFrame):
        if not df_edges:  # None arba tuščias sąrašas
            return node_elements  # Grąžinti mazgus, jei nėra jungčių tarp mazgų (ryšių tarp lentelių)
        df_edges = pd.DataFrame(df_edges)

    # Tikrinti ryšių lentelę. Ar turi įrašų
    if df_edges.empty:
        return node_elements  # Grąžinti mazgus
    # Ar turi visus reikalingus stulpelius
    mandatory_cols = ["source_tbl", "source_col", "target_tbl", "target_col"]
    if not all(c in df_edges.columns for c in mandatory_cols):
        warnings.warn(
            f'References df_edges variable requires "source_tbl", "source_col", "target_tbl", "target_col" columns. '
            f'Found columns: {df_edges.columns}'
        )
        return node_elements


    # Vienos jungties tarp stulpelių užrašas: "link_info" bus rodomas pažymėjus jungtį iškylančiame debesėlyje
    df_edges["link_info"] = df_edges.apply(
        lambda x:
            x["source_col"] if x["source_col"] == x["target_col"]
            else f'{x["source_col"]} -> {x["target_col"]}',
        axis=1
    )

    # Sujungti užrašus, jei jungtys tarp tų pačių lentelių
    df_edges = (
        df_edges
        .groupby(["source_tbl", "target_tbl"])["link_info"]
        .apply(list)  # būtinai sąrašo pavidalu
        .reset_index()
    )
    # "link_info_str" bus rodomas pažymėjus mazgą kaip jungties užrašas pačiame grafike - tai sutrumpinta "link_info"
    df_edges["link_info_str"] = df_edges["link_info"].apply(
        lambda x: "; ".join(x[:1]) + ("; ..." if len(x) > 1 else "") if isinstance(x, list) and len(x) > 0 else ""
    )

    df_edges = df_edges.loc[df_edges["source_tbl"].notna() & df_edges["target_tbl"].notna(), :]
    edge_elements = [
        # nors "id" nėra privalomas, bet `get_cytoscape_network_chart` f-joje pastovus ID
        # padės atnaujinti grafiko elementus neperpiešiant viso grafiko ir išlaikant esamas elementų padėtis
        {"data": {"id": f"{s} -> {t}", "source": s, "target": t, "link_info": i, "link_info_str": l}}
        for s, t, i, l in zip(
            df_edges["source_tbl"], df_edges["target_tbl"], df_edges["link_info"], df_edges["link_info_str"]
        )
    ]

    elements = node_elements + edge_elements
    return elements


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
        encoding = chardet.detect(byte_string)["encoding"]  # automatiškai nustatyti CSV koduotę
        decoded_string = byte_string.decode(encoding)  # Decode the byte string into a regular string
        dialect = csv.Sniffer().sniff(decoded_string)  # automatiškai nustatyti laukų skirtuką
        if dialect.delimiter in [";", ",", "\t"]:
            df = pd.read_csv(io.StringIO(decoded_string), delimiter=dialect.delimiter)
        else:
            # Kartais blogai aptinka skirtuką ir vis tiek reikia tikrinti kiekvieną jų priverstinai
            df = None
            for delimiter in [";", ",", "\t"]:
                if delimiter in decoded_string:
                    try:
                        df = pd.read_csv(io.StringIO(decoded_string), delimiter=delimiter)
                        break
                    except Exception:  # noqa: Mums visai nerūpi, kokia tai klaida
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
    :param df_edges: ryšių poros, surašytais pandas.DataFrame su "source_tbl" ir "target_tbl" stulpeliuose
    :return: tik tarpusavyje tiesioginių ryšių turinčių mazgų sąrašas
    """
    # Filter df_edges to include only rows where both source_tbl and target_tbl are in selected_items
    filtered_edges = df_edges[df_edges["source_tbl"].isin(nodes_sublist) & df_edges["target_tbl"].isin(nodes_sublist)]
    # Create a set of inter-related items
    inter_related_items = set(filtered_edges["source_tbl"]).union(set(filtered_edges["target_tbl"]))
    # Filter the selected items to keep only those that are inter-related
    filtered_items = [item for item in nodes_sublist if item in inter_related_items]
    return filtered_items


def create_pdsa_sheet_column_dropdowns(xlsx_data, sheet):
    """
    Iš PDSA struktūros "memory-uploaded-pdsa-plus" pasirinktam lakštui ištraukti jo visus stulpelius.
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
