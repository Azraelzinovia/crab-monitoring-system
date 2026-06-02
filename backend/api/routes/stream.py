"""
API Routes — Camera Streaming
GET /stream/cam1 — MJPEG stream kamera 1
GET /stream/cam2 — MJPEG stream kamera 2
GET /stream/snapshot/{cam_id} — Snapshot kamera
WS  /stream/ws/{cam_id} — WebSocket stream
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, Response
import asyncio
import logging
import cv2

from services.camera_service import camera_service
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def _ensure_cameras():
    """Initialize cameras if not started."""
    if not camera_service._started:
        await camera_service.initialize()


@router.get(
    "/stream/cam1",
    summary="Live MJPEG stream Kamera 1 (Tampak Atas)",
    response_class=StreamingResponse,
)
async def stream_camera_1():
    """
    Live MJPEG stream dari Kamera 1 (tampak atas).
    
    Gunakan di HTML:
    ```html
    <img src="/api/v1/stream/cam1" />
    ```
    """
    await _ensure_cameras()
    return StreamingResponse(
        camera_service.mjpeg_stream(1),
        media_type="multipart/x-mixed-replace;boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get(
    "/stream/cam2",
    summary="Live MJPEG stream Kamera 2 (Tampak Samping)",
    response_class=StreamingResponse,
)
async def stream_camera_2():
    """
    Live MJPEG stream dari Kamera 2 (tampak samping).
    
    Gunakan di HTML:
    ```html
    <img src="/api/v1/stream/cam2" />
    ```
    """
    await _ensure_cameras()
    return StreamingResponse(
        camera_service.mjpeg_stream(2),
        media_type="multipart/x-mixed-replace;boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get(
    "/stream/snapshot/{camera_id}",
    summary="Snapshot frame terkini dari kamera",
)
async def get_snapshot(camera_id: int):
    """
    Ambil snapshot JPEG dari kamera yang dipilih.
    
    - **camera_id**: 1 (atas) atau 2 (samping)
    """
    if camera_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="camera_id harus 1 atau 2")

    await _ensure_cameras()
    jpeg_bytes = camera_service.get_jpeg(camera_id, quality=90)

    if jpeg_bytes is None:
        raise HTTPException(status_code=503, detail=f"Kamera {camera_id} tidak tersedia")

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"},
    )


@router.websocket("/stream/ws/{camera_id}")
async def websocket_stream(websocket: WebSocket, camera_id: int):
    """
    WebSocket stream untuk mendapatkan frame real-time.
    
    Setiap frame dikirim sebagai binary JPEG data.
    
    Contoh client JavaScript:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/stream/ws/1');
    ws.binaryType = 'blob';
    ws.onmessage = (event) => {
        const url = URL.createObjectURL(event.data);
        img.src = url;
    };
    ```
    """
    await websocket.accept()
    logger.info(f"WebSocket client connected for camera {camera_id}")

    await _ensure_cameras()
    frame_interval = 1.0 / settings.STREAM_FPS

    try:
        while True:
            start = asyncio.get_event_loop().time()

            jpeg = camera_service.get_jpeg(camera_id, quality=settings.STREAM_QUALITY)
            if jpeg:
                await websocket.send_bytes(jpeg)

            elapsed = asyncio.get_event_loop().time() - start
            sleep_time = max(0, frame_interval - elapsed)
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))
