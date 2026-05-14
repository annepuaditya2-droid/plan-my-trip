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
os.environ["GOOGLE_API_KEY"] = "ADD THE API"
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
def load_data():
    """Load data from separate CSV files"""
    try:
        df_places = pd.read_csv("data_places.csv")
        df_hotels = pd.read_csv("data_hotels.csv")
        df_transport = pd.read_csv("data_transport.csv")
        return df_places, df_hotels, df_transport
    except FileNotFoundError as e:
        st.error(f"❌ Error loading data files: {e}")
        st.stop()

# Load all data from separate CSV files
df_places, df_hotels, df_transport = load_data()
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 0
if 'step' not in st.session_state:
    st.session_state.step = "input" 
# Add a mode tracker for AI vs Manual
if 'use_ai_mode' not in st.session_state:
    st.session_state.use_ai_mode = False
def optimize_route(destinations_df):
    return destinations_df.sort_values(by="distance_from_center").reset_index(drop=True)
def get_hotel_options(city, pref):
    suitable = df_hotels[(df_hotels['city'] == city) & (df_hotels['location_type'] == pref) & (df_hotels['available_rooms'] > 0)]
    if suitable.empty:
        suitable = df_hotels[(df_hotels['city'] == city) & (df_hotels['available_rooms'] > 0)]
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
        
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, bytearray):
        return bytes(pdf_bytes)
    return pdf_bytes

st.set_page_config(page_title="AI Travel Planner", layout="wide", initial_sidebar_state="expanded")

