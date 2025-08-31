import time
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from .detector import get_detector, use_webcam, use_video, start_recording, stop_recording, use_camera
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, 'stream/index.html')


def _mjpeg():
    boundary = b'--frame'
    det = get_detector()
    while True:
        jpeg = det.get_frame()
        if jpeg:
            yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
        time.sleep(0.02)


def video_feed(request):
    return StreamingHttpResponse(_mjpeg(), content_type='multipart/x-mixed-replace; boundary=frame')


# Control endpoints (POST recommended; allow GET for simplicity during dev)
@csrf_exempt
def api_use_webcam(request):
    if request.method not in ("POST", "GET"):
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    return JsonResponse(use_webcam())


@csrf_exempt
def api_use_video(request):
    if request.method not in ("POST", "GET"):
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    return JsonResponse(use_video())


@csrf_exempt
def api_use_camera(request):
    if request.method not in ("POST", "GET"):
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    try:
        idx = int(request.GET.get('i', '0'))
    except ValueError:
        return JsonResponse({"ok": False, "error": "invalid index"}, status=400)
    return JsonResponse(use_camera(idx))


@csrf_exempt
def api_start_recording(request):
    if request.method not in ("POST", "GET"):
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    return JsonResponse(start_recording())


@csrf_exempt
def api_stop_recording(request):
    if request.method not in ("POST", "GET"):
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    return JsonResponse(stop_recording())
