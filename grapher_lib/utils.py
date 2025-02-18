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

import re
import pandas as pd
import polars as pl
import fastexcel  # noqa: būtina XLSX importavimui per polars
import base64
import io
import csv
import chardet
import warnings


def get_fig_cytoscape_elements(
        node_elements=None, df_edges=None, node_neighbors=None, set_link_info_str=True
):
    """
    Sukuria Dash Cytoscape objektui elementų - mazgų ir jungčių - žodyną.

    Args:
        node_elements (list): sąrašas mazgų
        df_edges (pandas.DataFrame, pasirinktinai): tinklo mazgų jungtys, pvz.,
            df_edges =  pd.DataFrame().from_records([{"source_tbl": "VardasX"}, {"target_tbl": "VardasY"}])
            (numatytuoju atveju braižomas tuščias grąfikas - be mazgas)
        node_neighbors (list): kurie iš node_elements yra kaimynai
        set_link_info_str (bool): ar turi būti jungčių ["data"]["link_info_str"] reikšmė
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
    if set_link_info_str:
        df_edges["link_info_str"] = df_edges["link_info"].apply(
            lambda x: "; ".join(x[:1]) + ("; ..." if len(x) > 1 else "") if isinstance(x, list) and len(x) > 0 else ""
        )
    else:
        df_edges["link_info_str"] = ""  # Užrašai virš jungčių visada tušti

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


def get_graphviz_dot(
        nodes, df_tbl=None, df_col=None, neighbors=None, df_edges=None, layout="fdp", show_all_columns=True
    ):
    """
    Sukurti Graphviz DOT sintaksę pagal pateiktus mazgų ir ryšių duomenis
    :param df_tbl: DataFrame su lentelių duomenimis
    :param df_col: DataFrame su stulpelių duomenimis
    :param nodes: sąrašas su mazgų pavadinimais
    :param neighbors: sąrašas su kaimyninių mazgų pavadinimais
    :param df_edges: pandas.DataFrame su stulpeliais
        "source_tbl", "source_col", "target_tbl", "target_col"
    :param layout: Graphviz stilius - circo, dot, fdp, neato, osage, sfdp, twopi.
    :param show_all_columns: ar rodyti visus lentelės stulpelius (numatyta True); ar tik turinčius ryšių (False)
    :return: DOT sintaksės tekstas
    """

    # FIXME: Graphviz nepalaiko ilgo teksto laužymo, į tokį reiktų rankiniu būdu įterpti „\n“
    #  žr. https://stackoverflow.com/questions/5277864/text-wrapping-with-dot-graphviz
    #  dabar bent bandoma automatiškai pašalinti tekstą tarp skliaustų ().

    # Kintamieji
    nt1 = f"\n{' ' * 4}"
    nt2 = f"\n{' ' * 8}"
    if neighbors is None:
        neighbors = []
    if df_tbl is None:
        df_tbl = pd.DataFrame()
    if df_col is None:
        df_col = pd.DataFrame()
    if df_edges is None:
        df_edges = pd.DataFrame()

    def san(x):
        """
        Konvertuoti bet kokią pateiktą reikšmę naudojimui DOT sintaksėje.
        :param x: tekstas, skaičius arba None
        :return: tekstas be < ir >
        """
        if pd.isna(x):
            return ""
        # DOT/HTML viduje negali būti < arba > tekste.
        return f"{x}".replace('>', '&gt;').replace('<', '&lt;')

    # Sintaksės antraštė
    # Papildomai būtų galima pakeisti šriftą, nes numatytasis Times-Roman prastai žiūrisi mažuose paveiksluose.
    # Juose geriau būtų fontname=Verdana arba fontname=Arial, bet su pastaraisiais yra problemų dėl pločio neatitikimų
    dot = f"// Graphviz DOT sintaksė sukurta naudojant\n// https://github.com/embar-/pdsa-grapher\n\n"
    dot += "digraph {" + nt1
    dot += '// fontname="Times-Roman" yra numatytasis šriftas' + nt1
    dot += "// fontname=Verdana tinkamesnis mažuose šriftuose, bet gali netikti pločiai" + nt1
    dot += 'node [margin=0.3 shape=none fontname="Times-Roman"]' + nt1
    dot += "// layout: circo dot fdp neato osage sfdp twopi" + nt1
    dot += f"graph [layout={layout} overlap=false]\n" + nt1

    # Lentelių komentarų stulpelis
    tbl_comment_col = next((col for col in ["comment", "description"] if col in df_tbl.columns), None)

    # Stulpelių komentarų stulpelis
    col_comment_col = next((col for col in ["comment", "description"] if col in df_col.columns), None)

    # Sintaksė mazgams
    for table in nodes:
        # Lentelės vardas, fono spalva
        background = ' BGCOLOR="lightgray"' if table in neighbors else ""
        dot += f'"{san(table)}" [label=<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0"{background}>' + nt2
        dot += f'<TR><TD PORT=" "><FONT POINT-SIZE="20"><B>{san(table)}</B></FONT></TD></TR>' + nt2

        # Lentelės paaiškinimas
        df_table_comment = df_tbl[df_tbl["table"] == table][tbl_comment_col] if tbl_comment_col else None
        if df_table_comment is not None and not df_table_comment.empty:
            table_comment = df_table_comment.iloc[0]
            if table_comment and pd.notna(table_comment) and f"{table_comment}".strip():
                table_comment = f"{san(table_comment)}".strip()
                if len(table_comment) > 50 and "(" in table_comment:
                    # warnings.warn(f"Lentelės „{table}“ aprašas ilgesnis nei 50 simbolių!")
                    table_comment = re.sub(r"\(.*?\)", "", table_comment).strip()  # trumpinti šalinant tai, kas tarp ()
                dot += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="16" COLOR="blue">{table_comment}</FONT></TD></TR>' + nt2

        # Lentelės stulpeliai
        df_col1 = df_col[df_col["table"] == table]  # atsirinkti tik šios lentelės stulpelius
        if "column" in df_col1.columns:
            df_col1 = df_col1.dropna(subset=["column"])
        if df_col1.empty or ("column" not in df_col1.columns) or (not show_all_columns):
            # PDSA aprašuose lentelės nėra, bet galbūt stulpeliai minimi yra ryšiuose?
            if (not df_edges.empty) and (table in (df_edges["source_tbl"].to_list() + df_edges["target_tbl"].to_list())):
                # Imti ryšiuose minimus lentelių stulpelius
                if show_all_columns:
                    # visi stulpeliai, minimi ryšiuose (net jeigu jungtys nematomos)
                    edges_t_src = set(df_edges[df_edges["source_tbl"] == table]["source_col"].to_list())
                    edges_t_trg = set(df_edges[df_edges["target_tbl"] == table]["target_col"].to_list())
                else:
                    # tik stulpeliai, turintys matomų ryšių dabartiniame grafike
                    edges_t_src = set(df_edges[
                                          (df_edges["source_tbl"] == table) & (df_edges["target_tbl"].isin(nodes))
                                      ]["source_col"].to_list())
                    edges_t_trg = set(df_edges[
                                          (df_edges["target_tbl"] == table) & (df_edges["source_tbl"].isin(nodes))
                                      ]["target_col"].to_list())
                edges_t_trg = [c for c in edges_t_trg if pd.notna(c)]  # jei kartais stulpelis yra None - praleisti
                # Įeinančių ryšių turinčiuosius išvardinti pirmiausia
                edges_t = edges_t_trg + [c for c in edges_t_src if pd.notna(c) and (c not in edges_t_trg)]
                if df_col1.empty or ("column" not in df_col1.columns):
                    df_col1 = pd.DataFrame({"column": edges_t})
                    if col_comment_col:
                        df_col1[col_comment_col] = None
                else:
                    col1_n1 = len(df_col1)
                    df_col1 = df_col1[df_col1["column"].isin(edges_t)]
                    col1_n2 = len(df_col1)
                    if col1_n1 > col1_n2:
                        df_col1.loc[col1_n2, "column"] = "..."  # tai nėra stulpelis, tik žyma, kad jų yra daugiau nei matoma
        if (not df_col1.empty) and ("column" in df_col1.columns):
            # Pirmiausia rodyti tuos, kurie yra raktiniai
            if "is_primary" in df_col1.columns:
                df_col1 = df_col1.sort_values(by="is_primary", ascending=False)
            hr_added = False  # Linija tarp antraštės ir stulpelių dar nepridėta
            for idx, row in df_col1.iterrows():
                col = row["column"]
                if pd.isna(col):
                    continue
                elif not hr_added:
                    dot += f"<HR></HR>" + nt2  # Linija tarp antraštės ir stulpelių
                    hr_added = True
                dot += f'<TR><TD PORT="{san(col)}" ALIGN="LEFT" BORDER="1" COLOR="lightgray"><TABLE BORDER="0"><TR>' + nt2
                column_str = f"{san(col)}".strip()
                if (
                    ("is_primary" in row) and row["is_primary"] and
                    pd.notna(row["is_primary"]) and str(row["is_primary"]).upper() != "FALSE"
                ):
                    column_str += " 🔑"
                dot += f'    <TD ALIGN="LEFT"><FONT POINT-SIZE="16">{column_str}</FONT></TD>' + nt2
                if col_comment_col and san(row[col_comment_col]).strip():
                    col_label = san(row[col_comment_col]).strip()
                    if len(f"{col_label}") > 30 and "(" in col_label:
                        # warnings.warn(f"Lentelės „{table}“ stulpelio „{col}“ aprašas ilgesnis nei 30 simbolių!")
                        col_label = re.sub(r"\(.*?\)", "", col_label).strip()  # trumpinti šalinant tai, kas tarp ()
                    dot += f'    <TD ALIGN="RIGHT"><FONT COLOR="blue">   {col_label}</FONT></TD>' + nt2
                dot += f'</TR></TABLE></TD></TR>' + nt2
        dot += "</TABLE>>]\n" + nt1  # uždaryti sintaksę

    # Sintaksė jungtims
    if not df_edges.empty:
        df_edges = df_edges.drop_duplicates()
        refs = [tuple(x) for x in df_edges.to_records(index=False)]
        for ref_from_table, ref_from_column, ref_to_table, ref_to_column in refs:

            # Jei yra ta pati jungtis atvirkščia kryptimi, tai piešti kaip vieną
            if (ref_to_table, ref_to_column, ref_from_table, ref_from_column) in refs:
                if (ref_to_table, ref_to_column) < (ref_from_table, ref_from_column):
                    continue
                else:
                    direction = "both"
            else:
                direction = "forward"

            if ref_from_column:
                ref_from = f'"{san(ref_from_table)}":"{san(ref_from_column)}"'
            else:
                ref_from = f'"{san(ref_from_table)}":" "'
            if ref_to_column:
                ref_to = f'"{san(ref_to_table)}":"{san(ref_to_column)}"'
            else:
                ref_to =  f'"{san(ref_to_table)}":" "'
            dot += f'{ref_from} -> {ref_to} [dir="{direction}"];' + nt1

    dot += "\n}"
    return dot


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
        xlsx_file = pl.read_excel(io.BytesIO(byte_string), sheet_id=0)
    except Exception as e:
        msg = _("There was an error while processing Excel file")
        warnings.warn(f"{msg}:\n {e}")
        return msg

    # Kiekvieną lakštą nuskaityti atskirai tam, kad būtų galima lengviau aptikti klaidą
    # Pvz., jei įjungtas duomenų filtravimas viename lakšte, jį nuskaitant  išmes klaidą
    # ValueError: Value must be either numerical or a string containing a wildcard
    for sheet_name in xlsx_file.keys():
        try:
            df = xlsx_file[sheet_name]
            info_table = {
                "df_columns": list(df.columns),
                "df": df.to_dicts()
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
            df = pl.read_csv(io.StringIO(decoded_string), separator=dialect.delimiter)
        else:
            # Kartais blogai aptinka skirtuką ir vis tiek reikia tikrinti kiekvieną jų priverstinai
            df = None
            for delimiter in [";", ",", "\t"]:
                if delimiter in decoded_string:
                    try:
                        df = pl.read_csv(io.StringIO(decoded_string), separator=delimiter)
                        break
                    except Exception:  # noqa: Mums visai nerūpi, kokia tai klaida
                        pass
            if df is None:
                return _("There was an error while processing file of unknown type")
        info_table = {
            "df_columns": list(df.columns),
            "df": df.to_dicts()
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


def get_sheet_columns(xlsx_data, sheet):
    """
    Iš XLSX ar CSV turinio (kurį sukuria `parse_file` f-ja) pasirinktam lakštui ištraukti jo visus stulpelius.
    :param xlsx_data: žodynas {"file_data": lakštas: {"df": [], "df_columns": [stulpelių sąrašas]}}
    :param sheet: pasirinkto lakšto vardas
    :return: lakšto stulpeliai
    """
    if (
        isinstance(xlsx_data, dict) and "file_data" in xlsx_data.keys() and
        isinstance(xlsx_data["file_data"], dict) and sheet in xlsx_data["file_data"].keys() and
        (xlsx_data["file_data"][sheet] is not None)
    ):
        sheet_columns = xlsx_data["file_data"][sheet]["df_columns"]
        return sheet_columns
    return []


def change_style_display_value(whether_set_visible, style_dict=None):
    """
    Dash objekto stilių žodyne pakeisti jų matomumo reikšmę.
    :param whether_set_visible: ar objektas turi būti matomas
    :param style_dict: Dash objekto "style" kaip žodynas.
    :return: pakeistas "style" žodynas.
    """
    if not style_dict:
        style_dict = {}
    if whether_set_visible:
        style_dict["display"] = "block"  # matomas
    else:
        style_dict["display"] = "none"  # nematomas
    return style_dict
