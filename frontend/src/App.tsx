
// import React, { useState } from 'react';
// import { MapPin, AlertTriangle, Sun, Navigation } from 'lucide-react';
// import ChatComponent from './ChatComponent';

// interface WeatherData {
//   temperature: number;
//   conditions: string;
//   windSpeed: number;
// }

// interface FishingZone {
//   name: string;
//   distance: string;
//   conditions: string;
//   borderProximity: number;
// }

// function App() {
//   const [location, setLocation] = useState('');
//   const [showZones, setShowZones] = useState(false);
//   const [showBorderAlert, setShowBorderAlert] = useState(false);
//   const [borderDistance, setBorderDistance] = useState(0);
//   const [weather, setWeather] = useState<WeatherData | null>(null);
//   const [fishingZones, setFishingZones] = useState<FishingZone[]>([]);

//   const fetchData = async () => {
//     try {
//       const response = await fetch(`http://localhost:8000/get_fishing_data?location=${location}`);
//       const data = await response.json();
//       setWeather(data.weather);
//       setFishingZones(data.fishing_zones);
//       setShowZones(true);
      
//       if (data.border_warning) {
//         setShowBorderAlert(true);
//         setBorderDistance(data.border_distance);
//       } else {
//         setShowBorderAlert(false);
//       }
//     } catch (error) {
//       console.error('Error fetching data:', error);
//     }
//   };

//   const handleSearch = (e: React.FormEvent) => {
//     e.preventDefault();
//     if (location) fetchData();
//   };

//   return (
//     <div className="min-h-screen bg-gray-50">
//       <header className="bg-blue-900 text-white p-4">
//         <h1 className="text-2xl font-bold text-center">SmartSea Tamil Nadu</h1>
//         <p className="text-center">Fishing Zone Information System</p>
//       </header>

//       {showBorderAlert && (
//         <div className="border-l-4 p-4 m-4 bg-red-100 border-red-500">
//           <div className="flex items-center gap-2">
//             <AlertTriangle className="text-red-500" size={24} />
//             <div>
//               <p className="font-bold">WARNING: You are {borderDistance} km from international waters. Stay cautious!</p>
//               <div className="mt-2 flex items-center gap-2">
//                 <Navigation className="text-blue-500" />
//                 <p>Distance to border: {borderDistance} km</p>
//               </div>
//             </div>
//           </div>
//         </div>
//       )}

//       {weather && (
//         <div className="bg-white p-4 m-4 rounded shadow">
//           <h2 className="text-xl mb-3 flex items-center gap-2">
//             <Sun className="text-yellow-500" />
//             Current Weather
//           </h2>
//           <div className="grid grid-cols-3 gap-4 text-center">
//             <div><p className="font-bold">{weather.temperature}°C</p><p>Temperature</p></div>
//             <div><p className="font-bold">{weather.conditions}</p><p>Conditions</p></div>
//             <div><p className="font-bold">{weather.windSpeed} km/h</p><p>Wind Speed</p></div>
//           </div>
//         </div>
//       )}

//       <div className="p-4">
//         <form onSubmit={handleSearch} className="flex gap-2">
//           <input
//             type="text"
//             value={location}
//             onChange={(e) => setLocation(e.target.value)}
//             placeholder="Enter your port location"
//             className="flex-1 p-2 border rounded"
//           />
//           <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Find Zones</button>
//         </form>
//       </div>

//       {showZones && (
//         <div className="p-4">
//           <h2 className="text-xl mb-3 flex items-center gap-2">
//             <MapPin />
//             Recommended Fishing Zones
//           </h2>
//           <div className="grid gap-4">
//             {fishingZones.map((zone, index) => (
//               <div key={index} className="bg-white p-4 rounded shadow">
//                 <h3 className="font-bold">{zone.name}</h3>
//                 <p>Distance: {zone.distance}</p>
//                 <p>Conditions: {zone.conditions}</p>
//                 {zone.borderProximity <= 8 && (
//                   <p className={`mt-2 ${zone.borderProximity <= 5 ? 'text-red-600' : 'text-orange-600'}`}>
//                     ⚠️ {zone.borderProximity}km from international border
//                   </p>
//                 )}
//               </div>
//             ))}
//           </div>
//         </div>
//       )}

//       <div className="bg-yellow-50 p-4 m-4 border-l-4 border-yellow-400">
//         <p className="font-bold">Current Ban Period Notice:</p>
//         <p>Annual fishing ban period: April 15 - June 15</p>
//       </div>
      
//       {/* Add ChatComponent here */}
//       <ChatComponent />
//     </div>
//   );
// }

