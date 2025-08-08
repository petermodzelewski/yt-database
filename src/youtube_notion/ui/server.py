import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import queue
from src.youtube_notion.config.factory import ComponentFactory
from src.youtube_notion.processors.video_processor import VideoProcessor
from src.youtube_notion.config import load_application_config
from src.youtube_notion.utils.chat_logger import ChatLogger
from src.youtube_notion.queue import UrlQueue
from fastapi.responses import PlainTextResponse, FileResponse
import os
import webbrowser
from threading import Timer
from typing import List

app = FastAPI()

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, 'index.html'))

url_queue = UrlQueue()
active_connections: List[WebSocket] = []

async def broadcast(message: dict):
    for connection in active_connections:
        await connection.send_json(message)

async def process_urls():
    config = load_application_config(youtube_mode=True)
    if not config:
        await broadcast({"status": "failed", "error": "Server configuration error."})
        return

    factory = ComponentFactory(config)
    processor = VideoProcessor(
        factory.create_metadata_extractor(),
        factory.create_summary_writer(),
        factory.create_storage()
    )
    processor.validate_configuration()

    while True:
        try:
            url = url_queue.get_nowait()

            async def status_callback(message: str, progress: int):
                await broadcast({
                    "status": "processing",
                    "url": url,
                    "message": message,
                    "progress": progress
                })

            await status_callback("Queued for processing...", 0)

            try:
                success, metadata = await asyncio.to_thread(
                    processor.process_video,
                    video_url=url,
                    custom_prompt=None,
                    status_callback=status_callback
                )
                if success:
                    await broadcast({"status": "done", "url": url, "progress": 100, "metadata": metadata})
                else:
                    await broadcast({"status": "failed", "url": url, "error": "Processing failed."})
            except Exception as e:
                await broadcast({"status": "failed", "url": url, "error": str(e)})
        except queue.Empty:
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_urls())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            url_queue.add(data)
            await broadcast({"status": "queued", "url": data})
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")

@app.get("/logs/{video_id}")
async def get_log(video_id: str, chunk: int = -1):
    chat_logger = ChatLogger()
    log_files = chat_logger.get_log_files(video_id)

    if not log_files:
        return PlainTextResponse("Log file not found.", status_code=404)

    log_file_to_read = None
    if chunk == -1:
        # Find the main log file (not a chunk)
        for log_file in log_files:
            if f"_{video_id}_" in os.path.basename(log_file) and "_chunk_" not in os.path.basename(log_file):
                log_file_to_read = log_file
                break
    else:
        # Find the specific chunk log file
        for log_file in log_files:
            if f"_{video_id}_chunk_{chunk}_" in os.path.basename(log_file):
                log_file_to_read = log_file
                break

    if not log_file_to_read:
        return PlainTextResponse("Log file for the specified chunk not found.", status_code=440)

    with open(log_file_to_read, 'r', encoding='utf-8') as f:
        return PlainTextResponse(f.read())

def open_browser():
    webbrowser.open_new_tab("http://localhost:8000")

def start_server():
    Timer(1, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server()
