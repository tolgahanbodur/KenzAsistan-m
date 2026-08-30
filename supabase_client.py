import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
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
    
    res = supabase.table('clothes').insert({
        "image_url": image_url,
        "category": category,
        "color": color,
        "description": description
    }).execute()
    
    return getattr(res, 'data', res)

def get_all_clothes():
    supabase = get_supabase()
    if not supabase: return []
    
    res = supabase.table('clothes').select("*").order('added_date', desc=True).execute()
    return getattr(res, 'data', [])

def upload_image(file_bytes, file_name):
    supabase = get_supabase()
    if not supabase: return None
    
    bucket_name = "wardrobe_images"
    
    try:
        supabase.storage.from_(bucket_name).upload(
            file_name,
            file_bytes,
            {"content-type": "image/jpeg"}
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        print(f"Yükleme hatası: {e}")
        return None
