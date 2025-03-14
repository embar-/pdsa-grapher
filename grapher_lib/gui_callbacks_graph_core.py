"""
PDSA grapher Dash app common callbacks in "Graphic" tab.
"""
"""
(c) 2023-2024 Lukas Vasionis
(c) 2025 Mindaugas B.

This code is distributed under the MIT License. For more details, see the LICENSE file in the project root.
"""

import polars as pl
from dash import Output, Input, State, callback, callback_context, dash_table
from grapher_lib import utils as gu
import fnmatch

# ========================================
# Interaktyvumai grafiko kortelėje
# ========================================

@callback(
    Output("filter-tbl-in-df", "options"),  # išskleidžiamojo sąrašo pasirinkimai
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    config_prevent_initial_callbacks=True,
)
def set_dropdown_tables_for_selected_table_cols_info(data_submitted):
    """
    Informacija apie pasirinktų lentelių stulpelius - išskleidžiamasis sąrašas
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :return: visų galimų lentelių sąrašas
    """
    if data_submitted:
        # Lentelės iš PDSA, gali apimti rodinius ir nebūtinai turinčios ryšių
        return data_submitted["node_data"]["list_all_tables"]
    else:
        return []


@callback(
    Output("dropdown-tables", "options"),  # galimos pasirinkti braižymui lentelės
    Output("dropdown-tables", "value"),  # automatiškai braižymui parinktos lentelės (iki 10)
    Output("graph-info", "children"),  # paaiškinimas
    State("memory-selected-tables", "data"),  # senos braižymui pažymėtos lentelės
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-no-records", "value"),
    # tik kaip paleidikliai įkeliant lenteles:
    Input("draw-tables-refs", "n_clicks"),  # Susijungiančios pagal ryšių dokumentą
    Input("draw-tables-pdsa", "n_clicks"),  # Pagal PDSA lentelių lakštą
    Input("draw-tables-common", "n_clicks"),  # Pagal PDSA lentelių lakštą, kurios turi ryšių
    Input("draw-tables-all", "n_clicks"),  # Visos visos
    Input("draw-tables-auto", "n_clicks"),  # Automatiškai parinkti
    config_prevent_initial_callbacks=True,
)
def set_dropdown_tables_for_graph(
    old_tables, data_submitted, pdsa_tbl_records, pdsa_tbl_exclude_empty,
    *args,  # noqa
):
    """
    Nustatyti galimus pasirinkimus braižytinoms lentelėms.
    :param old_tables: sąrašas senų braižymui pažymėtų lentelių
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data"), žr. f-ją `summarize_submission`
    :param pdsa_tbl_records: PDSA lakšte, aprašančiame lenteles, stulpelis su eilučių (įrašų) skaičiumi
    :param pdsa_tbl_exclude_empty: ar išmesti PDSA lentelių lakšto lenteles, kuriose nėra įrašų
    :return: "dropdown-tables" galimų pasirinkimų sąrašas ir iš anksto parinktos reikšmės
    """
    # Tikrinimas
    if not data_submitted:
        info_msg = [
            _("You cannot select any table yet."), " ",
            _("Please go to the 'File upload' tab, upload the PDSA and/or references document, and select the desired data!")
        ]
        return [], [], info_msg
    info_msg = []

    # Galimos lentelės
    tables_pdsa_real = data_submitted["node_data"]["list_tbl_tables"]  # tikros lentelės iš PDSA lakšto, aprašančio lenteles
    tables_pdsa = data_submitted["node_data"]["list_all_tables"]  # lyginant su pdsa_tbl_tables, papildomai gali turėti rodinių (views) lenteles
    tables_refs = data_submitted["edge_data"]["list_all_tables"]  # lentelės, kurios panaudotos ryšiuose

    # Šalintinos lentelės
    if pdsa_tbl_records and pdsa_tbl_exclude_empty:
        tables_excludable = data_submitted["node_data"]["list_tbl_tables_empty"]
        tables_pdsa_real = list(set(tables_pdsa_real) - set(tables_excludable))
        tables_pdsa = list(set(tables_pdsa) - set(tables_excludable))
        tables_refs = list(set(tables_refs) - set(tables_excludable))
    else:
        tables_excludable = []

    # Visų visų lentelių sąrašas - tiek iš PDSA, tiek iš ryšių dokumento
    tables_all = sorted(list(set(tables_pdsa) | set(tables_refs)))
    tables_pdsa_refs_intersect = list(set(tables_pdsa_real) & set(tables_refs))

    # Ryšiai
    df_edges = pl.DataFrame(data_submitted["edge_data"]["ref_sheet_data"], infer_schema_length=None)
    if df_edges.height == 0:  # jei nėra eilučių, nėra ir reikalingų stulpelių struktūros
        df_edges = pl.DataFrame(schema={
            "source_tbl": pl.Utf8, "source_col": pl.Utf8, "target_tbl": pl.Utf8, "target_col": pl.Utf8
        })

    # Sužinoti, kuris mygtukas buvo paspaustas, pvz., „Pateikti“, „Braižyti visas“ (jei paspaustas)
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]

    # Pagal naudotojo pasirinkimą arba automatiškai žymėti lenteles piešimui.
    # Atsižvelgimas į naudotojo pasirinkimus turi būti išdėstytas aukščiau nei automatiniai
    preselected_tables = []  # Numatyta laikina tuščia reikšmė išvedimui
    if "draw-tables-all" in changed_id:
        # visos visos lentelės
        preselected_tables = tables_all
    elif "draw-tables-pdsa" in changed_id:
        # braižyti visas, PDSA apibrėžtas lentelių lakšte (gali neįtraukti rodinių)
        preselected_tables = tables_pdsa_real
    elif "draw-tables-common" in changed_id:
        # braižyti tas iš apibrėžtų PDSA lentelių lakšte (gali neįtraukti rodinių), kurios turi ryšių
        preselected_tables = tables_pdsa_refs_intersect
    elif (
        old_tables and any((t in tables_pdsa_real) for t in old_tables) and
        ("draw-tables-refs" not in changed_id) and ("draw-tables-auto" not in changed_id)
    ):
        # Palikti naudotojo anksčiau pasirinktas lenteles, nes jos tebėra kaip buvusios; nėra iškviesta nustatyti naujas
        preselected_tables = list(set(old_tables) & set(tables_pdsa_real))
    elif (
        ("draw-tables-refs" in changed_id) or
        ((len(tables_refs) <= 10) and df_edges.height) # jei iš viso ryšius turinčių lentelių iki 10
    ):
        # susijungiančios lentelės. Netinka imti tiesiog `tables_refs`, nes tarp jų gali būti nuorodos į save
        df_edges2 = df_edges.filter(pl.col("source_tbl") != pl.col("target_tbl"))
        preselected_tables = pl.concat([df_edges2["source_tbl"], df_edges2["target_tbl"]]).unique().to_list()
        preselected_tables = list(set(preselected_tables) - set(tables_excludable))
    elif tables_pdsa_real and len(tables_pdsa_real) <= 10:  # jei iš viso PDSA lentelių iki 10
        # braižyti visas, apibrėžtas lentelių lakšte (gali neįtraukti rodinių)
        preselected_tables = tables_pdsa_real
    elif df_edges.is_empty():
        # Nėra ryšių
        if tables_pdsa_real:
            df_tbl = pl.DataFrame(data_submitted["node_data"]["tbl_sheet_data"], infer_schema_length=None)
            if df_tbl.height > 0:

                if data_submitted["node_data"]["tbl_sheet_renamed_cols"]["n_records"]:
                    # Daugiausia įrašų turinčios lentelės
                    list_tbl_tables_empty = data_submitted["node_data"]["list_tbl_tables_empty"]
                    df_tbl_flt = df_tbl.filter(~pl.col("table").is_in(list_tbl_tables_empty))
                    if df_tbl_flt.height > 0:
                        df_tbl_flt = df_tbl_flt.sort("n_records", descending=True)
                        preselected_tables = df_tbl_flt.head(10)["table"].to_list()

                if not preselected_tables:
                    # Bent komentarus turinčios lentelės
                    df_tbl_flt = df_tbl.filter(pl.col("comment").is_not_null())
                    if df_tbl_flt.height <= 10:
                        preselected_tables = df_tbl_flt["table"].to_list()

    elif tables_pdsa_real and tables_refs and len(tables_pdsa_refs_intersect) <= 10:
        # Susijungiančios ir turinčios ryšių, iki 10
        preselected_tables = gu.remove_orphaned_nodes_from_sublist(tables_pdsa_refs_intersect, df_edges)
    else:
        # iki 10 populiariausių lentelių tarpusavio ryšiuose; nebūtinai tarpusavyje susijungiančios
        # ryšių su lentele dažnis mažėjančia tvarka
        df_edges_tbl = df_edges[["source_tbl", "target_tbl"]].unique()  # tik lentelės, be stulpelių
        df_edges_tbl = df_edges_tbl.filter(pl.col("source_tbl") != pl.col("target_tbl"))  # neskaičiuoti ryšių į save
        df_edges_tbl_ = pl.concat([df_edges_tbl["source_tbl"], df_edges_tbl["target_tbl"]]).alias("table")
        table_links_n = df_edges_tbl_.value_counts(sort=True, name="n")
        if tables_pdsa_refs_intersect:  # Jei yra bendrų ryšių ir PDSA lentelių
            # Atrinkti tik lenteles, esančias abiejuose dokumentuose: tiek PDSA, tiek ryšių
            table_links_n = table_links_n.filter(pl.col("table").is_in(tables_pdsa_refs_intersect))
        if tables_excludable:
            # Neįtraukti šalintinų lentelių
            table_links_n = table_links_n.filter(~pl.col("table").is_in(tables_excludable))
        if table_links_n["n"][9] < table_links_n["n"][10]:
            preselected_tables = table_links_n["table"][:10].to_list()
        else:
            table_links_n_threshold = table_links_n["n"][9] + 1
            preselected_tables = table_links_n.filter(pl.col("n") >= table_links_n_threshold)["table"].to_list()
        # Pašalinti mazgus, kurie neturi tarpusavio ryšių su parinktaisiais
        preselected_tables = gu.remove_orphaned_nodes_from_sublist(preselected_tables, df_edges_tbl)
        if not preselected_tables:  # jei netyčia nei vienas tarpusavyje nesijungia, imti du su daugiausia kt. ryšių
            preselected_tables = table_links_n["table"][:2].to_list()

    preselected_tables = sorted(preselected_tables)  # aukščiau galėjo būti nerikiuotos; rikiuoti abėcėliškai

    triggers = [
        "draw-tables-refs.n_clicks", "draw-tables-pdsa.n_clicks", "draw-tables-common.n_clicks",
        "draw-tables-all.n_clicks", "draw-tables-auto.n_clicks"
    ]
    if not tables_all:
        info_msg = [
            _("You cannot select any table yet."), " ",
            _("Please go to the 'File upload' tab, upload the PDSA and/or references document, and select the desired data!")
        ]
    elif not preselected_tables:
        info_msg = [
            _("No tables were automatically preselected to be displayed in the graph."), " ",
            _("You can select tables here.")
        ]
    elif (len(preselected_tables) < len(tables_all)) and (changed_id not in triggers):
        info_msg = [
            _("Some tables are not displayed in the graph."), " ",
            _("You can select tables here.")
        ]

    # Perduoti duomenis naudojimui grafiko kortelėje, bet likti pirmoje kortelėje
    return tables_all, preselected_tables, info_msg


