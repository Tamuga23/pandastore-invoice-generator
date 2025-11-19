import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: No se encontró la API KEY en .env")
else:
    print(f"✅ API KEY encontrada (empieza con {api_key[:5]}...)")
    genai.configure(api_key=api_key)
    
    print("\n🔍 Buscando modelos disponibles...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"❌ Error al conectar con Google: {e}")
        