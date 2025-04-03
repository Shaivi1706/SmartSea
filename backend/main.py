from fastapi import FastAPI, HTTPException
import pandas as pd
import joblib
import os
import numpy as np
import re
from pydantic import BaseModel
from sklearn.preprocessing import LabelEncoder
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv  # Add this import
import requests
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_LAT_PATH = os.path.join(BASE_DIR, "latitude_model.pkl")
MODEL_LON_PATH = os.path.join(BASE_DIR, "longitude_model.pkl")
MODEL_DEPTH_PATH = os.path.join(BASE_DIR, "depth_model.pkl")
COAST_ENCODER_PATH = os.path.join(BASE_DIR, "coast_encoder.pkl")
CSV_PATH = os.path.join(BASE_DIR, "PfzForecast_NORTH TAMILNADU (merged).csv")

# Weather API Configuration
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    print("Warning: OPENWEATHER_API_KEY not found in environment variables")
else :
    print("OPENWEATHER_API_KEY found in environment variables")

# Dictionary of Tamil Nadu coastal locations with their coordinates
TN_COASTAL_LOCATIONS = {
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Cuddalore": {"lat": 11.7480, "lon": 79.7714},
    "Nagapattinam": {"lat": 10.7672, "lon": 79.8449},
    "Rameswaram": {"lat": 9.2876, "lon": 79.3129},
    "Thoothukudi": {"lat": 8.7642, "lon": 78.1348},
    "Kanyakumari": {"lat": 8.0883, "lon": 77.5385},
    "Pondicherry": {"lat": 11.9416, "lon": 79.8083},
    "Pulicat": {"lat": 13.4142, "lon": 80.3175},
    "Karaikal": {"lat": 10.9254, "lon": 79.8380},
    "Mandapam": {"lat": 9.2771, "lon": 79.1253},
    # Add more coastal locations as needed
}

# Load models and other initialization code (unchanged)
models_loaded = True
try:
    model_latitude = joblib.load(MODEL_LAT_PATH)
    print(f"Latitude model loaded from {MODEL_LAT_PATH}")
except Exception as e:
    print(f"Error loading latitude model: {e}")
    model_latitude = None
    models_loaded = False

try:
    model_longitude = joblib.load(MODEL_LON_PATH)
    print(f"Longitude model loaded from {MODEL_LON_PATH}")
except Exception as e:
    print(f"Error loading longitude model: {e}")
    model_longitude = None
    models_loaded = False

try:
    model_depth = joblib.load(MODEL_DEPTH_PATH)
    print(f"Depth model loaded from {MODEL_DEPTH_PATH}")
except Exception as e:
    print(f"Error loading depth model: {e}")
    model_depth = None
    models_loaded = False

# Load dataset
def load_data():
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"CSV data loaded successfully from {CSV_PATH}")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

df = load_data()

# Load or create label encoder for coast locations
try:
    label_encoder = joblib.load(COAST_ENCODER_PATH)
    print(f"Coast encoder loaded from {COAST_ENCODER_PATH}")
except Exception as e:
    print(f"Error loading coast encoder: {e}. Creating a new one.")
    label_encoder = LabelEncoder()
    if df is not None and "From the coast of" in df.columns:
        label_encoder.fit(df["From the coast of"])
        # Save the encoder for future use
        try:
            joblib.dump(label_encoder, COAST_ENCODER_PATH)
            print(f"New coast encoder saved to {COAST_ENCODER_PATH}")
        except Exception as e:
            print(f"Error saving coast encoder: {e}")

# Feature Extraction function (unchanged)
def extract_average(value):
    if isinstance(value, str):
        try:
            # For ranges like "10-15"
            if '-' in value:
                numbers = [float(num.strip()) for num in value.split('-')]
                return np.mean(numbers)
            # For single numbers
            return float(value)
        except ValueError:
            # For other formats, try to extract all numbers
            numbers = list(map(float, re.findall(r'\d+(?:\.\d+)?', value)))
            return np.mean(numbers) if numbers else np.nan
    return value

