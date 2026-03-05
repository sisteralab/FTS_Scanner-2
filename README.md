# FTS Scanner (PySide6)

Refactored project with clean `src` entry point and modular architecture:

- `devices` - hardware adapters (`XIMC` motor + `SR830` lock-in, plus simulators)
- `use_cases` - initialization, monitoring, and spectrogram measurement workflows
- `store` - in-memory measurement storage + Qt table model + JSON export
- `presentation` - isolated PySide6 UI (main window, controller, dialogs, table actions)

## Run

```bash
.venv/bin/python src/main.py
```

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Build (PyInstaller)

macOS/Linux:

```bash
./build.sh
```

Windows:

```bat
build.bat
```

## Notes

- Default mode is **Simulation**, so UI works without devices.
- Disable simulation and click **Initialize** for real hardware.
- Measurements are stored in table and can be viewed/commented/saved/deleted.
- `Save all` writes all measurements to `dumps/dump_YYYY-mm-dd_HH-MM-SS.json`.
- Build scripts package `ximc` and `assets` into the app bundle.