@callback(
    Output("memory-filtered-data", "data"),
    Output("memory-selected-tables", "data"),  # pasirinktos lentelės, bet be kaimynų
    Output("depicted-tables-info", "children"),
    Input("tabs-container", "active_tab"),
    Input("memory-submitted-data", "data"),  # žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    Input("dropdown-tables", "value"),
    Input("input-list-tables", "value"),
    Input("checkbox-get-neighbours", "value"),
    Input("dropdown-neighbors", "value"),
    Input("pdsa-tables-records", "value"),
    Input("checkbox-tables-no-records", "value"),
    config_prevent_initial_callbacks=True,
)
def get_filtered_data_for_network(
    active_tab, data_submitted, selected_dropdown_tables, input_list_tables,
    get_neighbours, neighbours_type, pdsa_tbl_records, pdsa_tbl_exclude_empty
):
    """
    Gauna visas pasirinktas lenteles kaip tinklo mazgus su jungtimis ir įrašo į atmintį.
    :param active_tab: aktyvi kortelė ("file_upload" arba "graph")
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param selected_dropdown_tables: išskleidžiamajame sąraše pasirinktos braižytinos lentelės
    :param input_list_tables: tekstiniame lauke surašytos papildomos braižytinos lentelės
    :param get_neighbours: ar rodyti kaimynus
    :param neighbours_type: kaimynystės tipas: "all" (visi), "source" (iš), "target" (į)
    :param pdsa_tbl_records: PDSA lakšte, aprašančiame lenteles, stulpelis su eilučių (įrašų) skaičiumi
    :param pdsa_tbl_exclude_empty: ar išmesti PDSA lentelių lakšto lenteles, kuriose nėra įrašų
    """
    if (
        (not data_submitted) or  # apskritai nėra įkeltų duomenų
        (active_tab != "graph")  # esame kitoje nei grafiko kortelėje
    ):
        depicted_tables_msg = _("%d of %d") % (0, 0)
        return {}, [], depicted_tables_msg

    # Visos galimos lentelės
    tables_pdsa = data_submitted["node_data"]["list_all_tables"]
    tables_refs = data_submitted["edge_data"]["list_all_tables"]
    tables_all = list(set(tables_pdsa) | set(tables_refs))

    # Šalintinos lentelės. Jų negalėjo pasirinkti, bet jas čia reikės šalinti ir iš kaimynų
    if pdsa_tbl_records and pdsa_tbl_exclude_empty:
        tables_excludable = data_submitted["node_data"]["list_tbl_tables_empty"]
    else:
        tables_excludable = []
    tables_not_excluded_n = len(tables_all) - len(tables_excludable)

    if not selected_dropdown_tables and not input_list_tables:  # įkelti, bet nepasirinkti
        # Nieko nepasirinkta
        depicted_tables_msg = _("%d of %d") % (0, tables_not_excluded_n)
        return {}, [], depicted_tables_msg

    # Imti lenteles, kurias pasirinko išskleidžiamame meniu
    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Prijungti lenteles, kurias įraše sąraše tekstiniu pavidalu. Nepaisyti raidžių dydžio
    if input_list_tables is not None:
        tables_all_lc = {t.lower(): t for t in tables_all}
        input_list_tables = [
            tables_all_lc[t_lower]
            for x in input_list_tables.split(",")
            for t_lower in tables_all_lc
            if fnmatch.fnmatch(t_lower, x.strip().lower())  # palaikomi pakaitos simboliai kaip *, ?
        ]
        selected_tables = list(set(selected_dropdown_tables + input_list_tables))
    else:
        selected_tables = selected_dropdown_tables

    # Ryšiai
    submitted_edge_data = data_submitted["edge_data"]["ref_sheet_data"]

    # Priklausomai nuo langelio „Rodyti kaimynus“/„Get neighbours“
    if not get_neighbours:
        # Langelis „Rodyti kaimynus“/„Get neighbours“ nenuspaustas, tad
        # atrenkami tik tie ryšiai, kurie viename ar kitame gale turi bent vieną iš pasirinktų lentelių
        neighbors = []
        selected_tables_and_neighbors = selected_tables
        df_edges = [
            x
            for x in submitted_edge_data
            if x["source_tbl"] in selected_tables
            and x["target_tbl"] in selected_tables
        ]
        df_edges = pl.DataFrame(df_edges, infer_schema_length=None)

    else:
        # Langelis „Rodyti kaimynus“/„Get neighbours“ nuspaustas,

        # Pirminė ryšių atranka, kuri reikalinga kaimynų radimui; pvz., A>B, A>C ras ryšį, bet praleis B>C.
        # tik žinodami kaimynus vėliau iš naujo ieškosime ryšių, nes ryšių galėjo būti tarp pačių kaimynų
        if neighbours_type == "source":
            # turime target, bet papildomai rodyti source
            df_edges = [
                x
                for x in submitted_edge_data
                if x["target_tbl"] in selected_tables
            ]
        elif neighbours_type == "target":
            # turime source, bet papildomai rodyti target
            df_edges = [
                x
                for x in submitted_edge_data
                if x["source_tbl"] in selected_tables
            ]
        else:  # visi kaimynai
            df_edges = [
                x
                for x in submitted_edge_data
                if x["source_tbl"] in selected_tables
                or x["target_tbl"] in selected_tables
            ]
        df_edges = pl.DataFrame(df_edges, infer_schema_length=None)

        if df_edges.height == 0:
            neighbors = []
            selected_tables_and_neighbors = selected_tables
        else:
            selected_tables_and_neighbors = list(
                set(selected_tables) | set(  # naudotojo nurodytos lentelės turi likti
                    set(  # kaimyninės lentelės
                        df_edges["source_tbl"].unique().to_list() +
                        df_edges["target_tbl"].unique().to_list()
                    ) - set(tables_excludable)  # kaimynuose negali būti šalintinų lentelių
                )
            )
            neighbors = list(set(selected_tables_and_neighbors) - set(selected_tables))

        # Ryšius atsirenkame iš naujo, nes jungčių galėjo būti tarp pačių kaimynų,
        # pvz., jei iš pradžių turėjome A>B ir A>C, tai dabar jau ras ir B>C.
        df_edges = [
            x
            for x in submitted_edge_data
            if  x["source_tbl"] in selected_tables_and_neighbors
            and x["target_tbl"] in selected_tables_and_neighbors
        ]
        df_edges = pl.DataFrame(df_edges, infer_schema_length=None)

    depicted_tables_msg = _("%d of %d") % (len(selected_tables_and_neighbors), tables_not_excluded_n)
    if not selected_tables_and_neighbors:
        return {}, [], depicted_tables_msg

    if df_edges.height == 0:
        df_edges = pl.DataFrame(schema={
            "source_tbl": pl.Utf8, "source_col": pl.Utf8, "target_tbl": pl.Utf8, "target_col": pl.Utf8
        })
    return {
        "node_elements": selected_tables_and_neighbors,
        "node_neighbors": neighbors,
        "edge_elements": df_edges.to_dicts(),  # df būtina paversti į žodyno/JSON tipą, antraip Dash nulūš
    }, selected_tables, depicted_tables_msg


