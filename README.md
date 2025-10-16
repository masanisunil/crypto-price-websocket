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
✅ Connects to Binance WebSocket for BTC/USDT,ETH/USDT,BNB/USDT
✅ Broadcasts live prices to connected WebSocket clients  
✅ REST API `/price` returns latest price snapshot  
✅ Frontend dashboard (`index.html`)  
✅ Dockerfile for deployment  

---

## ▶️ Run Locally
```bash
pip install -r requirements.txt
python main.py
```

- REST: http://localhost:8000/price  
- WebSocket: ws://localhost:8000/ws

Open `index.html` to see live BTC/USDT,ETH/USDT,BNB/USDT updates.

---

## 🌍 Deployment
Deploy backend on Render  
Deploy frontend on Vercel

---

## 👤 Author
**Sunil Masani**  
📧 sunil.m0711@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/masani-sunil-kumar-84162426a?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app)  
💻 [GitHub](https://github.com/masanisunil)
