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
- Use `SetUp` tab to configure addresses and click **Initialize / Test**.
- Lock-In backends in `SetUp`:
  - `Prologix Ethernet` (via `thzdaqapi`)
  - `Prologix USB` (via `thzdaqapi`)
  - `VISA (legacy)`
- For Prologix mode install library:
  - `uv pip install -e ~/Labs/scripts/thzdaqapi`
- Disable simulation for real hardware. If you use legacy VISA and see `VI_ERROR_LIBRARY_NOT_FOUND`, install NI-VISA/Keysight VISA runtime.
- `Monitor` tab provides:
  - motor position, set-zero, target move
  - press-and-hold jog buttons for relative motion
  - real-time lock-in stream with adjustable visible time window
- `Measure` tab provides scan setup, progress bar, interferogram and FFT spectrum plots.
- Measurements are stored in table and can be viewed/commented/saved/deleted.
- Runtime errors are logged to console with traceback.
- `Save all` writes all measurements to `dumps/dump_YYYY-mm-dd_HH-MM-SS.json`.
- Build scripts package `ximc` and `assets` into the app bundle.
