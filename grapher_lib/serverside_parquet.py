# Optimizuotas Serverside variklis naudojantis Parquet+ZSTD vietoj Pickle
# Polars DataFrame serializacija: ~100 MB (pickle) > ~2 MB (parquet+zstd)

import io
import pickle
import typing as _t
import polars as pl
from cachelib.serializers import BaseSerializer
from dash_extensions.enrich import FileSystemBackend


class ParquetSerializer(BaseSerializer):
    """Hibridinis serializatorius, pritaikytas tinklo srautams ir kintančioms struktūroms."""

    MARKER_PARQUET = b"P"
    MARKER_PICKLE = b"K"
    MARKER_HYBRID = b"H"

    def dump(self, value: _t.Any, f: _t.IO[bytes], protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        """Serializuoja objektą ir tiesiogiai rašo jį į pateiktą duomenų srautą."""
        if isinstance(value, dict) and "file_data" in value:
            f.write(self.MARKER_HYBRID)

            dfs_to_write = {}
            clean_file_data = {}

            for sheet_name, sheet_content in value["file_data"].items():
                clean_sheet = {k: v for k, v in sheet_content.items() if k != "df"}
                if "df" in sheet_content and isinstance(sheet_content["df"], pl.DataFrame):
                    dfs_to_write[sheet_name] = sheet_content["df"]
                else:
                    clean_sheet["df"] = sheet_content.get("df")
                clean_file_data[sheet_name] = clean_sheet

            meta_dict = {k: v for k, v in value.items() if k != "file_data"}
            meta_dict["file_data"] = clean_file_data

            pickle.dump(meta_dict, f, protocol)
            pickle.dump(list(dfs_to_write.keys()), f, protocol)

            for sheet_name, df in dfs_to_write.items():
                df_buf = io.BytesIO()
                df.write_parquet(df_buf, compression="zstd", compression_level=3)
                df_bytes = df_buf.getvalue()

                f.write(len(df_bytes).to_bytes(4, byteorder="big"))
                f.write(df_bytes)

        elif isinstance(value, pl.DataFrame):
            f.write(self.MARKER_PARQUET)
            value.write_parquet(f, compression="zstd", compression_level=3)
        else:
            f.write(self.MARKER_PICKLE)
            pickle.dump(value, f, protocol)

    def load(self, f: _t.BinaryIO) -> _t.Any:
        """Deserializuoja objektą tiesiai iš gauto duomenų srauto."""
        marker = f.read(1)

        if marker == self.MARKER_HYBRID:
            meta_dict = pickle.load(f)
            parquet_sheets = pickle.load(f)

            for sheet_name in parquet_sheets:
                length_bytes = f.read(4)
                if not length_bytes:
                    break
                df_length = int.from_bytes(length_bytes, byteorder="big")
                df_bytes = f.read(df_length)
                meta_dict["file_data"][sheet_name]["df"] = pl.read_parquet(io.BytesIO(df_bytes))

            return meta_dict

        elif marker == self.MARKER_PARQUET:
            return pl.read_parquet(io.BytesIO(f.read()))
        elif marker == self.MARKER_PICKLE:
            return pickle.load(f)
        else:
            try:
                if f.seekable():
                    f.seek(0)
                    return pickle.load(f)
            except Exception:
                pass
            return None

    def dumps(self, value: _t.Any, protocol: int = pickle.HIGHEST_PROTOCOL) -> bytes:
        """Serializuoja objektą ar hibridinę struktūrą į baitų masyvą operatyviojoje atmityje."""
        buf = io.BytesIO()
        self.dump(value, buf, protocol)
        return buf.getvalue()

    def loads(self, bvalue: bytes) -> _t.Any:
        """Deserializuoja objektą ar hibridinę struktūrą iš gauto baitų masyvo."""
        buf = io.BytesIO(bvalue)
        return self.load(buf)


class ParquetFileSystemBackend(FileSystemBackend):
    """
    FileSystemBackend su Parquet serializacija Polars DataFrame'ams.

    Naudojimas:
        from drip_dash.serverside_parquet import ParquetFileSystemBackend

        app = DashProxy(
            ...,
            transforms=[ServersideOutputTransform(
                backends=[ParquetFileSystemBackend(cache_dir="data-tmp")]
            )],
        )
    """

    def __init__(self, cache_dir="data-tmp", **kwargs):
        super().__init__(cache_dir, **kwargs)
        # Pakeisti numatytąjį pickle serializatorių mūsų Parquet serializatoriumi
        self.serializer = ParquetSerializer()