// export default App;

import React, { useState, useEffect } from 'react';
import { MapPin, AlertTriangle, Sun, Navigation, CloudRain, Compass, Wind } from 'lucide-react';
import ChatComponent from './ChatComponent';

interface WeatherData {
  temperature: number;
  conditions: string;
  description?: string;
  windSpeed: number;
  humidity?: number;
  icon?: string;
  timestamp?: string;
}

interface ForecastData {
  date: string;
  time: string;
  temperature: number;
  conditions: string;
  description: string;
  windSpeed: number;
  icon: string;
}

interface MarineData {
  time: string;
  wind_speed: number;
  wind_direction: number;
  wind_direction_compass: string;
  conditions: string;
  rain_chance: number;
  sea_level?: number;
}

interface AlertData {
  title: string;
  description: string;
  start: string;
  end: string;
  source: string;
  severity: string;
}

interface FishingZone {
  name: string;
  distance: string;
  conditions: string;
  borderProximity: number;
}

function App() {
  const [location, setLocation] = useState('');
  const [showZones, setShowZones] = useState(false);
  const [showBorderAlert, setShowBorderAlert] = useState(false);
  const [borderDistance, setBorderDistance] = useState(0);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [forecast, setForecast] = useState<ForecastData[] | null>(null);
  const [marine, setMarine] = useState<MarineData[] | null>(null);
  const [alerts, setAlerts] = useState<AlertData[] | null>(null);
  const [fishingZones, setFishingZones] = useState<FishingZone[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`http://localhost:8000/get_fishing_data?location=${location}`);
      const data = await response.json();
      
      setWeather(data.weather);
      setFishingZones(data.fishing_zones);
      setShowZones(true);
      
      // Handle border warning
      if (data.border_warning) {
        setShowBorderAlert(true);
        setBorderDistance(data.border_distance);
      } else {
        setShowBorderAlert(false);
      }
      
      // Handle weather alerts
      if (data.alerts && data.alerts.length > 0) {
        setAlerts(data.alerts);
      } else {
        setAlerts(null);
      }

      // Fetch additional weather data
      const weatherResponse = await fetch(`http://localhost:8000/weather/${location}`);
      const weatherData = await weatherResponse.json();
      
      if (weatherData.current) setWeather(weatherData.current);
      if (weatherData.forecast) setForecast(weatherData.forecast);
      if (weatherData.marine) setMarine(weatherData.marine);
      if (weatherData.alerts) setAlerts(weatherData.alerts);

    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (location) fetchData();
  };

  // Format date string for better readability
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      weekday: 'short', 
      day: 'numeric', 
      month: 'short' 
    });
  };

  // Weather icon helper function
  const getWeatherIcon = (iconCode: string) => {
    return `http://openweathermap.org/img/wn/${iconCode}@2x.png`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-900 text-white p-4">
        <h1 className="text-2xl font-bold text-center">SmartSea Tamil Nadu</h1>
        <p className="text-center">Fishing Zone Information System</p>
      </header>

      {/* Search Form */}
      <div className="p-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Enter your port location"
            className="flex-1 p-2 border rounded"
          />
          <button 
            type="submit" 
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center gap-2"
            disabled={isLoading}
          >
            {isLoading ? 'Searching...' : 'Find Zones'}
          </button>
        </form>
      </div>

      {/* Border Alert */}
      {showBorderAlert && (
        <div className="border-l-4 p-4 m-4 bg-red-100 border-red-500">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-red-500" size={24} />
            <div>
              <p className="font-bold">WARNING: You are {borderDistance} km from international waters. Stay cautious!</p>
              <div className="mt-2 flex items-center gap-2">
                <Navigation className="text-blue-500" />
                <p>Distance to border: {borderDistance} km</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Weather Alerts */}
      {alerts && alerts.length > 0 && (
        <div className="border-l-4 p-4 m-4 bg-yellow-100 border-yellow-500">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-2">
            <AlertTriangle className="text-yellow-600" />
            Weather Alerts
          </h2>
          {alerts.map((alert, index) => (
            <div key={index} className={`mb-2 p-2 rounded ${alert.severity === 'severe' ? 'bg-red-50' : 'bg-yellow-50'}`}>
              <p className="font-bold">{alert.title}</p>
              <p>{alert.description}</p>
              <p className="text-sm text-gray-600">
                {alert.start} {alert.end !== alert.start ? `to ${alert.end}` : ''}
                <span className="ml-2">Source: {alert.source}</span>
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Current Weather */}
      {weather && (
        <div className="bg-white p-4 m-4 rounded shadow">
          <h2 className="text-xl mb-3 flex items-center gap-2">
            <Sun className="text-yellow-500" />
            Current Weather at {location || 'Selected Location'}
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-2">
              <p className="text-3xl font-bold">{weather.temperature}°C</p>
              <p className="text-gray-600">Temperature</p>
            </div>
            
            <div className="text-center p-2">
              <p className="font-bold flex items-center justify-center">
                {weather.icon && <img src={getWeatherIcon(weather.icon)} alt={weather.conditions} className="h-8 w-8 mr-1" />}
                {weather.conditions}
              </p>
              <p className="text-gray-600">Conditions</p>
              {weather.description && <p className="text-sm">{weather.description}</p>}
            </div>
            
            <div className="text-center p-2">
              <p className="font-bold flex items-center justify-center">
                <Wind className="mr-1 h-5 w-5 text-blue-500" />
                {weather.windSpeed} km/h
              </p>
              <p className="text-gray-600">Wind Speed</p>
            </div>
            
            {weather.humidity && (
              <div className="text-center p-2">
                <p className="font-bold flex items-center justify-center">
                  <CloudRain className="mr-1 h-5 w-5 text-blue-500" />
                  {weather.humidity}%
                </p>
                <p className="text-gray-600">Humidity</p>
              </div>
            )}
          </div>
          
          {weather.timestamp && (
            <p className="text-xs text-right text-gray-500 mt-2">
              Last updated: {new Date(weather.timestamp).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Weather Forecast */}
      {forecast && forecast.length > 0 && (
        <div className="bg-white p-4 m-4 rounded shadow">
          <h2 className="text-xl mb-3 flex items-center gap-2">
            <CloudRain className="text-blue-500" />
            5-Day Weather Forecast
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2">
            {forecast.map((day, index) => (
              <div key={index} className="border rounded p-2 text-center">
                <p className="font-bold">{formatDate(day.date)}</p>
                {day.icon && <img 
                  src={getWeatherIcon(day.icon)} 
                  alt={day.conditions} 
                  className="h-10 w-10 mx-auto"
                />}
                <p className="text-lg font-semibold">{day.temperature}°C</p>
                <p>{day.conditions}</p>
                <p className="text-sm flex items-center justify-center">
                  <Wind className="h-4 w-4 mr-1" /> 
                  {day.windSpeed} km/h
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Marine Forecast */}
      {marine && marine.length > 0 && (
        <div className="bg-white p-4 m-4 rounded shadow">
          <h2 className="text-xl mb-3 flex items-center gap-2">
            <Compass className="text-blue-600" />
            Marine Conditions
          </h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-blue-50">
                  <th className="p-2 text-left">Time</th>
                  <th className="p-2 text-left">Wind</th>
                  <th className="p-2 text-left">Direction</th>
                  <th className="p-2 text-left">Conditions</th>
                  <th className="p-2 text-left">Rain Chance</th>
                </tr>
              </thead>
              <tbody>
                {marine.slice(0, 4).map((item, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="p-2">{new Date(item.time).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}</td>
                    <td className="p-2">{item.wind_speed} km/h</td>
                    <td className="p-2">
                      <div className="flex items-center">
                        <span style={{ transform: `rotate(${item.wind_direction}deg)` }} className="mr-1">
                          ↑
                        </span>
                        {item.wind_direction_compass}
                      </div>
                    </td>
                    <td className="p-2">{item.conditions}</td>
                    <td className="p-2">{item.rain_chance}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fishing Zones */}
      {showZones && (
        <div className="p-4">
          <h2 className="text-xl mb-3 flex items-center gap-2">
            <MapPin />
            Recommended Fishing Zones
          </h2>
          <div className="grid gap-4">
            {fishingZones.map((zone, index) => (
              <div key={index} className="bg-white p-4 rounded shadow">
                <h3 className="font-bold">{zone.name}</h3>
                <p>Distance: {zone.distance}</p>
                <p>Conditions: {zone.conditions}</p>
                {zone.borderProximity <= 8 && (
                  <p className={`mt-2 ${zone.borderProximity <= 5 ? 'text-red-600' : 'text-orange-600'}`}>
                    ⚠️ {zone.borderProximity}km from international border
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ban Period Notice */}
      <div className="bg-yellow-50 p-4 m-4 border-l-4 border-yellow-400">
        <p className="font-bold">Current Ban Period Notice:</p>
        <p>Annual fishing ban period: April 15 - June 15</p>
      </div>
      
      {/* ChatComponent */}
      <ChatComponent />
    </div>
  );
}

export default App;