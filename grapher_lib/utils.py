"""
Pagalbinės funkcijos.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import re
import polars as pl
import warnings


def get_fig_cytoscape_elements(
        node_elements=None, df_edges=None, node_neighbors=None, set_link_info_str=True
):
    """
    Sukuria Dash Cytoscape objektui elementų - mazgų ir jungčių - žodyną.

    Args:
        node_elements (list): sąrašas mazgų
        df_edges (polars.DataFrame, pasirinktinai): tinklo mazgų jungtys, pvz.,
            df_edges =  pl.DataFrame([{
                "source_tbl": "VardasX",
                "source_col": None,
                "target_tbl": "VardasY",
                "target_col": None
            }])
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
    if not isinstance(df_edges, pl.DataFrame):
        if df_edges in [[], None]:
            return node_elements  # Grąžinti mazgus, jei nėra jungčių tarp mazgų (ryšių tarp lentelių)
        df_edges = pl.DataFrame(df_edges, infer_schema_length=None)

    # Tikrinti ryšių lentelę. Ar turi įrašų
    if df_edges.height == 0:
        return node_elements  # Grąžinti mazgus
    # Ar turi visus reikalingus stulpelius
    mandatory_cols = ["source_tbl", "source_col", "target_tbl", "target_col"]
    if not all(c in df_edges.columns for c in mandatory_cols):
        warnings.warn(
            f'References df_edges variable requires "source_tbl", "source_col", "target_tbl", "target_col" columns. '
            f'Found columns: {df_edges.columns}'
        )
        return node_elements
    df_edges = df_edges.filter(
        pl.col("source_tbl").is_not_null() & pl.col("target_tbl").is_not_null()
    )

    # Vienos jungties tarp stulpelių užrašas: "link_info" bus rodomas pažymėjus jungtį iškylančiame debesėlyje
    df_edges = df_edges.with_columns(
        pl.when(pl.col("source_col") == pl.col("target_col"))
        .then(pl.col("source_col"))
        .otherwise(pl.col("source_col") + " -> " + pl.col("target_col"))
        .alias("link_info")
    )

    # Sujungti užrašus, jei jungtys tarp tų pačių lentelių
    df_edges = df_edges.group_by(["source_tbl", "target_tbl"]).agg(pl.col("link_info"))
    # "link_info_str" bus rodomas pažymėjus mazgą kaip jungties užrašas pačiame grafike - tai sutrumpinta "link_info"
    if set_link_info_str:
        df_edges = df_edges.with_columns(
            pl.when(pl.col("link_info").list.len() > 0)
            .then(
                pl.col("link_info").list.first() +
                pl.when(pl.col("link_info").list.len() > 1)
                .then(pl.lit("; ..."))
                .otherwise(pl.lit(""))
            )
            .otherwise(pl.lit(""))
            .alias("link_info_str")
        )
    else:
        df_edges = df_edges.with_columns(pl.lit("").alias("link_info_str"))  # Užrašai virš jungčių visada tušti

    edges_dicts = df_edges.to_dicts()
    edge_elements = [
        # nors "id" nėra privalomas, bet `get_cytoscape_network_chart` f-joje pastovus ID
        # padės atnaujinti grafiko elementus neperpiešiant viso grafiko ir išlaikant esamas elementų padėtis
        {
            "data": {
                "id": f"{row['source_tbl']} -> {row['target_tbl']}",
                "source": row["source_tbl"],
                "target": row["target_tbl"],
                "link_info": row["link_info"],
                "link_info_str": row["link_info_str"]
            }
        }
        for row in edges_dicts
    ]

    elements = node_elements + edge_elements
    return elements


