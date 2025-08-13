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
import unicodedata
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
        table_id = txt(table)
        df_tbl1 = df_tbl.filter(pl.col("table") == table)  # visi dabartinės lentelės duomenys

        # Lentelės vardas, fono spalva
        background = ' BGCOLOR="lightgray"' if table in neighbors else ""
        dot += f'"{table_id}" [id="{table_id}"' + nt2  # id nebūtinas, tik kad SVG node vadintųsi vardu vietoj „node1“
        dot += f'label=<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0"{background}>' + nt2
        dot += f'<TR><TD PORT=" "><FONT POINT-SIZE="20"><B>{table_id}</B></FONT></TD></TR>' + nt2

        # Lentelės paaiškinimas
        table_comment_html = ""  # Laikina reikšmė
        if show_descriptions and ("comment" in df_tbl1.columns):
            if df_tbl1.height == 1:
                table_comment = df_tbl1["comment"][0]
            else:
                # Jei naudotojas tyčia (skirtingos schemos turi vienodai besivadinančių lentelių)
                # ar per klaidą (sumaišęs lakštus) pasirinko taip, kad lentelė turi kelis aprašymus, juos sujungti tam,
                # kad vizualiai matytųsi, jog kažkas ne taip, juolab kad nebus galimybės atskirti susijusius stulpelius.
                # Kita vertus, gali būti naudojamas vienas ir tas pats lakštas lentelėms ir stulpeliams, nepaisyti tuščių
                table_comments_list = df_tbl1["comment"].drop_nulls().to_list()
                table_comments_list = [txt(comment1, 90) for comment1 in table_comments_list]
                table_comment = " | ".join(table_comments_list)
            table_comment = f"{txt(table_comment, 100)}".strip()
            if table_comment:
                table_comment_html = '    <TD ALIGN="LEFT"><FONT POINT-SIZE="16" COLOR="blue">'
                table_comment_html += f'{table_comment}</FONT></TD>' + nt2
        # Įrašų (eilučių) skaičius
        table_n_records_html = ""  # Laikina reikšmė
        if "n_records" in df_tbl1.columns:
            df_tbl1_n_records = df_tbl1["n_records"]
            if df_tbl1.height == 1:
                table_n_records = df_tbl1_n_records[0]
            else:
                # Paprastai taip neturėtų būti. Bet parodyti, kad yra daug reikšmių tam, kad naudotojas pats tikrintų
                table_n_records_list = df_tbl1_n_records.drop_nulls().unique().to_list()
                table_n_records_list = [txt(x, 10) for x in table_n_records_list]
                if len(table_n_records_list) > 2:
                    table_n_records_list = table_n_records_list[:2] + ["…"]
                table_n_records = " | ".join(table_n_records_list)
            if table_n_records not in [None, ""]:  # Bet jei table_n_records būtų False kaip loginė reikšmė – vykdyti
                table_n_records_html = '    <TD ALIGN="RIGHT" COLOR="blue"><FONT POINT-SIZE="16">'
                table_n_prefix = "N=" if (df_tbl1_n_records.dtype not in [pl.Boolean, pl.String]) else ""
                table_n_records_html += f' {table_n_prefix}{table_n_records}</FONT></TD>' + nt2
        # Lentelės aprašas ir eilučių skaičius vienoje eilutėje
        if table_comment_html or table_n_records_html:
            dot += '<TR><TD><TABLE BORDER="0"><TR>' + nt2
            dot += f'{table_comment_html}{table_n_records_html}</TR></TABLE></TD></TR>' + nt2


        # %% Lentelės stulpeliai
        # Apjungti PSDA minimus pasirinktos lentelės stulpelius su ryšiuose minimais pasirinktos lentelės stulpeliais
        df_col1 = merge_pdsa_and_refs_columns(
            df_col, df_edges, table=table, tables_in_context=nodes, get_all_columns=show_all_columns
        )

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
                if ("alias" in df_col1.columns) and row["alias"]:
                    column_str = f'{txt(row["alias"])}'.strip()
                else:
                    column_str = f"{col_id}".strip()
                if (
                    ("is_primary" in row) and row["is_primary"] and
                    (str(row["is_primary"]).upper() != "FALSE")
                ):
                    column_str += " 🔑"
                if show_checkbox:
                    checkbox_symb = convert2checkbox(row["checkbox"]) if ("checkbox" in row) else "⬜"
                    checkbox_html = f'<FONT POINT-SIZE="16">{checkbox_symb}</FONT>'
                    # SVG kūrimo pradžioje "⬜" yra siauresnis nei spalvotieji langeliai (matyt Viz.js bėda), tad pridėti tarpą.
                    # Universalumo prasme, pridėti tarpą visiems neplatiems spalvotiems simboliams, kuriuos naudotojas bepateiktų.
                    checkbox_html += "" if checkbox_symb in ["🟩", "🟨", "🟥", "🟦"] else " "
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


