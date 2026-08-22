# Optimizuotas Serverside variklis naudojantis Parquet+ZSTD vietoj Pickle
# Polars DataFrame serializacija: ~100 MB (pickle) > ~2 MB (parquet+zstd)

import io
import pickle
import typing as _t
import polars as pl
from cachelib.serializers import BaseSerializer
from dash_extensions.enrich import FileSystemBackend


class ParquetSerializer(BaseSerializer):
    """
    Pasirinktinis serializatorius, kuris:
    - Polars DataFrame > Parquet su zstd glaudinimu (greita + kompaktiška) - ~50 kartų  mažiau vietos nei su pickle
    - Visi kiti objektai > Pickle (atsarginis variantas)

    Formato žymė (pirmas baitas):
    - b'P' (0x50) = Parquet
    - b'K' (0x4B) = Pickle
    """

    MARKER_PARQUET = b"P"
    MARKER_PICKLE = b"K"

    def dump(self, value: _t.Any, f: _t.IO[bytes], protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        """Serializuoja objektą ir tiesiogiai rašo jį į pateiktą duomenų srautą."""
        if isinstance(value, pl.DataFrame):
            f.write(self.MARKER_PARQUET)
            # write_parquet su zstd kompresija – greita ir kompaktiška
            value.write_parquet(f, compression="zstd", compression_level=3)
        else:
            f.write(self.MARKER_PICKLE)
            pickle.dump(value, f, protocol)

    def load(self, f: _t.BinaryIO) -> _t.Any:
        """Deserializuoja objektą tiesiai iš gauto duomenų srauto."""
        marker = f.read(1)
        if marker == self.MARKER_PARQUET:
            # Nuskaitome likusius baitus į naują buferį, kad parquet duomenys
            # prasidėtų nuo pozicijos 0 (kitaip seek pozicijos būtų pasislinkusios per 1 baitą)
            return pl.read_parquet(io.BytesIO(f.read()))
        elif marker == self.MARKER_PICKLE:
            return pickle.load(f)
        else:
            # Atgalinis suderinamumas: jei nėra žymės, bandyti pickle (senas formatas)
            f.seek(0)
            try:
                return pickle.load(f)
            except Exception:
                return None

    def dumps(self, value: _t.Any, protocol: int = pickle.HIGHEST_PROTOCOL) -> _t.Optional[bytes]:
        """Serializuoja objektą į autonomišką baitų masyvą operatyviojoje atmintyje."""
        buf = io.BytesIO()
        self.dump(value, buf, protocol)
        return buf.getvalue()

    def loads(self, bvalue: bytes) -> _t.Any:
        """Deserializuoja objektą iš jau gauto ir atmintyje esančio baitų masyvo."""
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
