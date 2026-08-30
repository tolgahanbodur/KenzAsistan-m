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
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# CLIENT ID
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

    try:

        conversation = create_conversation(
            client_id=client_id,
            title="Yeni sohbet",
        )

        if not conversation:
            return False

        st.session_state.conversation_id = (
            conversation["id"]
        )

        st.session_state.messages = []

        return True

    except Exception as e:

        st.error(
            "Yeni sohbet oluşturulamadı."
        )

        st.exception(e)

        return False


# ============================================================
# SOHBET YÜKLE
# ============================================================

def load_conversation(
    conversation_id
):

    try:

        messages = get_messages(
            conversation_id
        )

        st.session_state.conversation_id = (
            conversation_id
        )

        st.session_state.messages = (
            messages or []
        )

        return True

    except Exception as e:

        st.error(
            "Sohbet yüklenemedi."
        )

        st.exception(e)

        return False


# ============================================================
# GARDIROP GETİR
# ============================================================

def get_wardrobe():

    try:

        wardrobe = get_all_clothes()

        if not wardrobe:
            return []

        return wardrobe

    except Exception as e:

        print(
            "WARDROBE ERROR:",
            repr(e)
        )

        return []


# ============================================================
# GARDIROP BELLEĞİNİ AI İÇİN HAZIRLA
# ============================================================

def get_wardrobe_context():

    wardrobe = get_wardrobe()

    if not wardrobe:

        return (
            "Kullanıcının gardırobunda "
            "henüz kayıtlı kıyafet yok."
        )

    lines = []

    for index, item in enumerate(
        wardrobe,
        start=1
    ):

        name = (
            item.get("name")
            or "İsimsiz parça"
        )

        category = (
            item.get("category")
            or "Belirtilmemiş"
        )

        color = (
            item.get("color")
            or "Belirtilmemiş"
        )

        style = (
            item.get("style")
            or "Belirtilmemiş"
        )

        season = (
            item.get("season")
            or "Belirtilmemiş"
        )

        description = (
            item.get("description")
            or ""
        )

        lines.append(
            f"{index}. "
            f"{name} | "
            f"Kategori: {category} | "
            f"Renk: {color} | "
            f"Stil: {style} | "
            f"Mevsim: {season} | "
            f"Detay: {description}"
        )

    return "\n".join(lines)


# ============================================================
# KIYAFET ANALİZİ
# ============================================================

def analyze_clothing_image(
    image_bytes,
    user_message
):

    if not image_bytes:
        return None

    prompt = """
Bir görsel gönderildi.

Kullanıcının mesajı:

""" + (
        user_message
        if user_message
        else
        "Kullanıcı sadece bir görsel gönderdi."
    ) + """

Bu görseli analiz et.

Özellikle görselde kıyafet, ayakkabı veya
aksesuar olup olmadığını belirle.

Eğer kıyafet / ayakkabı / aksesuar varsa
aşağıdaki JSON formatını kullan:

{
    "is_clothing": true,
    "items": [
        {
            "name": "kısa isim",
            "category": "kategori",
            "color": "renk",
            "style": "stil",
            "season": "mevsim",
            "description": "kısa açıklama"
        }
    ]
}

Kıyafet yoksa:

{
    "is_clothing": false,
    "items": []
}

Sadece JSON döndür.
"""

    try:

        result = ask_ai(
            prompt=prompt,
            image=image_bytes,
        )

        if not result:
            return None

        text = result.strip()

        # Markdown kod bloğunu temizle
        if "```json" in text:

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        elif "```" in text:

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        # JSON başlangıcını bul
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:

            return None

        text = text[
            start:end + 1
        ]

        data = json.loads(text)

        return data

    except Exception as e:

        print(
            "CLOTHING ANALYSIS ERROR:",
            repr(e)
        )

        return None


# ============================================================
# KIYAFET KAYDET
# ============================================================