def merge_pdsa_and_refs_columns(df_col, df_edges, table, get_all_columns=True, tables_in_context=None):
    """
    Apjungti PSDA minimus pasirinktos lentelės stulpelius su ryšiuose minimais pasirinktos lentelės stulpeliais.
    :param df_col: polars.DataFrame su stulpelių duomenimis; būtinas "column" stulpelis, kiti stulpeliai nebūtini:
        "table", "is_primary", "checkbox".
    :param df_edges: polars.DataFrame su stulpeliais "source_tbl", "source_col", "target_tbl", "target_col"
    :param table: vardas lentelės, kuriai priklauso stulpeliai
    :param get_all_columns: ar grąžinti visus lentelės stulpelius (numatyta True);
                            ar tik pirminius raktus ir turinčius ryšių (False)
    :param tables_in_context: sąrašas su mazgų/lentelių pavadinimais, kurie tikrintini ryšiuose
    :return: DOT sintaksės tekstas
    """
    if not isinstance(df_col, pl.DataFrame):
        df_col = pl.DataFrame(df_col, infer_schema_length=None)
    if not isinstance(df_edges, pl.DataFrame):
        df_edges = pl.DataFrame(df_edges, infer_schema_length=None)

    if ("table" in df_col.columns) and (df_col["table"].dtype == pl.String):
        df_col1 = df_col.filter(pl.col("table") == table)  # atsirinkti tik pasirinktos lentelės stulpelius
    else:
        df_col1 = df_col
        # Jei PDSA neįkeltas, o įkelta tik ryšių lentelė, dirbtinai sukurti "table" stulpelį
        # To prireiks grąžinant į copy_displayed_nodes_metadata_to_clipboard()
        # Visada privalo būti String tipo (jei tuščias, galėjo būti Null tipo!), nes vardai g.b. papildomi pg. ryšius
        df_col1.with_columns(pl.lit(table).cast(pl.String).alias("table"))
    checked_boxes = []  # Stulpeliai, kurie nuspalvinti "checkbox" stulpelyje

    # Pirminiai raktai
    prim_keys = []  # Pirminių stulpelių sąrašas reikalingas dar iki nuoseklaus visų stulpelių perėjimo
    if "column" in df_col1.columns:
        # Visada privalo būti String tipo (jei tuščias, galėjo būti Null tipo!)
        df_col1 = df_col1.with_columns(pl.col("column").cast(pl.String))

        # Atrinkti netuščius
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
                checked_boxes = filter_df_by_checkbox(df_col1)["column"].to_list()

    # Lentelės stulpelių keitimas pagal aplinkybes
    col1_n1 = df_col1.height  # dabartinis tikrinamos lentelės eilučių (įrašų) skaičius sutikrinimui, ar visus rodome
    hide_some_columns = False  # False reikšmė liks kai show_all_columns=True ir tik retais show_all_columns=False atvejais
    if (not df_edges.is_empty()) and (table in (df_edges["source_tbl"].to_list() + df_edges["target_tbl"].to_list())):
        # Imti ryšiuose minimus lentelių stulpelius
        if get_all_columns or (tables_in_context is None):
            # visi stulpeliai, minimi ryšiuose (net jeigu jungtys nematomos)
            edges_t_src = set(df_edges.filter(pl.col("source_tbl") == table)["source_col"].to_list())
            edges_t_trg = set(df_edges.filter(pl.col("target_tbl") == table)["target_col"].to_list())
        else:
            # tik stulpeliai, turintys matomų ryšių dabartiniame grafike arba yra pirminiai raktai
            edges_t_src = set(df_edges.filter(
                (pl.col("source_tbl") == table) & (pl.col("target_tbl").is_in(tables_in_context))
            )["source_col"].to_list())
            edges_t_trg = set(df_edges.filter(
                (pl.col("target_tbl") == table) & (pl.col("source_tbl").is_in(tables_in_context))
            )["target_col"].to_list())
            # Pirmiausia ties edges_t_trg sudėti tuos, kurie yra raktiniai, net jei neturi ryšių
            edges_t_trg = prim_keys + [c for c in edges_t_trg if c is not None and (c not in prim_keys)]

        # Jei kartais stulpelis yra None - praleisti
        # Paprastai taip būna, jei naudotojas nenurodė, kuriame ryšių XLSX/CSV stulpelyje yra DB lentelių stulpeliai
        edges_t_trg = [c for c in edges_t_trg if c is not None]
        # Įeinančių ryšių turinčiuosius išvardinti pirmiausia
        edges_t = edges_t_trg + [c for c in edges_t_src if (c is not None) and (c not in edges_t_trg)]

        # Rodyti stulpelius, kurie nuspalvinti "checkbox" stulpelyje
        edges_t = edges_t + [c for c in checked_boxes if c not in edges_t]

        # Raidžių dydis Graphviz DOT sintaksėje nurodant ryšius nėra svarbus
        if df_col1.height and ("column" in df_col1.columns):
            col1_columns_lowercase = [item.lower() for item in df_col1["column"].to_list()]
        else:
            col1_columns_lowercase = []
        # Pridėti stulpelius, kurie yra minimi ryšiuose, bet nėra df_col1 lentelėje.
        missing_cols = [col for col in edges_t if col.lower() not in col1_columns_lowercase]
        if missing_cols:
            df_col1_missing = pl.DataFrame({"column": missing_cols}, schema={"column": pl.String})
            df_col1_missing = df_col1_missing.with_columns(pl.lit(table).alias("table"))
            df_col1 = pl.concat([df_col1, df_col1_missing], how="diagonal_relaxed")
            col1_n1 += len(missing_cols)  # kad papildyti stulpeliai vėliau nesutrukdytų uždėti "…" lentelės apačioje

        if df_col1.is_empty() or ("column" not in df_col1.columns):
            # PDSA neturėjo duomenų
            df_col1 = pl.DataFrame({"column": edges_t}, schema={"column": pl.String})
            if "comment" in df_col.columns:
                df_col1 = df_col1.with_columns(pl.lit(None).alias("comment"))
        elif not get_all_columns:
            # Raidžių dydis Graphviz DOT sintaksėje nurodant ryšius nėra svarbus
            edges_t_lower = [edge.lower() for edge in edges_t]
            df_col1 = df_col1.filter(pl.col("column").str.to_lowercase().is_in(edges_t_lower))
            col1_n2 = df_col1.height
            if col1_n1 > col1_n2:
                hide_some_columns = True
    elif (prim_keys or checked_boxes) and (not get_all_columns):
        # Yra pirminių raktų arba nuspalvintųjų, bet ryšių nėra - rodyti tik raktus ir nuspalvintuosius
        df_col1 = df_col1.filter(pl.col("column").is_in(prim_keys + checked_boxes))
        col1_n2 = df_col1.height
        if col1_n1 > col1_n2:
            hide_some_columns = True
    elif col1_n1 and (not get_all_columns):
        # Nors stulpelių yra, bet nėra jungčių, pirminių raktų ar nuspalvintųjų, o naudotojas neprašė rodyti visus stulpelius.
        df_col1 = pl.DataFrame(schema=df_col1.schema)  # pačių stulpelių neberodys
        hide_some_columns = True
    if (not df_col1.is_empty()) and ("is_primary" in df_col1.columns) and df_col1["is_primary"].is_not_null().any():
        # Perrikiuoti aukščiausiai iškeliant tuos, kurie yra raktiniai.
        df_col1 = df_col1.sort(by="is_primary", descending=True, nulls_last=True)
    if hide_some_columns:
        # Pridedama „…“ žyma, kad stulpelių yra daugiau nei matoma
        row_more = {"column": "…", "table": table}
        df_row_more = pl.DataFrame([row_more], schema={"column": pl.String, "table": pl.String})
        df_col1 = pl.concat([df_col1, df_row_more], how="diagonal_relaxed")
    return df_col1


