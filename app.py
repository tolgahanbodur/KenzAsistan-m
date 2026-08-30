import os
import json
import google.generativeai as genai
from PIL import Image
import io
import streamlit as st

def configure_api():
    api_key = os.environ.get("GEMINI_API_KEY")
    try:
        if not api_key: api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def extract_text(response):
    """Gemini cevabından metni güvenle çıkarır."""
    if hasattr(response, 'text'):
        try:
            return response.text
        except Exception:
            pass
    if isinstance(response, dict):
        if 'candidates' in response and len(response['candidates']) > 0:
            try:
                return response['candidates'][0]['content']['parts'][0]['text']
            except Exception:
                pass
    return str(response)

def analyze_clothing_item(image_bytes):
    if not configure_api():
        raise ValueError("API anahtarı bulunamadı.")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    
    prompt = """
    Bu fotoğraftaki kıyafeti bir gardırop asistanı olarak analiz et. Lütfen cevabını SADECE geçerli bir JSON formatında ver. 
    JSON formatı şu anahtarları tam olarak içermelidir:
    - "category": Kıyafetin türü (örneğin: Tişört, Pantolon, Elbise, Kazak, Ceket vb.)
    - "color": Kıyafetin baskın rengi veya renkleri
    - "description": Kıyafetin stili, deseni, materyali ve genel görünümü hakkında yaratıcı ve kısa bir açıklama (1-2 cümle)
    
    Sadece JSON çıktısı ver, markdown işaretleri kullanma.
    """
    
    try:
        response = model.generate_content([prompt, img])
        text = extract_text(response).strip()
        
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini API Hatası: {e}")
        return {
            "category": "Bilinmiyor",
            "color": "Bilinmiyor",
            "description": f"Analiz yapılamadı: {str(e)}"
        }

def rate_outfit(image_bytes):
    if not configure_api():
        raise ValueError("API anahtarı bulunamadı.")
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    
    prompt = """
    Sen uzman bir moda asistanı ve stilistsin. Bu fotoğraftaki kombini (outfit) analiz et.
    Kullanıcıya samimi, motive edici, yapıcı ve tamamen Türkçe bir değerlendirme yaz.
    
    Şu başlıklara değinmelisin:
    1. Renklerin uyumu
    2. Tarz ve parçaların birbiriyle uyumu
    3. Gelişim tavsiyesi (Daha iyi yapmak için ne değiştirilebilir?)
    
    En alt satırda kombine 10 üzerinden bir puan ver. (Örnek: "Puan: 8/10")
    """
    
    try:
        response = model.generate_content([prompt, img])
        return extract_text(response)
    except Exception as e:
        return f"Kombin değerlendirilirken bir hata oluştu: {str(e)}"
