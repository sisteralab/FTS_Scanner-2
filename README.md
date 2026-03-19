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

- Use `SetUp` tab to configure addresses and click **Initialize / Test**.
- Lock-In backends in `SetUp`:
  - `Keysight VISA` (via `pyvisa`)
  - `Prologix Ethernet` (via `thzdaqapi`)
  - `Prologix USB` (via `thzdaqapi`)
- Settings are stored in the native OS settings backend (`ASC / FTS Scanner`):
  - Windows: Registry (`regedit`)
  - macOS: user preferences (`plist`)
  - Linux: user config store (Qt native settings backend)
- Legacy `settings.ini` is migrated automatically on first start.
- For Prologix mode install library:
  - `uv pip install -e ~/Labs/scripts/thzdaqapi`
- For VISA mode install:
  - `uv pip install pyvisa pyvisa-py`
- Disable simulation for real hardware.
- `Monitor` tab provides:
  - motor position, set-zero, target move
  - continuous motor state tracking (idle/moving/error + target)
  - press-and-hold jog buttons for relative motion
  - real-time lock-in stream with adjustable visible time window
- `Measure` tab provides scan setup, progress bar, interferogram and FFT spectrum plots.
- Measurements are stored in table and can be viewed/commented/saved/deleted.
- Runtime errors are logged to console with traceback.
- `Save all` writes all measurements to `dumps/dump_YYYY-mm-dd_HH-MM-SS.json`.
- Build scripts package `ximc` and `assets` into the app bundle.