@callback(
    Output("clipboard-filter-tbl-in-df", "content"),  # tekstas iškarpinei
    State("filter-tbl-in-df", "value"),
    Input("clipboard-filter-tbl-in-df", "n_clicks"),  # kopijavimo mygtuko paspaudimai
    config_prevent_initial_callbacks=True,
)
def copy_selected_tables_to_clipboard(selected_dropdown_tables, n_clicks):  # noqa
    """
    Nustatyti tekstą, kurį imtų "clipboard-filter-tbl-in-df" į iškarpinę.
    Tačiau kad tekstas tikrai atsidurtų iškarpinėje, turi būti iš tiesų paspaustas "clipboard-filter-tbl-in-df"
    (vien programinis "clipboard-filter-tbl-in-df":"content" pakeitimas nepadėtų) -
    tik tuomet būtų nukopijuotas sąrašas lentelių, apie kurias naudotojas pasirinko žiūrinėti lentelių stulpelių info.
    :param selected_dropdown_tables: išskleidžiamajame sąraše naudotojo pasirinktos lentelės
    :param n_clicks:  tik kaip paleidiklis, reikšmė nenaudojama
    :return: naudotojo pasirinktų lentelių sąrašas kaip tekstas
    """
    if not selected_dropdown_tables:
        return ""
    return ", ".join(selected_dropdown_tables)