def get_graphviz_dot(
    nodes, df_tbl=None, df_col=None, neighbors=None, df_edges=None,
    layout="fdp", show_all_columns=True, show_descriptions=True
):
    """
    Sukurti Graphviz DOT sintaksę pagal pateiktus mazgų ir ryšių duomenis
    :param df_tbl: DataFrame su lentelių duomenimis
    :param df_col: DataFrame su stulpelių duomenimis
    :param nodes: sąrašas su mazgų pavadinimais
    :param neighbors: sąrašas su kaimyninių mazgų pavadinimais
    :param df_edges: polars.DataFrame su stulpeliais "source_tbl", "source_col", "target_tbl", "target_col"
    :param layout: Graphviz stilius - circo, dot, fdp, neato, osage, sfdp, twopi.
    :param show_all_columns: ar rodyti visus lentelės stulpelius (numatyta True); ar tik pirminius raktus ir turinčius ryšių (False)
    :param show_descriptions: ar rodyti lentelių ir stulpelių aprašus pačiame grafike (numatyta True)
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
        df_tbl = pl.DataFrame()
    if df_col is None:
        df_col = pl.DataFrame()
    if df_edges is None:
        df_edges = pl.DataFrame()

    def san(x):
        """
        Konvertuoti bet kokią pateiktą reikšmę naudojimui DOT sintaksėje.
        :param x: tekstas, skaičius arba None
        :return: tekstas be < ir >
        """
        if x is None:
            return ""
        # DOT/HTML viduje negali būti < arba > tekste.
        return f"{x}".replace('>', '&gt;').replace('<', '&lt;')

    # Sintaksės antraštė
    # Papildomai būtų galima pakeisti šriftą, nes numatytasis Times-Roman prastai žiūrisi mažuose paveiksluose.
    # Juose geriau būtų fontname=Verdana arba fontname=Arial, bet su pastaraisiais yra problemų dėl pločio neatitikimų
    dot = f"// Graphviz DOT sintaksė sukurta naudojant\n// https://github.com/embar-/pdsa-grapher\n\n"
    dot += "digraph {" + nt1
    dot += "// layout: circo dot fdp neato osage sfdp twopi" + nt1
    dot += f'graph [layout={layout} overlap=false rankdir="LR"]\n' + nt1
    dot += '// fontname="Times-Roman" yra numatytasis šriftas' + nt1
    dot += '// fontname="Verdana" tinka mažoms raidėms, bet gali netikti plotis' + nt1
    dot += 'node [margin=0.3 shape=none fontname="Verdana"]' + nt1 + nt1

    # Sintaksė mazgams
    for table in nodes:
        # Lentelės vardas, fono spalva
        background = ' BGCOLOR="lightgray"' if table in neighbors else ""
        dot += f'"{san(table)}" [label=<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0"{background}>' + nt2
        dot += f'<TR><TD PORT=" "><FONT POINT-SIZE="20"><B>{san(table)}</B></FONT></TD></TR>' + nt2

        # Lentelės paaiškinimas
        table_comment_html = ""  # Laikina reikšmė
        df_tbl1 = df_tbl.filter(pl.col("table") == table)
        df_tbl1_comment = df_tbl1.select("comment").to_series() if "comment" in df_tbl1.columns else None
        if show_descriptions and (df_tbl1_comment is not None) and (not df_tbl1_comment.is_empty()):
            table_comment = df_tbl1_comment[0]
            if table_comment and table_comment is not None and f"{table_comment}".strip():
                table_comment = f"{san(table_comment)}".strip()
                if len(table_comment) > 50 and "(" in table_comment:
                    # warnings.warn(f"Lentelės „{table}“ aprašas ilgesnis nei 50 simbolių!")
                    table_comment = re.sub(r"\(.*?\)", "", table_comment).strip()  # trumpinti šalinant tai, kas tarp ()
                table_comment_html = '    <TD ALIGN="LEFT"><FONT POINT-SIZE="16" COLOR="blue">'
                table_comment_html += f'{table_comment}</FONT></TD>' + nt2
        # Įrašų (eilučių) skaičius
        table_n_records_html = ""  # Laikina reikšmė
        df_tbl1_n_records = df_tbl1.select("n_records").to_series() if "n_records" in df_tbl1.columns else None
        if df_tbl1_n_records is not None and not df_tbl1_n_records.is_empty():
            table_n_records = df_tbl1_n_records[0]
            if table_n_records is not None:
                table_n_records_html = '    <TD ALIGN="RIGHT" COLOR="blue"><FONT POINT-SIZE="16">'
                table_n_records_html += f' N={table_n_records}</FONT></TD>' + nt2
        # Lentelės aprašas ir eilučių skaičius vienoje eilutėje
        if table_comment_html or table_n_records_html:
            dot += '<TR><TD><TABLE BORDER="0"><TR>' + nt2
            dot += f'{table_comment_html}{table_n_records_html}</TR></TABLE></TD></TR>' + nt2

        # Lentelės stulpeliai
        prim_keys = []  # Pirminių stulpelių sąrašas reikalingas dar iki nuoseklaus visų stulpelių perėjimo
        df_col1 = df_col.filter(pl.col("table") == table)  # atsirinkti tik šios lentelės stulpelius
        if "column" in df_col1.columns:
            df_col1 = df_col1.drop_nulls(subset=["column"])

            # Rasti pirminius raktus
            if (not df_col1.is_empty()) and ("is_primary" in df_col1.columns):
                prim_keys = df_col1.filter(
                    pl.when(
                        pl.col("is_primary").is_null() |
                        pl.col("is_primary").cast(pl.Utf8).str.to_lowercase().is_in(
                            ["false", "no", "ne", "0", ""]
                        )
                    )
                    .then(pl.lit(False))
                    .otherwise(pl.lit(True))
                )["column"].to_list()
        if df_col1.is_empty() or ("column" not in df_col1.columns) or (not show_all_columns):
            # A) PDSA aprašuose lentelės nėra, bet galbūt stulpeliai minimi yra ryšiuose?
            # B) Naudotojas prašė rodyti tik ryšių turinčius stulpelius (show_all_columns=False)
            col1_n1 = df_col1.height  # dabartinis tikrinamos lentelės eilučių (įrašų) skaičius
            row_more = {col: "..." if (col == "column") else None for col in df_col1.columns} # Eilutė „...“ kaip žyma, kad stulpelių yra daugiau nei matoma
            if (not df_edges.is_empty()) and (table in (df_edges["source_tbl"].to_list() + df_edges["target_tbl"].to_list())):
                # Imti ryšiuose minimus lentelių stulpelius
                if show_all_columns:
                    # visi stulpeliai, minimi ryšiuose (net jeigu jungtys nematomos)
                    edges_t_src = set(df_edges.filter(pl.col("source_tbl") == table)["source_col"].to_list())
                    edges_t_trg = set(df_edges.filter(pl.col("target_tbl") == table)["target_col"].to_list())
                else:
                    # tik stulpeliai, turintys matomų ryšių dabartiniame grafike arba yra pirminiai raktai
                    edges_t_src = set(df_edges.filter(
                            (pl.col("source_tbl") == table) & (pl.col("target_tbl").is_in(nodes))
                        )["source_col"].to_list())
                    edges_t_trg = set(df_edges.filter(
                            (pl.col("target_tbl") == table) & (pl.col("source_tbl").is_in(nodes))
                        )["target_col"].to_list())
                    # Pirmiausia ties edges_t_trg sudėti tuos, kurie yra raktiniai, net jei neturi ryšių
                    edges_t_trg = prim_keys + [c for c in edges_t_trg if c is not None and (c not in prim_keys)]

                # Jei kartais stulpelis yra None - praleisti
                # Paprastai taip būna, jei naudotojas nenurodė, kuriame ryšių XLSX/CSV stulpelyje yra DB lentelių stulpeliai
                edges_t_trg = [c for c in edges_t_trg if c is not None]
                # Įeinančių ryšių turinčiuosius išvardinti pirmiausia
                edges_t = edges_t_trg + [c for c in edges_t_src if c is not None and (c not in edges_t_trg)]
                if df_col1.is_empty() or ("column" not in df_col1.columns):
                    # PDSA neturėjo duomenų
                    df_col1 = pl.DataFrame({"column": edges_t}, infer_schema_length=None)
                    if "comment" in df_col.columns:
                        df_col1 = df_col1.with_columns(pl.lit(None).alias("comment"))
                else:
                    df_col1 = df_col1.filter(pl.col("column").is_in(edges_t))
                    col1_n2 = df_col1.height
                    if col1_n1 > col1_n2:
                        df_col1 = df_col1.vstack(pl.DataFrame([row_more], infer_schema_length=None))
            elif prim_keys:
                # Yra pirminių raktų, bet ryšių nėra - rodyti tik raktus
                df_col1 = df_col1.filter(pl.col("column").is_in(prim_keys))
                col1_n2 = df_col1.height
                if col1_n1 > col1_n2:
                    df_col1 = df_col1.vstack(pl.DataFrame([row_more], infer_schema_length=None))
            elif col1_n1 and (not show_all_columns):
                # Nors stulpelių yra, bet nėra jungčių, o naudotojas prašė rodyti tik turinčius ryšių.
                df_col1 = pl.DataFrame([row_more], infer_schema_length=None)  # Uždėti tik žymą, kad eilučių yra, bet pačių stulpelių neberodys

        if (not df_col1.is_empty()) and ("column" in df_col1.columns):
            # Pirmiausia rodyti tuos, kurie yra raktiniai
            if "is_primary" in df_col1.columns:
                df_col1 = df_col1.sort(by="is_primary", descending=True, nulls_last=True)
            hr_added = False  # Linija tarp antraštės ir stulpelių dar nepridėta
            for row in df_col1.iter_rows(named=True):
                col = row["column"]
                if col is None:
                    continue
                elif not hr_added:
                    dot += f"<HR></HR>" + nt2  # Linija tarp antraštės ir stulpelių
                    hr_added = True
                dot += f'<TR><TD PORT="{san(col)}" ALIGN="LEFT" BORDER="1" COLOR="lightgray"><TABLE BORDER="0"><TR>' + nt2
                column_str = f"{san(col)}".strip()
                if (
                    ("is_primary" in row) and row["is_primary"] and
                    row["is_primary"] is not None and str(row["is_primary"]).upper() != "FALSE"
                ):
                    column_str += " 🔑"
                dot += f'    <TD ALIGN="LEFT"><FONT POINT-SIZE="16">{column_str}</FONT></TD>' + nt2
                if show_descriptions and ("comment" in row) and san(row["comment"]).strip():
                    col_label = san(row["comment"]).strip()
                    if len(f"{col_label}") > 30 and "(" in col_label:
                        # warnings.warn(f"Lentelės „{table}“ stulpelio „{col}“ aprašas ilgesnis nei 30 simbolių!")
                        col_label = re.sub(r"\(.*?\)", "", col_label).strip()  # trumpinti šalinant tai, kas tarp ()
                    dot += f'    <TD ALIGN="RIGHT"><FONT COLOR="blue"> {col_label}</FONT></TD>' + nt2
                dot += f'</TR></TABLE></TD></TR>' + nt2
        dot += "</TABLE>>]\n" + nt1  # uždaryti sintaksę

    # Sintaksė jungtims
    if not df_edges.is_empty():
        df_edges = df_edges.unique()
        refs = df_edges.rows()
        for ref_from_table, ref_from_column, ref_to_table, ref_to_column in refs:

            # Jei lentelė rodo į save, o stulpeliai nenurodyti, tokio ryšio nepiešti
            if (ref_from_table == ref_to_table) and not (ref_from_column or ref_to_column):
                continue

            # Jei yra ta pati jungtis atvirkščia kryptimi, tai piešti iš jų tik vieną
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


def remove_orphaned_nodes_from_sublist(nodes_sublist, df_edges):
    """
    Pašalinti mazgus, kurie neturi tarpusavio ryšių su išvardintaisiais
    :param nodes_sublist: pasirinktų mazgų poaibio sąrašas
    :param df_edges: ryšių poros, surašytais polars.DataFrame su "source_tbl" ir "target_tbl" stulpeliuose
    :return: tik tarpusavyje tiesioginių ryšių turinčių mazgų sąrašas
    """
    df_edges = pl.DataFrame(df_edges, infer_schema_length=None)
    # Filter df_edges to include only rows where both source_tbl and target_tbl are in selected_items
    filtered_edges = df_edges.filter(
        pl.col("source_tbl").is_in(nodes_sublist) &
        pl.col("target_tbl").is_in(nodes_sublist)
    )
    # Create a set of inter-related items
    inter_related_items = set(filtered_edges["source_tbl"]).union(set(filtered_edges["target_tbl"]))
    # Filter the selected items to keep only those that are inter-related
    filtered_items = [item for item in nodes_sublist if item in inter_related_items]
    return filtered_items


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
