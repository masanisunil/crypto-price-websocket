# import asyncio
# import json
# import logging
# from typing import Dict, List
# import websockets
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from pydantic import BaseModel
# from datetime import datetime
# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware

# # --- Configuration ---
# BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
# LOCAL_HOST = "0.0.0.0"
# LOCAL_PORT = 8000
# QUEUE_SIZE = 100

# # --- Logging Setup ---
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger("CryptoServer")

# # --- Data Structures ---
# class TickerData(BaseModel):
#     symbol: str
#     last_price: float
#     price_change_percent: float
#     timestamp: str

# latest_price_storage: Dict[str, TickerData] = {}
# broadcast_queue: asyncio.Queue[TickerData] = asyncio.Queue(maxsize=QUEUE_SIZE)
# active_connections: List[WebSocket] = []


# # --- Binance Listener ---
# async def binance_listener():
#     logger.info(f"Connecting to Binance WebSocket at: {BINANCE_WS_URL}")
#     try:
#         async with websockets.connect(BINANCE_WS_URL) as websocket:
#             logger.info("Successfully connected to Binance.")
#             while True:
#                 try:
#                     message = await websocket.recv()
#                     data = json.loads(message)
#                     if data.get('e') == '24hrTicker':
#                         symbol = data.get('s')
#                         last_price = float(data.get('c', 0.0))
#                         price_change_percent = float(data.get('P', 0.0))
#                         timestamp_ms = data.get('E', int(datetime.now().timestamp() * 1000))
#                         timestamp_str = datetime.fromtimestamp(timestamp_ms / 1000).isoformat() + "Z"

#                         ticker_data = TickerData(
#                             symbol=symbol,
#                             last_price=last_price,
#                             price_change_percent=price_change_percent,
#                             timestamp=timestamp_str
#                         )

#                         latest_price_storage[symbol] = ticker_data
#                         try:
#                             broadcast_queue.put_nowait(ticker_data)
#                         except asyncio.QueueFull:
#                             logger.warning("Broadcast queue is full. Dropping message.")
#                 except Exception as e:
#                     logger.error(f"Binance listener error: {e}", exc_info=True)
#                     await asyncio.sleep(1)
#     except Exception as e:
#         logger.error(f"Failed to connect to Binance: {e}")
#     logger.info("Reconnecting in 5 seconds...")
#     await asyncio.sleep(5)
#     asyncio.create_task(binance_listener())


# # --- Broadcaster ---
# async def broadcaster():
#     logger.info("Broadcaster task started.")
#     while True:
#         try:
#             ticker_data = await broadcast_queue.get()
#             message = ticker_data.model_dump_json()
#             send_tasks = [asyncio.create_task(conn.send_text(message)) for conn in active_connections]
#             if send_tasks:
#                 await asyncio.gather(*send_tasks, return_exceptions=True)
#             broadcast_queue.task_done()
#         except Exception as e:
#             logger.error(f"Error in broadcaster: {e}", exc_info=True)
#             await asyncio.sleep(0.1)


# # --- Lifespan setup ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     asyncio.create_task(binance_listener())
#     asyncio.create_task(broadcaster())
#     yield
#     logger.info("Shutting down server...")


# # --- Create single FastAPI app instance ---
# app = FastAPI(title="Crypto Price Server", lifespan=lifespan)

# # ✅ Add CORS middleware to the *same* app
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # You can restrict to your Vercel domain later
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # --- WebSocket Endpoint ---
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     active_connections.append(websocket)
#     logger.info(f"Client connected. Total: {len(active_connections)}")
#     try:
#         while True:
#             await websocket.receive_text()
#     except WebSocketDisconnect:
#         logger.info("Client disconnected.")
#     except Exception as e:
#         logger.error(f"WebSocket error: {e}")
#     finally:
#         active_connections.remove(websocket)
#         logger.info(f"Client removed. Total: {len(active_connections)}")


# # --- REST Endpoint ---
# @app.get("/price", response_model=Dict[str, TickerData])
# def get_latest_price():
#     if not latest_price_storage:
#         return {"message": "Price data not yet available."}
#     return latest_price_storage


# # --- Main Runner ---
# if __name__ == "__main__":
#     import uvicorn
#     logger.info(f"Starting server on http://{LOCAL_HOST}:{LOCAL_PORT}")
#     uvicorn.run(
#         app,
#         host=LOCAL_HOST,
#         port=LOCAL_PORT,
#         log_level="info",
#         server_header=False
#     )