@callback(
    Output("table-selected-tables", "children"),
    Input("memory-submitted-data", "data"),
    Input("filter-tbl-in-df", "value"),
    Input("memory-viz-clicked-checkbox", "data"),
    config_prevent_initial_callbacks=True,
)
def create_dash_table_about_selected_table_cols(data_submitted, selected_dropdown_tables, viz_selection_dict):
    """
    Parodo lentelę su informacija apie stulpelius iš PDSA lakšto „columns“ priklausomai nuo naudotojo pasirinkimo
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param selected_dropdown_tables: išskleidžiamajame sąraše naudotojo pasirinktos lentelės
    :param viz_selection_dict: Visų sužymėtų langelių simboliai žodyne,
        kur pirmasis lygis yra lentelės, antrasis – stulpeliai, pvz:
        {
            "Skaitytojas": {"ID": "⬜"},
            "Rezervacija": {"ClientID": "🟩", "BookCopyID": "🟥"}}
        }
    :return: dash_table objektas
    """
    if not (data_submitted and selected_dropdown_tables):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["col_sheet_data_orig"]
    df_col = pl.DataFrame(data_about_nodes, infer_schema_length=None)

    if type(selected_dropdown_tables) == str:
        selected_dropdown_tables = [selected_dropdown_tables]

    # Jei prašoma rodyti informaciją apie pasirinktų lentelių stulpelius
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if changed_id in ["filter-tbl-in-df.value", "memory-viz-clicked-checkbox.data"]:
        tables_col = data_submitted["node_data"]["col_sheet_renamed_cols"]["table"]
        if tables_col in df_col.columns:
            df_col = df_col.filter(pl.col(tables_col).is_in(selected_dropdown_tables))

            # Papildomai prijungti Viz langelių nuspalvinimus
            columns_col = data_submitted["node_data"]["col_sheet_renamed_cols"]["column"]
            if viz_selection_dict and columns_col:
                df_checkbox = gu.convert_nested_dict2df(viz_selection_dict, [tables_col, columns_col, "⬜"])
                df_col = df_col.join(df_checkbox, on=[tables_col, columns_col], how="left")

            dash_tbl = dash_table.DataTable(
                data=df_col.to_dicts(),
                columns=[{"name": i, "id": i} for i in df_col.columns],
                sort_action="native",
                filter_action="native",
                filter_options={"case": "insensitive", "placeholder_text": _("Filter...")},
                style_table={
                    "overflowX": "auto"  # jei lentelė netelpa, galėti ją slinkti
                },
                page_size=50,
            )
            return dash_tbl
    return dash_table.DataTable()


