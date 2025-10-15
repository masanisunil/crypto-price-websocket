# 🪙 Crypto Price WebSocket Project

## 📌 Overview
A Python application that connects to **Binance’s WebSocket API** for live crypto prices and broadcasts them via a **FastAPI WebSocket server** in real time.

---

## ⚙️ Tech Stack
- **FastAPI** (REST + WebSocket)
- **websockets** (Binance connection)
- **Pydantic**
- **asyncio.Queue**
- **HTML + JavaScript** frontend

---

## 🚀 Features
✅ Connects to Binance WebSocket for BTC/USDT  
✅ Broadcasts live prices to connected WebSocket clients  
✅ REST API `/price` returns latest price snapshot  
✅ Frontend dashboard (`ws_client.html`)  
✅ Dockerfile for deployment  

---

## ▶️ Run Locally
```bash
pip install -r requirements.txt
python main.py
```

- REST: http://localhost:8000/price  
- WebSocket: ws://localhost:8000/ws

Open `ws_client.html` to see live BTC/USDT updates.

---

## 🌍 Deployment
Deploy backend on Render/Railway/Deta  
Deploy frontend on Vercel/Netlify

---

## 👤 Author
**Sunil Masani**  
📧 sunil.m0711@gmail.com  
💼 [LinkedIn](https://linkedin.com/in/sunil-shetty)  
💻 [GitHub](https://github.com/sunilvshetty)