def convert2checkbox(x):
    """
    Konvertuoja bet kokią pavienę reikšmę į spalvotą langelį.
    Toks langelis automatiškai būtų interpretuojamas kaip žymimasis langelis naudojant renderPdsaDotViaViz.js
    :param x: bet kokia reikšmė, įskaitant None, teksto eilutę, skaičių, loginę reikšmę (True ar False).
    :return: "⬜", "🟩", "🟨" arba "🟥"
    """
    if x in [None, "", "⬜", "🔲", "☐"]:
        return "⬜"
    elif isinstance(x, str):
        if x in ["✅", "☑️", "☑", "🗹", "🟨", "🟩", "🟥", "🟦"]:
            return x  # palikti originalų
        elif x.lower() in ["false", "f", "no", "ne", "n", "0"]:
            return "🟥"
        elif x.lower() in ["true", "taip", "t", "yes", "y", "1"]:
            return "🟩"
        else:
            return "🟨"
    elif x:
        return "🟩"  # Greičiausiai True arba 1 kaip loginė reikšmė
    else:
        return "🟥"  # Greičiausiai False arba 0 kaip loginė reikšmė


def filter_df_by_checkbox(df, column="checkbox", include_unexpected=False):
    """
    Atrinkti lentelės eilutes pagal pasirinktame stulpelyje sužymėjimą spalvomis arba kitas logines, skaitines reikšmes.
    :param df: polars DataFrame arba duomenys lentelei sudaryti
    :param column: stulpelis, pagal kurį atrenkama (numatytasis yra "checkbox")
    :param include_unexpected: ar netikėtas reikšmes užskaityti kaip grąžintinas
    :return: polars DataFrame
    """
    df = pl.DataFrame(df, infer_schema_length=None)
    df = df.filter(
        pl.when(
            pl.col(column).is_null() |
            pl.col(column).cast(pl.Utf8).str.to_lowercase().is_in([
                "false", "f", "no", "ne", "n", "0", "",
                "⬜", "🔲", "☐",  # tušti langeliai
                "🟥"  # raudoni langeliai yra atmetimui
            ])
        ).then(pl.lit(False))
        .when(
            pl.col(column).cast(pl.Utf8).str.to_lowercase().is_in([
                "true", "taip", "t", "yes", "y", "1",
                "🟩", "✅", "☑️", "☑", "🗹"  # neabejotinai pasirinkti žalius ir pažymėtuosius varnele
            ])
        ).then(pl.lit(True))
        # paprastai kitų neturėtų būti, nebent įrašyta ranka į JSON arba iš naudotojo stulpelio
        .otherwise(pl.lit(include_unexpected))
    )
    return df