@callback(
    Output("table-displayed-nodes", "children"),
    Input("memory-submitted-data", "data"),
    Input("memory-filtered-data", "data"),
    Input("checkbox-get-displayed-nodes-info-to-table", "value"),
    config_prevent_initial_callbacks=True,
)
def create_dash_table_about_displayed_tables(data_submitted, filtered_elements, get_displayed_nodes_info):
    """
    Informacija apie grafike rodomas lenteles iš PDSA lakšto „tables“

    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param filtered_elements: žodynas {
        "node_elements": [],  # mazgai (įskaitant mazgus)
        "node_neighbors": []  # kaimyninių mazgų sąrašas
        "edge_elements": df  # ryšių lentelė
        }
    :param get_displayed_nodes_info: ar pateikti nubraižytų lentelių informaciją
    :return: dash_table objektas
    """

    if (not data_submitted) or (not filtered_elements):
        return dash_table.DataTable()
    data_about_nodes = data_submitted["node_data"]["tbl_sheet_data_orig"]
    df_tbl = pl.DataFrame(data_about_nodes, infer_schema_length=None)
    col = data_submitted["node_data"]["tbl_sheet_renamed_cols"]["table"]
    if get_displayed_nodes_info and (col in df_tbl):
        # tinklo mazgai turi raktą "id" ir "label", bet jungimo linijos jų neturi (jos turi tik "source" ir "target")
        displayed_nodes = filtered_elements["node_elements"]
        df_tbl = df_tbl.filter(pl.col(col).is_in(displayed_nodes))

        dash_tbl = dash_table.DataTable(
            data=df_tbl.to_dicts(),
            columns=[{"name": i, "id": i} for i in df_tbl.columns],
            sort_action="native",
            filter_action="native",
            filter_options={"case": "insensitive", "placeholder_text": _("Filter...")},
            page_size=50,
        )
        return dash_tbl
    else:
        return dash_table.DataTable()


