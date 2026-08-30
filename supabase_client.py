import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    # Hem ortam değişkenlerini hem de Streamlit Secrets'ı kontrol et
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    try:
        if not url: url = st.secrets["SUPABASE_URL"]
        if not key: key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass
        
    if not url or not key:
        return None
        
    return create_client(url, key)

def add_clothing_item(image_url, category, color, description):
    supabase = get_supabase()
    if not supabase: return None
    
    data, count = supabase.table('clothes').insert({
        "image_url": image_url,
        "category": category,
        "color": color,
        "description": description
    }).execute()
    return data

def get_all_clothes():
    supabase = get_supabase()
    if not supabase: return []
    
    response = supabase.table('clothes').select("*").order('added_date', desc=True).execute()
    return response.data[1] if len(response.data) == 2 else response.data

def upload_image(file_bytes, file_name):
    supabase = get_supabase()
    if not supabase: return None
    
    bucket_name = "wardrobe_images"
    
    # Dosyayı yükle
    res = supabase.storage.from_(bucket_name).upload(
        file_name,
        file_bytes,
        {"content-type": "image/jpeg"}
    )
    
    # Herkesin görebileceği (Public) internet linkini al
    public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
    return public_url
