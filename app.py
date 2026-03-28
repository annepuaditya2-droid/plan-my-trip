import streamlit as st
import pandas as pd
import os
import time
import math
import requests
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from fpdf import FPDF

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
os.environ["GOOGLE_API_KEY"] = "AIzaSyB8927dQuaRax3qM_nrYC_X03aaunSwwbk"
class TripIntent(BaseModel):
    city: str = Field(description="The city the user wants to visit. Must be exactly: Delhi, Jaipur, Goa, Hyderabad, Bangalore, Chennai, Mumbai, or Varanasi.")
    people: int = Field(description="Number of people traveling. Default is 2.")
    days: int = Field(description="Number of days for the trip. Default is 2.")
    budget_type: str = Field(description="Hotel preference. Must be exactly: 'low budget', 'medium', or 'luxury'.")
    transport_type: str = Field(description="Transport preference. Must be exactly: 'auto', 'cab', or 'bus'.")
    interests: list[str] = Field(description="List of place categories they want to see, like 'historical', 'nature', 'spiritual', 'shopping', 'museum'.")

def analyze_user_prompt(user_text):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    parser = PydanticOutputParser(pydantic_object=TripIntent)
    prompt = PromptTemplate(
        template="Analyze the user's travel request and extract the parameters.\n{format_instructions}\nUser Request: {query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    return chain.invoke({"query": user_text})
def get_current_weather(lat, lon):
    """Fetches real-time weather from Open-Meteo (No API Key needed!)"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = requests.get(url)
        data = response.json()
        current = data['current_weather']
        return current['temperature'], current['windspeed']
    except Exception as e:
        return None, None
def create_mock_data():
    needs_regen = False    
    if os.path.exists("places.csv"):
        temp_df = pd.read_csv("places.csv")
        if len(temp_df) < 20: 
            needs_regen = True
    if not os.path.exists("places.csv") or needs_regen:
        data = [
            ["Delhi", "Red Fort", "historical", 35, 2.0, 5, 28.6562, 77.2410],
            ["Delhi", "Qutub Minar", "historical", 30, 2.0, 15, 28.5245, 77.1855],
            ["Delhi", "India Gate", "monument", 0, 1.0, 2, 28.6129, 77.2295],
            ["Delhi", "Lotus Temple", "spiritual", 0, 1.5, 12, 28.5535, 77.2588],
            ["Delhi", "Akshardham", "spiritual", 0, 3.0, 10, 28.6127, 77.2773],
            ["Delhi", "Chandni Chowk", "shopping", 0, 2.5, 6, 28.6505, 77.2303],
            ["Jaipur", "Amber Fort", "historical", 100, 3.0, 11, 26.9855, 75.8513],
            ["Jaipur", "Hawa Mahal", "historical", 50, 1.0, 1, 26.9239, 75.8267],
            ["Jaipur", "City Palace", "museum", 200, 2.0, 2, 26.9255, 75.8236],
            ["Jaipur", "Jal Mahal", "monument", 50, 1.0, 8, 26.9673, 75.8456],
            ["Jaipur", "Albert Hall Museum", "museum", 40, 1.5, 4, 26.9116, 75.8193],
            ["Goa", "Baga Beach", "nature", 0, 3.0, 18, 15.5528, 73.7514],
            ["Goa", "Dudhsagar Falls", "nature", 100, 4.0, 60, 15.3144, 74.3143],
            ["Goa", "Anjuna Beach", "nature", 0, 2.5, 20, 15.5819, 73.7426],
            ["Goa", "Chapora Fort", "historical", 0, 1.5, 22, 15.6057, 73.7346],
            ["Goa", "Palolem Beach", "nature", 0, 3.0, 70, 15.0099, 74.0232],
            ["Hyderabad", "Charminar", "historical", 25, 1.0, 4, 17.3616, 78.4747],
            ["Hyderabad", "Golconda Fort", "historical", 25, 2.5, 12, 17.3833, 78.4011],
            ["Hyderabad", "Hussain Sagar Lake", "nature", 0, 1.5, 5, 17.4239, 78.4738],
            ["Hyderabad", "Chowmahalla Palace", "historical", 60, 2.0, 5, 17.3578, 78.4717],
            ["Hyderabad", "Nehru Zoological Park", "nature", 50, 3.5, 16, 17.3496, 78.4510],
            ["Bangalore", "Lalbagh Garden", "nature", 30, 2.0, 4, 12.9507, 77.5848],
            ["Bangalore", "Cubbon Park", "nature", 0, 1.5, 1, 12.9779, 77.5952],
            ["Bangalore", "Bangalore Palace", "historical", 230, 2.0, 5, 12.9988, 77.5921],
            ["Bangalore", "Vidhana Soudha", "monument", 0, 1.0, 2, 12.9796, 77.5906],
            ["Bangalore", "Wonderla", "adventure", 1200, 6.0, 28, 12.8343, 77.4010],
            ["Chennai", "Marina Beach", "nature", 0, 2.0, 5, 13.0500, 80.2824],
            ["Chennai", "Kapaleeshwarar Temple", "spiritual", 0, 1.0, 7, 13.0335, 80.2697],
            ["Chennai", "Government Museum", "museum", 50, 2.5, 4, 13.0732, 80.2566],
            ["Chennai", "Elliot Beach", "nature", 0, 2.0, 10, 13.0003, 80.2736],
            ["Chennai", "Guindy National Park", "nature", 20, 2.0, 12, 13.0076, 80.2389],
            ["Mumbai", "Gateway of India", "monument", 0, 1.0, 2, 18.9220, 72.8347],
            ["Mumbai", "Marine Drive", "nature", 0, 1.5, 3, 18.9440, 72.8227],
            ["Mumbai", "Siddhivinayak Temple", "spiritual", 0, 1.0, 8, 19.0166, 72.8302],
            ["Mumbai", "Haji Ali Dargah", "spiritual", 0, 1.5, 6, 18.9827, 72.8089],
            ["Mumbai", "Sanjay Gandhi National Park", "nature", 60, 4.0, 30, 19.2147, 72.9106],
            ["Varanasi", "Kashi Vishwanath Temple", "spiritual", 0, 1.5, 2, 25.3109, 83.0107],
            ["Varanasi", "Dashashwamedh Ghat", "cultural", 0, 1.0, 1, 25.3065, 83.0106],
            ["Varanasi", "Sarnath Museum", "historical", 20, 2.0, 10, 25.3811, 83.0242],
            ["Varanasi", "Ramnagar Fort", "historical", 50, 2.0, 14, 25.2698, 83.0252],
            ["Varanasi", "Assi Ghat", "cultural", 0, 1.5, 4, 25.2886, 83.0055],
        ]
        pd.DataFrame(data, columns=["city", "place_name", "category", "entry_fee", "avg_time_spent", "distance_from_center", "lat", "lon"]).to_csv("places.csv", index=False)

    if not os.path.exists("hotels.csv") or needs_regen:
        pd.DataFrame({
            "hotel_name": [
                "Backpacker Hostel", "City Budget Inn", "Moonlight Hostel", "Nomad Pods", "Budget Stay", "Wanderers Nest",
                "Standard Hotel", "Riverside View", "Urban Retreat", "Comfort Inn", "Oasis Hotel", "Zenith Rooms", 
                "Grand Palace", "Luxury Resort", "Taj View", "Royal Heritage", "Elite Suites", "The Crown Resort"
            ],
            "price_per_night": [
                40, 60, 35, 50, 55, 45,
                150, 180, 200, 160, 220, 190,
                500, 800, 750, 600, 900, 850
            ],
            "rating": [
                4.0, 3.8, 4.3, 4.1, 3.9, 4.4,
                4.2, 4.5, 4.3, 4.1, 4.6, 4.4,
                4.8, 4.7, 4.9, 4.6, 4.8, 4.9
            ],
            "location_type": [
                "low budget", "low budget", "low budget", "low budget", "low budget", "low budget",
                "medium", "medium", "medium", "medium", "medium", "medium",
                "luxury", "luxury", "luxury", "luxury", "luxury", "luxury"
            ],
            "available_rooms": [
                10, 5, 8, 12, 4, 6,
                2, 3, 5, 8, 4, 7,
                0, 5, 2, 4, 1, 3 
            ] 
        }).to_csv("hotels.csv", index=False)

    if not os.path.exists("transport.csv") or needs_regen:
        pd.DataFrame({
            "vehicle_type": ["bus", "auto", "bike", "cab"],
            "price_per_km": [1, 2, 1.5, 3],
            "max_capacity": [40, 3, 2, 4],
            "available_units": [5, 0, 10, 2] 
        }).to_csv("transport.csv", index=False)

create_mock_data()

df_places = pd.read_csv("places.csv")
df_hotels = pd.read_csv("hotels.csv")
df_transport = pd.read_csv("transport.csv")
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 0
if 'step' not in st.session_state:
    st.session_state.step = "input" 
# Add a mode tracker for AI vs Manual
if 'use_ai_mode' not in st.session_state:
    st.session_state.use_ai_mode = False
def optimize_route(destinations_df):
    return destinations_df.sort_values(by="distance_from_center").reset_index(drop=True)
def get_hotel_options(pref):
    suitable = df_hotels[(df_hotels['location_type'] == pref) & (df_hotels['available_rooms'] > 0)]
    if suitable.empty:
        suitable = df_hotels[df_hotels['available_rooms'] > 0]
    return suitable.sort_values(by="rating", ascending=False).head(5)
def assign_transport(primary, secondary):
    t_df = df_transport
    p_trans = t_df[t_df['vehicle_type'] == primary].iloc[0]
    if p_trans['available_units'] > 0:
        return p_trans, "Primary"
    
    s_trans = t_df[t_df['vehicle_type'] == secondary].iloc[0]
    if s_trans['available_units'] > 0:
        return s_trans, "Secondary (Primary Unavailable)"
    
    available = t_df[t_df['available_units'] > 0].iloc[0]
    return available, "Tertiary Fallback"

def calculate_costs(hotel_price, transport, route_df, days, num_people):
    rooms_needed = math.ceil(num_people / 2) 
    hotel_cost = hotel_price * days * rooms_needed
    
    vehicles_needed = math.ceil(num_people / transport['max_capacity'])
    total_km = route_df['distance_from_center'].sum() * 2 + 15 + 20 
    transport_cost = total_km * transport['price_per_km'] * vehicles_needed
    
    food_cost = 50 * days * num_people 
    entry_tickets = route_df['entry_fee'].sum() * num_people
    
    total = hotel_cost + transport_cost + food_cost + entry_tickets
    return hotel_cost, transport_cost, food_cost, entry_tickets, total

def generate_itinerary_pdf(city, start_date, arrival_time, days, num_people, hotel, transport, route, total_cost):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"AI Travel Planner: {city} Itinerary", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Confirmed Booking Details", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 6, txt=f"Travelers: {num_people}", ln=True)
    pdf.cell(200, 6, txt=f"Hotel: {hotel['hotel_name']} (Paid & Confirmed)", ln=True)
    pdf.cell(200, 6, txt=f"Local Transport: {transport['vehicle_type'].capitalize()} (Approved)", ln=True)
    pdf.cell(200, 6, txt=f"Total Cost: ${total_cost}", ln=True)
    pdf.ln(10)
    
    places_per_day = len(route) // days
    places_per_day = 1 if places_per_day == 0 else places_per_day
    current_place_idx = 0
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, txt=f"Day {day + 1} - {current_date.strftime('%A, %b %d')}", ln=True)
        pdf.set_font("Arial", size=11)
        
        if day == 0:
            current_time = datetime.combine(current_date, arrival_time)
            pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Arrive at {city} Station/Airport", ln=True)
            current_time += timedelta(minutes=25)
            pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Travel to {hotel['hotel_name']}", ln=True)
            current_time += timedelta(minutes=45)
        else:
            current_time = datetime.combine(current_date, datetime.strptime("09:00 AM", "%I:%M %p").time())
            pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Start day from {hotel['hotel_name']}", ln=True)
            
        tasks_today = 0
        while current_place_idx < len(route) and tasks_today < places_per_day:
            place = route.iloc[current_place_idx]
            current_time += timedelta(minutes=15)
            pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Visit {place['place_name']}", ln=True)
            current_time += timedelta(hours=place['avg_time_spent'])
            tasks_today += 1
            current_place_idx += 1
            
            if current_time.hour >= 13 and current_time.hour < 15:
                pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Lunch Break", ln=True)
                current_time += timedelta(hours=1)
                
        current_time += timedelta(minutes=20)
        pdf.cell(200, 6, txt=f"{current_time.strftime('%I:%M %p')} : Return to {hotel['hotel_name']}", ln=True)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

st.set_page_config(page_title="AI Travel Planner", layout="wide")
st.title("SMART PLANNER")

with st.sidebar:
    st.header("💳 Travel Wallet")
    st.metric("Current Balance", f"$ {st.session_state.wallet_balance}")
    
    colA, colB = st.columns(2)
    with colA:
        add_amount = st.number_input("Deposit Amount", min_value=0, step=100)
        if st.button("Deposit"):
            st.session_state.wallet_balance += add_amount
            st.rerun()
    with colB:
        withdraw_amount = st.number_input("Withdraw Amount", min_value=0, step=100)
        if st.button("Withdraw"):
            if withdraw_amount <= st.session_state.wallet_balance:
                st.session_state.wallet_balance -= withdraw_amount
                st.success(f"Withdrew $ {withdraw_amount}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Insufficient balance!")
        
    st.markdown("---")
    
    # --- TOGGLE BUTTON FOR AI vs MANUAL ---
    button_label = "Switch to Manual Mode ⚙️" if st.session_state.use_ai_mode else "Try AI Mode ✨"
    if st.button(button_label, use_container_width=True):
        st.session_state.use_ai_mode = not st.session_state.use_ai_mode
        st.rerun()
    
    st.markdown("---")
    if st.session_state.use_ai_mode:
        st.header("✨ AI Planner")
        st.write("Just tell me what you want to do!")
        
        user_input = st.text_area(
            "Example: 'I want to go to Jaipur with 3 friends for 2 days. We want a luxury hotel, we like historical places, and we prefer cabs.'",
            height=120
        )
        
        # Keep Date and Time inputs available in AI mode so we don't lose that feature!
        col_date, col_time = st.columns(2)
        with col_date:
            ai_travel_date = st.date_input("Start Date", datetime.today(), key="ai_date")
        with col_time:
            ai_arrival_time = st.time_input("Arrival Time", datetime.strptime("09:00 AM", "%I:%M %p").time(), key="ai_time")
            
        if st.button("Generate Plan with AI", type="primary"):
            if not user_input:
                st.warning("Please enter a prompt first.")
            else:
                with st.spinner("🧠 AI is analyzing your request..."):
                    try:
                        intent = analyze_user_prompt(user_input)
                        city_places = df_places[df_places.city.str.lower() == intent.city.lower()]
                        
                        if city_places.empty:
                            st.error(f"Oops! The AI understood you want to go to *{intent.city}*, but we don't have any data for that city. Try Delhi or Jaipur!")
                        else:
                            if intent.interests:
                                filtered_places = city_places[city_places.category.isin(intent.interests)]
                                if filtered_places.empty: 
                                    filtered_places = city_places.head(4)
                            else:
                                filtered_places = city_places.head(4)

                            # Populate the exact same temporary session variables used by manual mode!
                            st.session_state.temp_city = intent.city
                            st.session_state.temp_date = ai_travel_date
                            st.session_state.temp_time = ai_arrival_time
                            st.session_state.temp_days = intent.days
                            st.session_state.temp_people = intent.people
                            st.session_state.temp_selected_places = filtered_places['place_name'].tolist()
                            st.session_state.temp_hotel_pref = intent.budget_type
                            st.session_state.temp_primary_transport = intent.transport_type
                            st.session_state.temp_secondary_transport = "cab" # AI default fallback
                            
                            st.session_state.step = "preview"
                            st.rerun()
                    except Exception as e:
                        st.error("The AI had trouble understanding that. Please ensure you mention a valid city and some preferences!")

    else:
        st.header("1. The Journey")
        selected_city = st.selectbox("Destination City", df_places['city'].unique())
        num_people = st.number_input("Number of Travelers", min_value=1, value=2, step=1)
        
        col_date, col_time = st.columns(2)
        with col_date:
            travel_date = st.date_input("Start Date", datetime.today())
        with col_time:
            arrival_time = st.time_input("Arrival Time", datetime.strptime("09:00 AM", "%I:%M %p").time())
            
        days = st.number_input("Days", min_value=1, value=2, step=1)
        
        city_attractions = df_places[df_places['city'] == selected_city]
        selected_places = st.multiselect(f"Destinations", city_attractions['place_name'].tolist(), default=city_attractions['place_name'].tolist()[:2])
        
        st.header("2. Preferences")
        hotel_pref = st.selectbox("Hotel Level", ["low budget", "medium", "luxury"])
        
        st.markdown("Transport Preferences")
        primary_transport = st.selectbox("Primary Choice", ["cab", "auto", "bike", "bus"], index=0)
        secondary_transport = st.selectbox("Secondary Choice", ["cab", "auto", "bike", "bus"], index=1)
        
        if st.button("Calculate Quotes & Preview Trip", type="primary"):
            if selected_places:
                st.session_state.step = "preview"
                # Store manual selections in session
                st.session_state.temp_city = selected_city
                st.session_state.temp_date = travel_date
                st.session_state.temp_time = arrival_time
                st.session_state.temp_days = days
                st.session_state.temp_people = num_people
                st.session_state.temp_selected_places = selected_places
                st.session_state.temp_hotel_pref = hotel_pref
                st.session_state.temp_primary_transport = primary_transport
                st.session_state.temp_secondary_transport = secondary_transport
                st.rerun()
            else:
                st.warning("Please select at least one destination.")
if st.session_state.step == "preview":
    st.header("📝 Step 1: Preview & Customize Your Trip")
    
    # Retrieve data from session state (works perfectly for BOTH Manual and AI modes!)
    preview_places = st.session_state.temp_selected_places
    preview_hotel_pref = st.session_state.temp_hotel_pref
    preview_primary_transport = st.session_state.temp_primary_transport
    preview_secondary_transport = st.session_state.temp_secondary_transport
    
    route_df = df_places[df_places['place_name'].isin(preview_places)]
    optimized_df = optimize_route(route_df)
    
    assigned_transport, transport_status = assign_transport(preview_primary_transport, preview_secondary_transport)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("🏨 Select Your Hotel")
        st.info(f"AI found the top available options based on your '{preview_hotel_pref}' preference.")
        hotel_options = get_hotel_options(preview_hotel_pref)
        
        hotel_display_list = []
        for _, h in hotel_options.iterrows():
            hotel_display_list.append(f"{h['hotel_name']} ({h['rating']}⭐) - $ {h['price_per_night']}/night per room")
            
        selected_hotel_str = st.radio("Choose one to proceed:", hotel_display_list)
        
        selected_hotel_name = selected_hotel_str.split(" (")[0]
        final_hotel = hotel_options[hotel_options['hotel_name'] == selected_hotel_name].iloc[0]

    with col2:
        st.subheader("💰 Cost Estimate")
        h_cost, t_cost, f_cost, e_cost, total_cost = calculate_costs(
            final_hotel['price_per_night'], assigned_transport, optimized_df, st.session_state.temp_days, st.session_state.temp_people
        )
        
        st.write(f"Travelers: {st.session_state.temp_people}")
        st.write(f"Rooms Needed: {math.ceil(st.session_state.temp_people / 2)}")
        st.markdown("---")
        st.metric(f"Hotel ({st.session_state.temp_days} days)", f"$ {h_cost}")
        st.metric("Local Transport", f"$ {t_cost}")
        st.metric(f"Food & Entry (x{st.session_state.temp_people})", f"$ {f_cost + e_cost}")
        st.markdown(f"### Total: $ {total_cost}")
        st.markdown("---")
        st.subheader(f"🌤️ Live Weather in {st.session_state.temp_city}")
        # We use the coordinates of the first place in their route to get the city's weather
        city_lat = optimized_df.iloc[0]['lat']
        city_lon = optimized_df.iloc[0]['lon']
        
        temp, wind = get_current_weather(city_lat, city_lon)
        if temp is not None:
            w_col1, w_col2 = st.columns(2)
            w_col1.metric("Temperature", f"{temp} °C")
            w_col2.metric("Wind Speed", f"{wind} km/h")
        else:
            st.warning("Weather data currently unavailable.")
        # ---------------------------
        
        if st.button("Confirm Booking & Pay", type="primary"):
            if st.session_state.wallet_balance >= total_cost:
                st.toast(f"📡 Sending booking request to {final_hotel['hotel_name']}...", icon="🏨")
                time.sleep(1.5)
                st.toast(f"📡 Requesting ride approval from Uber/Rapido...", icon="📱")
                time.sleep(1.5)
                
                st.session_state.wallet_balance -= total_cost
                st.session_state.locked_total = total_cost
                st.session_state.locked_hotel = final_hotel
                st.session_state.locked_transport = assigned_transport
                st.session_state.locked_route = optimized_df
                st.session_state.step = "booked"
                st.rerun()
            else:
                st.error("❌ Insufficient Wallet Balance. Please deposit funds in the sidebar.")
# 7. UI STATE: BOOKED & ITINERARY
elif st.session_state.step == "booked":
    st.success("✅ PAYMENT SUCCESSFUL & TRIP BOOKED!")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🗺️ Interactive Route Map")
        df_locked = st.session_state.locked_route
        map_center = [df_locked['lat'].mean(), df_locked['lon'].mean()]
        m = folium.Map(location=map_center, zoom_start=12)
        
        route_coords = []
        for i, row in df_locked.iterrows():
            folium.Marker([row['lat'], row['lon']], popup=row['place_name']).add_to(m)
            route_coords.append([row['lat'], row['lon']])
        
        folium.PolyLine(route_coords, color="blue", weight=2.5, opacity=0.8).add_to(m)
        st_folium(m, width=700, height=400)

        st.subheader(f"🗓️ Itinerary ({st.session_state.temp_city})")
        
        places_per_day = len(df_locked) // st.session_state.temp_days
        places_per_day = 1 if places_per_day == 0 else places_per_day
        current_place_idx = 0
        
        for day in range(st.session_state.temp_days):
            current_date = st.session_state.temp_date + timedelta(days=day)
            st.markdown(f"### Day {day + 1} - {current_date.strftime('%A, %b %d')}")
            
            if day == 0:
                current_time = datetime.combine(current_date, st.session_state.temp_time)
                st.write(f"- 🚉 {current_time.strftime('%I:%M %p')} | Arrive at {st.session_state.temp_city} Station/Airport.")
                current_time += timedelta(minutes=15)
                
                st.write(f"- 📱 {current_time.strftime('%I:%M %p')} | Uber/Rapido approval received for {st.session_state.locked_transport['vehicle_type']}.")
                current_time += timedelta(minutes=10)
                
                st.write(f"- 🚕 {current_time.strftime('%I:%M %p')} | Travel to {st.session_state.locked_hotel['hotel_name']} and drop luggage.")
                current_time += timedelta(minutes=45)
            else:
                current_time = datetime.combine(current_date, datetime.strptime("09:00 AM", "%I:%M %p").time())
                st.write(f"- 🏨 {current_time.strftime('%I:%M %p')} | Start day from {st.session_state.locked_hotel['hotel_name']}.")
            
            tasks_today = 0
            while current_place_idx < len(df_locked) and tasks_today < places_per_day:
                place = df_locked.iloc[current_place_idx]
                
                st.write(f"- 📱 {current_time.strftime('%I:%M %p')} | Uber/Rapido approval received for ride to {place['place_name']}.")
                current_time += timedelta(minutes=15)
                
                st.write(f"- 📍 {current_time.strftime('%I:%M %p')} | Visit {place['place_name']} ({place['avg_time_spent']} hrs)")
                current_time += timedelta(hours=place['avg_time_spent'])
                tasks_today += 1
                current_place_idx += 1
                
                if current_time.hour >= 13 and current_time.hour < 15:
                    st.write(f"- 🍽️ {current_time.strftime('%I:%M %p')} | Lunch Break.")
                    current_time += timedelta(hours=1)
            
            st.write(f"- 📱 {current_time.strftime('%I:%M %p')} | Uber/Rapido approval received for return trip.")
            current_time += timedelta(minutes=20)
            st.write(f"- 🚕 {current_time.strftime('%I:%M %p')} | Return to {st.session_state.locked_hotel['hotel_name']} and rest.")
            st.write("")

    with col2:
        st.info(f"💵 Remaining Balance: $ {st.session_state.wallet_balance}")
        st.markdown("### Confirmed Details")
        st.write(f"🏨 {st.session_state.locked_hotel['hotel_name']} (Booking Approved)")
        st.write(f"🚕 {st.session_state.locked_transport['vehicle_type'].capitalize()} (Uber/Rapido Approved)")
        st.write(f"👥 {st.session_state.temp_people} Travelers")
        st.metric(f"Total Paid", f"$ {st.session_state.locked_total}")
        
        st.markdown("---")
        
        pdf_bytes = generate_itinerary_pdf(
            st.session_state.temp_city, 
            st.session_state.temp_date, 
            st.session_state.temp_time, 
            st.session_state.temp_days, 
            st.session_state.temp_people, 
            st.session_state.locked_hotel, 
            st.session_state.locked_transport, 
            st.session_state.locked_route, 
            st.session_state.locked_total
        )
        
        st.download_button(
            label="📄 Download Itinerary PDF",
            data=pdf_bytes,
            file_name=f"{st.session_state.temp_city}_Itinerary.pdf",
            mime="application/pdf"
        )
        
        if st.button("Start New Plan"):
            st.session_state.step = "input"
            st.rerun()