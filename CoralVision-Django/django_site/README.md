# CoralVision Django + Channels

This app streams YOLO-annotated video to the browser and broadcasts inference data over WebSocket. It also saves detections to CSV and the annotated video to MP4 under `django_site/stream/logs`.

## Quick start (Windows PowerShell)

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r ..\requirements.txt
```

3. Run the Django server:

```powershell
python manage.py runserver 0.0.0.0:8000
```

4. Open http://127.0.0.1:8000

Notes:
- Place `coralaiv3.pt` and optionally `v2videotesting.mp4` in either `CoralVision-Django` or `CoralVision-Tkinter`. The app searches both.
- To use a webcam, remove/rename `v2videotesting.mp4`; it will fall back to device 0.
- Logs and MP4 are written to `django_site/stream/logs/`.
