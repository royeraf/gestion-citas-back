import requests
from config import Config

API_PERU_DEV_TOKEN = Config.API_PERU_DEV_TOKEN

class ApiPeruDevService:
    BASE_URL = "https://apiperu.dev/api/dni"

    @staticmethod
    def get_data_by_dni(dni: str):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_PERU_DEV_TOKEN}"
        }
        payload = {
            "dni": dni
        }

        response = requests.post(ApiPeruDevService.BASE_URL, json=payload, headers=headers)

        try:
            return response.json()
        except Exception:
            return {
                "error": "La API no devolvió JSON",
                "status": response.status_code,
                "raw": response.text
            }
