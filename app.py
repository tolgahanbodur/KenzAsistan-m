import streamlit as st
import uuid
import json

from ai_router import ask_ai

from supabase_client import (
    get_client_id,
    get_conversations,
    create_conversation,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title,
    upload_image,
    add_clothing_item,
    get_all_clothes,
)


# ============================================================
# SAYFA
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# CLIENT
# ============================================================

client_id = get_client_id()


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# ============================================================
# YENİ SOHBET
# ============================================================

def start_new_conversation():

    conversation = create_conversation(
        client_id=client_id,
        title="Yeni sohbet",
    )

    if not conversation:
        return False

    st.session_state.conversation_id = conversation["id"]

    st.session_state.messages = []

    return True


# ============================================================
# SOHBET YÜKLE
# ============================================================

def load_conversation(conversation_id):

    messages = get_messages(
        conversation_id
    )

    st.session_state.conversation_id = conversation_id

    st.session_state.messages = messages


# ============================================================
# GARDIROP BELLEĞİ
# ============================================================

def get_wardrobe_context():

    try:

        clothes = get_all_clothes()

    except Exception:

        return "Gardırop belleği şu anda kullanılamıyor."

    if not clothes:

        return (
            "Kullanıcının gardırop belleğinde "
            "henüz kayıtlı kıyafet bulunmuyor."
        )

    lines = []

    for item in clothes:

        name = item.get("name") or "İsimsiz parça"

        category = item.get("category") or "Belirtilmemiş"

        color = item.get("color") or "Belirtilmemiş"

        style = item.get("style") or "Belirtilmemiş"

        season = item.get("season") or "Belirtilmemiş"

        description = (
            item.get("description")
            or ""
        )

        lines.append(
            f"- {name} | "
            f"Kategori: {category} | "
            f"Renk: {color} | "
            f"Stil: {style} | "
            f"Mevsim: {season} | "
            f"Detay: {description}"
        )

    return "\n".join(lines)


# ============================================================
# GÖRSEL KIYAFET Mİ?
# ============================================================

def analyze_clothing_image(image_bytes):

    if not image_bytes:
        return None

    prompt = """
Bu görseli analiz et.

Eğer görselde bir veya daha fazla kıyafet,
ayakkabı veya aksesuar varsa bunları gardırop
hafızasına kaydedilebilecek şekilde analiz et.

Sadece kıyafet/ayakkabı/aksesuar varsa JSON döndür.

JSON formatı:

{
    "is_clothing": true,
    "items": [
        {
            "name": "kıyafetin kısa adı",
            "category": "kategori",
            "color": "renk",
            "style": "stil",
            "season": "mevsim",
            "description": "detaylı kısa açıklama"
        }
    ]
}

Eğer görsel kıyafet içermiyorsa:

{
    "is_clothing": false,
    "items": []
}

JSON dışında hiçbir şey yazma.
"""

    try:

        result = ask_ai(
            prompt=prompt,
            image=image_bytes,
        )

        if not result:
            return None

        # Markdown JSON temizleme
        text = result.strip()

        if text.startswith("```"):
            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        data = json.loads(text)

        return data

    except Exception:

        return None


# ============================================================
# KIYAFETLERİ KAYDET
# ============================================================

def save_clothing_items(
    image_url,
    clothing_data
):

    if not clothing_data:
        return 0

    if not clothing_data.get(
        "is_clothing",
        False
    ):
        return 0

    items = clothing_data.get(
        "items",
        []
    )

    saved = 0

    for item in items:

        try:

            add_clothing_item(

                image_url=image_url,

                category=(
                    item.get("category")
                    or "Diğer"
                ),

                color=(
                    item.get("color")
                    or "Belirtilmemiş"
                ),

                description=(
                    (
                        item.get("name")
                        or ""
                    )
                    + " - "
                    + (
                        item.get("description")
                        or ""
                    )
                ),
            )

            saved += 1

        except Exception:

            continue

    return saved


