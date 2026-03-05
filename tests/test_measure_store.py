from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from fts_scanner.store.measure_store import MeasureManager, MeasureModel, MeasureTableModel, MeasureType


class TestMeasureStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self) -> None:
        MeasureManager._instances.clear()
        MeasureManager.latest_id = 0
        MeasureManager.table = None

    def test_create_and_filter(self) -> None:
        one = MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": []})
        MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": [1]})

        self.assertEqual(one.id, 1)
        self.assertEqual(MeasureManager.count(), 2)
        self.assertIsNotNone(MeasureManager.get(id=2))

    def test_table_model_updates(self) -> None:
        model = MeasureTableModel()
        MeasureManager.table = model

        MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": [1, 2, 3]})
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), len(MeasureModel.ind_attr_map))

    def test_save_all_creates_dump(self) -> None:
        MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": [{"x": 1}]})

        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                path = MeasureManager.save_all()
                self.assertIsNotNone(path)
                self.assertTrue(Path(path).exists())
                self.assertEqual(Path(path).suffix, ".json")
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
