
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
