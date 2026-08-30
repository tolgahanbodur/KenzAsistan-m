import uuid

import streamlit as st

from ai_router import ask_ai

from supabase_client import (
    get_client_id,
    get_conversations,
    create_conversation,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title,
    upload_file,
    get_all_clothes,
)


# ============================================================
# PAGE
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

defaults = {
    "conversation_id": None,
    "messages": [],
    "initialized": False,
    "last_provider": None,
    "show_wardrobe": False,

    # Chat attachment
    "attached_file_bytes": None,
    "attached_file_name": None,
    "attached_file_type": None,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CONVERSATION
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


def load_conversation(conversation_id):

    messages = get_messages(
        conversation_id
    )

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = messages or []


# ============================================================
# INITIALIZE
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

        st.error("Kenz başlatılamadı.")
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
    # NEW CHAT
    # ========================================================

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
    ):

        if start_new_conversation():

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

        st.rerun()


    if st.session_state.show_wardrobe:

        st.subheader("👕 Gardırobum")

        try:

            clothes = get_all_clothes(
                client_id
            )

        except Exception as e:

            clothes = []

            st.error(
                "Gardırop yüklenemedi."
            )

            st.exception(e)


        st.caption(
            f"{len(clothes)} parça"
        )


        if clothes:

            for item in clothes:

                name = (
                    item.get("name")
                    or item.get("category")
                    or "Kıyafet"
                )

                image_url = item.get(
                    "image_url"
                )


                if image_url:

                    st.image(
                        image_url,
                        use_container_width=True
                    )


                st.write(
                    "👕 " + name
                )


                if item.get("color"):

                    st.caption(
                        "Renk: "
                        + str(
                            item["color"]
                        )
                    )


                if item.get("style"):

                    st.caption(
                        "Stil: "
                        + str(
                            item["style"]
                        )
                    )


                if item.get("season"):

                    st.caption(
                        "Sezon: "
                        + str(
                            item["season"]
                        )
                    )


                st.divider()

        else:

            st.caption(
                "Gardırop henüz boş."
            )


    st.divider()


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    st.subheader(
        "💬 Sohbet geçmişi"
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


    for conversation in conversations:

        conversation_id = conversation["id"]

        title = (
            conversation.get("title")
            or "Yeni sohbet"
        )


        if len(title) > 32:

            title = title[:32] + "..."


        if st.button(
            "💬 " + title,
            key="conversation_" + conversation_id,
            use_container_width=True,
        ):

            load_conversation(
                conversation_id
            )

            st.rerun()


    st.divider()


    # ========================================================
    # PROVIDER
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
    # DELETE
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
# MAIN
# ============================================================

st.title(
    "🤖 Kenz Asistan"
)

st.caption(
    "Metin, fotoğraf, video ve ses analiz edebilen "
    "kişisel yapay zeka asistanın."
)


# ============================================================
# PREVIOUS MESSAGES
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


    with st.chat_message(role):

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
# EMPTY CHAT
# ============================================================

if not st.session_state.messages:

    with st.chat_message("assistant"):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Bana metin yazabilir veya sohbet çubuğundaki
**📎 butonundan dosya ekleyebilirsin.**

Desteklenen medya:

📷 Fotoğraf  
🎥 Video  
🎵 Ses  
💬 Metin

Örneğin:

**"Bu kombin nasıl?"**

**"Bu videoda ne oluyor?"**

**"Bu ses kaydını özetle."**

**"Bugün ne giysem?"**

**"Gardırobumdan bana kombin yap."**
"""
        )


# ============================================================
# CHAT ATTACHMENT AREA
# ============================================================

st.markdown(
    """
<style>

.chat-attachment-label {
    font-size: 14px;
    color: #888;
    margin-bottom: 4px;
}

.attachment-box {
    border: 1px solid rgba(128,128,128,.35);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 8px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# FILE SELECTOR
# ============================================================

with st.popover(
    "📎",
    use_container_width=False,
):

    st.markdown(
        "### 📎 Dosya ekle"
    )

    attachment = st.file_uploader(

        "Fotoğraf, video veya ses seç",

        type=[
            # IMAGE
            "jpg",
            "jpeg",
            "png",
            "webp",

            # VIDEO
            "mp4",
            "mov",
            "webm",

            # AUDIO
            "mp3",
            "wav",
            "m4a",
            "aac",
            "ogg",
        ],

        accept_multiple_files=False,

        key="chat_file_picker",
    )


    if attachment:

        st.session_state.attached_file_bytes = (
            attachment.getvalue()
        )

        st.session_state.attached_file_name = (
            attachment.name
        )

        st.session_state.attached_file_type = (
            attachment.type
            or "application/octet-stream"
        )


# ============================================================
# ATTACHED FILE PREVIEW
# ============================================================

attached_bytes = (
    st.session_state.attached_file_bytes
)

attached_name = (
    st.session_state.attached_file_name
)

attached_type = (
    st.session_state.attached_file_type
)


if attached_bytes:

    st.markdown(
        '<div class="attachment-box">',
        unsafe_allow_html=True
    )


    st.caption(
        "📎 Eklenen dosya"
    )


    if attached_type.startswith("image/"):

        st.image(
            attached_bytes,
            use_container_width=True
        )


    elif attached_type.startswith("video/"):

        st.video(
            attached_bytes
        )


    elif attached_type.startswith("audio/"):

        st.audio(
            attached_bytes
        )


    st.caption(
        attached_name
    )


    if st.button(
        "✕ Dosyayı kaldır",
        key="remove_attachment",
    ):

        st.session_state.attached_file_bytes = None
        st.session_state.attached_file_name = None
        st.session_state.attached_file_type = None

        st.rerun()


    st.markdown(
        "</div>",
        unsafe_allow_html=True
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

    user_message = user_message.strip()


    if not user_message:

        st.warning(
            "Mesaj boş olamaz."
        )

        st.stop()


    # ========================================================
    # CURRENT FILE
    # ========================================================

    file_bytes = (
        st.session_state.attached_file_bytes
    )

    file_name = (
        st.session_state.attached_file_name
    )

    file_type = (
        st.session_state.attached_file_type
    )

    file_url = None


    # ========================================================
    # CONVERSATION
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.error(
                "Sohbet oluşturulamadı."
            )

            st.stop()


    # ========================================================
    # UPLOAD TO SUPABASE
    # ========================================================

    if file_bytes:

        extension = ""

        if file_name and "." in file_name:

            extension = (
                "."
                + file_name
                .split(".")[-1]
                .lower()
            )


        storage_name = (
            "chat/"
            + str(uuid.uuid4())
            + extension
        )


        try:

            file_url = upload_file(
                file_bytes,
                storage_name,
                file_type,
                "chat_images",
            )

        except Exception as e:

            st.warning(
                "Dosya Supabase'e kaydedilemedi."
            )

            st.exception(e)


    # ========================================================
    # SHOW USER MESSAGE
    # ========================================================

    with st.chat_message("user"):

        if file_bytes:

            if file_type.startswith("image/"):

                st.image(
                    file_bytes,
                    use_container_width=True
                )

            elif file_type.startswith("video/"):

                st.video(
                    file_bytes
                )

            elif file_type.startswith("audio/"):

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
    # WARDROBE
    # ========================================================

    wardrobe_text = ""


    try:

        clothes = get_all_clothes(
            client_id
        )


        if clothes:

            for item in clothes:

                wardrobe_text += (
                    "\n- "
                    + str(
                        item.get("name")
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
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı sana metin, fotoğraf, video veya
ses gönderebilir.

MEDYA:

- Kullanıcı bir fotoğraf gönderirse fotoğrafı analiz et.
- Kullanıcı video gönderirse videoyu analiz et.
- Kullanıcı ses gönderirse sesi analiz et.
- Dosyayı görmeden görmüş gibi davranma.
- Kullanıcı dosya hakkında soru soruyorsa doğrudan
  dosyaya göre cevap ver.

SOHBET:

Önceki konuşmaları dikkate al.
Kullanıcının daha önce söylediği bilgileri
gerektiğinde kullan.

GARDIROP:

Aşağıdaki liste kullanıcının kayıtlı gardırobudur.

Kullanıcı:

"Bugün ne giysem?"

"Gardırobumdan kombin yap."

"Bu pantolonla ne giyilir?"

"Elimde ne var?"

gibi sorular sorarsa öncelikle aşağıdaki
gardırop verilerini kullan.

Gardıropta bulunmayan bir parçayı kullanıcıda
varmış gibi kabul etme.

KULLANICININ GARDIROBU:

""" + wardrobe_text + """

ÖNCEKİ SOHBET:

""" + history_text


    # ========================================================
    # CURRENT PROMPT
    # ========================================================

    prompt = (
        system_prompt
        + "\n\nYENİ KULLANICI MESAJI:\n"
        + user_message
    )


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    try:

        add_message(

            conversation_id=(
                st.session_state.conversation_id
            ),

            role="user",

            content=user_message,

            image_url=file_url,

            provider=None,
        )

    except Exception as e:

        st.warning(
            "Kullanıcı mesajı kaydedilemedi."
        )

        st.exception(e)


    # ========================================================
    # AI
    # ========================================================

    with st.chat_message("assistant"):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = ask_ai(

                    prompt=prompt,

                    uploaded_file=None
                    if not file_bytes
                    else {
                        "bytes": file_bytes,
                        "name": file_name,
                        "type": file_type,
                    },
                )


                provider = (
                    st.session_state.get(
                        "last_provider"
                    )
                )


                st.markdown(
                    answer
                )


                # ==========================================
                # SAVE AI
                # ==========================================

                add_message(

                    conversation_id=(
                        st.session_state.conversation_id
                    ),

                    role="assistant",

                    content=answer,

                    image_url=None,

                    provider=provider,
                )


                # ==========================================
                # SESSION
                # ==========================================

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": user_message,
                        "image_url": file_url,
                        "provider": None,
                    }
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "image_url": None,
                        "provider": provider,
                    }
                )


                # ==========================================
                # TITLE
                # ==========================================

                conversations = get_conversations(
                    client_id
                )


                current = None


                for conversation in conversations:

                    if (
                        conversation["id"]
                        ==
                        st.session_state.conversation_id
                    ):

                        current = conversation
                        break


                if current:

                    if (
                        current.get("title")
                        ==
                        "Yeni sohbet"
                    ):

                        title = (
                            user_message[:40]
                            if user_message
                            else "Medya sohbeti"
                        )


                        update_conversation_title(

                            st.session_state.conversation_id,

                            client_id,

                            title,
                        )


                # ==========================================
                # CLEAR ATTACHMENT
                # ==========================================

                st.session_state.attached_file_bytes = None
                st.session_state.attached_file_name = None
                st.session_state.attached_file_type = None


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
    "Kenz • Metin + Görsel + Video + Ses"
)