# Custom CSS Styling
st.markdown("""
<style>
    /* Main Theme */
    :root {
        --primary-color: #FF6B35;
        --secondary-color: #004E89;
        --accent-color: #F77F00;
        --success-color: #06A77D;
        --bg-light: #F8F9FA;
    }
    
    /* Title Styling */
    .main-title {
        background: linear-gradient(135deg, #FF6B35 0%, #F77F00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5em !important;
        font-weight: 800 !important;
        margin-bottom: 0.5em;
        text-align: center;
        letter-spacing: -2px;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 2em;
        font-weight: 500;
    }
    
    /* Card Styling */
    .card-container {
        background: white;
        border-radius: 12px;
        padding: 1.5em;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        border-left: 5px solid #FF6B35;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1em;
        color: #333;
    }
    
    .card-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .hotel-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        border-radius: 12px;
        padding: 1.5em;
        margin: 1em 0;
        border-left: 5px solid #FF6B35;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: #111;
    }
    
    .hotel-card:hover {
        box-shadow: 0 8px 20px rgba(255, 107, 53, 0.2);
        transform: translateY(-3px);
    }
    
    /* Progress Indicator */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin: 2em 0;
        padding: 1.5em;
        background: linear-gradient(90deg, #f0f0f0 0%, #ffffff 50%, #f0f0f0 100%);
        border-radius: 10px;
    }
    
    .progress-step {
        text-align: center;
        flex: 1;
        color: #1f2937;
    }
    
    .progress-step .step-label {
        color: #1f2937;
        font-size: 0.95em;
        font-weight: 700;
        margin-top: 0.35em;
        line-height: 1.2;
    }
    
    .progress-step.active .step-label,
    .progress-step.completed .step-label {
        color: #111;
    }
    
    .progress-step.active .step-circle {
        background: linear-gradient(135deg, #FF6B35 0%, #F77F00 100%);
        color: white;
        box-shadow: 0 0 15px rgba(255, 107, 53, 0.4);
    }
    
    .progress-step.completed .step-circle {
        background: #06A77D;
        color: white;
        font-size: 1.5em;
    }
    
    .step-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5em;
        font-weight: bold;
        font-size: 1.2em;
        transition: all 0.3s ease;
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B35 0%, #F77F00 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        font-size: 1em !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(255, 107, 53, 0.3) !important;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5em;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 4px solid #FF6B35;
    }
    
    .metric-value {
        font-size: 2em;
        font-weight: 800;
        color: #FF6B35;
        margin: 0.5em 0;
    }
    
    .metric-label {
        font-size: 0.9em;
        color: #333;
        font-weight: 600;
    }
    
    /* Section Headers */
    .section-header {
        border-bottom: 3px solid rgba(255, 107, 53, 0.85);
        padding-bottom: 0.5em;
        margin-bottom: 1.5em;
        font-size: 1.5em;
        font-weight: 700;
        color: #fff;
    }
    
    /* Info Boxes */
    .info-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%);
        border-left: 4px solid #004E89;
        padding: 1em;
        border-radius: 8px;
        margin: 1em 0;
        color: #333;
    }
    
    /* Success State */
    .success-banner {
        background: linear-gradient(135deg, #06A77D 0%, #118b74 100%);
        color: white;
        padding: 2em;
        border-radius: 12px;
        text-align: center;
        margin: 1.5em 0;
        box-shadow: 0 8px 25px rgba(6, 168, 125, 0.2);
    }

    .manual-panel-header {
        background: #1f2937;
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.12);
        font-size: 1.35em;
        font-weight: 700;
    }

    .manual-step-box {
        background: #111827;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.12);
    }

    .manual-step-box strong {
        color: white;
    }
    
    /* Select Box Styling */
    .stSelectbox, .stMultiSelect {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<div class='main-title'>✈️ SMART PLANNER</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI-Powered Travel Itinerary Generator</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    st.markdown("<div style='text-align: center; margin: 1em 0;'><h2>💳 Travel Wallet</h2></div>", unsafe_allow_html=True)
    
    # Wallet Balance
    wallet_col1, wallet_col2, wallet_col3 = st.columns(3)
    with wallet_col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF6B35 0%, #F77F00 100%); 
                    color: white; padding: 1.5em; border-radius: 12px; text-align: center;'>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 0.5em;'>Balance</div>
            <div style='font-size: 2em; font-weight: 800;'>$ {st.session_state.wallet_balance}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_deposit, col_withdraw = st.columns(2)
    with col_deposit:
        st.markdown("<div style='font-weight: 600; margin-bottom: 0.5em;'>➕ Deposit</div>", unsafe_allow_html=True)
        add_amount = st.number_input("Deposit Amount", min_value=0, step=100, key="deposit_input", label_visibility="collapsed")
        if st.button("Deposit", use_container_width=True, key="deposit_btn"):
            st.session_state.wallet_balance += add_amount
            st.success(f"✅ Added $ {add_amount}")
            time.sleep(1)
            st.rerun()
    
    with col_withdraw:
        st.markdown("<div style='font-weight: 600; margin-bottom: 0.5em;'>➖ Withdraw</div>", unsafe_allow_html=True)
        withdraw_amount = st.number_input("Withdraw Amount", min_value=0, step=100, key="withdraw_input", label_visibility="collapsed")
        if st.button("Withdraw", use_container_width=True, key="withdraw_btn"):
            if withdraw_amount <= st.session_state.wallet_balance:
                st.session_state.wallet_balance -= withdraw_amount
                st.success(f"✅ Withdrew $ {withdraw_amount}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Insufficient balance!")
        
    st.markdown("---")
    
    # --- TOGGLE BUTTON FOR AI vs MANUAL ---
    button_label = "⚙️ Switch to Manual" if st.session_state.use_ai_mode else "✨ Try AI Mode"
    if st.button(button_label, use_container_width=True, key="mode_toggle"):
        st.session_state.use_ai_mode = not st.session_state.use_ai_mode
        st.rerun()
    
    st.markdown("---")
    if st.session_state.use_ai_mode:
        st.markdown("<div class='section-header'>✨ AI Planner</div>", unsafe_allow_html=True)
        st.markdown("<div class='info-box'>Just tell me about your dream trip and I'll create the perfect itinerary!</div>", unsafe_allow_html=True)
        
        user_input = st.text_area(
            "Your Travel Request",
            placeholder="Example: 'I want to visit Jaipur with 3 friends for 2 days. We want a luxury hotel, we like historical places, and we prefer cabs.'",
            height=120,
            label_visibility="collapsed"
        )
        
        # Keep Date and Time inputs available in AI mode so we don't lose that feature!
        col_date, col_time = st.columns(2)
        with col_date:
            ai_travel_date = st.date_input("📅 Start Date", datetime.today(), key="ai_date")
        with col_time:
            ai_arrival_time = st.time_input("⏰ Arrival Time", datetime.strptime("09:00 AM", "%I:%M %p").time(), key="ai_time")
            
        if st.button("✨ Generate Plan with AI", type="primary", use_container_width=True):
            if not user_input:
                st.warning("📝 Please describe your travel plan first.")
            else:
                with st.spinner("🧠 AI is analyzing your request..."):
                    try:
                        intent = analyze_user_prompt(user_input)
                        city_places = df_places[df_places.city.str.lower() == intent.city.lower()]
                        
                        if city_places.empty:
                            st.error(f"❌ Oops! I understood you want to visit **{intent.city}**, but we don't have data for that city.\n\n**Available cities:** Delhi, Jaipur, Goa, Hyderabad, Bangalore, Chennai, Mumbai, Varanasi")
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
                        st.error("❌ Hmm, I couldn't understand that. Make sure to mention a valid city (Delhi, Jaipur, Goa, Hyderabad, Bangalore, Chennai, Mumbai, or Varanasi) and some preferences!")

    else:
        st.markdown("<div class='manual-panel-header'>🗺️ Manual Planner</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='manual-step-box'><strong>Step 1: Your Journey</strong></div>", unsafe_allow_html=True)
        selected_city = st.selectbox("🏙️ Destination City", df_places['city'].unique())
        num_people = st.number_input("👥 Number of Travelers", min_value=1, value=2, step=1)
        
        col_date, col_time = st.columns(2)
        with col_date:
            travel_date = st.date_input("📅 Start Date", datetime.today())
        with col_time:
            arrival_time = st.time_input("⏰ Arrival Time", datetime.strptime("09:00 AM", "%I:%M %p").time())
            
        days = st.number_input("📆 Trip Duration (days)", min_value=1, value=2, step=1)
        
        city_attractions = df_places[df_places['city'] == selected_city]
        selected_places = st.multiselect(
            "📍 Select Attractions",
            city_attractions['place_name'].tolist(),
            default=city_attractions['place_name'].tolist()[:2],
            help="Choose multiple places you want to visit"
        )
        
        st.markdown("<div class='manual-step-box'><strong>Step 2: Your Preferences</strong></div>", unsafe_allow_html=True)
        hotel_pref = st.selectbox("🏨 Hotel Budget Level", ["low budget", "medium", "luxury"])
        
        st.markdown("**🚕 Transport Preferences**", help="Choose your preferred transportation")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            primary_transport = st.selectbox("Primary Choice", ["cab", "auto", "bike", "bus"], index=0)
        with col_t2:
            secondary_transport = st.selectbox("Backup Option", ["cab", "auto", "bike", "bus"], index=1)
        
        if st.button("📋 Preview & Calculate Quotes", type="primary", use_container_width=True):
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
                st.warning("⚠️ Please select at least one destination.")
if st.session_state.step == "preview":
    # Progress Indicator
    st.markdown("""
    <div class='progress-container'>
        <div class='progress-step completed'>
            <div class='step-circle'>✅</div>
            <div class='step-label'>Trip Details</div>
        </div>
        <div class='progress-step active'>
            <div class='step-circle'>2</div>
            <div class='step-label'>Select & Pay</div>
        </div>
        <div class='progress-step'>
            <div class='step-circle'>3</div>
            <div class='step-label'>Itinerary</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>📋 Step 2: Select Hotel & Preview Costs</div>", unsafe_allow_html=True)
    
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
        st.markdown("<div style='font-size: 1.2em; font-weight: 700; margin-bottom: 1em;'>🏨 Hotel Options</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'>Top-rated hotels based on <strong>{st.session_state.temp_hotel_pref}</strong> budget preference</div>", unsafe_allow_html=True)
        
        hotel_options = get_hotel_options(st.session_state.temp_city, st.session_state.temp_hotel_pref)
        
        hotel_display_list = []
        for _, h in hotel_options.iterrows():
            hotel_display_list.append(f"{h['hotel_name']} ({h['rating']}⭐) - $ {h['price_per_night']}/night")
            
        selected_hotel_str = st.radio("Choose one to proceed:", hotel_display_list, key="hotel_radio")
        
        selected_hotel_name = selected_hotel_str.split(" (")[0]
        final_hotel = hotel_options[hotel_options['hotel_name'] == selected_hotel_name].iloc[0]
        
        # Display Hotel Details
        st.markdown(f"""
        <div class='hotel-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1em;'>
                <div>
                    <div style='font-size: 1.3em; font-weight: 700;'>{final_hotel['hotel_name']}</div>
                    <div style='color: #FF6B35; margin: 0.5em 0;'>{'⭐' * int(final_hotel['rating'])} {final_hotel['rating']}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 1.5em; font-weight: 800; color: #FF6B35;'>$ {final_hotel['price_per_night']}</div>
                    <div style='font-size: 0.9em; color: #666;'>per room/night</div>
                </div>
            </div>
            <div style='padding-top: 1em; border-top: 1px solid #eee;'>
                <div>✅ {final_hotel['available_rooms']} rooms available</div>
                <div>✅ {final_hotel['location_type'].title()} accommodation</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='font-size: 1.2em; font-weight: 700; margin-bottom: 1em;'>💰 Cost Breakdown</div>", unsafe_allow_html=True)
        
        # Retrieve data from session state
        preview_places = st.session_state.temp_selected_places
        preview_hotel_pref = st.session_state.temp_hotel_pref
        preview_primary_transport = st.session_state.temp_primary_transport
        preview_secondary_transport = st.session_state.temp_secondary_transport
        
        route_df = df_places[df_places['place_name'].isin(preview_places)]
        optimized_df = optimize_route(route_df)
        
        assigned_transport, transport_status = assign_transport(preview_primary_transport, preview_secondary_transport)
        
        h_cost, t_cost, f_cost, e_cost, total_cost = calculate_costs(
            final_hotel['price_per_night'], assigned_transport, optimized_df, st.session_state.temp_days, st.session_state.temp_people
        )
        
        # Cost breakdown cards
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Travelers</div>
            <div class='metric-value'>{st.session_state.temp_people}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='metric-card' style='margin-top: 0.5em;'>
            <div class='metric-label'>Rooms ({st.session_state.temp_days} nights)</div>
            <div class='metric-value'>$ {h_cost}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='metric-card' style='margin-top: 0.5em;'>
            <div class='metric-label'>Transport & Food</div>
            <div class='metric-value'>$ {t_cost + f_cost}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='metric-card' style='margin-top: 0.5em;'>
            <div class='metric-label'>Entry Fees</div>
            <div class='metric-value'>$ {e_cost}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF6B35 0%, #F77F00 100%); color: white; 
                    padding: 1.5em; border-radius: 12px; text-align: center; margin-top: 1em;'>
            <div style='font-size: 0.95em; opacity: 0.9; margin-bottom: 0.5em;'>TOTAL TRIP COST</div>
            <div style='font-size: 2.5em; font-weight: 800;'>$ {total_cost}</div>
            <div style='font-size: 0.85em; opacity: 0.85; margin-top: 0.5em;'>Per person: $ {total_cost // st.session_state.temp_people}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"<div style='font-size: 1.1em; font-weight: 700; margin-bottom: 0.5em;'>🌤️ Live Weather</div>", unsafe_allow_html=True)
        
        city_lat = optimized_df.iloc[0]['lat']
        city_lon = optimized_df.iloc[0]['lon']
        
        temp, wind = get_current_weather(city_lat, city_lon)
        if temp is not None:
            w_col1, w_col2 = st.columns(2)
            w_col1.metric("🌡️ Temperature", f"{temp}°C")
            w_col2.metric("💨 Wind", f"{wind} km/h")
        else:
            st.info("ℹ️ Weather data currently unavailable.")
        
        st.markdown("---")
        
        if st.button("✅ Confirm & Pay Now", type="primary", use_container_width=True, key="pay_btn"):
            if st.session_state.wallet_balance >= total_cost:
                with st.spinner("⏳ Processing payment..."):
                    time.sleep(1)
                    st.toast(f"🏨 Booking {final_hotel['hotel_name']}...", icon="👍")
                    time.sleep(0.8)
                    st.toast(f"🚕 Arranging {assigned_transport['vehicle_type']}...", icon="👍")
                    time.sleep(0.8)
                    
                    st.session_state.wallet_balance -= total_cost
                    st.session_state.locked_total = total_cost
                    st.session_state.locked_hotel = final_hotel
                    st.session_state.locked_transport = assigned_transport
                    st.session_state.locked_route = optimized_df
                    st.session_state.step = "booked"
                    st.success("✅ Payment successful! Your trip is booked.")
                    time.sleep(1.5)
                    st.rerun()
            else:
                missing = total_cost - st.session_state.wallet_balance
                st.error(f"❌ Insufficient balance! You need $ {missing} more. Please deposit in the wallet.")
# 7. UI STATE: BOOKED & ITINERARY
elif st.session_state.step == "booked":
    # Progress Indicator
    st.markdown("""
    <div class='progress-container'>
        <div class='progress-step completed'>
            <div class='step-circle'>✅</div>
            <div>Trip Details</div>
        </div>
        <div class='progress-step completed'>
            <div class='step-circle'>✅</div>
            <div>Select & Pay</div>
        </div>
        <div class='progress-step active'>
            <div class='step-circle'>3</div>
            <div>Itinerary</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='success-banner'>
        <div style='font-size: 2.5em; margin-bottom: 0.5em;'>✅ Payment Successful!</div>
        <div style='font-size: 1.1em;'>Your dream trip to <strong>""" + st.session_state.temp_city + """</strong> is now booked!</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<div class='section-header'>🗺️ Your Interactive Route Map</div>", unsafe_allow_html=True)
        df_locked = st.session_state.locked_route
        map_center = [df_locked['lat'].mean(), df_locked['lon'].mean()]
        m = folium.Map(location=map_center, zoom_start=12)
        
        route_coords = []
        for i, row in df_locked.iterrows():
            folium.Marker([row['lat'], row['lon']], popup=f"<b>{row['place_name']}</b>", tooltip=row['place_name']).add_to(m)
            route_coords.append([row['lat'], row['lon']])
        
        folium.PolyLine(route_coords, color="#FF6B35", weight=3, opacity=0.9).add_to(m)
        st_folium(m, width=700, height=450)

        st.markdown("<div class='section-header' style='margin-top: 2em;'>🗓️ Your Complete Itinerary</div>", unsafe_allow_html=True)
        
        places_per_day = len(df_locked) // st.session_state.temp_days
        places_per_day = 1 if places_per_day == 0 else places_per_day
        current_place_idx = 0
        
        for day in range(st.session_state.temp_days):
            current_date = st.session_state.temp_date + timedelta(days=day)
            
            st.markdown(f"""
            <div class='card-container' style='background: linear-gradient(135deg, #FFF9E6 0%, #FFF5CC 100%);'>
                <div style='font-size: 1.3em; font-weight: 800; color: #FF6B35;'>
                    📅 Day {day + 1} · {current_date.strftime('%A, %B %d')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if day == 0:
                current_time = datetime.combine(current_date, st.session_state.temp_time)
                st.markdown(f"- 🚉 **{current_time.strftime('%I:%M %p')}** → Arrive at {st.session_state.temp_city} Station/Airport")
                current_time += timedelta(minutes=15)
                
                st.markdown(f"- 📱 **{current_time.strftime('%I:%M %p')}** → Transport approved: {st.session_state.locked_transport['vehicle_type'].upper()}")
                current_time += timedelta(minutes=10)
                
                st.markdown(f"- 🏨 **{current_time.strftime('%I:%M %p')}** → Check-in at {st.session_state.locked_hotel['hotel_name']}")
                current_time += timedelta(minutes=45)
            else:
                current_time = datetime.combine(current_date, datetime.strptime("09:00 AM", "%I:%M %p").time())
                st.markdown(f"- 🏨 **{current_time.strftime('%I:%M %p')}** → Start day from {st.session_state.locked_hotel['hotel_name']}")
            
            tasks_today = 0
            while current_place_idx < len(df_locked) and tasks_today < places_per_day:
                place = df_locked.iloc[current_place_idx]
                
                current_time += timedelta(minutes=15)
                st.markdown(f"- 🚕 **{current_time.strftime('%I:%M %p')}** → Travel to {place['place_name']}")
                
                current_time += timedelta(hours=place['avg_time_spent'])
                st.markdown(f"- 📍 **{current_time.strftime('%I:%M %p')}** → Visit **{place['place_name']}** ({place['avg_time_spent']}h) | Entry: ${place['entry_fee']}")
                
                tasks_today += 1
                current_place_idx += 1
                
                if current_time.hour >= 13 and current_time.hour < 15:
                    st.markdown(f"- 🍽️ **{current_time.strftime('%I:%M %p')}** → Lunch break")
                    current_time += timedelta(hours=1)
            
            current_time += timedelta(minutes=20)
            st.markdown(f"- 🚕 **{current_time.strftime('%I:%M %p')}** → Return to {st.session_state.locked_hotel['hotel_name']}")
            st.markdown("")

    with col2:
        st.markdown("<div class='section-header'>📋 Trip Summary</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='card-container'>
            <div style='margin-bottom: 1em;'>
                <div style='font-size: 0.9em; color: #666; margin-bottom: 0.5em;'>DESTINATION</div>
                <div style='font-size: 1.5em; font-weight: 700;'>{st.session_state.temp_city}</div>
            </div>
            <hr style='margin: 1em 0; border: none; border-top: 1px solid #eee;'>
            <div style='margin-bottom: 1em;'>
                <div style='font-size: 0.85em; margin-bottom: 0.3em;'>🏨 Hotel</div>
                <div style='font-weight: 600;'>{st.session_state.locked_hotel['hotel_name']}</div>
                <div style='font-size: 0.85em; color: #FF6B35; margin-top: 0.3em;'>{'⭐' * int(st.session_state.locked_hotel['rating'])}</div>
            </div>
            <div style='margin-bottom: 1em;'>
                <div style='font-size: 0.85em; margin-bottom: 0.3em;'>🚕 Transport</div>
                <div style='font-weight: 600;'>{st.session_state.locked_transport['vehicle_type'].upper()}</div>
            </div>
            <div style='margin-bottom: 1em;'>
                <div style='font-size: 0.85em; margin-bottom: 0.3em;'>👥 Travelers</div>
                <div style='font-weight: 600;'>{st.session_state.temp_people} people</div>
            </div>
            <div>
                <div style='font-size: 0.85em; margin-bottom: 0.3em;'>📆 Duration</div>
                <div style='font-weight: 600;'>{st.session_state.temp_days} days</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                    padding: 1.5em; border-radius: 12px; border-left: 5px solid #06A77D; margin: 1em 0;'>
            <div style='font-size: 0.9em; color: #2E7D32; margin-bottom: 0.5em;'>💰 Wallet Balance</div>
            <div style='font-size: 1.8em; font-weight: 800; color: #06A77D;'>$ {st.session_state.wallet_balance}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FCE4EC 0%, #F8BBD0 100%); 
                    padding: 1.5em; border-radius: 12px; border-left: 5px solid #FF6B35;'>
            <div style='font-size: 0.9em; color: #C2185B; margin-bottom: 0.5em;'>💳 Amount Paid</div>
            <div style='font-size: 1.8em; font-weight: 800; color: #FF6B35;'>$ {st.session_state.locked_total}</div>
        </div>
        """, unsafe_allow_html=True)
        
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
            label="📄 Download Itinerary (PDF)",
            data=pdf_bytes,
            file_name=f"{st.session_state.temp_city}_Itinerary_{st.session_state.temp_date.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.markdown("---")
        
        if st.button("🔄 Start New Trip", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()
