import os, threading, time, csv, datetime
import cv2
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ...\CoralVision-Django\django_site
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # ...\CoralVision-Django
# Look for weights/video in project root or provide your own paths
MODEL_PATH = os.path.join(PROJECT_ROOT, 'coralaiv3.pt')
ALT_MODEL_PATHS = [
    os.path.join(os.path.dirname(PROJECT_ROOT), 'CoralVision-Tkinter', 'coralaiv3.pt'),
]
SOURCE_PATH = os.path.join(PROJECT_ROOT, 'v2videotesting.mp4')
ALT_SOURCE_PATHS = [
    os.path.join(os.path.dirname(PROJECT_ROOT), 'CoralVision-Tkinter', 'v2videotesting.mp4'),
]

LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_CSV = os.path.join(LOG_DIR, f"detections_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
REC_OUT = os.path.join(LOG_DIR, f"record_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")


def _first_existing(paths):
    for p in paths:
        if isinstance(p, str) and os.path.exists(p):
            return p
    return None

MODEL_PATH = _first_existing([MODEL_PATH] + ALT_MODEL_PATHS)
if not MODEL_PATH:
    raise FileNotFoundError('YOLO weights not found; expected coralaiv3.pt in project or CoralVision-Tkinter folder')

_source_candidate = _first_existing([SOURCE_PATH] + ALT_SOURCE_PATHS)
SOURCE = _source_candidate if _source_candidate else 0  # fallback to webcam


class Detector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self.cap = cv2.VideoCapture(SOURCE)
        if not self.cap.isOpened() and SOURCE == 0:
            # Windows often needs DirectShow backend
            try:
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            except Exception:
                pass
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video source: {SOURCE}")
        # Video writer for annotated recording (only when recording flag is True)
        self.writer = None
        self.recording = False
        self._record_path = None
        self._record_reset = False  # request to (re)open writer on next frame
        # Source switching
        self._switch_req = None  # None or 0 or filepath str
        self.source_label = 'file' if isinstance(SOURCE, str) else 'webcam'
        # Shared state
        self.lock = threading.Lock()
        self.latest_jpeg = None
        self.latest_meta = {"ts": None, "fps": 0.0, "detections": []}
        self.stop_event = threading.Event()
        self.fps_smooth = 0.0
        # CSV header
        with open(LOG_CSV, 'w', newline='') as f:
            import csv as _csv
            w = _csv.writer(f)
            w.writerow(['timestamp','class_id','class_name','conf','x1','y1','x2','y2'])
        # Start thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _ensure_writer(self, frame):
        if not self.recording:
            return
        if self.writer is None or self._record_reset:
            # Try to use source FPS when available, else 30
            src_fps = self.cap.get(cv2.CAP_PROP_FPS)
            fps = float(src_fps) if src_fps and src_fps > 0 else 30.0
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            path = self._record_path or os.path.join(
                LOG_DIR, f"record_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            # Close any existing writer before reopening
            if self.writer is not None:
                try:
                    self.writer.release()
                except Exception:
                    pass
            self.writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
            self._record_reset = False

    def _run(self):
        while not self.stop_event.is_set():
            # Apply pending source switch
            if self._switch_req is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                new_src = self._switch_req
                self.cap = cv2.VideoCapture(new_src)
                if not self.cap.isOpened() and new_src == 0:
                    try:
                        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    except Exception:
                        pass
                if not self.cap.isOpened():
                    # Revert to previous if failed
                    self.cap = cv2.VideoCapture(SOURCE)
                else:
                    self.source_label = 'webcam' if new_src == 0 else 'file'
                # reset writer size on new source
                self._record_reset = True
                self._switch_req = None

            ok, frame = self.cap.read()
            if not ok:
                if isinstance(SOURCE, str):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            start = time.time()
            results = self.model.predict(source=frame, conf=0.6, verbose=False)
            r = results[0]
            annotated = r.plot()

            # encode JPEG for HTTP stream
            ok, buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue

            # compute FPS
            dt = time.time() - start
            fps = 1.0/dt if dt > 0 else 0.0
            self.fps_smooth = 0.9*self.fps_smooth + 0.1*fps if self.fps_smooth else fps

            # gather detections
            dets = []
            if hasattr(r, 'boxes') and r.boxes is not None:
                boxes = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                clss = r.boxes.cls.cpu().numpy().astype(int)
                names = r.names
                for (x1,y1,x2,y2), conf, cid in zip(boxes, confs, clss):
                    dets.append({
                        'class_id': int(cid),
                        'class_name': names.get(int(cid), str(cid)) if isinstance(names, dict) else str(cid),
                        'conf': float(conf),
                        'x1': float(x1), 'y1': float(y1), 'x2': float(x2), 'y2': float(y2)
                    })

            ts = datetime.datetime.utcnow().isoformat()
            # write CSV rows
            if dets:
                with open(LOG_CSV, 'a', newline='') as f:
                    import csv as _csv
                    w = _csv.writer(f)
                    for d in dets:
                        w.writerow([ts, d['class_id'], d['class_name'], f"{d['conf']:.4f}", f"{d['x1']:.2f}", f"{d['y1']:.2f}", f"{d['x2']:.2f}", f"{d['y2']:.2f}"])

            # ensure mp4 writer and write frame (only if recording)
            self._ensure_writer(annotated)
            if self.recording and self.writer:
                self.writer.write(annotated)

            with self.lock:
                self.latest_jpeg = buf.tobytes()
                self.latest_meta = {
                    "ts": ts,
                    "fps": round(self.fps_smooth, 2),
                    "detections": dets,
                    "source": self.source_label,
                    "recording": bool(self.recording),
                }

            time.sleep(0.001)

    def get_frame(self):
        with self.lock:
            return self.latest_jpeg

    def get_meta(self):
        with self.lock:
            return self.latest_meta

    def stop(self):
        self.stop_event.set()
        try:
            self.thread.join(timeout=2)
        except Exception:
            pass
        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
        self.cap.release()

# create singleton on import
_detector_singleton = None

def get_detector():
    global _detector_singleton
    if _detector_singleton is None:
        _detector_singleton = Detector()
    return _detector_singleton

# Public control methods (thread-safe requests)
def use_camera(index: int = 0):
    det = get_detector()
    # Probe availability first, with DSHOW fallback
    test = cv2.VideoCapture(index)
    if not test.isOpened() and index == 0:
        try:
            test = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception:
            pass
    try:
        if not test.isOpened():
            return {"ok": False, "error": f"Webcam {index} not available"}
    finally:
        try:
            test.release()
        except Exception:
            pass
    det._switch_req = int(index)
    return {"ok": True, "source": "webcam", "index": int(index)}


def use_webcam():
    return use_camera(0)

def use_video():
    det = get_detector()
    path = _first_existing([SOURCE_PATH] + ALT_SOURCE_PATHS)
    if not path:
        return {"ok": False, "error": "Sample video not found"}
    # probe video can be opened
    test = cv2.VideoCapture(path)
    try:
        if not test.isOpened():
            return {"ok": False, "error": f"Cannot open video: {path}"}
    finally:
        try:
            test.release()
        except Exception:
            pass
    det._switch_req = path
    return {"ok": True, "source": "file", "path": path}

def start_recording():
    det = get_detector()
    det.recording = True
    det._record_path = os.path.join(
        LOG_DIR, f"record_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )
    det._record_reset = True
    return {"ok": True, "path": det._record_path}

def stop_recording():
    det = get_detector()
    det.recording = False
    try:
        if det.writer:
            det.writer.release()
    finally:
        det.writer = None
    return {"ok": True}
