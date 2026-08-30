import uuid
import streamlit as st

from ai_router import ask_ai

from supabase_client import (
    get_current_user,
    get_profile,

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
    append_memory,
    get_memory,
    clear_memory,
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
    border: 1px solid rgba(128,128,128,.25);
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

    "conversation_id": None,

    "messages": [],

    "initialized": False,

    "last_provider": None,

    "show_wardrobe": False,

    "show_settings": False,

    "chat_file": None,

}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CURRENT LOCAL USER
# ============================================================

try:

    current_user = get_current_user()

except Exception as e:

    st.error(
        "Kenz kullanıcı sistemi başlatılamadı."
    )

    st.exception(e)

    st.stop()


user_id = str(
    current_user["id"]
)

user_name = "Kullanıcı"


try:

    profile = get_profile()

    if profile:

        user_name = (
            profile.get("name")
            or "Kullanıcı"
        )

except Exception:

    pass


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
    # MEMORY
    # ========================================================

    if st.button(
        "🧠 Hafıza",
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
        "KENZ KULLANICISI"
    )

    st.write(
        "👤 " + user_name
    )

    st.caption(
        "Bu cihazın yerel Kenz kimliği"
    )

    st.code(
        user_id,
        language=None
    )


# ============================================================
# WARDROBE PAGE
# ============================================================

if st.session_state.show_wardrobe:

    st.title(
        "👕 Gardırobum"
    )

    st.caption(
        "Kenz'in kombin önerilerinde kullanacağı gerçek kıyafetlerin."
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
            Fotoğraf gönderip:

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
# MEMORY PAGE
# ============================================================

if st.session_state.show_settings:

    st.title(
        "🧠 Kenz Hafızası"
    )

    st.caption(
        "Kenz'in senin hakkında sakladığı bilgiler."
    )


    try:

        current_memory = (
            get_memory()
        )

    except Exception:

        current_memory = ""


    st.markdown(
        '<div class="memory-box">',
        unsafe_allow_html=True
    )


    memory_text = st.text_area(
        "Hafıza",
        value=current_memory,
        height=300,
        placeholder=(
            "Kenz'in senin hakkında bilmesini istediğin "
            "bilgiler burada tutulur."
        ),
        label_visibility="collapsed",
    )


    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    st.write("")


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "💾 Hafızayı kaydet",
            type="primary",
            use_container_width=True,
        ):

            try:

                save_preferences(
                    memory_text
                )

                st.success(
                    "Hafıza kaydedildi."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Hafıza kaydedilemedi."
                )

                st.exception(e)


    with col2:

        if st.button(
            "🗑️ Hafızayı temizle",
            use_container_width=True,
        ):

            try:

                clear_memory()

                st.success(
                    "Hafıza temizlendi."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Hafıza temizlenemedi."
                )

                st.exception(e)


    st.divider()


    st.subheader(
        "Otomatik hafıza"
    )

    st.write(
        """
Kenz bundan sonra önemli ve uzun süre geçerli
olabilecek bilgileri otomatik olarak hafızaya
ekleyebilecek şekilde hazırlanmıştır.

Örneğin:

• Sevdiğin tarzlar
• Kıyafet tercihlerin
• Genel tercihlerin
• Sürekli kullandığın ayarlar
• Kenz'e verdiğin kalıcı bilgiler
        """
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


        elif (
            file_url
            and file_type.startswith(
                "video/"
            )
        ):

            st.video(
                file_url
            )


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
            f"""
### Merhaba 👋

Ben **Kenz**.

Senin kişisel yapay zeka asistanınım.

Normal şekilde sohbet edebiliriz, dosyaları
inceleyebilir, görselleri analiz edebilir ve
gardırobunu öğrenebilirim.

Ayrıca önemli bilgilerini otomatik olarak
hafızama kaydedebilirim.

Örneğin:

📸 **"Bu kombin nasıl?"**

🎥 **"Bu videoda ne oluyor?"**

🎵 **"Bu ses kaydını özetle."**

👕 **"Bugün ne giysem?"**

🧥 **"Bu gömleği gardırobuma ekle."**

🧠 **"Ben sade ve klasik giyinmeyi seviyorum."**
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
    # MEMORY
    # ========================================================

    preference_text = ""


    try:

        preference_text = (
            get_memory()
        )

    except Exception:

        preference_text = ""


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
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """

Sen Kenz adında kişisel yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcının verdiği bilgileri sonraki sohbetlerde
kullanmak için hafıza sistemini dikkate al.

Kullanıcı aynı bilgiyi tekrar söylemek zorunda
kalmamalıdır.

============================================================
MEDYA
============================================================

Kullanıcı sana metin, fotoğraf, video veya ses
gönderebilir.

Fotoğraf gönderilirse görüntüyü gerçekten analiz et.

Video gönderilirse içeriğini analiz et.

Ses gönderilirse mümkün olduğunda içeriğini analiz et.

Medyayı görmediğin veya analiz edemediğin halde
görmüş gibi davranma.

============================================================
GARDIROP
============================================================

Kullanıcının gerçek gardırop parçaları:

""" + wardrobe_text + """

Gardıropta olmayan bir parçayı kullanıcıda varmış
gibi gösterme.

Kullanıcı "bunu gardırobuma ekle" derse uygun
kıyafet bilgilerini çıkarmaya çalış.

============================================================
KULLANICI HAFIZASI
============================================================

Daha önce kaydedilmiş bilgiler:

""" + preference_text + """

Bu bilgileri gerektiğinde cevaplarında kullan.

============================================================
ÖNCEKİ SOHBET
============================================================

""" + history_text


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


                # =================================================
                # SESSION HISTORY
                # =================================================

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


                # =================================================
                # AUTOMATIC MEMORY
                # =================================================

                # Basit otomatik hafıza:
                # Kullanıcı kalıcı bir bilgi verdiğinde
                # bu bilgi hafızaya eklenir.

                memory_triggers = [

                    "ben ",
                    "bende ",
                    "seviyorum",
                    "sevmiyorum",
                    "tercih ederim",
                    "tercih etmiyorum",
                    "hoşlanıyorum",
                    "hoşlanmıyorum",
                    "boyum",
                    "kilom",
                    "yaşım",
                    "yaşındayım",
                    "favorim",
                    "tercihim",
                    "kullanıyorum",
                    "kullanmıyorum",
                    "istiyorum",
                    "istemiyorum",
                    "gardırobumda",
                    "tarzım",
                ]


                lower_message = (
                    user_message.lower()
                )


                should_remember = any(
                    trigger in lower_message
                    for trigger in memory_triggers
                )


                if should_remember:

                    try:

                        memory_entry = (
                            "Kullanıcı: "
                            + user_message
                        )

                        append_memory(
                            memory_entry
                        )

                    except Exception:

                        pass


                # =================================================
                # CONVERSATION TITLE
                # =================================================

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


                # =================================================
                # CLEAR FILE
                # =================================================

                st.session_state.chat_file = None


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
    "Kenz • Kişisel AI • Metin + Görsel + Video + Ses • Otomatik Hafıza"
)
