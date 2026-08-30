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
    add_clothing_item,
    get_all_clothes,
    delete_clothing_item,
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
# SESSION
# ============================================================

defaults = {

    "conversation_id":
        None,

    "messages":
        [],

    "initialized":
        False,

    "last_provider":
        None,

    "selected_file":
        None,

    "selected_file_name":
        None,

    "selected_file_type":
        None,

    "show_wardrobe":
        False,
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

    st.session_state.conversation_id = (
        conversation["id"]
    )

    st.session_state.messages = []

    return True


def load_conversation(
    conversation_id
):

    messages = get_messages(
        conversation_id
    )

    st.session_state.conversation_id = (
        conversation_id
    )

    st.session_state.messages = (
        messages or []
    )


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

        st.error(
            "Kenz başlatılamadı."
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

        st.subheader(
            "👕 Gardırobum"
        )

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
                        + item["color"]
                    )

                if item.get("style"):

                    st.caption(
                        "Stil: "
                        + item["style"]
                    )

                st.divider()

        else:

            st.caption(
                "Gardırop henüz boş."
            )


    st.divider()


    # ========================================================
    # HISTORY
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

        conversation_id = (
            conversation["id"]
        )

        title = (
            conversation.get(
                "title"
            )
            or "Yeni sohbet"
        )


        if len(title) > 32:

            title = title[:32] + "..."


        if st.button(
            "💬 " + title,
            key=
                "conversation_"
                + conversation_id,
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

            delete_conversation(
                st.session_state.conversation_id,
                client_id,
            )

            st.session_state.conversation_id = (
                None
            )

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

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Bana:

📷 Fotoğraf  
🎥 Video  
🎵 Ses  
💬 Metin

gönderebilirsin.

Örneğin:

**"Bu kombin nasıl?"**

**"Bu videoda ne oluyor?"**

**"Bu ses kaydını özetle."**

**"Bugün ne giysem?"**

**"Gardırobumdan bana kombin yap."**
"""
        )


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(

    "📎 Dosya ekle",

    type=[

        # Images
        "jpg",
        "jpeg",
        "png",
        "webp",

        # Video
        "mp4",
        "mov",
        "webm",

        # Audio
        "mp3",
        "wav",
        "m4a",
        "aac",
        "ogg",
    ],

    accept_multiple_files=False,

    key="media_uploader",
)


# ============================================================
# FILE PREVIEW
# ============================================================

if uploaded_file:

    file_type = (
        uploaded_file.type
        or ""
    )


    st.markdown(
        "### 📎 Eklenen dosya"
    )


    if file_type.startswith(
        "image/"
    ):

        st.image(
            uploaded_file,
            use_container_width=True
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


    st.caption(
        uploaded_file.name
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
    # FILE BYTES
    # ========================================================

    file_bytes = None
    file_url = None
    file_type = None
    file_name = None


    if uploaded_file:

        file_bytes = uploaded_file.getvalue()

        file_type = (
            uploaded_file.type
            or "application/octet-stream"
        )

        file_name = (
            uploaded_file.name
        )


    # ========================================================
    # CHAT ID
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.error(
                "Sohbet oluşturulamadı."
            )

            st.stop()


    # ========================================================
    # UPLOAD
    # ========================================================

    if file_bytes:

        extension = ""

        if "." in file_name:

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
    # WARDROBE MEMORY
    # ========================================================

    wardrobe_text = ""


    try:

        clothes = get_all_clothes(
            client_id
        )

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

    except Exception:

        wardrobe_text = ""


    # ========================================================
    # SYSTEM
    # ========================================================

    system_prompt = """

Sen Kenz adında kişisel yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı sana metin, fotoğraf, video veya
ses gönderebilir.

MEDYA KURALLARI:

- Görsel gönderilirse gerçekten analiz et.
- Video gönderilirse videonun içeriğini analiz et.
- Ses gönderilirse sesi analiz et ve gerekiyorsa
  konuşmayı yazıya dök.
- Medyayı görmediğin halde görmüş gibi davranma.
- Kullanıcı dosya hakkında soru soruyorsa doğrudan
  dosyayı analiz ederek cevap ver.

GARDIROP:

Kullanıcının gardırobunda bulunan parçalar aşağıdadır.

Kullanıcı "bugün ne giysem?",
"gardırobumdan kombin yap",
"şu pantolonla ne giyilir?" gibi sorular
sorarsa öncelikle bu parçaları kullan.

Gardıropta olmayan bir parçayı kullanıcıda
varmış gibi kabul etme.

GARDIROP:

""" + wardrobe_text + """

ÖNCEKİ SOHBET:

""" + history_text


    # ========================================================
    # CURRENT PROMPT
    # ========================================================

    prompt = (
        system_prompt
        + "\n\nYENİ MESAJ:\n"
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

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = ask_ai(

                    prompt=prompt,

                    uploaded_file=
                        uploaded_file,
                )


                provider = (
                    st.session_state
                    .get(
                        "last_provider"
                    )
                )


                st.markdown(
                    answer
                )


                # ============================================
                # SAVE AI
                # ============================================

                add_message(

                    conversation_id=
                        st.session_state
                        .conversation_id,

                    role="assistant",

                    content=answer,

                    image_url=None,

                    provider=provider,
                )


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
                            file_url,

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
                # TITLE
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
                            else "Medya sohbeti"
                        )


                        update_conversation_title(

                            st.session_state
                            .conversation_id,

                            client_id,

                            title,
                        )


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