# ============================================================
# İLK AÇILIŞ
# ============================================================

if not st.session_state.initialized:

    try:

        conversations = get_conversations(
            client_id
        )

        if conversations:

            load_conversation(
                conversations[0]["id"]
            )

        else:

            start_new_conversation()

        st.session_state.initialized = True

    except Exception as e:

        st.error(
            "Kenz başlatılırken hata oluştu."
        )

        st.exception(e)

        st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 Kenz")

    st.caption(
        "Kişisel yapay zeka asistanın"
    )

    st.divider()


    # ========================================================
    # YENİ SOHBET
    # ========================================================

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
    ):

        try:

            if start_new_conversation():

                st.rerun()

        except Exception as e:

            st.error(
                "Yeni sohbet oluşturulamadı."
            )

            st.exception(e)


    st.divider()


    # ========================================================
    # SOHBETLER
    # ========================================================

    st.subheader(
        "💬 Sohbetler"
    )

    try:

        conversations = get_conversations(
            client_id
        )

    except Exception as e:

        conversations = []

        st.error(
            "Sohbetler alınamadı."
        )

        st.exception(e)


    if not conversations:

        st.caption(
            "Henüz sohbet yok."
        )


    for conversation in conversations:

        conversation_id = conversation["id"]

        title = (
            conversation.get("title")
            or "Yeni sohbet"
        )

        if len(title) > 32:

            title = (
                title[:32]
                + "..."
            )

        is_current = (
            conversation_id
            ==
            st.session_state.conversation_id
        )

        button_text = (
            "🟢 "
            if is_current
            else "💬 "
        ) + title

        if st.button(
            button_text,
            key="chat_" + conversation_id,
            use_container_width=True,
        ):

            load_conversation(
                conversation_id
            )

            st.rerun()


    st.divider()


    # ========================================================
    # GARDIROP
    # ========================================================

    st.subheader(
        "👕 Gardırop"
    )

    try:

        wardrobe = get_all_clothes()

        wardrobe_count = len(
            wardrobe
        )

        st.caption(
            f"{wardrobe_count} kayıtlı parça"
        )

    except Exception:

        st.caption(
            "Gardırop belleği yüklenemedi."
        )


    st.divider()


    # ========================================================
    # SON MODEL
    # ========================================================

    if st.session_state.last_provider:

        st.caption(
            "Son kullanılan model"
        )

        st.write(
            st.session_state.last_provider
        )

        st.divider()


    # ========================================================
    # SOHBET SİL
    # ========================================================

    if st.session_state.conversation_id:

        if st.button(
            "🗑️ Bu sohbeti sil",
            use_container_width=True,
        ):

            try:

                delete_conversation(
                    st.session_state.conversation_id,
                    client_id,
                )

                st.session_state.conversation_id = None

                st.session_state.messages = []

                conversations = get_conversations(
                    client_id
                )

                if conversations:

                    load_conversation(
                        conversations[0]["id"]
                    )

                else:

                    start_new_conversation()

                st.rerun()

            except Exception as e:

                st.error(
                    "Sohbet silinemedi."
                )

                st.exception(e)


# ============================================================
# ANA EKRAN
# ============================================================

st.title(
    "🤖 Kenz Asistan"
)

st.caption(
    "Yazılı ve görsel sohbet edebilirsin."
)


# ============================================================
# GEÇMİŞ MESAJLAR
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    content = message.get(
        "content",
        ""
    )

    image_url = message.get(
        "image_url"
    )

    with st.chat_message(
        role
    ):

        if image_url:

            st.image(
                image_url,
                use_container_width=True
            )

        if content:

            st.markdown(
                content
            )


# ============================================================
# BOŞ SOHBET
# ============================================================

if not st.session_state.messages:

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Benimle normal şekilde sohbet edebilirsin.

