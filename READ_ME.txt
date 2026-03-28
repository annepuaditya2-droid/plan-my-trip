🧠 Smart Planner – AI Travel Planner

Smart Planner is an AI-powered travel planning web app that automatically creates personalized travel itineraries based on user preferences such as budget, interests, number of travelers, and trip duration.

The system uses LLM (Gemini AI via LangChain) to understand natural language travel requests and generate a complete trip plan, including:

destination recommendations
hotel suggestions
transport options
cost estimation
optimized route map
real-time weather
downloadable itinerary PDF
✨ Features
🤖 AI Travel Planning

Users can simply type:

“I want to visit Jaipur for 2 days with 3 friends, medium budget hotel, historical places, prefer cab”

The AI extracts:

city
number of people
days
interests
transport preference
budget type

and automatically generates a full trip plan.

🧭 Dual Mode System

Users can plan trips in two ways:

1. AI Mode

Enter natural language prompt
AI creates plan automatically

2. Manual Mode

Select city
choose places
choose hotel type
choose transport
customize trip
🏨 Smart Hotel Recommendation

Hotels are selected based on:

budget type
rating
room availability

Budget options:

low budget
medium
luxury
🚕 Intelligent Transport Assignment

Transport is automatically assigned based on:

user preference
vehicle availability
fallback logic if unavailable

Transport types:

cab
auto
bike
bus
💰 Cost Estimation Engine

System calculates total cost including:

hotel cost
transport cost (per km)
food estimate
entry tickets

Example formula:

Total Cost =
Hotel Cost +
Transport Cost +
Food Cost +
Entry Fees

🗺️ Route Optimization

Destinations are optimized based on distance from city center to reduce travel time.

Interactive map shows:

destination markers
travel route path
🌤️ Live Weather Integration

Weather data is fetched using Open-Meteo API.

Shows:

temperature
wind speed

Helps users plan better.

💳 Travel Wallet Simulation

Simulates real booking flow:

deposit money
confirm booking
deduct balance

Adds real-world experience.

📄 PDF Itinerary Generator

Generates structured travel plan including:

day wise schedule
travel timing
hotel details
destination visits

Users can download itinerary as PDF.

🛠️ Tech Stack
Frontend
Streamlit
AI / NLP
Google Gemini
LangChain
Pydantic
Data Processing
Pandas
CSV datasets
Maps & Visualization
Folium
streamlit-folium
APIs
Open Meteo Weather API
Document Generation
FPDF
📂 Project Structure
smart-planner/
│
├── app.py
├── places.csv
├── hotels.csv
├── transport.csv
│
├── modules/
│   ├── ai_engine.py
│   ├── cost_calculator.py
│   ├── route_optimizer.py
│   ├── pdf_generator.py
│
└── README.md