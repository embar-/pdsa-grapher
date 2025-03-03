"""
Pagalbinės funkcijos rinkmenų turinio analizavimui importuojant.

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

import polars as pl
import fastexcel  # noqa: būtina XLSX importavimui per polars
import base64
import io
import csv
import chardet
import json
import warnings
from pydbml import PyDBML


def parse_file(contents, list_of_names=None):
    """
    Įkelto dokumento duomenų gavimas.
    :param contents: XLSX, XLS, ODS, CSV, TSV, JSON, DBML turinys kaip base64 duomenys
    :param list_of_names: įkeltų rinkmenų vardų sąrašas.
    :return: nuskaitytos rinkmenos duomenų struktūra kaip žodynas XLSX atveju arba tekstas (string) klaidos atveju.
    Duomenų struktūros kaip žodyno pavyzdys:
        {
            "file_data":
                {"sheet_name_1":
                    {
                        "df_columns": [],      # visi stulpeliai
                        "df_columns_str": [],  # tik tekstinio tipo stulpeliai
                        "df": []
                    }
                },
        }
    """
    if not contents:
        return
    filename = list_of_names[0] if (list_of_names and isinstance(list_of_names, list)) else ""
    content_base64 = contents[0].split(",")[1]
    content_bytestring = base64.b64decode(content_base64)

    # Ar tai Excel .xls (\xD0\xCF\x11\xE0) arba .zip/.xlsx/.ods (PK\x03\x04)?
    is_excel = content_bytestring.startswith(b"\xD0\xCF\x11\xE0") or content_bytestring.startswith(b"PK\x03\x04")
    if is_excel:
        return parse_excel(content_bytestring)  # Bandyti nuskaityti tarsi Excel XLS, XLSX arba LibreOffice ODS
    elif not filename.lower().endswith((".json", ".csv", ".tsv", ".txt", ".dbml")):
        return _("Unsupported file format")  # Nepalaikomas formatas
    else:
        text_encoding = chardet.detect(content_bytestring)["encoding"]  # automatiškai nustatyti koduotę
        if not text_encoding:
            return _("Can not detect text encoding")
        content_text = content_bytestring.decode(text_encoding)  # Iškoduoti bitų eilutę į paprasto testo eilutę
        if filename.lower().endswith(".json"):
            return parse_json(content_text, filename[:-5])  # Bandyti nuskaityti tarsi JSON
        elif filename[-5:].lower() in [".dbml"]:
            return parse_dbml(content_text)  # Bandyti nuskaityti tarsi DBML
        elif filename[-4:].lower() in [".csv", ".tsv"]:
            return parse_csv(content_text, filename[:-4])  # Bandyti nuskaityti tarsi CSV
        else:
            # Bandyti paeiliui kaip JSON arba CSV
            json_parse_output = parse_json(content_text, filename)  # Bandyti nuskaityti tarsi JSON
            if isinstance(json_parse_output, dict):
                return json_parse_output
            else:
                return parse_csv(content_text)  # Bandyti nuskaityti tarsi CSV


def parse_excel(byte_string):
    """
    Pagalbinė `parse_file` funkcija skaičiuoklės dokumentų XLSX, XLS, ODS formatais nuskaitymui.

    :param byte_string: dokumento turinys (jau iškoduotas su base64.b64decode)
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """
    xlsx_parse_output = {"file_data": {}}

    try:
        xlsx_file = pl.read_excel(io.BytesIO(byte_string), sheet_id=0)
    except Exception as e:
        msg = _("There was an error while processing spreadsheet file")
        warnings.warn(f"{msg}:\n {e}")
        return msg

    # Kiekvieną lakštą nuskaityti atskirai tam, kad būtų galima lengviau aptikti klaidą
    # Pvz., jei įjungtas duomenų filtravimas viename lakšte, jį nuskaitant  išmes klaidą
    # ValueError: Value must be either numerical or a string containing a wildcard
    for sheet_name in xlsx_file.keys():
        try:
            df = xlsx_file[sheet_name]
            info_table = {
                "df_columns": list(df.columns),  # visi stulpeliai
                "df_columns_str": df.select(pl.col(pl.Utf8)).columns,  # tik tekstinio tipo stulpeliai
                "df": df.to_dicts()
            }
            xlsx_parse_output["file_data"][sheet_name] = info_table
        except Exception as e:
            msg = _("There was an error while processing sheet \"%s\"") % sheet_name
            warnings.warn(f"{msg}:\n {e}")
            return msg
    if xlsx_parse_output["file_data"]:
        return xlsx_parse_output
    else:
        return _("There was an error while processing spreadsheet file")


def parse_json(content_text, filename="JSON"):
    """
    Pagalbinė `parse_file` funkcija JSON nuskaitymui.

    :param content_text: JSON turinys kaip tekstas
    :param filename: rinkmenos vardas, kuris naudojamas kaip vardas išvedimo žodyne, jei būtų maža JSON struktūra
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """
    json_parse_output = {"file_data": {}}

    def json_depth(json_obj, level=1):
        # Nustatyti JSON lygių skačių
        if not isinstance(json_obj, (dict, list)):
            return level
        if isinstance(json_obj, list):
            return max(json_depth(item, level + 1) for item in json_obj)
        if isinstance(json_obj, dict):
            return max(json_depth(value, level + 1) for value in json_obj.values())

    try:
        json_data = json.loads(content_text)
        json_depth_level = json_depth(json_data)
    except Exception as e:
        msg = _("There was an error while reading file as JSON")
        msg = f"{msg}:\n {e}"
        return msg

    while (len(json_data) == 1) and (json_depth_level > 4):
        if isinstance(json_data, list):
            json_data = json_data[0]
        else:
            json_data = json_data[list(json_data.keys())[0]]
        json_depth_level -= 1
    if isinstance(json_data, list) or (json_depth_level < 4):
        json_data = {filename: json_data}
        json_depth_level += 1
    for sheet_name in json_data.keys():
        try:
            df = pl.DataFrame(json_data[sheet_name], infer_schema_length=None)
            if any([df.schema[col] not in [pl.String, pl.Int64, pl.Boolean] for col in df.columns]):
                msg = _("Unexpected JSON schema")
                warnings.warn(f"{msg}:\n {df.schema}")
                return msg
            info_table = {
                "df_columns": list(df.columns),  # visi stulpeliai
                "df_columns_str": df.select(pl.col(pl.Utf8)).columns,  # tik tekstinio tipo stulpeliai
                "df": df.to_dicts()
            }
            json_parse_output["file_data"][sheet_name] = info_table
        except Exception as e:
            msg = _("There was an error while processing sheet \"%s\"") % sheet_name
            warnings.warn(f"{msg}:\n {e}")
            # return msg
    if json_parse_output["file_data"]:
        return json_parse_output
    else:
        return _("There was an error while processing file as JSON")


def parse_dbml(content_text):
    """
    Pagalbinė `parse_file` funkcija DBML nuskaitymui.

    :param content_text: DBML turinys kaip tekstas
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """

    def remove_constant_columns(pl_df):
        """
        Šalinti stulpelius, kuriuose visos reikšmės vienodos
        """
        columns_to_drop = []
        for col in pl_df.columns:
            unique_values = pl_df[col].unique()
            if len(unique_values) == 1:
                columns_to_drop.append(col)
        return pl_df.drop(columns_to_drop)

    try:
        dbml = PyDBML(content_text)
        tables = []
        columns = []
        refs = []

        # Info apie lenteles
        for table in dbml.tables:
            table_schema = table.schema
            table_name = table.name
            tables.append({
                "schema": table_schema,
                "table": table_name,
                "alias": table.alias,
                "comment": f"{table.note}"  # table.note yra objektas, kurį būtina paversti tekstu
            })

            # Info apie stulpelius
            columns.extend([{
                "schema": table_schema,
                "table": table_name,
                "column": column.name,
                "comment": f"{column.note}",  # table.note yra objektas, kurį būtina paversti tekstu
                "type": f"{column.type}",  # column.type dažniausiai būna str tipo, bet kartais gali būti objektas, pvz., <Enum>
                "is_primary": column.pk,
                "unique": column.unique,
                "not_null": column.not_null,
            } for column in table.columns
            ])

            # Ryšiai
            for ref in dbml.refs:
                if all([ref.table1, ref.col1, ref.table2, ref.col2]):
                    # Jei kryptis atvirkščia, apversti table1 ir table2
                    source_tbl, target_tbl = (ref.table2, ref.table1) if ref.type == "<" else (ref.table1, ref.table2)
                    source_cols, target_cols = (ref.col2, ref.col1) if ref.type == "<" else (ref.col1, ref.col2)
                    refs.extend([{
                        "table": source_tbl.name,
                        "column": source_col.name,
                        "referenced_table": target_tbl.name,
                        "referenced_column": target_col.name,
                    } for source_col in source_cols for target_col in target_cols
                    ])

        # Polars DataFrame. Šalinti stulpelius, kuriuose reikšmė viena ir ta pati numatytoji iš PyDBML, o ne naudotojo
        df_tables = remove_constant_columns(pl.DataFrame(tables))  # šalinti schemą, jei visur būti schema numatytoji
        df_columns = remove_constant_columns(pl.DataFrame(columns))  # šalinti savybių stulpelius, jei niekas juos neapibrėžta
        df_refs = pl.DataFrame(refs)

        # Išvedimo struktūra
        parse_output = {"file_data": {}}
        for sheet_name, df in [("tables", df_tables), ("columns", df_columns), ("refs", df_refs)]:
            info_table = {
                "df_columns": list(df.columns),
                "df_columns_str": df.select(pl.col(pl.Utf8)).columns,
                "df": df.to_dicts()
            }
            parse_output["file_data"][sheet_name] = info_table

        return parse_output

    except Exception as e:
        msg = _("There was an error while processing file as DBML")
        warnings.warn(f"{msg}:\n {e}")
        return msg


def parse_csv(content_text, filename="CSV"):
    """
    Pagalbinė `parse_file` funkcija CSV nuskaitymui, automatiškai pasirenkant skirtuką ir koduotę.
    Standartinė polars.read_csv() komanda neaptinka koduotės ir skirtukų automatiškai.

    :param content_text: CSV turinys (jau iškoduotas su base64.b64decode)
    :param filename: rinkmenos vardas, kuris naudojamas kaip vardas išvedimo žodyne
    :return: žodynas, kaip aprašyta prie `parse_file` f-jos
    """
    try:
        dialect = csv.Sniffer().sniff(content_text)  # automatiškai nustatyti laukų skirtuką
        if dialect.delimiter in [";", ",", "\t"]:
            df = pl.read_csv(io.StringIO(content_text), separator=dialect.delimiter)
        else:
            # Kartais blogai aptinka skirtuką ir vis tiek reikia tikrinti kiekvieną jų priverstinai
            df = None
            for delimiter in [";", ",", "\t"]:
                if delimiter in content_text:
                    try:
                        df = pl.read_csv(io.StringIO(content_text), separator=delimiter)
                        break
                    except Exception:  # noqa: Mums visai nerūpi, kokia tai klaida
                        pass
            if df is None:
                return _("There was an error while processing file of unknown type")
        info_table = {
            "df_columns": list(df.columns),  # visi stulpeliai
            "df_columns_str": df.select(pl.col(pl.Utf8)).columns,  # tik tekstinio tipo stulpeliai
            "df": df.to_dicts()
        }
        csv_parse_output = {"file_data": {filename: info_table}}
        return csv_parse_output
    except Exception as e:
        msg = _("There was an error while processing file as CSV")
        warnings.warn(f"{msg}:\n {e}")
        return msg


def get_sheet_columns(dict_data, sheet, string_type=False):
    """
    Iš XLSX ar CSV turinio (kurį sukuria `parse_file` f-ja) pasirinktam lakštui ištraukti jo visus stulpelius.
    :param dict_data: žodynas {
        "file_data": lakštas: {
            "df": [],
            "df_columns": [],  # visų stulpelių sąrašas
            "df_columns_str": [],  # tekstinių stulpelių sąrašas
         }
    :param sheet: pasirinkto lakšto vardas
    :param string_type: ar norima gauti tik tekstinius stulpelius (numatyta: False)
    :return: lakšto stulpeliai
    """
    if (
        isinstance(dict_data, dict) and "file_data" in dict_data.keys() and
        isinstance(dict_data["file_data"], dict) and sheet in dict_data["file_data"].keys() and
        (dict_data["file_data"][sheet] is not None)
    ):
        if string_type and ("df_columns_str" in dict_data["file_data"][sheet]):
            sheet_columns = dict_data["file_data"][sheet]["df_columns_str"]
        elif "df_columns" in dict_data["file_data"][sheet]:
            sheet_columns = dict_data["file_data"][sheet]["df_columns"]
        else:
            # Struktūra ateina ne iš parse_csv(), bet iš gui_callbacks_file_upload.summarize_submission()
            if "df" in dict_data["file_data"][sheet]:
                df = dict_data["file_data"][sheet]["df"]
            else:
                df = dict_data["file_data"][sheet]
            df = pl.DataFrame(df, infer_schema_length=None)
            sheet_columns = df.select(pl.col(pl.Utf8)).columns if string_type else df.columns
        return sheet_columns
    return []


def select_renamed_or_add_columns(df, old_columns, new_columns):
    """
    Pakeisti ar papildyti stulpelių vardus pagal nurodytus naujus vardus.
    Jei stulpelio vardas yra tuščias, sukurti tuščią nauju vardu.
    Jei stulpelis yra, bet vardas skiriasi, tada pervadinti.

    :param df: polars DataFrame
    :param old_columns: sąrašas iš senų stulpelio vardų (pervadinimui) arba None (pridėjimui)
    :param new_columns: nauji stulpelio vardai pervadinimui arba pridėjimui
    :return: polars DataFrame su pervadintais arba pridėtais stulpeliais
    """
    df = pl.DataFrame(df, infer_schema_length=None)  # užtikrinti, kad df yra polars tipo
    for col, alias in zip(old_columns, new_columns):
        if (not col) or (col not in df.columns):
            # jei stulpelio dar nėra, sukurti tuščią nauju vardu
            df = df.with_columns(pl.lit(None).alias(alias))
        elif col != alias:
            # jei stulpelis yra, bet vardas skiriasi, tada pervadinti
            df = df.with_columns(pl.col(col).alias(alias))
    return df.select(new_columns)
