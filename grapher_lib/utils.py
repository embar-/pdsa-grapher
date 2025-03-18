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
    layout="dot", show_all_columns=True, show_descriptions=True, show_checkbox=False
):
    """
    Sukurti Graphviz DOT sintaksę pagal pateiktus mazgų ir ryšių duomenis
    :param df_tbl: DataFrame su lentelių duomenimis
    :param df_col: DataFrame su stulpelių duomenimis
    :param nodes: sąrašas su mazgų pavadinimais
    :param neighbors: sąrašas su kaimyninių mazgų pavadinimais
    :param df_edges: polars.DataFrame su stulpeliais "source_tbl", "source_col", "target_tbl", "target_col"
    :param layout: Graphviz stilius - circo, dot, fdp, neato, osage, sfdp, twopi (patariame: dot arba fdp).
    :param show_all_columns: ar rodyti visus lentelės stulpelius (numatyta True); ar tik pirminius raktus ir turinčius ryšių (False)
    :param show_descriptions: ar rodyti lentelių ir stulpelių aprašus pačiame grafike (numatyta True)
    :param show_checkbox: ar prie stulpelių pridėti žymimuosius langelius (numatyta False)
    :return: DOT sintaksės tekstas
    """

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

    def txt(x, cut_length=0):
        """
        Konvertuoti bet kokią pateiktą reikšmę į tekstą naudojimui DOT sintaksėje.
        :param x: tekstas, skaičius arba None
        :param cut_length: dydis, nuo kurio ilgą tekstą nukirpti; jei 0 (numatyta), tuomet nekarpyti
        :return: tekstas be < ir >, tačiau ilgame tekste įterpta <BR/>
        """
        if x is None:
            return ""

        # DOT/HTML viduje negali būti < arba > tekste.
        x_str = f"{x}".replace('>', '&gt;').replace('<', '&lt;')

        # Ilgo teksto nukirpimas
        if cut_length and (len(x_str) > cut_length) and "(" in x_str:
            # trumpinti šalinant tai, kas tarp ()
            x_str = re.sub(r"\(.*?\)", "…", x_str).strip()
        if cut_length and (len(x_str) > cut_length):
            # trumpinti iki nurodyto ilgio, bet nenukerpant viduryje žodžio, tad ieškoti paskutinio tarpo
            last_space_index = x_str.rfind(' ', 0, cut_length)   # Rasti paskutinį tarpą iki 100-osios pozicijos
            if last_space_index == -1:
                last_space_index = cut_length  # Jei nėra tarpų, perkelti ties 100-ąja pozicija
            x_str = x_str[:last_space_index] + " …"

        return x_str

    # %% DOT sintaksės antraštė
    # Papildomai būtų galima pakeisti šriftą, nes numatytasis Times-Roman prastai žiūrisi mažuose paveiksluose.
    # Juose geriau būtų fontname=Verdana arba fontname=Arial, bet su pastaraisiais yra problemų dėl pločio neatitikimų
    dot = f"// Graphviz DOT sintaksė sukurta naudojant\n// https://github.com/embar-/pdsa-grapher\n\n"
    dot += "digraph {" + nt1
    dot += "// Kaip išdėstymą patariama rinktis dot arba fdp, bet galite rinktis ir kt." + nt1
    dot += "// layout: circo dot fdp neato osage sfdp twopi" + nt1
    dot += "// Tik dot išdėstymas palaiko rankdir parinktį." + nt1
    dot += f'graph [layout={layout} overlap=false rankdir="LR"]\n' + nt1
    dot += '// fontname="Times-Roman" yra numatytasis šriftas' + nt1
    dot += '// fontname="Verdana" tinka mažoms raidėms, bet kartais gali netikti plotis' + nt1
    dot += 'node [margin=0.3 shape=none fontname="Verdana"]' + nt1 + nt1

    # %% DOT sintaksė mazgams
    for table in nodes:
        # Lentelės vardas, fono spalva
        table_id = txt(table)
        background = ' BGCOLOR="lightgray"' if table in neighbors else ""
        dot += f'"{table_id}" [id="{table_id}"' + nt2  # id nebūtinas, tik kad SVG node vadintųsi vardu vietoj „node1“
        dot += f'label=<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0"{background}>' + nt2
        dot += f'<TR><TD PORT=" "><FONT POINT-SIZE="20"><B>{table_id}</B></FONT></TD></TR>' + nt2

        # Lentelės paaiškinimas
        table_comment_html = ""  # Laikina reikšmė
        df_tbl1 = df_tbl.filter(pl.col("table") == table)
        df_tbl1_comment = df_tbl1.select("comment").to_series() if "comment" in df_tbl1.columns else None
        if show_descriptions and (df_tbl1_comment is not None) and (not df_tbl1_comment.is_empty()):
            table_comment = df_tbl1_comment[0]
            if table_comment and table_comment is not None and f"{table_comment}".strip():
                table_comment = f"{txt(table_comment, 100)}".strip()
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


        # %% Lentelės stulpeliai
        # Pirminiai raktai
        prim_keys = []  # Pirminių stulpelių sąrašas reikalingas dar iki nuoseklaus visų stulpelių perėjimo
        checked_boxs = []  # Stulpeliai, kurie nuspalvinti "checkbox" stulpelyje
        df_col1 = df_col.filter(pl.col("table") == table)  # atsirinkti tik šios lentelės stulpelius
        if "column" in df_col1.columns:
            df_col1 = df_col1.drop_nulls(subset=["column"])
            if not df_col1.is_empty():

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

                # Rodyti stulpelius, kurie nuspalvinti "checkbox" stulpelyje
                if "checkbox" in df_col1.columns:
                    checked_boxs = df_col1.filter(
                        pl.when(
                            pl.col("checkbox").is_null() |
                            pl.col("checkbox").cast(pl.Utf8).str.to_lowercase().is_in([
                                "false", "no", "ne", "0", "",
                                "⬜", "🔲", "☐",  # tušti langeliai
                                "🟨", "🟥"  # geltoni ir raudoni langeliai yra tik papildomos spalvos
                            ])
                        ).then(pl.lit(False))
                        .when(
                            pl.col("checkbox").cast(pl.Utf8).str.to_lowercase().is_in([
                                "🟩", "✅", "☑", "🗹"  # neabejotinai rodyti žalius ir pažymėtuosius varnele
                            ])
                        ).then(pl.lit(True))
                        .otherwise(pl.lit(True))  # paprastai kitų neturėtų būti, nebent įrašyti ranka į JSON
                    )["column"].to_list()

        # Lentelės stulpelių keitimas pagal aplinkybes
        col1_n1 = df_col1.height  # dabartinis tikrinamos lentelės eilučių (įrašų) skaičius sutikrinimui, ar visus rodome
        hide_some_columns = False  # False reikšmė liks kai show_all_columns=True ir tik retais show_all_columns=False atvejais
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
            edges_t = edges_t_trg + [c for c in edges_t_src if (c is not None) and (c not in edges_t_trg)]

            # Rodyti stulpelius, kurie nuspalvinti "checkbox" stulpelyje
            edges_t = edges_t + [c for c in checked_boxs if c not in edges_t]

            # Raidžių dydis Graphviz DOT sintaksėje nurodant ryšius nėra svarbus
            if df_col1.height and ("column" in df_col1.columns):
                col1_columns_lowercase = [item.lower() for item in df_col1["column"].to_list()]
            else:
                col1_columns_lowercase = []
            # Pridėti stulpelius, kurie yra minimi ryšiuose, bet nėra df_col1 lentelėje.
            missing_cols = [col for col in edges_t if col.lower() not in col1_columns_lowercase]
            if missing_cols:
                missing_columns_dict = {
                    col: missing_cols if (col == "column")
                    else [None] * len(missing_cols)
                    for col in df_col1.columns
                }
                df_col1 = df_col1.vstack(pl.DataFrame(missing_columns_dict, infer_schema_length=None))
                col1_n1 += len(missing_cols)  # kad papildyti stulpeliai vėliau nesutrukdytų uždėti "…" lentelės apačioje

            if df_col1.is_empty() or ("column" not in df_col1.columns):
                # PDSA neturėjo duomenų
                df_col1 = pl.DataFrame({"column": edges_t}, infer_schema_length=None)
                if "comment" in df_col.columns:
                    df_col1 = df_col1.with_columns(pl.lit(None).alias("comment"))
            elif not show_all_columns:
                # Raidžių dydis Graphviz DOT sintaksėje nurodant ryšius nėra svarbus
                edges_t_lower = [edge.lower() for edge in edges_t]
                df_col1 = df_col1.filter(pl.col("column").str.to_lowercase().is_in(edges_t_lower))
                col1_n2 = df_col1.height
                if col1_n1 > col1_n2:
                    hide_some_columns = True
        elif (prim_keys or checked_boxs) and (not show_all_columns):
            # Yra pirminių raktų arba nuspalvintųjų, bet ryšių nėra - rodyti tik raktus ir nuspalvintuosius
            df_col1 = df_col1.filter(pl.col("column").is_in(prim_keys + checked_boxs))
            col1_n2 = df_col1.height
            if col1_n1 > col1_n2:
                hide_some_columns = True
        elif col1_n1 and (not show_all_columns):
            # Nors stulpelių yra, bet nėra jungčių, pirminių raktų ar nuspalvintųjų, o naudotojas neprašė rodyti visus stulpelius.
            df_col1 = pl.DataFrame(schema=df_col1.schema)  # pačių stulpelių neberodys
            hide_some_columns = True
        if (not df_col1.is_empty()) and ("is_primary" in df_col1.columns) and df_col1["is_primary"].is_not_null().any():
            # Perrikiuoti aukščiausiai iškeliant tuos, kurie yra raktiniai.
            df_col1 = df_col1.sort(by="is_primary", descending=True, nulls_last=True)
        if hide_some_columns:
            # Pridedama „…“ žyma, kad stulpelių yra daugiau nei matoma
            row_more = {
                col: "…" if (col == "column") else None
                for col in df_col1.columns
            }
            df_row_more = pl.DataFrame([row_more], infer_schema_length=None)
            df_col1 = df_col1.vstack(df_row_more)

        # DOT sintaksės stulpeliams sukūrimas
        if (not df_col1.is_empty()) and ("column" in df_col1.columns):
            hr_added = False  # Linija tarp antraštės ir stulpelių dar nepridėta
            for row in df_col1.iter_rows(named=True):
                col = row["column"]
                if col is None:
                    continue
                elif not hr_added:
                    dot += f"<HR></HR>" + nt2  # Linija tarp antraštės ir stulpelių
                    hr_added = True
                # PORT reikalingas DOT ryšių suvedimui, o ID ir TITLE - dėl patogumo identifikuoti stulpelius SVG brėžinyje
                col_id = txt(col)
                col_id2 = f"{table_id}:{col_id}"
                dot += f'<TR><TD ALIGN="LEFT" BORDER="1" COLOR="lightgray">' + nt2
                dot += f'<TABLE PORT="{col_id}" TITLE="{col_id2}" ID="{col_id2}" BORDER="0" CELLSPACING="0"><TR>' + nt2
                column_str = f"{col_id}".strip()
                if (
                    ("is_primary" in row) and row["is_primary"] and
                    row["is_primary"] is not None and str(row["is_primary"]).upper() != "FALSE"
                ):
                    column_str += " 🔑"
                if show_checkbox:
                    checkbox_symb = row["checkbox"] if ("checkbox" in row) and (row["checkbox"]) else "⬜"
                    checkbox_html = f'<FONT POINT-SIZE="16">{checkbox_symb}</FONT> '
                else:
                    checkbox_html = ""
                dot += (f'    <TD ALIGN="LEFT">{"" if col_id == "…" else checkbox_html}'
                        f'<FONT POINT-SIZE="16">{column_str}</FONT></TD>') + nt2
                if show_descriptions and ("comment" in row) and txt(row["comment"]).strip():
                    col_label = txt(row["comment"], cut_length=50).strip()
                    dot += f'    <TD ALIGN="RIGHT"><FONT COLOR="blue"> {col_label}</FONT></TD>' + nt2
                dot += f'</TR></TABLE></TD></TR>' + nt2
        dot += "</TABLE>>]\n" + nt1  # uždaryti sintaksę

    # %% DOT sintaksė jungtims
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
                ref_from = f'"{txt(ref_from_table)}":"{txt(ref_from_column)}"'
            else:
                ref_from = f'"{txt(ref_from_table)}":" "'
            if ref_to_column:
                ref_to = f'"{txt(ref_to_table)}":"{txt(ref_to_column)}"'
            else:
                ref_to =  f'"{txt(ref_to_table)}":" "'
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


