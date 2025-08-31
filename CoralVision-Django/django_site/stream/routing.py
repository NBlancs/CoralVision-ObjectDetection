from django.urls import path
from .consumers import DetectionsConsumer

websocket_urlpatterns = [
    path('ws/detections/', DetectionsConsumer.as_asgi()),
]