import asyncio
import json
import logging
from typing import Dict, List, Tuple
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]
STREAMS = "/".join([f"{symbol}@ticker" for symbol in SYMBOLS])
BINANCE_WS_URL = f"wss://stream.binance.com:9443/stream?streams={STREAMS}"
LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 8000
QUEUE_SIZE = 100

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CryptoServer")

# --- Data Models ---
class TickerData(BaseModel):
    symbol: str
    last_price: float
    price_change_percent: float
    timestamp: str

# --- Shared State ---
latest_price_storage: Dict[str, TickerData] = {}
broadcast_queue: asyncio.Queue[TickerData] = asyncio.Queue(maxsize=QUEUE_SIZE)
active_connections: List[Tuple[WebSocket, List[str]]] = []
connections_lock = asyncio.Lock()


# --- Binance Listener (multi-symbol) ---
async def binance_listener():
    while True:
        try:
            logger.info(f"Connecting to Binance WebSocket at: {BINANCE_WS_URL}")
            async with websockets.connect(BINANCE_WS_URL) as websocket:
                logger.info("✅ Connected to Binance multi-stream WebSocket.")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Each Binance multi-stream message has: {"stream": "...", "data": {...}}
                    if "data" in data and data["data"].get("e") == "24hrTicker":
                        payload = data["data"]
                        symbol = payload.get("s")
                        last_price = float(payload.get("c", 0.0))
                        price_change_percent = float(payload.get("P", 0.0))
                        timestamp_ms = payload.get("E", int(datetime.now().timestamp() * 1000))
                        timestamp_str = datetime.fromtimestamp(timestamp_ms / 1000).isoformat() + "Z"

                        ticker_data = TickerData(
                            symbol=symbol,
                            last_price=last_price,
                            price_change_percent=price_change_percent,
                            timestamp=timestamp_str
                        )

                        latest_price_storage[symbol] = ticker_data

                        try:
                            broadcast_queue.put_nowait(ticker_data)
                        except asyncio.QueueFull:
                            logger.warning("Broadcast queue full — dropping message.")
        except Exception as e:
            logger.error(f"Binance listener error: {e}", exc_info=True)
            logger.info("🔁 Reconnecting to Binance in 5 seconds...")
            await asyncio.sleep(5)


# --- Broadcaster Task ---
async def broadcaster():
    logger.info("📡 Broadcaster task started.")
    while True:
        ticker_data = await broadcast_queue.get()
        message = ticker_data.model_dump_json()

        async with connections_lock:
            send_tasks = []
            for conn, symbols in list(active_connections):
                if ticker_data.symbol in symbols:
                    try:
                        send_tasks.append(asyncio.create_task(conn.send_text(message)))
                    except Exception as e:
                        logger.error(f"Send error: {e}")
            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)

        broadcast_queue.task_done()


# --- Lifespan Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(binance_listener())
    asyncio.create_task(broadcaster())
    yield
    logger.info("🛑 Server shutting down...")


# --- FastAPI App ---
app = FastAPI(title="Crypto Multi-Pair Price Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # ✅ Allow clients to subscribe to specific pairs (query param: ?symbols=BTCUSDT,ETHUSDT)
    params = websocket.query_params.get("symbols", "")
    subscribed_symbols = [s.strip().upper() for s in params.split(",") if s.strip()] or [s.upper() for s in SYMBOLS]

    async with connections_lock:
        active_connections.append((websocket, subscribed_symbols))
    logger.info(f"Client connected for {subscribed_symbols}. Total: {len(active_connections)}")

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        async with connections_lock:
            active_connections[:] = [(conn, syms) for conn, syms in active_connections if conn != websocket]
        logger.info(f"Client removed. Total: {len(active_connections)}")


# --- REST Endpoint (snapshot) ---
@app.get("/price", response_model=Dict[str, TickerData])
def get_latest_price():
    if not latest_price_storage:
        return {"message": "Price data not yet available."}
    return latest_price_storage


# --- Run Locally ---
if _name_ == "_main_":
    import uvicorn
    logger.info(f"🚀 Starting server on http://{LOCAL_HOST}:{LOCAL_PORT}")
    uvicorn.run(
        app,
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        log_level="info",
        server_header=False
    )