if df is not None:
    # Create processed features if they don't already exist
    if "Distance (km)" not in df.columns and "Distance (km) From-To" in df.columns:
        df["Distance (km)"] = df["Distance (km) From-To"].apply(extract_average)
    if "Depth (m)" not in df.columns and "Depth (mtr) From-To" in df.columns:
        df["Depth (m)"] = df["Depth (mtr) From-To"].apply(extract_average)
    df.dropna(inplace=True)

# Initialize Google Gemini AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables")
else :
    print("gemini key found")

genai.configure(api_key=GEMINI_API_KEY)

# Weather API Functions
def get_location_coordinates(location):
    """Get latitude and longitude for a location"""
    # First check if it's in our predefined coastal locations
    if location in TN_COASTAL_LOCATIONS:
        return TN_COASTAL_LOCATIONS[location]
    
    # Check for partial matches in our locations
    for key in TN_COASTAL_LOCATIONS:
        if location.lower() in key.lower():
            return TN_COASTAL_LOCATIONS[key]
    
    # Default to Chennai if location not found
    return TN_COASTAL_LOCATIONS["Chennai"]

def get_current_weather(lat, lon):
    """Get current weather conditions from OpenWeatherMap API"""
    if not OPENWEATHER_API_KEY:
        return {
            "temperature": 28,
            "conditions": "API Key Missing",
            "windSpeed": 0,
            "humidity": 75,
            "icon": "01d"
        }
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "temperature": round(data["main"]["temp"]),
                "conditions": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "windSpeed": round(data["wind"]["speed"] * 3.6),  # Convert m/s to km/h
                "humidity": data["main"]["humidity"],
                "icon": data["weather"][0]["icon"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        else:
            print(f"Error from OpenWeatherMap API: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Exception when fetching weather: {str(e)}")
        return None

def get_weather_forecast(lat, lon):
    """Get 5-day weather forecast from OpenWeatherMap API"""
    if not OPENWEATHER_API_KEY:
        return [{"dt_txt": "API Key Missing"}]
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            forecast = []
            
            # Get forecasts for next 5 days, one entry per day
            seen_dates = set()
            for item in data["list"]:
                date = item["dt_txt"].split(" ")[0]
                
                # Only include one forecast per day (at noon if possible)
                if date not in seen_dates:
                    time = item["dt_txt"].split(" ")[1]
                    if "12:00:00" in time or len(forecast) == 0:
                        forecast.append({
                            "date": date,
                            "time": time,
                            "temperature": round(item["main"]["temp"]),
                            "conditions": item["weather"][0]["main"],
                            "description": item["weather"][0]["description"],
                            "windSpeed": round(item["wind"]["speed"] * 3.6),  # Convert m/s to km/h
                            "icon": item["weather"][0]["icon"]
                        })
                        seen_dates.add(date)
                
                # Limit to 5 days
                if len(forecast) >= 5:
                    break
                    
            return forecast
        else:
            print(f"Error from OpenWeatherMap API: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Exception when fetching forecast: {str(e)}")
        return None

def get_marine_forecast(lat, lon):
    """Get marine forecast with sea conditions"""
    if not OPENWEATHER_API_KEY:
        return None
    
    try:
        # Using 3-hour forecast which includes more marine data
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            marine_data = []
            
            # Get next 24 hours in 3-hour increments
            for i in range(min(8, len(data["list"]))):
                item = data["list"][i]
                
                entry = {
                    "time": item["dt_txt"],
                    "wind_speed": round(item["wind"]["speed"] * 3.6),  # Convert m/s to km/h
                    "wind_direction": item["wind"]["deg"],
                    "wind_direction_compass": get_wind_direction(item["wind"]["deg"]),
                    "conditions": item["weather"][0]["main"],
                    "rain_chance": item.get("pop", 0) * 100  # Probability of precipitation (%)
                }
                
                # Add wave data if available
                if "sea_level" in item.get("main", {}):
                    entry["sea_level"] = item["main"]["sea_level"]
                
                marine_data.append(entry)
                
            return marine_data
        else:
            print(f"Error from OpenWeatherMap API: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Exception when fetching marine forecast: {str(e)}")
        return None

def get_wind_direction(degrees):
    """Convert wind direction degrees to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

def get_storm_alerts(lat, lon):
    """Check for storm alerts or severe weather"""
    if not OPENWEATHER_API_KEY:
        return []
    
    try:
        # Use the One Call API to get weather alerts
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        alerts = []
        if response.status_code == 200:
            # Check for actual alerts from API
            if "alerts" in data:
                for alert in data["alerts"]:
                    alerts.append({
                        "title": alert.get("event", "Weather Alert"),
                        "description": alert.get("description", ""),
                        "start": datetime.fromtimestamp(alert["start"]).strftime("%Y-%m-%d %H:%M"),
                        "end": datetime.fromtimestamp(alert["end"]).strftime("%Y-%m-%d %H:%M"),
                        "source": alert.get("sender_name", "Weather Service"),
                        "severity": "severe"
                    })
            
            # Check forecasts for potentially severe conditions
            # We'll create alerts for heavy rain, strong winds, and storms
            if "daily" in data:
                for day in data["daily"][:3]:  # Check next 3 days
                    date = datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d")
                    
                    # Check for heavy rain
                    if "rain" in day and day["rain"] > 20:
                        alerts.append({
                            "title": "Heavy Rain Warning",
                            "description": f"Expected rainfall of {day['rain']}mm on {date}",
                            "start": date,
                            "end": date,
                            "source": "SmartSea System",
                            "severity": "moderate"
                        })
                    
                    # Check for strong winds
                    if day["wind_speed"] > 10:  # About 36 km/h
                        alerts.append({
                            "title": "Strong Wind Warning",
                            "description": f"Expected wind speeds of {round(day['wind_speed'] * 3.6)} km/h on {date}",
                            "start": date,
                            "end": date,
                            "source": "SmartSea System",
                            "severity": "moderate"
                        })
                    
                    # Check for storms/bad weather
                    weather_id = day["weather"][0]["id"]
                    if weather_id < 600:  # Rain and storm IDs are below 600
                        if weather_id < 300:  # Thunderstorm
                            alerts.append({
                                "title": "Thunderstorm Warning",
                                "description": f"Thunderstorms expected on {date}",
                                "start": date,
                                "end": date,
                                "source": "SmartSea System",
                                "severity": "severe"
                            })
                        elif weather_id < 400:  # Drizzle
                            continue  # No alert needed for light drizzle
                        else:  # Rain
                            rain_desc = day["weather"][0]["description"]
                            if "heavy" in rain_desc or "extreme" in rain_desc:
                                alerts.append({
                                    "title": "Heavy Rain Warning",
                                    "description": f"{rain_desc.capitalize()} expected on {date}",
                                    "start": date,
                                    "end": date,
                                    "source": "SmartSea System",
                                    "severity": "moderate"
                                })
            
            return alerts
        else:
            print(f"Error from OpenWeatherMap API: {data.get('message', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Exception when checking for storm alerts: {str(e)}")
        return []

# API Request Models
class FishPredictionRequest(BaseModel):
    coast: str
    bearing: float
    distance: str
    direction: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class WeatherRequest(BaseModel):
    location: str
    coordinates: Optional[Dict[str, float]] = None

# Prepare the fishing knowledge information
fishing_knowledge = """
Important information about Tamil Nadu fishing:
1. Annual fishing ban period: April 15 - June 15
2. International waters are typically marked at distances of 12 nautical miles from the shore
3. The Palk Strait separates Tamil Nadu from Sri Lanka; fishing in this area requires caution
4. The Gulf of Mannar is a protected marine ecosystem with restrictions on fishing
5. Fishing near the international maritime boundary line (IMBL) with Sri Lanka can be risky and should be avoided
6. Powerful LED lights for fishing are banned in many areas
7. During monsoon season (October-December), fishing becomes more dangerous
8. Common fish species in Tamil Nadu waters include sardines, mackerel, tuna, and shrimp
9. Typical fishing boats include catamarans, vallams, and mechanized trawlers
10. Weather conditions can change rapidly, especially during cyclone seasons
"""

# API Endpoints
@app.get("/")
def home():
    status = "Models loaded successfully" if models_loaded else "One or more models failed to load"
    return {
        "message": "Fish Coordinates Prediction API is running!",
        "status": status,
        "available_coasts": list(label_encoder.classes_) if hasattr(label_encoder, 'classes_') else [],
    }

@app.post("/predict")
def predict_coordinates_and_depth(data: FishPredictionRequest):
    # Existing implementation (unchanged)
    if None in (model_latitude, model_longitude, model_depth):
        failed_models = []
        if model_latitude is None: failed_models.append("latitude")
        if model_longitude is None: failed_models.append("longitude")
        if model_depth is None: failed_models.append("depth")
        raise HTTPException(
            status_code=500, 
            detail=f"The following models failed to load: {', '.join(failed_models)}"
        )
    
    try:
        # Convert coast
        if not hasattr(label_encoder, 'classes_'):
            raise HTTPException(
                status_code=500, 
                detail="Coast encoder is not properly initialized"
            )
            
        if data.coast not in label_encoder.classes_:
            return {
                "error": f"Invalid coast location. Available options are: {list(label_encoder.classes_)}"
            }
            
        # Convert distance to numerical value
        distance_avg = extract_average(data.distance)
        if np.isnan(distance_avg):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid distance format: {data.distance}. Expected a number or range (e.g., '10-15')."
            )
            
        # Convert direction to numerical value (1 for East, 0 for West)
        direction_encoded = 1 if data.direction.lower() in ["east", "e"] else 0

        # Prepare input for model prediction
        input_data = np.array([[data.bearing, distance_avg, direction_encoded]])
        
        # Make predictions
        predicted_latitude = model_latitude.predict(input_data)[0]
        predicted_longitude = model_longitude.predict(input_data)[0]
        predicted_depth = model_depth.predict(input_data)[0]

        # Convert decimal coordinates to DMS format (optional)
        def decimal_to_dms(decimal, is_latitude=True):
            direction = 'N' if is_latitude and decimal >= 0 else 'S' if is_latitude else 'E' if decimal >= 0 else 'W'
            decimal = abs(decimal)
            degrees = int(decimal)
            minutes = int((decimal - degrees) * 60)
            seconds = round(((decimal - degrees) * 60 - minutes) * 60, 2)
            return f"{degrees}° {minutes}' {seconds}\" {direction}"

        return {
            "predicted_latitude": round(predicted_latitude, 6),
            "predicted_longitude": round(predicted_longitude, 6),
            "predicted_depth": round(predicted_depth, 2),
            "latitude_dms": decimal_to_dms(predicted_latitude, is_latitude=True),
            "longitude_dms": decimal_to_dms(predicted_longitude, is_latitude=False)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error in prediction: {str(e)}"
        )

@app.get("/data/")
def get_data():
    if df is None:
        raise HTTPException(status_code=500, detail="Dataset not available.")
    return df.head(50).to_dict(orient="records")

@app.get("/coasts/")
def get_coasts():
    if not hasattr(label_encoder, 'classes_'):
        raise HTTPException(status_code=500, detail="Coast encoder not properly initialized.")
    return {"coasts": list(label_encoder.classes_)}

@app.get("/get_fishing_data")
async def get_fishing_data(location: str):
    """
    Endpoint to get fishing data and weather for a specific location
    """
    coordinates = get_location_coordinates(location)
    current_weather = get_current_weather(coordinates["lat"], coordinates["lon"])
    
    # Mock data for fishing zones (as before)
    is_border_warning = "palk" in location.lower() or "gulf" in location.lower()
    border_distance = 3 if "palk" in location.lower() else 5 if "gulf" in location.lower() else 0
    
    # Get storm alerts
    alerts = get_storm_alerts(coordinates["lat"], coordinates["lon"])
    
    # Weather alert status
    weather_alert = False
    alert_message = ""
    
    if alerts:
        weather_alert = True
        # Use the most severe alert for the message
        severe_alerts = [a for a in alerts if a["severity"] == "severe"]
        if severe_alerts:
            alert_message = severe_alerts[0]["title"] + ": " + severe_alerts[0]["description"]
        else:
            alert_message = alerts[0]["title"] + ": " + alerts[0]["description"]
    
    return {
        "weather": current_weather if current_weather else {
            "temperature": 28,
            "conditions": "Partly Cloudy",
            "windSpeed": 15
        },
        "fishing_zones": [
            { 
                "name": f"Coastal Zone near {location.title()}", 
                "distance": "5km", 
                "conditions": "Favorable",
                "borderProximity": border_distance + 2
            },
            { 
                "name": f"Deep Sea Zone off {location.title()}", 
                "distance": "12km", 
                "conditions": "Good",
                "borderProximity": border_distance - 1 if border_distance > 1 else 0
            }
        ],
        "border_warning": is_border_warning,
        "border_distance": border_distance,
        "weather_alert": weather_alert,
        "alert_message": alert_message,
        "alerts": alerts
    }

@app.post("/chat")
async def chat_with_gemini(request: ChatRequest):
    try:
        # Configure the Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        )
        
        # Create system prompt with specialized fishing knowledge
        system_prompt = f"""
        You are a helpful fishing assistant for the SmartSea Tamil Nadu Fishing Zone Information System.
        Your purpose is to help fishermen with information about fishing zones, weather conditions, border warnings,
        and other fishing-related queries in Tamil Nadu, India. Please be concise in your responses.
        
        {fishing_knowledge}
        
        Today's date is {pd.Timestamp.now().strftime('%Y-%m-%d')}.
        
        If users ask about border warnings, emphasize the importance of safety and maintaining distance from international waters.
        """
        
        # Convert history to proper format if provided
        chat_history = []
        if request.history:
            for msg in request.history:
                if msg.role == "user":
                    chat_history.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "model":
                    chat_history.append({"role": "model", "parts": [msg.content]})
        
        # Create a chat session
        chat = model.start_chat(history=chat_history)
        
        # Get response from Gemini
        response = chat.send_message(
            [system_prompt, request.message]
        )
        
        return {"response": response.text}
        
    except Exception as e:
        print(f"Error with Gemini API: {str(e)}")
        return {"response": "Sorry, I'm having trouble processing your request right now. Please try again later."}

# New Weather API Endpoints
@app.post("/weather")
async def get_weather(request: WeatherRequest):
    """Get comprehensive weather data for a location"""
    try:
        # Get coordinates either from request or by looking up location
        if request.coordinates:
            lat = request.coordinates["lat"]
            lon = request.coordinates["lon"]
        else:
            coords = get_location_coordinates(request.location)
            lat = coords["lat"]
            lon = coords["lon"]
        
        # Get current weather, forecast and alerts
        current = get_current_weather(lat, lon)
        forecast = get_weather_forecast(lat, lon)
        marine = get_marine_forecast(lat, lon)
        alerts = get_storm_alerts(lat, lon)
        
        return {
            "location": request.location,
            "coordinates": {"lat": lat, "lon": lon},
            "current": current,
            "forecast": forecast,
            "marine": marine,
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weather data: {str(e)}"
        )

@app.get("/weather/{location}")
async def get_location_weather(location: str):
    """Get weather for a specific location by name"""
    try:
        coords = get_location_coordinates(location)
        current = get_current_weather(coords["lat"], coords["lon"])
        alerts = get_storm_alerts(coords["lat"], coords["lon"])
        
        # Simplified response for direct API calls
        return {
            "location": location,
            "coordinates": coords,
            "current": current,
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weather data: {str(e)}"
        )

@app.get("/weather/alerts/{location}")
async def get_location_alerts(location: str):
    """Get weather alerts for a specific location"""
    coords = get_location_coordinates(location)
    alerts = get_storm_alerts(coords["lat"], coords["lon"])
    
    return {
        "location": location,
        "alerts": alerts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)