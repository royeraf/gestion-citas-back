import requests
import json
from config import Config

GEMINI_API_KEY = Config.GEMINI_API_KEY

class GeminiService:
    # URL base para la API de Google Generative AI
    # Usamos gemini-flash-latest como fallback estable
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

    @staticmethod
    def recommend_area(sintomas, areas):
        """
        Recomienda un área médica basada en los síntomas y las áreas disponibles.
        """
        if not GEMINI_API_KEY:
            return {"error": "API Key no configurada"}

        # Formatear la lista de áreas para el prompt
        areas_text = "\n".join([f"- ID: {area['id']}, Nombre: {area['nombre']}, Descripción: {area['descripcion'] or 'Sin descripción'}" for area in areas])
        
        prompt = f"""
        Actúa como un asistente médico experto.
        Tengo un paciente con los siguientes síntomas: "{sintomas}".
        
        Las áreas médicas disponibles son:
        {areas_text}
        
        Tu tarea es recomendar la mejor área médica para atender a este paciente.
        Debes devolver tu respuesta ESTRICTAMENTE en formato JSON con la siguiente estructura:
        {{
            "area_id": <id_del_area_recomendada (numero entero)>,
            "nombre_area": "<nombre_del_area>",
            "razon": "<explicación breve y profesional de por qué esta área es la adecuada (max 2 frases)>",
            "nivel_urgencia": "<alta|media|baja>"
        }}
        
        No incluyas nada más que el JSON en tu respuesta. Si los síntomas no son claros, recomienda el área más general (como Medicina General) y sugiérelo en la razón.
        """

        url = f"{GeminiService.BASE_URL}?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2, # Baja temperatura para respuestas más deterministas
                "response_mime_type": "application/json"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 429:
                return {"error": "El servicio de IA está saturado momentáneamente. Por favor intente en un minuto.", "status": 429}
            
            if response.status_code != 200:
                return {"error": f"Error de Gemini API: {response.text}", "status": response.status_code}
            
            result = response.json()
            
            # Extraer el texto de la respuesta
            if 'candidates' in result and result['candidates']:
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                # Limpiar bloques de código markdown si existen (aunque response_mime_type ayuda, es buena práctica)
                content_text = content_text.replace('```json', '').replace('```', '').strip()
                return json.loads(content_text)
            else:
                return {"error": "No se pudo obtener una respuesta válida de Gemini"}
                
        except json.JSONDecodeError:
            return {"error": "Error al procesar la respuesta de la IA (no es un JSON válido)"}
        except Exception as e:
            return {"error": f"Error al comunicarse con Gemini: {str(e)}"}
