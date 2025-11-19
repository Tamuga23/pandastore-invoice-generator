import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

def parse_client_info(raw_text):
    """
    Envía el texto sin procesar a Gemini para extraer nombre, dirección, etc.
    Retorna un diccionario con los datos o un diccionario con clave 'error' si falla.
    """
    
    # 1. Verificación de la API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error Crítico: No se encontró la variable GEMINI_API_KEY en el archivo .env")
        return {"error": "Falta la API Key en el archivo .env"}

    try:
        # 2. Configuración del cliente de Google
        genai.configure(api_key=api_key)
        
        # USAMOS EL MODELO QUE APARECIÓ EN TU LISTA
        # 'gemini-2.5-flash' es rápido y está disponible en tu cuenta
        model_name = 'gemini-2.5-flash' 
        
        model = genai.GenerativeModel(model_name)

        # 3. Prompt (Instrucciones precisas)
        prompt = f"""
        Extract the client information from the following text. 
        The text typically contains a Name, Phone Number, Address, and a Transport/Delivery Provider.
        
        If a field is missing, leave it as an empty string. 
        Normalize the phone number to include country code if possible.
        
        Return ONLY a valid JSON object with this exact structure (no markdown code blocks):
        {{
            "fullName": "string",
            "address": "string",
            "phone": "string",
            "transportProvider": "string"
        }}

        Text to parse: "{raw_text}"
        """

        # 4. Llamada a la API
        response = model.generate_content(prompt)

        # 5. Procesar respuesta (Limpieza de Markdown)
        if response.text:
            # Limpiamos cualquier formato markdown que la IA pueda agregar
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        else:
            return {"error": "La IA no devolvió texto en la respuesta"}

    except Exception as e:
        # 6. Captura de errores
        print(f"❌ Error en gemini_service: {e}")
        return {"error": f"Fallo en el servicio de IA: {str(e)}"}