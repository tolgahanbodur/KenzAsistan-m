import streamlit as st
import os
import time
import supabase_client as sc
import gemini_helper as gh

st.set_page_config(page_title="Gardırop Asistanı (Cloud)", page_icon="👗", layout="centered")
st.title("☁️ Bulut Gardırop Asistanı")

# API ve Bulut Bağlantısı Kontrolü
def check_setup():
    is_setup = True
    missing = []
    keys = ["GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    
    for key in keys:
        val = os.environ.get(key)
        try:
            if not val: val = st.secrets.get(key)
        except Exception:
            pass
        if not val:
            is_setup = False
            missing.append(key)
            
    return is_setup, missing

is_setup, missing_keys = check_setup()

if not is_setup:
    st.warning("Uygulamanın çalışması için gerekli bağlantı ayarları eksik.")
    st.info("Kurulumu test etmek için aşağıdaki bilgileri girin:")
    
    gemini_key = st.text_input("GEMINI_API_KEY", type="password")
    supa_url = st.text_input("SUPABASE_URL")
    supa_key = st.text_input("SUPABASE_KEY", type="password")
    
    if st.button("Ayarları Kaydet ve Başla", use_container_width=True):
        if gemini_key and supa_url and supa_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["SUPABASE_URL"] = supa_url
            os.environ["SUPABASE_KEY"] = supa_key
            st.success("Ayarlar başarıyla kaydedildi! Lütfen bekleyin...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Lütfen tüm alanları doldurun.")
    st.stop()

# Uygulama Sekmeleri
tab1, tab2, tab3 = st.tabs(["➕ Gardıroba Ekle", "👚 Gardırobum", "🌟 Kombin Puanla"])

with tab1:
    st.header("Yeni Kıyafet Ekle")
    st.write("Telefon kamerasını kullanarak veya galeriden kıyafet yükleyin.")
    
    photo = st.camera_input("📷 Kamera ile Çek")
    upload = st.file_uploader("📂 Veya Galeriden Seç", type=["jpg", "jpeg", "png"])
    img_data = photo if photo else upload
    
    if img_data is not None:
        st.image(img_data, caption="Seçilen Kıyafet", use_column_width=True)
        if st.button("Kıyafeti Analiz Et ve Buluta Kaydet", type="primary", use_container_width=True):
            with st.spinner("🚀 Bulutta analiz ediliyor ve kaydediliyor..."):
                img_bytes = img_data.getvalue()
                timestamp = int(time.time())
                filename = f"item_{timestamp}.jpg"
                
                try:
                    # 1. Gemini Analizi
                    analysis = gh.analyze_clothing_item(img_bytes)
                    
                    # 2. Supabase Storage'a Yükle
                    public_url = sc.upload_image(img_bytes, filename)
                    
                    # 3. Supabase Veritabanına Kaydet
                    if public_url:
                        sc.add_clothing_item(
                            image_url=public_url,
                            category=analysis.get("category", "Bilinmiyor"),
                            color=analysis.get("color", "Bilinmiyor"),
                            description=analysis.get("description", "Açıklama yok")
                        )
                        st.success("✅ Kıyafet bulut gardırobunuza başarıyla eklendi!")
                        st.info(f"**Tür:** {analysis.get('category')} | **Renk:** {analysis.get('color')}\n\n*{analysis.get('description')}*")
                    else:
                        st.error("Fotoğraf buluta yüklenemedi.")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")

with tab2:
    st.header("Dijital Gardırobum")
    
    try:
        clothes = sc.get_all_clothes()
        if not clothes:
            st.info("Bulut gardırobunuz henüz boş.")
        else:
            st.write(f"Bulutta toplam **{len(clothes)}** parça kıyafetiniz var.")
            
            cols = st.columns(2)
            for i, item in enumerate(clothes):
                col = cols[i % 2]
                with col:
                    st.container(border=True)
                    st.image(item["image_url"], use_column_width=True)
                    st.markdown(f"**{item.get('category')}** ({item.get('color')})")
                    st.caption(f"{item.get('description')}")
                    st.write("")
    except Exception as e:
        st.error(f"Veriler çekilirken hata oluştu: {e}")

with tab3:
    st.header("Bugünkü Kombinim")
    st.write("Aynadan bugünkü kombininizin fotoğrafını çekin, yapay zeka stilistiniz değerlendirsin!")
    
    outfit_photo = st.camera_input("📷 Kombin Fotoğrafı Çek")
    outfit_upload = st.file_uploader("📂 Veya Galeriden Seç", type=["jpg", "jpeg", "png"], key="outfit")
    outfit_data = outfit_photo if outfit_photo else outfit_upload
    
    if outfit_data is not None:
        st.image(outfit_data, caption="Bugünkü Kombin", use_column_width=True)
        if st.button("Kombinimi Puanla!", type="primary", use_container_width=True):
            with st.spinner("✨ Stilistiniz kombininizi inceliyor..."):
                try:
                    img_bytes = outfit_data.getvalue()
                    rating_text = gh.rate_outfit(img_bytes)
                    st.success("Değerlendirme Tamamlandı!")
                    st.markdown(rating_text)
                except Exception as e:
                    st.error(f"Hata: {e}")