def convert_nested_dict2df(nested_dict, col_names):
    """
    Konvertuoti dviejų lygių žodyną į polars dataframe
    :param nested_dict: dviejų lygių žodynas, pvz.,
        {
            "Skaitytojas": {"ID": "⬜"},
            "Rezervacija": {"ClientID": "🟩", "BookCopyID": "🟥"}}
        }
    :param col_names: trijų būsimų stulpelių vardų sąrašas
    :return:
    """
    if (not col_names) or len(col_names) != 3:
        warnings.warn("Please provide 3 column names as col_names")
        return
    if not nested_dict:
        return pl.DataFrame(schema={f"{key}": pl.Utf8 for key in col_names})
    key1, key2, key3 = col_names
    list_of_dicts = [
        {f"{key1}": val1, f"{key2}": val2, f"{key3}": val3}
        for val1, dct2 in nested_dict.items()
        for val2, val3 in dct2.items()
    ]
    return pl.DataFrame(list_of_dicts, infer_schema_length=None)


def convert_df2nested_dict(df, col_names):
    """
    Konvertuoti polars dataframe į dviejų lygių žodyną
    :param df: polars dataframe
    :param col_names: trijų stulpelių vardų sąrašas
    :return: dviejų lygių žodynas
    """
    df = pl.DataFrame(df, infer_schema_length=None)  # užtikrinti, kad tikrai turim polars df
    if (not col_names) and (len(df.columns) == 3):
        col_names = df.columns
    elif len(col_names) != 3:
        warnings.warn("Please provide 3 column names as col_names")
        return
    elif not all([col in df.columns for col in col_names]):
        warnings.warn("Your provided 3 column names as col_names does not exist in df")
        return
    key1, key2, key3 = col_names
    nested_dict = {}
    list_of_dicts = df.filter(pl.col(key3).is_not_null()).to_dicts()  # praleisti Null reikšmes

    for row in list_of_dicts:
        val1 = f"{row[key1]}"
        val2 = f"{row[key2]}"
        val3 = row[key3]
        if val1 not in nested_dict:
            nested_dict[val1] = {}
        nested_dict[val1][val2] = val3

    return nested_dict


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