@callback(
    Output("graph-tab-pdsa-info-tables", "style"),
    Input("pdsa-tables-table", "value"),
    Input("memory-submitted-data", "data"),
    State("graph-tab-pdsa-info-tables", "style"),
    config_prevent_initial_callbacks=True,
)
def change_pdsa_tables_info_visibility(pdsa_tbl_table, data_submitted, div_style):
    """
    Informacijos, pateikiamos lentelėje po grafiku, apie pasirinktų lentelių stulpelius matomumas
    :param pdsa_tbl_table: PDSA lentelių lakšto stulpelis, kuriame nurodyti lentelių vardai
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param div_style: html.Div stiliaus žodynas
    :return: pakeistas "style" žodynas.
    """
    visibility = pdsa_tbl_table and data_submitted and data_submitted["node_data"]["tbl_sheet_data_orig"]
    return gu.change_style_display_value(visibility, div_style)


@callback(
    Output("graph-tab-pdsa-info-columns", "style"),
    Input("pdsa-columns-table", "value"),
    Input("memory-submitted-data", "data"),
    State("graph-tab-pdsa-info-columns", "style"),
    config_prevent_initial_callbacks=True,
)
def change_pdsa_columns_info_visibility(pdsa_col_table, data_submitted, div_style):
    """
    Informacijos, pateikiamos lentelėje po grafiku, apie nubraižytas lenteles matomumas
    :param pdsa_col_table: PDSA stulpelių lakšto stulpelis, kuriame nurodyti lentelių vardai
    :param data_submitted: žodynas su PDSA ("node_data") ir ryšių ("edge_data") duomenimis
    :param div_style: html.Div stiliaus žodynas
    :return: pakeistas "style" žodynas.
    """
    visibility = pdsa_col_table and data_submitted and data_submitted["node_data"]["col_sheet_data_orig"]
    return gu.change_style_display_value(visibility, div_style)