def filter_empty_df_columns(df):
    """
    Atsirinkti tik netuščius Polars DataFrame stulpelius: ne tik kurie nėra pl.Null tipo, bet ir neturi tuščių reikšmių.
    :param df: Polars DataFrame
    """
    empty_values = {None, ""}
    non_empty_columns = [
        col for col in df.columns
        if df[col].dtype != pl.Null and not empty_values.issuperset(df[col].unique().to_list())
    ]
    return df[non_empty_columns]


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
    :return: pl.DataFrame
    """
    if (not col_names) or len(col_names) != 3:
        warnings.warn("Please provide 3 column names as col_names")
        return pl.DataFrame()
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
        return {}
    elif not all([col in df.columns for col in col_names]):
        warnings.warn("Your provided 3 column names as col_names does not exist in df")
        return {}
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


def change_style_for_visibility(whether_set_visible, style_dict=None):
    """
    Dash objekto stilių žodyne pakeisti matomumo ("display") reikšmę.
    :param whether_set_visible: ar objektas turi būti matomas (True), ar nematomas (False).
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


def change_style_for_activity(whether_set_active, style_dict=None):
    """
    Dash objekto stilių žodyne pakeisti reikšmes, susijusias spalva ("color") ir jautrumu pelei ("pointer-events").
    :param whether_set_active: ar objektas turi būti rodomas kaip aktyvus (True), ar pilkas ir nereaguoti į pelę (False).
    :param style_dict: Dash objekto "style" kaip žodynas.
    :return: pakeistas "style" žodynas.
    """
    if not style_dict:
        style_dict = {}
    if whether_set_active:
        style_dict["pointerEvents"] = "auto"  # numatytasis pelės jautrumas paspaudimui
        style_dict["color"] = "unset"  # numatytoji spalva
    else:
        style_dict["pointerEvents"] = "none"  # negalima paspausti pele
        style_dict["color"] = "gray"  # pilkas
    return style_dict


