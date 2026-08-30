import uuid
import streamlit as st

from ai_router import ask_ai

from supabase_client import (
    create_conversation,
    get_conversations,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title,

    upload_file,

    add_clothing_item,
    get_all_clothes,
    delete_clothing_item,

    get_preferences,
    save_preferences,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Kenz",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

section[data-testid="stSidebar"] {
    min-width: 280px;
    max-width: 320px;
}

div[data-testid="stChatInput"] {
    bottom: 15px;
}

.kenz-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.kenz-subtitle {
    color: #777;
    margin-bottom: 2rem;
}

.wardrobe-card {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 12px;
}

.memory-box {
    border: 1px solid rgba(128,128,128,.2);
    border-radius: 12px;
    padding: 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {

    # Kenz'in kullanıcıyı tanıması için
    # tarayıcı oturumu boyunca kullanılacak ID
    "session_id": str(uuid.uuid4()),

    "conversation_id": None,

    "messages": [],

    "initialized": False,

    "last_provider": None,

    "show_wardrobe": False,

    "show_settings": False,

}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CONVERSATION
# ============================================================

def start_new_conversation():

    try:

        conversation = create_conversation(
            title="Yeni sohbet"
        )

        if not conversation:

            st.error(
                "Yeni sohbet oluşturulamadı."
            )

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
# LOAD CONVERSATION
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
# INITIALIZE
# ============================================================

if not st.session_state.initialized:

    try:

        conversations = get_conversations()


        if conversations:

            load_conversation(
                conversations[0]["id"]
            )

        else:

            start_new_conversation()


        st.session_state.initialized = True


    except Exception as e:

        st.error(
            "Kenz başlatılamadı."
        )

        st.exception(e)

        st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # ========================================================
    # LOGO
    # ========================================================

    st.markdown(
        """
        <div style="
            font-size:28px;
            font-weight:700;
            padding-bottom:10px;
        ">
            🤖 Kenz
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.caption(
        "Kişisel yapay zeka asistanın"
    )


    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
        type="primary",
    ):

        if start_new_conversation():

            st.rerun()


    st.divider()


    # ========================================================
    # CONVERSATIONS
    # ========================================================

    st.caption(
        "SOHBETLER"
    )


    try:

        conversations = get_conversations()

    except Exception:

        conversations = []


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


            if len(title) > 28:

                title = (
                    title[:28]
                    + "..."
                )


            if st.button(
                "💬 " + title,
                key="chat_" + str(
                    conversation_id
                ),
                use_container_width=True,
            ):

                load_conversation(
                    conversation_id
                )

                st.session_state.show_wardrobe = False
                st.session_state.show_settings = False

                st.rerun()


    st.divider()


    # ========================================================
    # WARDROBE
    # ========================================================

    if st.button(
        "👕 Gardırop",
        use_container_width=True,
    ):

        st.session_state.show_wardrobe = (
            not st.session_state.show_wardrobe
        )

        st.session_state.show_settings = False

        st.rerun()


    # ========================================================
    # SETTINGS
    # ========================================================

    if st.button(
        "⚙️ Ayarlar",
        use_container_width=True,
    ):

        st.session_state.show_settings = (
            not st.session_state.show_settings
        )

        st.session_state.show_wardrobe = False

        st.rerun()


    st.divider()


    # ========================================================
    # SESSION INFO
    # ========================================================

    st.caption(
        "KENZ OTURUMU"
    )

    st.caption(
        "Bu sürümde hesap sistemi yok."
    )

    st.caption(
        "Kenz doğrudan kullanılabilir."
    )


# ============================================================
# WARDROBE PAGE
# ============================================================

if st.session_state.show_wardrobe:

    st.title(
        "👕 Gardırobum"
    )

    st.caption(
        "Kenz'in kombin önerilerinde kullanacağı kıyafetlerin."
    )


    try:

        clothes = get_all_clothes()

    except Exception as e:

        clothes = []

        st.error(
            "Gardırop yüklenemedi."
        )

        st.exception(e)


    st.metric(
        "Toplam parça",
        len(clothes)
    )


    st.divider()


    if not clothes:

        st.info(
            "Gardırobun henüz boş."
        )

        st.markdown(
            """
Bir fotoğraf gönderip:

**"Bunu gardırobuma ekle."**

diyebilirsin.
"""
        )


    else:

        columns = st.columns(3)


        for index, item in enumerate(clothes):

            column = columns[
                index % 3
            ]


            with column:

                st.markdown(
                    '<div class="wardrobe-card">',
                    unsafe_allow_html=True
                )


                image_url = item.get(
                    "image_url"
                )


                if image_url:

                    st.image(
                        image_url,
                        use_container_width=True,
                    )


                name = (
                    item.get("name")
                    or item.get("category")
                    or "Kıyafet"
                )


                st.markdown(
                    "**"
                    + str(name)
                    + "**"
                )


                if item.get("color"):

                    st.caption(
                        "🎨 "
                        + str(
                            item["color"]
                        )
                    )


                if item.get("style"):

                    st.caption(
                        "✨ "
                        + str(
                            item["style"]
                        )
                    )


                if item.get("season"):

                    st.caption(
                        "🌤️ "
                        + str(
                            item["season"]
                        )
                    )


                if item.get("description"):

                    st.caption(
                        str(
                            item["description"]
                        )
                    )


                if st.button(
                    "🗑️ Sil",
                    key=
                        "delete_clothes_"
                        + str(
                            item["id"]
                        ),
                    use_container_width=True,
                ):

                    try:

                        delete_clothing_item(
                            item["id"]
                        )

                        st.success(
                            "Parça silindi."
                        )

                        st.rerun()


                    except Exception as e:

                        st.error(
                            "Parça silinemedi."
                        )

                        st.exception(e)


                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )


    st.stop()


# ============================================================
# SETTINGS
# ============================================================

if st.session_state.show_settings:

    st.title(
        "⚙️ Ayarlar"
    )


    st.subheader(
        "🧠 Kenz hafızası"
    )


    st.caption(
        "Kenz hakkında verdiğin bilgileri burada görebilir "
        "ve düzenleyebilirsin."
    )


    current_preferences = ""


    try:

        preferences = get_preferences()


        if preferences:

            current_preferences = (
                preferences.get(
                    "preferences"
                )
                or ""
            )


    except Exception:

        current_preferences = ""


    preference_text = st.text_area(

        "Kenz'in hafızası",

        value=current_preferences,

        height=250,

        placeholder=(
            "Örneğin:\n"
            "Old Money ve Smart Casual tarzını seviyorum.\n"
            "Yazın ince ve sade kıyafetler tercih ederim.\n"
            "Kahve seviyorum.\n"
            "Kenz bana Türkçe cevap versin."
        ),
    )


    if st.button(
        "💾 Hafızayı kaydet",
        type="primary",
        use_container_width=True,
    ):

        try:

            save_preferences(
                preference_text
            )

            st.success(
                "Hafıza kaydedildi."
            )


        except Exception as e:

            st.error(
                "Hafıza kaydedilemedi."
            )

            st.exception(e)


    st.divider()


    st.subheader(
        "ℹ️ Sistem"
    )

    st.info(
        "Bu Kenz sürümünde hesap sistemi bulunmuyor. "
        "Uygulama açıldığında otomatik bir oturum oluşturulur."
    )


    st.stop()


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="kenz-title">🤖 Kenz</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="kenz-subtitle">'
    'Kişisel yapay zeka asistanın'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.messages:

    role = (
        message.get(
            "role",
            "assistant"
        )
    )


    content = (
        message.get(
            "content"
        )
        or ""
    )


    file_url = (
        message.get(
            "file_url"
        )
    )


    file_type = (
        message.get(
            "file_type"
        )
        or ""
    )


    with st.chat_message(
        role
    ):

        # IMAGE

        if (
            file_url
            and file_type.startswith(
                "image/"
            )
        ):

            st.image(
                file_url,
                use_container_width=True
            )


        # VIDEO

        elif (
            file_url
            and file_type.startswith(
                "video/"
            )
        ):

            st.video(
                file_url
            )


        # AUDIO

        elif (
            file_url
            and file_type.startswith(
                "audio/"
            )
        ):

            st.audio(
                file_url
            )


        if content:

            st.markdown(
                content
            )


# ============================================================
# EMPTY CHAT
# ============================================================

if not st.session_state.messages:

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Seninle normal şekilde sohbet edebilirim.

Fotoğraf, video ve ses dosyalarını analiz edebilirim.

Ayrıca verdiğin bilgileri hafızamda tutabilir,
önceki sohbetlerini hatırlayabilir ve
gardırobunu öğrenebilirim.

Örneğin:

💬 **"Bugün ne yapmalıyım?"**

📸 **"Bu kombin nasıl?"**

🎥 **"Bu videoda ne oluyor?"**

🎵 **"Bu ses kaydını özetle."**

👕 **"Bugün ne giysem?"**

🧥 **"Bu gömleği gardırobuma ekle."**

✨ **"Gardırobumdan yazlık bir kombin yap."**

🧠 **"Benim hakkımda bunu hatırla: ..."**
"""
        )


# ============================================================
# FILE UPLOADER
# ============================================================

uploaded_file = st.file_uploader(

    "📎",

    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",

        "mp4",
        "mov",
        "webm",

        "mp3",
        "wav",
        "m4a",
        "aac",
        "ogg",
    ],

    accept_multiple_files=False,

    key="chat_file",

    label_visibility="collapsed",
)


# ============================================================
# FILE PREVIEW
# ============================================================

if uploaded_file:

    file_type = (
        uploaded_file.type
        or ""
    )


    st.caption(
        "📎 "
        + uploaded_file.name
        + " — Mesajını yazıp Enter'a bas."
    )


    if file_type.startswith(
        "image/"
    ):

        st.image(
            uploaded_file,
            width=350,
        )


    elif file_type.startswith(
        "video/"
    ):

        st.video(
            uploaded_file
        )


    elif file_type.startswith(
        "audio/"
    ):

        st.audio(
            uploaded_file
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_message = st.chat_input(
    "Kenz'e mesaj yaz..."
)


# ============================================================
# SEND
# ============================================================

if user_message:

    user_message = (
        user_message.strip()
    )


    if not user_message:

        st.warning(
            "Mesaj boş olamaz."
        )

        st.stop()


    # ========================================================
    # FILE DATA
    # ========================================================

    file_bytes = None
    file_url = None
    file_name = None
    file_type = None


    if uploaded_file:

        try:

            file_bytes = (
                uploaded_file.getvalue()
            )

            file_name = (
                uploaded_file.name
            )

            file_type = (
                uploaded_file.type
                or "application/octet-stream"
            )


        except Exception as e:

            st.error(
                "Dosya okunamadı."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # CONVERSATION
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.stop()


    # ========================================================
    # FILE UPLOAD
    # ========================================================

    if file_bytes:

        extension = ""


        if (
            file_name
            and "."
            in file_name
        ):

            extension = (
                "."
                + file_name
                .split(".")[-1]
                .lower()
            )


        storage_name = (
            "chat/"
            + str(
                uuid.uuid4()
            )
            + extension
        )


        try:

            file_url = upload_file(

                file_bytes,

                storage_name,

                file_type,

                "chat_files",
            )


        except Exception as e:

            st.warning(
                "Dosya buluta yüklenemedi."
            )

            st.exception(e)


    # ========================================================
    # SHOW USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user"
    ):

        if file_bytes:

            if file_type.startswith(
                "image/"
            ):

                st.image(
                    file_bytes,
                    use_container_width=True
                )


            elif file_type.startswith(
                "video/"
            ):

                st.video(
                    file_bytes
                )


            elif file_type.startswith(
                "audio/"
            ):

                st.audio(
                    file_bytes
                )


        st.markdown(
            user_message
        )


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    history_text = ""


    for message in st.session_state.messages:

        role = message.get(
            "role"
        )

        content = (
            message.get(
                "content"
            )
            or ""
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
    # WARDROBE MEMORY
    # ========================================================

    wardrobe_text = ""


    try:

        clothes = get_all_clothes()


        for item in clothes:

            wardrobe_text += (
                "\n- "
                + str(
                    item.get(
                        "name"
                    )
                    or "Kıyafet"
                )
            )


            if item.get("category"):

                wardrobe_text += (
                    " | kategori: "
                    + str(
                        item["category"]
                    )
                )


            if item.get("color"):

                wardrobe_text += (
                    " | renk: "
                    + str(
                        item["color"]
                    )
                )


            if item.get("style"):

                wardrobe_text += (
                    " | stil: "
                    + str(
                        item["style"]
                    )
                )


            if item.get("season"):

                wardrobe_text += (
                    " | sezon: "
                    + str(
                        item["season"]
                    )
                )


            if item.get("description"):

                wardrobe_text += (
                    " | açıklama: "
                    + str(
                        item["description"]
                    )
                )


    except Exception:

        wardrobe_text = ""


    # ========================================================
    # USER MEMORY
    # ========================================================

    preference_text = ""


    try:

        preferences = get_preferences()


        if preferences:

            preference_text = (
                preferences.get(
                    "preferences"
                )
                or ""
            )


    except Exception:

        preference_text = ""


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """

Sen Kenz adında kişisel yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcının sorusunu mümkün olduğunca doğrudan çöz.

Bilmediğin bir şeyi biliyormuş gibi gösterme.

============================================================
KULLANICI HAFIZASI
============================================================

Aşağıdaki bilgiler kullanıcı hakkında daha önce
kaydedilmiş bilgilerdir.

Bunları gerektiğinde cevaplarında kullan.

""" + preference_text + """

============================================================
GARDIROP
============================================================

Kullanıcının gerçek gardırop parçaları:

""" + wardrobe_text + """

Gardıropta olmayan bir parçayı kullanıcıda varmış
gibi gösterme.

Kullanıcı gardırobuna yeni bir kıyafet eklemek
istediğinde, gönderilen fotoğrafı analiz etmeye çalış.

============================================================
ÖNCEKİ SOHBET
============================================================

""" + history_text + """

============================================================
GENEL DAVRANIŞ
============================================================

Kullanıcı senden bir şey istediğinde yardımcı ol.

Gereksiz şekilde "bunu yapamam" deme.

Eğer bir işlemi gerçekleştirmek için araç veya
dış sistem gerekiyorsa bunu açıkça belirt.

Fotoğraf, video veya ses dosyasını gerçekten
analiz edemiyorsan görmüş gibi davranma.

Kullanıcı hakkında önemli ve uzun süre geçerli
bir bilgi söylediğinde, bunu hafıza sistemine
kaydetmek gerektiğini değerlendir.
"""


    # ========================================================
    # CURRENT PROMPT
    # ========================================================

    prompt = (
        system_prompt
        + "\n\n"
        + "==================================================\n"
        + "YENİ KULLANICI MESAJI\n"
        + "==================================================\n"
        + user_message
    )


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    try:

        add_message(

            conversation_id=
                st.session_state
                .conversation_id,

            role="user",

            content=user_message,

            file_url=file_url,

            file_name=file_name,

            file_type=file_type,

            provider=None,
        )


    except Exception as e:

        st.warning(
            "Mesaj kaydedilemedi."
        )

        st.exception(e)


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

                # ============================================
                # AI FILE
                # ============================================

                ai_file = None


                if file_bytes:

                    ai_file = {

                        "bytes":
                            file_bytes,

                        "name":
                            file_name,

                        "type":
                            file_type,
                    }


                # ============================================
                # ASK AI
                # ============================================

                answer = ask_ai(

                    prompt=prompt,

                    uploaded_file=ai_file,
                )


                provider = (
                    st.session_state.get(
                        "last_provider"
                    )
                )


                # ============================================
                # SHOW ANSWER
                # ============================================

                st.markdown(
                    answer
                )


                # ============================================
                # SAVE ANSWER
                # ============================================

                try:

                    add_message(

                        conversation_id=
                            st.session_state
                            .conversation_id,

                        role="assistant",

                        content=answer,

                        file_url=None,

                        file_name=None,

                        file_type=None,

                        provider=provider,
                    )


                except Exception as e:

                    st.warning(
                        "AI cevabı kaydedilemedi."
                    )

                    st.exception(e)


                # ============================================
                # SESSION HISTORY
                # ============================================

                st.session_state.messages.append(
                    {

                        "role":
                            "user",

                        "content":
                            user_message,

                        "file_url":
                            file_url,

                        "file_name":
                            file_name,

                        "file_type":
                            file_type,

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

                        "file_url":
                            None,

                        "file_name":
                            None,

                        "file_type":
                            None,

                        "provider":
                            provider,
                    }
                )


                # ============================================
                # CONVERSATION TITLE
                # ============================================

                try:

                    conversations = (
                        get_conversations()
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
                            current.get("title")
                            == "Yeni sohbet"
                        ):

                            title = (
                                user_message[:40]
                                if user_message
                                else "Medya sohbeti"
                            )


                            update_conversation_title(

                                st.session_state
                                .conversation_id,

                                title,
                            )


                except Exception:

                    pass


                # ============================================
                # CLEAR FILE
                # ============================================

                try:

                    del st.session_state[
                        "chat_file"
                    ]

                except Exception:

                    pass


                st.rerun()


            except Exception as e:

                st.error(
                    "Kenz cevap veremedi."
                )

                st.exception(e)


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "Kenz • Kişisel AI • Metin + Görsel + Video + Ses"
)