def save_clothing_items(
    image_url,
    clothing_data
):

    if not image_url:
        return 0

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

    if not items:
        return 0

    saved = 0

    for item in items:

        try:

            name = (
                item.get("name")
                or "Kıyafet"
            )

            category = (
                item.get("category")
                or "Diğer"
            )

            color = (
                item.get("color")
                or "Belirtilmemiş"
            )

            style = (
                item.get("style")
                or "Belirtilmemiş"
            )

            season = (
                item.get("season")
                or "Belirtilmemiş"
            )

            description = (
                item.get("description")
                or ""
            )

            result = add_clothing_item(

                image_url=image_url,

                category=category,

                color=color,

                description=description,

                name=name,

                style=style,

                season=season,
            )

            if result:

                saved += 1

        except Exception as e:

            print(
                "CLOTHING SAVE ERROR:",
                repr(e)
            )

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

        if start_new_conversation():

            st.rerun()


    st.divider()


    # ========================================================
    # SOHBET GEÇMİŞİ
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
            "Sohbet geçmişi alınamadı."
        )

        st.exception(e)


    if not conversations:

        st.caption(
            "Henüz sohbet yok."
        )

    else:

        for conversation in conversations:

            conversation_id = (
                conversation["id"]
            )

            title = (
                conversation.get("title")
                or "Yeni sohbet"
            )

            if len(title) > 32:

                title = (
                    title[:32]
                    + "..."
                )

            if (
                conversation_id
                ==
                st.session_state.conversation_id
            ):

                button_text = (
                    "🟢 "
                    + title
                )

            else:

                button_text = (
                    "💬 "
                    + title
                )

            if st.button(
                button_text,
                key="chat_" + conversation_id,
                use_container_width=True,
            ):

                if load_conversation(
                    conversation_id
                ):

                    st.rerun()


    st.divider()


    # ========================================================
    # GARDIROP
    # ========================================================

    st.subheader(
        "👕 Gardırop"
    )

    wardrobe = get_wardrobe()

    wardrobe_count = len(
        wardrobe
    )

    if wardrobe_count == 0:

        st.caption(
            "Henüz kayıtlı parça yok."
        )

    else:

        st.success(
            f"{wardrobe_count} kayıtlı parça"
        )

        for item in wardrobe[:8]:

            name = (
                item.get("name")
                or item.get("category")
                or "Kıyafet"
            )

            color = (
                item.get("color")
                or ""
            )

            if color:

                st.write(
                    f"👕 {name} — {color}"
                )

            else:

                st.write(
                    f"👕 {name}"
                )

        if wardrobe_count > 8:

            st.caption(
                f"+ {wardrobe_count - 8} "
                f"parça daha"
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

                conversations = (
                    get_conversations(
                        client_id
                    )
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

Normal şekilde benimle sohbet edebilirsin.

📷 Fotoğraf göndererek görsel analiz
yaptırabilirsin.

👕 Kıyafet fotoğrafı gönderip
gardırobuna kaydedebilirsin.

🧠 Gardırobundaki parçaları daha sonra
kombin önerilerinde kullanabilirim.

Örneğin:

**"Bu gömleği gardırobuma ekle."**

**"Bu pantolonla ne giyebilirim?"**

**"Bugün ne giysem?"**

**"Gardırobumda hangi siyah parçalar var?"**
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

    key=(
        "uploader_"
        + str(
            st.session_state.uploader_key
        )
    ),
)


# ============================================================
# CHAT INPUT
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
    # GÖRSEL
    # ========================================================

    image_bytes = None

    if uploaded_file:

        try:

            image_bytes = (
                uploaded_file.getvalue()
            )

        except Exception as e:

            st.error(
                "Görsel okunamadı."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # BOŞ MESAJ
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
    # KULLANICI MESAJI EKRANDA
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
    # SOHBET KONTROL
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.error(
                "Sohbet oluşturulamadı."
            )

            st.stop()


    # ========================================================
    # GÖRSEL STORAGE
    # ========================================================

    image_url = None

    if image_bytes:

        extension = "jpg"

        if uploaded_file:

            original_name = (
                uploaded_file.name.lower()
            )

            if original_name.endswith(
                ".png"
            ):

                extension = "png"

            elif original_name.endswith(
                ".webp"
            ):

                extension = "webp"

            elif original_name.endswith(
                ".jpeg"
            ):

                extension = "jpg"


        file_name = (

            "chat/"

            + str(
                uuid.uuid4()
            )

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
    # GARDIROP
    # ========================================================

    wardrobe_context = (
        get_wardrobe_context()
    )


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel bir yapay zeka
asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Normal sohbet yapabilirsin.

Kullanıcı görsel gönderirse gerçekten
görseli analiz et.

Görseli görmediğin halde görmüş gibi davranma.

Kullanıcının kişisel gardırop belleği aşağıda
verilmiştir.

Kullanıcı:

"Bugün ne giysem?"

"Ne giyebilirim?"

"Bana kombin yap."

"Bu gömlekle ne giyebilirim?"

"Gardırobumda ne var?"

gibi sorular sorarsa gardırop belleğini kullan.

Gardıropta olmayan bir parçayı kullanıcıda
varmış gibi söyleme.

Kombin oluştururken:

- renk uyumu
- mevsim
- hava koşulları
- stil
- parçaların uyumu
- kullanıcının mevcut gardırobu

gibi faktörleri dikkate al.

Kullanıcı bir kıyafet fotoğrafı gönderirse
görseli analiz edebilirsin.

Kullanıcı "bu kıyafeti gardırobuma ekle"
gibi bir şey söylerse bunun bir gardırop
kaydı olduğunu dikkate al.

Cevaplarını gereksiz yere uzatma.
"""


    # ========================================================
    # AI PROMPT
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
    # USER MESAJINI SUPABASE'E KAYDET
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

        # Kullanıcı açıkça kıyafet eklemek
        # istiyorsa kaydet.

        clothing_request_words = [

            "gardırobuma ekle",
            "gardrobuma ekle",
            "gardıroba ekle",
            "gardroba ekle",
            "dolabıma ekle",
            "dolaba ekle",
            "kıyafetlerime ekle",
            "kıyafetlerime kaydet",
            "gardırobumda olsun",
            "gardıroba kaydet",
        ]

        wants_to_save = any(

            word in user_message.lower()

            for word in clothing_request_words
        )


        if wants_to_save:

            clothing_data = (
                analyze_clothing_image(
                    image_bytes,
                    user_message
                )
            )

            clothing_saved = (
                save_clothing_items(
                    image_url,
                    clothing_data
                )
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


                # ====================================================
                # GARDIROP KAYIT BİLGİSİ
                # ====================================================

                if clothing_saved > 0:

                    answer += (

                        "\n\n"
                        "👕 **"
                        + str(
                            clothing_saved
                        )
                        + " parça "
                        "gardırop hafızama "
                        "kaydedildi.**"
                    )


                st.markdown(
                    answer
                )


                # ====================================================
                # AI MESAJINI KAYDET
                # ====================================================

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


                # ====================================================
                # SESSION'A EKLE
                # ====================================================

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


                # ====================================================
                # SOHBET BAŞLIĞI
                # ====================================================

                try:

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

                        current_title = (
                            current.get(
                                "title"
                            )
                        )


                        if (
                            current_title
                            ==
                            "Yeni sohbet"
                        ):

                            if user_message:

                                title = (
                                    user_message[:40]
                                )

                            elif image_bytes:

                                title = (
                                    "Görsel sohbet"
                                )

                            else:

                                title = (
                                    "Yeni sohbet"
                                )


                            update_conversation_title(

                                st.session_state
                                .conversation_id,

                                client_id,

                                title,
                            )

                except Exception as e:

                    print(
                        "TITLE UPDATE ERROR:",
                        repr(e)
                    )


                # ====================================================
                # UPLOADER SIFIRLA
                # ====================================================

                st.session_state.uploader_key += 1


                # ====================================================
                # YENİDEN ÇİZ
                # ====================================================

                st.rerun()


            except Exception as e:

                st.error(
                    "Kenz cevap veremedi."
                )

                st.exception(e)