Ayrıca fotoğraf gönderebilirsin.

📷 Bir kıyafet fotoğrafı gönderirsen
onu gardırop hafızama kaydedebilirim.

Örneğin:

👕 **"Bu gömleği gardırobuma ekle."**

👔 **"Bu kombin nasıl?"**

👖 **"Bu pantolonla ne giyebilirim?"**

🔥 **"Bugün ne giysem?"**

🧠 **"Gardırobumda hangi siyah parçalar var?"**
"""
        )


# ============================================================
# GÖRSEL YÜKLEME
# ============================================================

uploaded_file = st.file_uploader(
    "📷 Görsel ekle",

    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
    ],

    accept_multiple_files=False,

    key=f"uploader_{st.session_state.uploader_key}",
)


# ============================================================
# CHAT
# ============================================================

user_message = st.chat_input(
    "Kenz'e mesaj yaz..."
)


# ============================================================
# MESAJ GELDİ
# ============================================================

if user_message or uploaded_file:

    user_message = (
        user_message.strip()
        if user_message
        else ""
    )


    # ========================================================
    # GÖRSEL BYTES
    # ========================================================

    image_bytes = None

    if uploaded_file:

        try:

            image_bytes = uploaded_file.getvalue()

        except Exception as e:

            st.error(
                "Görsel okunamadı."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # HİÇBİR ŞEY YOK
    # ========================================================

    if (
        not user_message
        and not image_bytes
    ):

        st.warning(
            "Mesaj yaz veya görsel gönder."
        )

        st.stop()


    # ========================================================
    # KULLANICI MESAJI
    # ========================================================

    with st.chat_message(
        "user"
    ):

        if image_bytes:

            st.image(
                image_bytes,
                caption="Gönderilen görsel",
                use_container_width=True
            )

        if user_message:

            st.markdown(
                user_message
            )


    # ========================================================
    # SOHBET ID
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.error(
                "Sohbet oluşturulamadı."
            )

            st.stop()


    # ========================================================
    # STORAGE
    # ========================================================

    image_url = None

    if image_bytes:

        extension = "jpg"

        if uploaded_file:

            original_name = (
                uploaded_file.name
                .lower()
            )

            if original_name.endswith(".png"):
                extension = "png"

            elif original_name.endswith(".webp"):
                extension = "webp"


        file_name = (
            "chat/"
            + str(uuid.uuid4())
            + "."
            + extension
        )


        try:

            image_url = upload_image(
                image_bytes,
                file_name,
                bucket_name="chat_images",
            )

        except Exception as e:

            st.warning(
                "Görsel Storage'a kaydedilemedi."
            )

            st.exception(e)


    # ========================================================
    # SOHBET GEÇMİŞİ
    # ========================================================

    history_text = ""

    for message in st.session_state.messages:

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            ""
        )

        if not content:
            continue

        if role == "user":

            history_text += (
                "\nKullanıcı: "
                + content
            )

        elif role == "assistant":

            history_text += (
                "\nKenz: "
                + content
            )


    # ========================================================
    # GARDIROP BELLEĞİ
    # ========================================================

    wardrobe_context = get_wardrobe_context()


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı normal sohbet edebilir.

Kullanıcı görsel gönderirse görseli gerçekten analiz et.

Görselde kıyafet, kombin, saç, ürün, nesne,
mekan veya başka bir şey varsa analiz edebilirsin.

Görseli görmediğin halde görmüş gibi davranma.

Kullanıcının gardırop belleği aşağıda verilmiştir.

Kullanıcı "bugün ne giysem?",
"ne giyebilirim?",
"bana kombin yap",
"hangi pantolonla bu gömlek olur?"
gibi bir soru sorarsa gardırop belleğindeki
kıyafetleri kullan.

Gardıropta olmayan bir parçayı kullanıcıda
varmış gibi gösterme.

Kombin önerirken renk, mevsim, stil ve
parçaların birbiriyle uyumunu değerlendir.

Kullanıcı yeni bir kıyafet fotoğrafı gönderirse
görseli analiz et.

Soruyu doğrudan cevapla.

Gereksiz yere uzun cevap verme.
"""


    # ========================================================
    # PROMPT
    # ========================================================

    prompt = (

        system_prompt

        + "\n\n"
        + "KULLANICININ GARDIROP BELLEĞİ:"
        + "\n"
        + wardrobe_context

        + "\n\n"
        + "ÖNCEKİ SOHBET:"
        + history_text

        + "\n\n"
        + "YENİ KULLANICI MESAJI:"
        + "\n"
        + (
            user_message
            if user_message
            else
            "Kullanıcı bir görsel gönderdi. "
            "Görseli analiz et."
        )
    )


    # ========================================================
    # USER MESSAGE SAVE
    # ========================================================

    try:

        add_message(

            conversation_id=(
                st.session_state.conversation_id
            ),

            role="user",

            content=user_message,

            image_url=image_url,

            provider=None,
        )

    except Exception as e:

        st.warning(
            "Kullanıcı mesajı kaydedilemedi."
        )

        st.exception(e)


    # ========================================================
    # GARDIROP ANALİZİ
    # ========================================================

    clothing_saved = 0

    if image_bytes and image_url:

        # Kullanıcı kıyafetle ilgiliyse
        # otomatik olarak gardırop analizine çalış.
        clothing_saved_data = analyze_clothing_image(
            image_bytes
        )

        clothing_saved = save_clothing_items(
            image_url,
            clothing_saved_data
        )


    # ========================================================
    # AI
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = ask_ai(
                    prompt=prompt,
                    image=image_bytes,
                )


                provider = (
                    st.session_state
                    .get(
                        "last_provider"
                    )
                )


                # ============================================
                # GARDIROP BİLGİSİ
                # ============================================

                if clothing_saved > 0:

                    answer += (

                        f"\n\n"
                        f"👕 **{clothing_saved} parça "
                        f"gardırop hafızama kaydedildi.**"
                    )


                st.markdown(
                    answer
                )


                # ============================================
                # AI MESAJINI KAYDET
                # ============================================

                try:

                    add_message(

                        conversation_id=(
                            st.session_state
                            .conversation_id
                        ),

                        role="assistant",

                        content=answer,

                        image_url=None,

                        provider=provider,
                    )

                except Exception as e:

                    st.warning(
                        "AI cevabı kaydedilemedi."
                    )

                    st.exception(e)


                # ============================================
                # SESSION
                # ============================================

                st.session_state.messages.append(
                    {
                        "role":
                            "user",

                        "content":
                            user_message,

                        "image_url":
                            image_url,

                        "provider":
                            None,
                    }
                )


                st.session_state.messages.append(
                    {
                        "role":
                            "assistant",

                        "content":
                            answer,

                        "image_url":
                            None,

                        "provider":
                            provider,
                    }
                )


                # ============================================
                # SOHBET BAŞLIĞI
                # ============================================

                conversations = (
                    get_conversations(
                        client_id
                    )
                )


                current = None

                for conversation in conversations:

                    if (
                        conversation["id"]
                        ==
                        st.session_state
                        .conversation_id
                    ):

                        current = conversation

                        break


                if current:

                    if (
                        current.get(
                            "title"
                        )
                        ==
                        "Yeni sohbet"
                    ):

                        title = (

                            user_message[:40]

                            if user_message

                            else
                            "Görsel sohbet"
                        )


                        update_conversation_title(

                            st.session_state
                            .conversation_id,

                            client_id,

                            title,
                        )


                # ============================================
                # UPLOADER SIFIRLA
                # ============================================

                st.session_state.uploader_key += 1


                st.rerun()


            except Exception as e:

                st.error(
                    "Kenz cevap veremedi."
                )

                st.exception(e)
