from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QFileDialog

from fts_scanner.store.schemas import MeasurePayload, normalize_measure_data


class MeasureType:
    """Supported measurement types."""

    SPECTROGRAM = "spectrogram"

    CHOICES = {
        SPECTROGRAM: "FTS spectrogram",
    }


class MeasureList(list["MeasureModel"]):
    """Typed helper list for measurement collection."""

    def first(self) -> "MeasureModel | None":
        return self[0] if self else None

    def last(self) -> "MeasureModel | None":
        return self[-1] if self else None

    def _filter(self, **kwargs: Any) -> filter:
        def predicate(item: MeasureModel) -> bool:
            return all(getattr(item, key, None) == value for key, value in kwargs.items())

        return filter(predicate, self)

    def filter(self, **kwargs: Any) -> "MeasureList":
        return self.__class__(self._filter(**kwargs))

    def delete_by_index(self, index: int) -> None:
        del self[index]


class MeasureManager:
    """Global manager of measurement entities and table synchronization."""

    table: "MeasureTableModel | None" = None
    _instances: MeasureList = MeasureList()
    latest_id: int = 0

    @classmethod
    def create(cls, *args: Any, **kwargs: Any) -> "MeasureModel":
        instance = MeasureModel(*args, **kwargs)
        cls._instances.append(instance)
        cls.update_table()
        return instance

    @classmethod
    def update_table(cls) -> None:
        if isinstance(cls.table, MeasureTableModel):
            cls.table.update_data()

    @classmethod
    def all(cls) -> MeasureList:
        return cls._instances

    @classmethod
    def count(cls) -> int:
        return len(cls._instances)

    @classmethod
    def filter(cls, **kwargs: Any) -> MeasureList:
        return cls.all().filter(**kwargs)

    @classmethod
    def get(cls, **kwargs: Any) -> "MeasureModel | None":
        filtered = cls.filter(**kwargs)
        return filtered.first()

    @classmethod
    def delete_by_index(cls, index: int) -> None:
        cls.all().delete_by_index(index)
        cls.update_table()

    @classmethod
    def save_by_index(cls, index: int) -> None:
        measure = cls.all()[index]
        results = measure.to_json()
        caption = (
            f"Saving {measure.type_display} started at "
            f"{measure.started.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        filepath = QFileDialog.getSaveFileName(filter="*.json", caption=caption)[0]
        if not filepath:
            return

        path = Path(filepath)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        path.write_text(json.dumps(results, ensure_ascii=False, indent=4), encoding="utf-8")
        measure.saved = True
        measure.save(finish=False)

    @classmethod
    def save_all(cls) -> Path | None:
        data = [item.to_json() for item in cls.all()]
        if not data:
            return None

        dump_dir = Path("dumps")
        dump_dir.mkdir(parents=True, exist_ok=True)
        filepath = dump_dir / f"dump_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        return filepath


class MeasureModel:
    """In-memory representation of one completed or running measure."""

    objects = MeasureManager
    ind_attr_map: dict[int, str] = {
        0: "id",
        1: "measure_type",
        2: "comment",
        3: "started",
        4: "finished",
        5: "saved",
        6: "points_count",
    }
    type_class = MeasureType

    def __init__(
        self,
        measure_type: str,
        data: Any,
        finished: datetime | str = "--",
    ) -> None:
        self.validate_type(value=measure_type)
        self.measure_type = measure_type
        self.data = normalize_measure_data(measure_type=measure_type, data=data)
        self.objects.latest_id += 1
        self.id = self.objects.latest_id
        self.started = datetime.now()
        self.finished = finished
        self.saved = False
        self.comment = ""

    @staticmethod
    def validate_type(value: str) -> None:
        if value not in MeasureType.CHOICES:
            raise ValueError(f"Type '{value}' is not presented in MeasureType")

    @property
    def type_display(self) -> str | None:
        return MeasureType.CHOICES.get(self.measure_type)

    @property
    def points_count(self) -> int:
        points = self.data.get("points", [])
        return len(points) if isinstance(points, list) else 0

    def get_attr_by_ind(self, ind: int) -> Any:
        attr = self.ind_attr_map.get(ind)
        return getattr(self, attr) if attr else None

    def save(self, finish: bool = True) -> None:
        self.data = normalize_measure_data(measure_type=self.measure_type, data=self.data)
        if finish:
            self.finished = datetime.now()
        self.objects.update_table()

    def to_json(self) -> dict[str, Any]:
        finished = self.finished if isinstance(self.finished, datetime) else datetime.now()
        normalized_data = normalize_measure_data(measure_type=self.measure_type, data=self.data)
        self.data = normalized_data
        payload = MeasurePayload(
            id=self.id,
            comment=self.comment,
            type=self.measure_type,
            measure=self.type_display or "",
            started=self.started,
            finished=finished,
            data=normalized_data,
        )
        return payload.to_json()


class MeasureTableModel(QAbstractTableModel):
    """Qt table model bound to MeasureManager collection."""

    manager = MeasureManager

    def __init__(self, data: list[list[Any]] | None = None) -> None:
        super().__init__()
        self._data: list[list[Any]] = data or []
        self._headers: list[str] = [
            "Id",
            "Type",
            "Comment",
            "Started",
            "Finished",
            "Saved",
            "Points",
        ]

    def data(self, index: QModelIndex, role: int) -> Any:
        if not index.isValid() or not self._data:
            return None

        value = self._data[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(value, bool):
                return "Yes" if value else "No"
            return value
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def update_data(self) -> None:
        self.beginResetModel()
        measures = self.manager.all()
        self._data = [
            [m.id, m.type_display, m.comment, m.started, m.finished, m.saved, m.points_count]
            for m in measures
        ]
        self.endResetModel()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return str(section + 1)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(MeasureModel.ind_attr_map)
