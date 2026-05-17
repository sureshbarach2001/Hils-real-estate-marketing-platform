# 🏠 Zameed Real Estate Platform

> Premium real estate marketing platform for Pakistan market with JWT auth, property listings, Stripe payments, and admin/customer dashboards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend: React 19](https://img.shields.io/badge/Frontend-React%2019-61DAFB)](https://react.dev/)
[![Database: MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248)](https://www.mongodb.com/)

## ✨ Features

### Public Website
- 🎨 Premium dark luxury UI (#050505 obsidian + #D4AF37 champagne gold)
- 🔍 Advanced property search: city, price, type, area, purpose (buy/rent)
- 🗺️ Interactive maps with Leaflet + geospatial clustering
- 🖼️ Lazy-loaded image galleries with WebP/AVIF support
- 📱 Fully responsive: mobile-first design with animations

### Authentication
- 🔐 JWT-based auth with httpOnly cookies (12h access + 7d refresh)
- 📧 Email/password signup + login with brute-force protection
- 🔁 Password reset flow with secure tokens
- 👤 Optional Google social login (placeholder ready)

### Property Management
- 🏘️ CRUD for properties: plots, apartments, houses, commercial
- 🌍 Geospatial search: "properties within 5km" via MongoDB 2dsphere
- 🧹 Soft delete for audit compliance + dispute resolution
- 💰 PKR pricing with locale-aware formatting (en-PK)

### Dashboards
- 👤 Customer: saved properties, inquiry history, booking status, receipts
- 👨‍💼 Admin: revenue reports, lead CRM, user management, content moderation

### Payments & Leads
- 💳 Stripe Checkout integration (test mode) for booking deposits
- 📬 Automated lead capture + email notifications
- 📊 Admin reporting: pipeline stats, conversion tracking

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI + Motor + Pydantic | Async APIs, validation, security |
| Database | MongoDB + 2dsphere indexes | Flexible schema + geospatial search |
| Frontend | React 19 + Vite + Tailwind | Fast UX, dark luxury theme |
| UI | Shadcn-style + Framer Motion | Accessible components + micro-animations |
| Maps | Leaflet + react-leaflet | Interactive property maps |
| Auth | JWT + bcrypt + httpOnly cookies | Secure session management |
| Payments | Stripe Checkout (test mode) | PCI-compliant booking deposits |

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ & npm/yarn
- Python 3.11+ & pip
- MongoDB Atlas account (free tier)
- Stripe account (test mode)

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values
uvicorn server:app --reload --port 8000
# API running at: http://localhost:8000
# Health check: curl http://localhost:8000/api/health