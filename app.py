import uuid
import streamlit as st

from ai_router import ask_ai

from supabase_client import (
    get_current_user,
    get_profile,
    sign_up,
    sign_in,
    sign_out,

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
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

    /* Ana alan */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 320px;
    }

    /* Chat input */
    div[data-testid="stChatInput"] {
        bottom: 15px;
    }

    /* Dosya butonu */
    div[data-testid="stFileUploader"] {
        margin-top: 0;
    }

    /* Başlık */
    .kenz-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .kenz-subtitle {
        color: #777;
        margin-bottom: 2rem;
    }

    /* Gardırop kartı */
    .wardrobe-card {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 12px;
    }

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {

    "conversation_id": None,

    "messages": [],

    "initialized": False,

    "last_provider": None,

    "show_wardrobe": False,

    "show_settings": False,

    "auth_mode": "login",

    "selected_file": None,

    "selected_file_name": None,

    "selected_file_type": None,

}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CURRENT USER
# ============================================================

try:

    current_user = get_current_user()

except Exception:

    current_user = None


# ============================================================
# AUTH SCREEN
# ============================================================

if not current_user:

    st.markdown(
        """
        <div style="text-align:center; margin-top:80px;">
            <div style="font-size:55px;">🤖</div>
            <div class="kenz-title">Kenz</div>
            <div class="kenz-subtitle">
                Kişisel yapay zeka asistanın
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(
        [
            "🔐 Giriş yap",
            "✨ Üye ol",
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with tab_login:

        st.subheader("Tekrar hoş geldin 👋")

        login_email = st.text_input(
            "E-posta",
            key="login_email",
        )

        login_password = st.text_input(
            "Şifre",
            type="password",
            key="login_password",
        )

        if st.button(
            "Giriş yap",
            type="primary",
            use_container_width=True,
        ):

            if not login_email or not login_password:

                st.warning(
                    "E-posta ve şifre gir."
                )

            else:

                try:

                    sign_in(
                        login_email,
                        login_password,
                    )

                    st.success(
                        "Giriş başarılı."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        str(e)
                    )


    # ========================================================
    # REGISTER
    # ========================================================

    with tab_register:

        st.subheader("Kenz'e katıl 🚀")

        register_name = st.text_input(
            "Adın",
            key="register_name",
        )

        register_email = st.text_input(
            "E-posta",
            key="register_email",
        )

        register_password = st.text_input(
            "Şifre",
            type="password",
            key="register_password",
        )

        register_password2 = st.text_input(
            "Şifre tekrar",
            type="password",
            key="register_password2",
        )

        if st.button(
            "Üye ol",
            type="primary",
            use_container_width=True,
        ):

            if not register_email:

                st.warning(
                    "E-posta adresi gir."
                )

            elif not register_password:

                st.warning(
                    "Şifre gir."
                )

            elif len(register_password) < 6:

                st.warning(
                    "Şifre en az 6 karakter olmalı."
                )

            elif register_password != register_password2:

                st.warning(
                    "Şifreler aynı değil."
                )

            else:

                try:

                    response = sign_up(
                        register_email,
                        register_password,
                        register_name,
                    )

                    session = getattr(
                        response,
                        "session",
                        None,
                    )

                    if session:

                        st.success(
                            "Hesabın oluşturuldu!"
                        )

                        st.rerun()

                    else:

                        st.success(
                            "Kayıt başarılı. "
                            "E-posta adresini doğrulaman gerekebilir."
                        )

                except Exception as e:

                    st.error(
                        str(e)
                    )

    st.stop()


# ============================================================
# USER INFORMATION
# ============================================================

user_id = str(
    current_user.id
)

user_email = (
    getattr(
        current_user,
        "email",
        None
    )
    or ""
)


# ============================================================
# PROFILE
# ============================================================

try:

    profile = get_profile()

except Exception:

    profile = None


user_name = ""

if profile:

    user_name = (
        profile.get("name")
        or ""
    )


if not user_name:

    metadata = getattr(
        current_user,
        "user_metadata",
        {}
    ) or {}

    user_name = (
        metadata.get("name")
        or "Kullanıcı"
    )


# ============================================================
# CONVERSATION FUNCTIONS
# ============================================================

def start_new_conversation():

    try:

        conversation = (
            create_conversation(
                title="Yeni sohbet"
            )
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

        conversations = (
            get_conversations()
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

        conversations = (
            get_conversations()
        )

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
                conversation.get(
                    "title"
                )
                or "Yeni sohbet"
            )

            if len(title) > 28:

                title = (
                    title[:28]
                    + "..."
                )


            if st.button(
                "💬 " + title,
                key="chat_" + conversation_id,
                use_container_width=True,
            ):

                load_conversation(
                    conversation_id
                )

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
    # USER
    # ========================================================

    st.caption(
        "HESAP"
    )

    st.write(
        "👤 " + user_name
    )

    st.caption(
        user_email
    )


    if st.button(
        "🚪 Çıkış yap",
        use_container_width=True,
    ):

        try:

            sign_out()

            st.session_state.clear()

            st.rerun()

        except Exception as e:

            st.error(
                "Çıkış yapılamadı."
            )

            st.exception(e)


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
            Bir fotoğraf gönderip örneğin:

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

                image_url = (
                    item.get(
                        "image_url"
                    )
                )

                if image_url:

                    st.image(
                        image_url,
                        use_container_width=True,
                    )


                name = (
                    item.get(
                        "name"
                    )
                    or item.get(
                        "category"
                    )
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
# SETTINGS PAGE
# ============================================================

if st.session_state.show_settings:

    st.title(
        "⚙️ Ayarlar"
    )

    st.subheader(
        "Profil"
    )

    name = st.text_input(
        "Ad",
        value=user_name,
    )

    email = st.text_input(
        "E-posta",
        value=user_email,
        disabled=True,
    )


    if st.button(
        "Profili kaydet",
        type="primary",
    ):

        try:

            from supabase_client import update_profile

            update_profile(
                name=name
            )

            st.success(
                "Profil güncellendi."
            )

        except Exception as e:

            st.error(
                "Profil güncellenemedi."
            )

            st.exception(e)


    st.divider()

    st.subheader(
        "🧠 Kenz hafızası"
    )

    current_preferences = ""

    try:

        preferences = (
            get_preferences()
        )

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
        "Kenz'in senin hakkında hatırlamasını istediğin bilgiler",
        value=current_preferences,
        height=180,
        placeholder=(
            "Örneğin:\n"
            "Old Money ve Smart Casual tarzını seviyorum.\n"
            "Yazın ince ve sade kıyafetleri tercih ederim."
        ),
    )


    if st.button(
        "Hafızayı kaydet",
        type="primary",
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


    st.stop()


# ============================================================
# MAIN CHAT HEADER
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

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        elif (
            file_url
            and file_type.startswith(
                "video/"
            )
        ):

            st.video(
                file_url
            )


        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

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

        greeting_name = (
            user_name
            if user_name
            else "orada"
        )

        st.markdown(
            f"""
### Merhaba {greeting_name} 👋

Ben **Kenz**.

Seninle normal şekilde sohbet edebilir,
fotoğraf, video ve ses dosyalarını analiz edebilirim.

Ayrıca gardırobunu öğrenip sana kombin
önerileri hazırlayabilirim.

Örneğin:

📸 **"Bu kombin nasıl?"**

🎥 **"Bu videoda ne oluyor?"**

🎵 **"Bu ses kaydını özetle."**

👕 **"Bugün ne giysem?"**

🧥 **"Bu gömleği gardırobuma ekle."**

✨ **"Gardırobumdan yazlık bir kombin yap."**
"""
        )


# ============================================================
# FILE UPLOADER
# ============================================================

# ChatGPT'deki mesaj kutusunun hemen üstünde
# küçük dosya alanı.

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
    # UPLOAD FILE
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
    # DISPLAY USER MESSAGE
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
    # HISTORY
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

        clothes = (
            get_all_clothes()
        )


        if clothes:

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


                if item.get(
                    "category"
                ):

                    wardrobe_text += (
                        " | kategori: "
                        + str(
                            item["category"]
                        )
                    )


                if item.get(
                    "color"
                ):

                    wardrobe_text += (
                        " | renk: "
                        + str(
                            item["color"]
                        )
                    )


                if item.get(
                    "style"
                ):

                    wardrobe_text += (
                        " | stil: "
                        + str(
                            item["style"]
                        )
                    )


                if item.get(
                    "season"
                ):

                    wardrobe_text += (
                        " | sezon: "
                        + str(
                            item["season"]
                        )
                    )


                if item.get(
                    "description"
                ):

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

        preferences = (
            get_preferences()
        )

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

============================================================
MEDYA
============================================================

Kullanıcı sana metin, fotoğraf, video veya ses
gönderebilir.

Fotoğraf gönderilirse görüntüyü gerçekten analiz et.

Video gönderilirse içeriğini analiz et.

Ses gönderilirse mümkün olduğunda içeriğini analiz et,
konuşmayı anlamaya ve özetlemeye çalış.

Medyayı görmediğin veya analiz edemediğin halde
görmüş gibi davranma.

============================================================
GARDIROP
============================================================

Kullanıcının gardırobunda bulunan gerçek parçalar
aşağıda listelenmiştir.

Kullanıcı:

"Bugün ne giysem?"

"Gardırobumdan kombin yap."

"Bu pantolonla ne giyilir?"

"Yazlık kombin yap."

gibi bir şey sorarsa öncelikle aşağıdaki gerçek
gardırop parçalarını kullan.

Gardıropta olmayan bir parçayı kullanıcıda varmış
gibi gösterme.

Kullanıcı bir fotoğraf gönderip:

"Bunu gardırobuma ekle."

derse fotoğrafı analiz et ve uygun kıyafet bilgilerini
belirlemeye çalış.

============================================================
KULLANICI HAFIZASI
============================================================

Kullanıcı hakkında daha önce kaydedilmiş bilgiler:

""" + preference_text + """

============================================================
GARDIROP PARÇALARI
============================================================

""" + wardrobe_text + """

============================================================
ÖNCEKİ SOHBET
============================================================

""" + history_text


    # ========================================================
    # CURRENT PROMPT
    # ========================================================

    prompt = (
        system_prompt
        + "\n\n==================================================\n"
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

                # ------------------------------------------------
                # AI'YA DOSYAYI GÖNDER
                # ------------------------------------------------

                if file_bytes:

                    ai_file = {
                        "bytes":
                            file_bytes,

                        "name":
                            file_name,

                        "type":
                            file_type,
                    }

                else:

                    ai_file = None


                answer = ask_ai(
                    prompt=prompt,
                    uploaded_file=ai_file,
                )


                provider = (
                    st.session_state.get(
                        "last_provider"
                    )
                )


                # ------------------------------------------------
                # ANSWER
                # ------------------------------------------------

                st.markdown(
                    answer
                )


                # ------------------------------------------------
                # SAVE AI MESSAGE
                # ------------------------------------------------

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


                # ------------------------------------------------
                # SESSION
                # ------------------------------------------------

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


                # ------------------------------------------------
                # CONVERSATION TITLE
                # ------------------------------------------------

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
                            current.get(
                                "title"
                            )
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


                # ------------------------------------------------
                # CLEAR SELECTED FILE
                # ------------------------------------------------

                st.session_state.selected_file = None

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
