
import requests
import json

class LocationService:
    def __init__(self):
        self.api_key = "1b077296f67499a12ee28ce232bb48221d29be14"
        self.base_url = "https://google.serper.dev/places"
    
    def search_places(self, query, country="uz", language="uz"):
        """Joylashuvlarni qidirish"""
        data = {
            "q": query,
            "gl": country,
            "hl": language
        }
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API xatolik: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Tarmoq xatoligi: {str(e)}"}
    
    def validate_address(self, address):
        """Manzilni tekshirish"""
        result = self.search_places(address)
        
        if "error" not in result and "places" in result:
            places = result.get("places", [])
            if places:
                first_place = places[0]
                return {
                    "valid": True,
                    "formatted_address": first_place.get("title", ""),
                    "latitude": first_place.get("gps_coordinates", {}).get("latitude"),
                    "longitude": first_place.get("gps_coordinates", {}).get("longitude"),
                    "place_type": first_place.get("type", "")
                }
        
        return {"valid": False, "error": "Manzil topilmadi"}
    
    def get_nearby_places(self, query="restoran", location="Tashkent"):
        """Yaqin atrofdagi joylarni topish"""
        search_query = f"{query} {location}"
        return self.search_places(search_query)
"""
Location Service for Restaurant App
Provides address validation and location search functionality
"""

import requests
import logging
import os
from typing import Dict, List, Optional, Tuple

class LocationService:
    def __init__(self):
        self.serper_api_key = os.environ.get('SERPER_API_KEY', '1b077296f67499a12ee28ce232bb48221d29be14')
        self.yandex_api_key = os.environ.get('YANDEX_GEOCODER_API', '')
        self.logger = logging.getLogger('location_service')

    def search_places(self, query: str, gl: str = "uz", hl: str = "uz") -> Dict:
        """Joylarni qidirish"""
        try:
            if not self.serper_api_key:
                self.logger.warning("Serper API key not found")
                return {"places": [], "error": "API key not configured"}

            url = "https://google.serper.dev/places"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            data = {
                "q": f"{query} Tashkent Uzbekistan",
                "gl": gl,
                "hl": hl,
                "limit": 10
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                places = []

                # Places ma'lumotlarini qayta ishlash
                if 'places' in result:
                    for place in result['places'][:5]:  # Faqat birinchi 5 ta
                        place_data = {
                            'title': place.get('title', ''),
                            'address': place.get('address', ''),
                            'gps_coordinates': {
                                'latitude': place.get('gpsCoordinates', {}).get('latitude', 0),
                                'longitude': place.get('gpsCoordinates', {}).get('longitude', 0)
                            },
                            'rating': place.get('rating', 0),
                            'category': place.get('category', '')
                        }
                        places.append(place_data)

                return {"places": places, "total": len(places)}
            else:
                self.logger.error(f"Serper API error: {response.status_code} - {response.text}")
                return {"places": [], "error": f"API error: {response.status_code}"}

        except requests.RequestException as e:
            self.logger.error(f"Network error in search_places: {str(e)}")
            return {"places": [], "error": "Network error"}
        except Exception as e:
            self.logger.error(f"Unexpected error in search_places: {str(e)}")
            return {"places": [], "error": "Unexpected error"}

    def validate_address(self, address: str) -> Tuple[bool, str]:
        """Manzilni tekshirish"""
        if not address or len(address.strip()) < 5:
            return False, "Manzil juda qisqa"

        # Oddiy tekshirish
        address_lower = address.lower()
        valid_keywords = ['ko\'cha', 'mahalla', 'tuman', 'yo\'l', 'mfy', 'shoh', 'ko\'ch']
        
        if any(keyword in address_lower for keyword in valid_keywords):
            return True, "Manzil to'g'ri formatda"
        
        # Agar keywords bo'lmasa, uzunlik bo'yicha tekshirish
        if len(address.strip()) >= 10:
            return True, "Manzil qabul qilindi"
        
        return False, "Manzilni to'liqroq kiriting"

    def calculate_distance(self, from_coords: Tuple[float, float], to_coords: Tuple[float, float]) -> float:
        """Ikki nuqta orasidagi masofani hisoblash (Haversine formula)"""
        import math
        
        lat1, lng1 = math.radians(from_coords[0]), math.radians(from_coords[1])
        lat2, lng2 = math.radians(to_coords[0]), math.radians(to_coords[1])

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c  # Yer radiusi

        return round(distance_km, 2)

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Manzil bo'yicha koordinatalarni olish"""
        try:
            if not self.yandex_api_key:
                # Fallback coordinates (Tashkent center)
                return (41.2995, 69.2401)

            url = "https://geocode-maps.yandex.ru/1.x/"
            params = {
                'apikey': self.yandex_api_key,
                'geocode': f"{address}, Tashkent, Uzbekistan",
                'format': 'json',
                'results': 1
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

                if geo_objects:
                    point = geo_objects[0]['GeoObject']['Point']['pos'].split()
                    return (float(point[1]), float(point[0]))  # lat, lng

        except Exception as e:
            self.logger.error(f"Geocoding error: {str(e)}")

        # Fallback Tashkent coordinates
        return (41.2995, 69.2401)