def snake_case_short(string):
    """
    Funkcija panaši į snake_case(), tačiau su įjungta turinio šalinimo tarp skliaustų parinktimi ir
    papildomai sutrumpinami gale esantys žodžiai: „identifikatorius“, „numeris“, „skaičius“.
    Patogiau turėti kaip atskiras funkcijas polars stulpelių skirtingam apdorojimui išvengiant parametrų perdavimo.
    :param string: bet kokia teksto eilutė (angl. string)
    """
    string = snake_case(string, remove_content_in_brackets=True)

    # Papildomai pervadinti
    string = re.sub(r'(_identifikatorius|_identifier)$', '_id', string)
    string = re.sub(r'(_numeris|_number)$', '_nr', string)
    string = re.sub(r'_skaicius$', '_sk', string)
    return string


def snake_case(string, remove_content_in_brackets=False):
    """
    Supaprastinti teksto eilutę leidžiant tik mažąsias lotyniškas raides
    be diakritinių raidžių, skaitmenis ir apatinį brūkšnį (angl. snake case),
    po mažosios raidės einant didžiajai raidei įterpiamas „_“. Pvz.:
    "Lietuviškas užrašas (pastaba)" -> "lietuviskas_uzrasas",
    "VienoŽodžioUžrašas" -> "vieno_zodzio_uzrasas".

    Pagal poreikį pirmiausia atmetama tai, kas pasitaiko tarp skliaustų.

    :param string: bet kokia teksto eilutė (angl. string)
    :param remove_content_in_brackets: ar pašalinti turinį tarp () ir [] skliaustų
    """
    if string is None:
        return ""
    elif not isinstance(string, str):
        string = f"{string}"
    if remove_content_in_brackets:
        string = re.sub(r'\([^)]+\)', '', string)  # pašalinti viską tarp paprastų () skliaustų
        string = re.sub(r'\[[^]]+\]', '', string)  # noqa, pašalinti viską tarp laužtinių [] skliaustų
    string = unidecode(string)  # be diakritinių ženklų

    # _ įterpimas žodžių atskyrimui, kad nesusiplaktų viską vėliau pavertus mažosiomis raidėmis
    string = re.sub(r'[\s\-./]+', '_', string.strip())
    string = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', string)  # po mažosios arba skaičiaus prie didžiąją
    string = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', string)  # po kelių didžiųjų eina žodis

    # mažosiomis raidėmis, atrinkti tik lotyniškas raides ir skaičius
    string = re.sub(r'[^a-z0-9_]', '', string.lower())
    string = re.sub(r'_+', '_', string)  # jei šalia atsirado bent du „_“ greta - palikti tik vieną
    return string.strip('_')


def unidecode(string):
    """
    Pakeičia žodį su diakritiniais ženklais į šveplą (pvz., Čiuožėjas -> Ciuozejas):
    pirmiausia išskaido ženklus į sudėtinius (pvz., „Č“ į „C“ ir paukščiuką),
    po to pašalina ASCII koduotėje nesančius simbolius (pvz., paukščiukus, ilguosius brūkšnius).

    :param string: bet kokia teksto eilutė (angl. string)
    """
    return unicodedata.normalize("NFKD", string).encode('ascii', errors='ignore').decode('utf-8')
