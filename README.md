# ✈️ AI Travel Planner

An AI-powered travel planning prototype that combines hotel recommendations, transport planning, route mapping, weather updates, and itinerary generation into one platform.

## 🌍 Problem Statement

Planning a trip usually requires multiple applications:

- 🏨 Hotel booking apps
- 🚕 Transport apps
- 🗺️ Map/navigation apps
- 🍽️ Restaurant discovery apps
- 🌦️ Weather apps

This project explores the idea of creating a **single intelligent platform** where users can manage their entire trip experience in one place using natural language.

---

## 💡 Project Idea

The app acts as a unified travel assistant.

Users can enter prompts like:

> "I want to visit Jaipur with 3 friends for 2 days with a luxury hotel and cab transport."

The AI then:
- Understands the travel request
- Suggests attractions
- Recommends hotels
- Estimates transport costs
- Generates optimized routes
- Shows weather updates
- Creates downloadable itinerary PDFs

---

## 🚀 Features

### ✨ AI Mode
- Natural language trip planning
- AI-powered intent extraction using Gemini + LangChain
- Automatic attraction filtering based on interests

### ⚙️ Manual Mode
- Manual city and attraction selection
- Transport preference selection
- Budget customization

### 🏨 Smart Hotel Suggestions
- Budget-based hotel filtering
- Availability checking
- Rating-based recommendations

### 🚕 Transport Planning
- Cab/auto/bus assignment
- Cost estimation
- Fallback transport system

### 🗺️ Route Optimization
- Optimized attraction ordering
- Interactive maps using Folium

### 🌦️ Live Weather Integration
- Real-time weather using Open-Meteo API

### 📄 PDF Itinerary Generator
- Generates downloadable travel itineraries

### 💳 Travel Wallet System
- Deposit/withdraw simulation
- Booking confirmation workflow

---

## 🛠️ Tech Stack

| Technology | Usage |
|------------|-------|
| Python | Backend Logic |
| Streamlit | Web Application |
| LangChain | AI Workflow |
| Gemini API | Natural Language Understanding |
| Pandas | Data Processing |
| Folium | Interactive Maps |
| FPDF | PDF Generation |

---

## 🧠 AI Workflow

1. User enters travel request
2. Gemini AI extracts trip details
3. Attractions are filtered
4. Hotels and transport are assigned
5. Costs are calculated
6. Route is optimized
7. PDF itinerary is generated

---

## 📂 Dataset

The prototype currently uses local CSV datasets for:
- Places
- Hotels
- Transport services

This project is a prototype and does not use real integrations with platforms like Booking.com, Rapido, Ola, etc.

---

## 📸 Screenshots

(Add screenshots here)

---

## 🔮 Future Improvements

- Real hotel booking integrations
- Live transport APIs
- Restaurant recommendations
- AI budget optimization
- Multi-city trip planning
- User authentication
- Payment gateway integration

---

## ▶️ Installation

```bash
git clone <your-repo-link>
cd ai-travel-planner

pip install -r requirements.txt

streamlit run app.py
