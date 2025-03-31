"""
PDSA grapher Dash app callbacks in "File upload" tab for submitting PDSA and references data into "Graph" tab.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import (
    Output, Input, State, callback, callback_context, html
)
from grapher_lib import utils_file_upload as fu
from locale_utils.translations import pgettext


@callback(
    Output("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Output("button-submit", "color"),  # pateikimo mygtuko spalva
    Output("submit-error-message", "children"),  # pateikimo klaidos paaiškinimas
    Output("submit-warning-message", "children"),  # pateikimo įspėjimo paaiškinimas
    Output("tabs-container", "active_tab"),  # aktyvios kortelės identifikatorius (perjungimui, jei reikia)
    State("memory-uploaded-pdsa", "data"),  # žodynas su PDSA duomenimis, papildytas
    State("memory-uploaded-refs", "data"),  # žodynas su ryšių tarp lentelių duomenimis
    Input("radio-sheet-tbl", "value"),  # Naudotojo pasirinktas PDSA lentelių lakštas
    Input("pdsa-tables-table", "value"),
    Input("pdsa-tables-comment", "value"),
    Input("pdsa-tables-records", "value"),
    Input("pdsa-tables-selected", "value"),
    Input("dropdown-sheet-tbl", "value"),
    Input("radio-sheet-col", "value"),  # Naudotojo pasirinktas PDSA stulpelių lakštas
    Input("pdsa-columns-table", "value"),
    Input("pdsa-columns-column", "value"),
    Input("pdsa-columns-primary", "value"),
    Input("pdsa-columns-checkbox", "value"),
    Input("pdsa-columns-comment", "value"),
    Input("pdsa-columns-alias", "value"),
    Input("dropdown-sheet-col", "value"),
    Input("radio-sheet-refs", "value"),  # Pasirinktas ryšių lakštas
    Input("ref-source-tables", "value"),
    Input("ref-source-columns", "value"),
    Input("ref-target-tables", "value"),
    Input("ref-target-columns", "value"),
    State("tabs-container", "active_tab"),
    Input("button-submit", "n_clicks"),  # tik kaip f-jos paleidiklis paspaudžiant Pateikti
    config_prevent_initial_callbacks=True,
)
def summarize_submission(
    pdsa_file_data, refs_file_data,
    pdsa_tbl_sheet,
    pdsa_tbl_table, pdsa_tbl_comment, pdsa_tbl_records, pdsa_tbl_selected,
    dropdown_sheet_tbl,
    pdsa_col_sheet,
    pdsa_col_table, pdsa_col_column, pdsa_col_primary, pdsa_col_checkbox, pdsa_col_comment, pdsa_col_alias,
    dropdown_sheet_col,
    refs_sheet,
    ref_source_tbl, ref_source_col,
    ref_target_tbl, ref_target_col,
    active_tab,
    submit_clicks,  # noqa
):
    """
    Suformuoti visuminę naudingų duomenų struktūrą, jei turime visus reikalingus PDSA ir ryšių duomenis.
    :param pdsa_file_data: žodynas su PDSA duomenimis:
        "file_data" - žodynas su visu PDSA turiniu;
        "sheet_tbl" - PDSA lakšto, aprašančio lenteles, pavadinimas
        "sheet_col" - PDSA lakšto, aprašančio stulpelius, pavadinimas
    :param refs_file_data: žodynas su ryšių tarp lentelių duomenimis:
        "file_data" - žodynas su visu dokumento turiniu;
    :param pdsa_tbl_sheet: PDSA lakšto, aprašančio lenteles, vardas
    :param pdsa_tbl_table: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių vardais
    :param pdsa_tbl_comment: PDSA lakšte, aprašančiame lenteles, stulpelis su lentelių apibūdinimais
    :param pdsa_tbl_records: PDSA lakšte, aprašančiame lenteles, stulpelis su eilučių (įrašų) skaičiumi
    :param pdsa_tbl_selected: metaduomenų (paprastai ne PDSA) lakšte, aprašančiame lenteles, stulpelis su vertingumo žyma
    :param dropdown_sheet_tbl: sąrašas stulpelių, kurie yra pdsa_info["sheet_tbl"] (lentelių) lakšte
    :param pdsa_col_sheet: PDSA lakšto, aprašančio stulpelius, vardas
    :param pdsa_col_table: PDSA lakšte, aprašančiame stulpelius, stulpelis su lentelių vardais
    :param pdsa_col_column: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių vardais
    :param pdsa_col_primary: PDSA lakšte, aprašančiame stulpelius, stulpelis su požymiu, ar stulpelis yra pirminis raktas
    :param pdsa_col_checkbox: virtualiame PDSA lakšte, aprašančiame lenteles, stulpelis su vertingumo žyma ar
        spalvotų langelių simboliais; įprastas PDSA tokio stulpelio neturi,
        bet juos turi eksportuoti ir vėliau vėl importuoti JSON; naudingas tik braižant su Viz varikliu.
    :param pdsa_col_comment: PDSA lakšte, aprašančiame stulpelius, stulpelis su stulpelių apibūdinimais
    :param pdsa_col_alias: virtualiame PDSA lakšte, aprašančiame stulpelius, stulpelis su alternatyviu vardu rodymui.
        PDSA lakšte tam atskiro stulpelio nebūna, nebent naudotojas pridėjo rankiniu būdu; gali sutapti su pdsa_col_column.
    :param dropdown_sheet_col: sąrašas stulpelių, kurie yra pdsa_info["sheet_col"] (stulpelių) lakšte
    :param refs_sheet: pasirinktas ryšių lakštas
    :param ref_source_tbl: vardas stulpelio, kuriame surašytos ryšio pradžių („IŠ“) lentelės (su išoriniu raktu)
    :param ref_source_col: vardas stulpelio, kuriame surašyti ryšio pradžių („IŠ“) stulpeliai (su išoriniu raktu)
    :param ref_target_tbl: vardas stulpelio, kuriame surašytos ryšio galų („Į“) lentelės (su pirminiu raktu)
    :param ref_target_col: vardas stulpelio, kuriame surašyti ryšio galų („Į“) stulpeliai (su pirminiu raktu)
    :param submit_clicks: mygtuko „Pateikti“ paspaudimų skaičius, bet pati reikšmė nenaudojama
    :param active_tab: aktyvi kortelė "file_upload" arba "graph"
    :return: visų pagrindinių duomenų struktūra, pateikimo mygtuko spalva, paaiškinimai naudotojui, aktyvi kortelė.

    visų naudingų duomenų struktūros pavyzdys:
        data_final = {
            "node_data": {  # Mazgų duomenys iš PDSA
                "tbl_sheet_data_orig": [],  # PDSA lakšto, aprašančio lenteles, turinys su originaliais stulpeliais
                "col_sheet_data_orig": [],  # PDSA lakšto, aprašančio stulpelius, turinys su originaliais stulpeliais
                "tbl_sheet_data": [],  # PDSA lakšto, aprašančio lenteles, turinys su pervadintais stulpeliais
                "col_sheet_data": [],  # PDSA lakšto, aprašančio stulpelius, turinys su pervadintais stulpeliais
                "tbl_sheet_renamed_cols": {},  # PDSA lakšte, aprašančiame lenteles, stulpelių vidiniai pervadinimai
                "col_sheet_renamed_cols": {},  # PDSA lakšte, aprašančiame stulpelius, stulpelių vidiniai pervadinimai
                "sheet_tbl": "",  # PDSA lakšto, aprašančio lenteles, pavadinimas
                "sheet_col": "",  # PDSA lakšto, aprašančio stulpelius, pavadinimas
                "list_tbl_tables": [],  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
                "list_tbl_tables_empty": [],  # tuščios lentelės iš PDSA lakšto, aprašančio lenteles (n_records=0)
                "list_col_tables": [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
                "list_all_tables": [],  # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
            },
            "edge_data":{  # Ryšiai
                "ref_sheet_data": [],  # Ryšių lakšto turinys
                "ref_sheet_name": "",  # Ryšių lakšto vardas
                "ref_source_tbl":"",  # vardas stulpelio, kuriame surašytos ryšio pradžių („IŠ“) lentelės (su išoriniu raktu)
                "ref_source_col": "",  # vardas stulpelio, kuriame surašyti ryšio pradžių („IŠ“) stulpeliai (su išoriniu raktu)
                "ref_target_tbl":"",  # vardas stulpelio, kuriame surašytos ryšio galų („Į“) lentelės (su pirminiu raktu)
                "ref_target_col": "",  # vardas stulpelio, kuriame surašyti ryšio galų („Į“) stulpeliai (su pirminiu raktu)
                "list_all_tables": [],  # tos lentelės, kurios panaudotos ryšiuose
            }}
    """

    # Tikrinimai
    err_msg = []  # Klaidų sąrašas, rodomas po „Pateikimo“ mygtuku raudonai
    wrn_msg = []  # Įspėjimų sąrašas, rodomas po „Pateikimo“ mygtuku rudai
    if (not refs_file_data) and (not pdsa_file_data):
        err_msg.append(html.P(_("Please select PDSA and/or references document!")))
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    if pdsa_file_data:
        if None in [pdsa_tbl_sheet, pdsa_col_sheet]:
            err_msg.append(html.P(_("Please select PDSA document sheets!")))
    else:
        wrn_msg.append(html.P(_("Please select PDSA document and its sheets!")))
    if refs_file_data:
        if refs_sheet:
            if None in [ref_source_tbl, ref_target_tbl]:
                if refs_file_data["file_data"][refs_sheet]["df"]:
                    err_msg.append(html.P(_("Please select references columns that contain tables!")))
            elif ref_source_tbl == ref_target_tbl:
                err_msg.append(html.P(_("Reference columns for source and target tables are the same!")))
        else:
            err_msg.append(html.P(_("Please select references document sheet!")))
    else:
        wrn_msg.append(html.P(_("Please select references document!")))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    if pdsa_col_sheet and pdsa_tbl_sheet == pdsa_col_sheet:
        wrn_msg.append(html.P(_("PDSA sheets for tables and columns are the same!")))
    pre_msg = _("Enhance analysis by selecting from the sheet defining the %s (%s), the column describing the %s.")

    # %% Surinktą informaciją transformuoju ir paruošiu graferiui

    # PDSA lakšto (pdsa_tbl_sheet), aprašančio LENTELES, turinys
    df_tbl = pdsa_file_data["file_data"][pdsa_tbl_sheet]["df"] if pdsa_tbl_sheet else {}
    df_tbl = pl.DataFrame(df_tbl, infer_schema_length=None)
    list_tbl_tables_empty = []  # Tuščių lentelių (t.y. su n_records=0) kintamasis;
    dropdown_sheet_tbl = dropdown_sheet_tbl or []
    if df_tbl.height == 0:
        if pdsa_tbl_sheet:
            msg = _("PDSA sheet describing %s (%s) has no data.")
            msg = msg % (pgettext("PDSA sheet describing...", "tables"), pdsa_tbl_sheet)
            wrn_msg.append(html.P(msg))
        df_tbl_orig = df_tbl  # Tuščias df
        pdsa_tbl_tables = []
    else:
        if not pdsa_tbl_table:
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "tables"),  # lenteles
                pdsa_tbl_sheet,
                pgettext("pdsa column for", "tables")  # ... nurodysite stulpelį, kuriame yra lentelės.
            )
            wrn_msg.append(html.P(msg))
        elif dropdown_sheet_tbl and (pdsa_tbl_table not in dropdown_sheet_tbl):
            dropdown_sheet_tbl = [pdsa_tbl_table] + dropdown_sheet_tbl  # lentelės vardas privalomas
        df_tbl_orig = df_tbl[dropdown_sheet_tbl].clone()
        # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui
        selected_tbl_columns = [pdsa_tbl_table, pdsa_tbl_comment, pdsa_tbl_records, pdsa_tbl_selected]
        internal_tbl_columns = ["table", "comment", "n_records", "selected"]
        df_tbl = fu.select_renamed_or_add_columns(df_tbl, selected_tbl_columns, internal_tbl_columns)
        if pdsa_tbl_records:
            # Rasti lenteles, kuriose eilučių skaičius yra 0 (bet palikti jei jų yra None).
            # Tačiau vėliau gali kilti painiavos vėlesniuose įspėjimuose, pvz., neva nėra apibrėžtų kai kurių lentelių
            n_records_dtype = df_tbl.schema["n_records"]
            numeric_polars_dtypes = [
                pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Int128, pl.Decimal,
                pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64
            ]
            if  n_records_dtype in numeric_polars_dtypes:
                list_tbl_tables_empty = df_tbl.filter(pl.col("n_records") == 0)["table"].to_list()
            elif n_records_dtype == pl.Utf8:  # pl.String
                list_tbl_tables_empty = df_tbl.filter(pl.col("n_records") == "0")["table"].to_list()
            else:
                msg = _("In the PDSA sheet '%s', the column '%s' has unexpected dtype '%s'!")
                msg = msg % (pdsa_tbl_sheet, pdsa_tbl_records, n_records_dtype)
                wrn_msg.append(html.P(msg))
        pdsa_tbl_tables = df_tbl["table"].drop_nulls().to_list()
        pdsa_tbl_tables = sorted(list(set(pdsa_tbl_tables)))
        if pdsa_tbl_table and (not pdsa_tbl_tables):
            warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (pdsa_tbl_sheet, pdsa_tbl_table)
            wrn_msg.append(html.P(warning_str))
        if not all([isinstance(x, str) for x in pdsa_tbl_tables]):
            error_str = _("In the PDSA sheet '%s', the column '%s' some values are not strings!")
            error_str = error_str  % (pdsa_tbl_sheet, pdsa_tbl_table)
            err_msg.append(html.P(error_str))
            return {}, "secondary", err_msg, wrn_msg, "file_upload"
    # Prisiminti naudotojo pasirinktas lentelių lakšto stulpelių sąsajas; bet tai nereiškia, kad tie stulpeliai iš tiesų yra!
    tbl_sheet_renamed_cols = {
        "table": pdsa_tbl_table,
        "comment": pdsa_tbl_comment,
        "n_records": pdsa_tbl_records,
        "selected": pdsa_tbl_selected
    }

    # PDSA lakšto (pdsa_col_sheet), aprašančio STULPELIUS, turinys
    df_col = pdsa_file_data["file_data"][pdsa_col_sheet]["df"] if pdsa_col_sheet else {}
    df_col = pl.DataFrame(df_col, infer_schema_length=None)
    dropdown_sheet_col = dropdown_sheet_col or []
    if df_col.height == 0:
        if pdsa_col_sheet:
            msg = _("PDSA sheet describing %s (%s) has no data.")
            msg = msg % (pgettext("PDSA sheet describing...", "columns"), pdsa_col_sheet)
            wrn_msg.append(html.P(msg))
        df_col_orig = df_col  # Tuščias df
        pdsa_col_tables = None  # Tyčia ne [], kad būtų galima atskirti vėlesniame etape
        pdsa_col_checkbox = None
    else:
        if dropdown_sheet_col:
            # lentelės ir stulpelio vardas privalomi
            if pdsa_col_column and (pdsa_col_column not in dropdown_sheet_col):
                dropdown_sheet_col = [pdsa_col_column] + dropdown_sheet_col
            if pdsa_col_table and (pdsa_col_table not in dropdown_sheet_col):
                dropdown_sheet_col = [pdsa_col_table] + dropdown_sheet_col
        df_col_orig = df_col[dropdown_sheet_col].clone()
        # Persivadinti standartiniais PDSA stulpelių vardais vidiniam naudojimui
        selected_col_columns = [
            pdsa_col_table, pdsa_col_column, pdsa_col_primary, pdsa_col_comment, pdsa_col_checkbox, pdsa_col_alias
        ]
        internal_col_columns = ["table", "column", "is_primary", "comment", "checkbox", "alias"]
        df_col = fu.select_renamed_or_add_columns(df_col, selected_col_columns, internal_col_columns)
        if pdsa_col_table:
            pdsa_col_tables = df_col["table"].drop_nulls().unique().sort().to_list()
            if not pdsa_col_tables:
                warning_str = _("In the PDSA sheet '%s', the column '%s' is empty!") % (pdsa_col_sheet, pdsa_col_table)
                wrn_msg.append(html.P(warning_str))
            if not all([isinstance(x, str) for x in pdsa_col_tables]):
                error_str = _("In the PDSA sheet '%s', the column '%s' some values are not strings!")
                error_str = error_str  % (pdsa_col_sheet, pdsa_col_table)
                err_msg.append(html.P(error_str))
                return {}, "secondary", err_msg, wrn_msg, "file_upload"
        else:
            pdsa_col_tables = None
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "columns"),  # stulpelius
                pdsa_col_sheet,
                pgettext("pdsa column for", "tables")  # ... nurodysite stulpelį, kuriame yra lentelės.
            )
            wrn_msg.append(html.P(msg))
        if not pdsa_col_column:
            msg = pre_msg % (  # Analizė bus naudingesnė, jei lakšte, aprašančiame ...
                pgettext("PDSA sheet describing...", "columns"),  # stulpelius
                pdsa_col_sheet,
                pgettext("pdsa column for", "columns")  # ... nurodysite stulpelį, kuriame yra stulpeliai.
            )
            wrn_msg.append(html.P(msg))
        elif df_col.schema["column"] != pl.Utf8:
            error_str = _("In the PDSA sheet '%s', the column '%s' values are not strings!")
            error_str = error_str % (pdsa_col_sheet, pdsa_col_column)
            err_msg.append(html.P(error_str))
            return {}, "secondary", err_msg, wrn_msg, "file_upload"
        elif pdsa_col_table:
            # Tikrinti, ar nėra besidubliuojančių stulpelių vardų toje pačioje lentelėje
            df_cols_dupl = fu.find_duplicates_in_group(df_col, "table", "column")
            if df_cols_dupl.height:
                df_cols_dupl_merged_names = df_cols_dupl.with_columns(
                    pl.concat_str([
                        pl.lit('"'), pl.col("table"), pl.lit('"."'), pl.col("column"), pl.lit('"')
                    ]).alias("merged")
                )
                duplicated_cols_list = df_cols_dupl_merged_names["merged"].drop_nulls().to_list()
                if duplicated_cols_list:
                    # Parinkti PDSA stulpeliai tikrai kartojasi toje pačioje lentelėje
                    warning_str = _("In the PDSA sheet '%s', the column '%s' values are not unique within '%s'!")
                    warning_str = warning_str % (pdsa_col_sheet, pdsa_col_column, pdsa_col_table)
                    warning_str += " " + ", ".join(duplicated_cols_list)
                    wrn_msg.append(html.P(warning_str))
    # Prisiminti naudotojo pasirinktas stulpelių lakšto stulpelių sąsajas; bet tai nereiškia, kad tie stulpeliai iš tiesų yra!
    col_sheet_renamed_cols = {
        "table": pdsa_col_table,
        "column": pdsa_col_column,
        "is_primary": pdsa_col_primary,
        "comment": pdsa_col_comment,
        "checkbox": pdsa_col_checkbox,
        "alias": pdsa_col_alias
    }

    # RYŠIAI
    df_edges = refs_file_data["file_data"][refs_sheet]["df"] if refs_file_data else {}
    df_edges = pl.DataFrame(df_edges, infer_schema_length=None)
    if refs_file_data and df_edges.height == 0:
        wrn_msg.append(html.P(_("There are no relationships between different tables!")))
    selected_refs_columns = [ref_source_tbl, ref_source_col, ref_target_tbl, ref_target_col]
    ref_cols_uniq = list(set(selected_refs_columns))  # unikalūs ryšių lakšto stulpeliai
    ref_cols_uniq = [c for c in ref_cols_uniq if c]  # netušti ryšių lakšto stulpeliai
    for ref_col in ref_cols_uniq:
        if (ref_col in df_edges.columns) and (df_edges.schema[ref_col] != pl.Utf8):
            error_str = _("In the references sheet '%s', the column '%s' values are not strings!")
            error_str = error_str % (refs_sheet, ref_col)
            err_msg.append(html.P(error_str))
    if err_msg:
        return {}, "secondary", err_msg, wrn_msg, "file_upload"
    # Pervadinti stulpelius į toliau viduje sistemiškai naudojamus
    internal_refs_columns = ["source_tbl", "source_col", "target_tbl", "target_col"]
    df_edges = fu.select_renamed_or_add_columns(df_edges, selected_refs_columns, internal_refs_columns)
    df_edges = df_edges.filter(~pl.all_horizontal(pl.all().is_null()))  # išmesti tuščias eilutes

    # Sutikrinimas tarp pdsa_tbl_sheet ir pdsa_col_sheet „table“ stulpelių
    if pdsa_tbl_table and pdsa_col_table and (pdsa_col_tables is not None):
        tables_diff = list(set(pdsa_tbl_tables) - (set(pdsa_col_tables) & set(pdsa_tbl_tables)))
        if tables_diff:
            # Smulkesniuose stulpelių aprašymuose kai kuriuose PDSA būna daugiau lentelių -
            # paprastai tai rodiniai (views) ir į šį įspėjimą galima nekreipti dėmesio
            # Be to dalis lentelių galėjo būti pašalinta ties `if pdsa_tbl_records and pdsa_tbl_exclude_empty`
            warning_str = _(
                "PDSA sheet '%s' column '%s' has some tables (%d in total) not present in sheet '%s' column '%s', but it's not a problem:"
            )
            warning_str = warning_str % (pdsa_tbl_sheet, pdsa_tbl_table, len(tables_diff), pdsa_col_sheet, pdsa_col_table)
            warning_str += " " + ", ".join(tables_diff) + "."
            wrn_msg.append(html.P(warning_str))

    # visos lentelės iš duombazės lentelių ir stulpelių lakštų aprašų
    pdsa_all_tables = sorted(list(set(pdsa_col_tables or []) | set(pdsa_tbl_tables)))

    # Visų unikalių lentelių, turinčių ryšių, sąrašas
    edge_source_tbl = df_edges["source_tbl"].drop_nulls().to_list()  # ryšių pradžių lentelės
    edge_target_tbl = df_edges["target_tbl"].drop_nulls().to_list()  # ryšių galų lentelės
    edge_tables = sorted(list(set(edge_source_tbl + edge_target_tbl)))
    edge_tables_extra = list(set(edge_tables) - set(pdsa_all_tables))
    if pdsa_tbl_table and pdsa_col_table and edge_tables_extra:
        # Įspėjimas gali klaidinti, jei dalis lentelių pašalinta ties `if pdsa_tbl_records and pdsa_tbl_exclude_empty`
        warning_str = _("References contain some tables (%d) that are not present in the defined tables:")
        warning_str = warning_str % len(edge_tables_extra)
        warning_str += " " + ", ".join(edge_tables_extra) + "."
        wrn_msg.append(html.P(warning_str))
        ## Lentelės, tik esančios PDSA dokumente:
        # df_edges = df_edges.loc[
        #            df_edges["source_tbl"].isin(pdsa_all_tables) & df_edges["target_tbl"].isin(pdsa_all_tables), :
        #            ]
    # Paprastai neturėtų būti pasikartojančių ryšių, nebent nebuvo nurodyti ryšių stulpeliai apie DB lentelės stulpelius
    df_edges = df_edges.unique()

    if (not edge_tables) and (not pdsa_all_tables):
        # Dokumentai įkelti, bet tušti
        err_msg.append(html.P(_("Your selected document sheet has no required data.")))
        return {}, "secondary", err_msg, wrn_msg, "file_upload"

    # %% VISĄ SURINKTĄ INFORMACIJĄ SUKELIU Į VIENĄ STRUKTŪRĄ
    data_final = {
        # Mazgų duomenys iš PDSA
        "node_data": {
            "file_name": pdsa_file_data["file_name"] if pdsa_file_data and ("file_name" in pdsa_file_data) else "",
            "tbl_sheet_data_orig": df_tbl_orig.to_dicts(),  # PDSA lakšto, aprašančio lenteles, originalus turinys
            "col_sheet_data_orig": df_col_orig.to_dicts(),  # PDSA lakšto, aprašančio stulpelius, originalus turinys
            "tbl_sheet_data": df_tbl.to_dicts(),  # PDSA lakšto, aprašančio lenteles, turinys pervadinus stulpelius
            "col_sheet_data": df_col.to_dicts(),  # PDSA lakšto, aprašančio stulpelius, turinys pervadinus stulpelius
            "tbl_sheet_renamed_cols": tbl_sheet_renamed_cols,  # PDSA lakšte, aprašančiame lenteles, stulpelių vidiniai pervadinimai
            "col_sheet_renamed_cols": col_sheet_renamed_cols,  # PDSA lakšte, aprašančiame stulpelius, stulpelių vidiniai pervadinimai
            "sheet_tbl": pdsa_tbl_sheet,  # PDSA lakšto, aprašančio lenteles, vardas
            "sheet_col": pdsa_col_sheet,  # PDSA lakšto, aprašančio stulpelius, vardas
            "list_tbl_tables": pdsa_tbl_tables,  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
            "list_tbl_tables_empty": list_tbl_tables_empty,  # tuščios lentelės iš PDSA lakšto, aprašančio lenteles
            "list_col_tables": pdsa_col_tables or [],  # lentelės iš PDSA lakšto, aprašančio stulpelius, gali būti papildyta rodiniais (views)
            "list_all_tables": pdsa_all_tables,  # visos iš PDSA kartu
        },
        # Ryšių duomenys
        "edge_data": {
            "file_name": refs_file_data["file_name"] if refs_file_data and ("file_name" in refs_file_data) else "",
            "ref_sheet_data": df_edges.to_dicts(),  # Ryšių lakšto turinys
            "ref_sheet_name": refs_sheet,      # ryšių lakšto vardas
            "ref_source_tbl": ref_source_tbl,  # stulpelis, kuriame pradžių („IŠ“) lentelės
            "ref_source_col": ref_source_col,  # stulpelis, kuriame pradžių („IŠ“) stulpeliai
            "ref_target_tbl": ref_target_tbl,  # stulpelis, kuriame galų („Į“) lentelės
            "ref_target_col": ref_target_col,  # stulpelis, kuriame galų („Į“) stulpeliai
            "list_all_tables": edge_tables,  # lentelės, kurios panaudotos ryšiuose
        }
    }

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    if "button-submit" in changed_id:  # Paspaustas „Pateikti“ mygtukas
        # Perduoti duomenis naudojimui grafiko kortelėje ir į ją pereiti
        active_tab = "graph"
    else:
        # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje.
        # active_tab gali neturėti reikšmės darbo pradžioje ar pakeitus kalbą. Tai padeda išlaikyti kortelę
        active_tab = active_tab or "file_upload"  # jei nėra, pereiti į rinkmenų įkėlimą;
    return data_final, "primary", err_msg, wrn_msg, active_tab
