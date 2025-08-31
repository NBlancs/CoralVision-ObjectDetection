import asyncio, json
from channels.generic.websocket import AsyncWebsocketConsumer
from .detector import get_detector

class DetectionsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self._task = asyncio.create_task(self._send_loop())

    async def disconnect(self, close_code):
        try:
            self._task.cancel()
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        # Placeholder if you want to accept client commands later
        pass

    async def _send_loop(self):
        det = get_detector()
        while True:
            meta = det.get_meta()
            await self.send(text_data=json.dumps(meta))
            await asyncio.sleep(0.1)
