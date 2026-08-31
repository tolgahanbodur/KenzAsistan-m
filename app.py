import base64
import mimetypes
import os
import re

import streamlit as st

from gemini_helper import (
    chat_with_kenz,
    convert_media_url,
    extract_wardrobe_item,
)

from supabase_client import (
    get_user_client,
    get_messages,
    save_message,
    get_memories,
    save_memory,
    delete_memory,
    get_wardrobe,
    add_wardrobe_item,
    get_conversations,
    switch_conversation,
    new_conversation,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Kenz",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
<style>

#MainMenu {
    visibility: hidden;
}

header {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.stApp {
    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(99,102,241,.16),
            transparent 38%
        ),
        #09090b;

    color: #f4f4f5;
}

section[data-testid="stSidebar"] {
    background: #111113;
    border-right: 1px solid #27272a;
}

.kenz-logo {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
}

.kenz-subtitle {
    color: #a1a1aa;
    font-size: 13px;
    margin-bottom: 15px;
}

.user-badge {
    padding: 8px 11px;
    border-radius: 10px;
    background: #18181b;
    border: 1px solid #27272a;
    color: #71717a;
    font-size: 10px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.main-logo {
    text-align: center;
    font-size: 54px;
    font-weight: 900;
    margin-top: 120px;
}

.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -1.5px;
}

.main-subtitle {
    text-align: center;
    color: #a1a1aa;
    margin-top: 5px;
    margin-bottom: 40px;
}

.memory-item,
.wardrobe-item {
    padding: 9px 11px;
    border-radius: 10px;
    background: #18181b;
    border: 1px solid #27272a;
    margin-bottom: 7px;
    font-size: 12px;
}

.small-muted {
    color: #71717a;
}

.stButton > button {
    border-radius: 11px;
    border: 1px solid #27272a;
    background: #18181b;
}

.stButton > button:hover {
    border-color: #52525b;
    background: #27272a;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# USER
# ============================================================

try:

    supabase, session_id = get_user_client()

except Exception as e:

    st.error(
        "Kenz başlatılamadı."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# CURRENT CONVERSATION
# ============================================================

if "kenz_conversation_id" not in st.session_state:

    st.session_state.kenz_conversation_id = None


# ============================================================
# LOAD MESSAGES
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = get_messages(
        supabase,
        session_id,
        100,
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    st.markdown(
        '<div class="kenz-logo">✦ KENZ</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="kenz-subtitle">'
        'Kişisel yapay zekâ asistanın'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="user-badge">
        Kullanıcı: {session_id[:16]}...
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
        key="new_chat_button",
    ):

        new_conversation(
            supabase,
            session_id,
        )

        st.session_state.messages = []

        st.rerun()


    st.divider()


    # ========================================================
    # CONVERSATIONS
    # ========================================================

    st.subheader("💬 Sohbetler")

    try:

        conversations = get_conversations(
            supabase,
            session_id,
        )

    except Exception as e:

        conversations = []

        st.caption(
            "Sohbetler yüklenemedi."
        )


    if conversations:

        for conversation in conversations[:30]:

            conversation_id = conversation.get(
                "id"
            )

            title = (
                conversation.get(
                    "title"
                )
                or "Yeni sohbet"
            )

            title = str(title)

            if len(title) > 30:

                title = (
                    title[:30]
                    + "..."
                )


            current_id = (
                st.session_state.get(
                    "kenz_conversation_id"
                )
            )


            if (
                str(current_id)
                == str(conversation_id)
            ):

                button_text = (
                    f"● {title}"
                )

            else:

                button_text = (
                    f"○ {title}"
                )


            if st.button(
                button_text,
                key=(
                    f"conversation_"
                    f"{conversation_id}"
                ),
                use_container_width=True,
            ):

                switch_conversation(
                    supabase,
                    session_id,
                    conversation_id,
                )

                st.rerun()

    else:

        st.caption(
            "Henüz sohbet yok."
        )


    st.divider()


    # ========================================================
    # MEMORY
    # ========================================================

    st.subheader("🧠 Hafıza")

    try:

        memories = get_memories(
            supabase,
            session_id,
        )

    except Exception:

        memories = []


    if memories:

        for memory in memories[:15]:

            memory_text = (
                memory.get(
                    "memory",
                    "",
                )
            )

            st.markdown(
                f"""
                <div class="memory-item">
                {memory_text}
                </div>
                """,
                unsafe_allow_html=True,
            )


        if st.button(
            "🗑️ Hafızayı temizle",
            use_container_width=True,
            key="clear_memory",
        ):

            for memory in memories:

                delete_memory(
                    supabase,
                    session_id,
                    memory["id"],
                )

            st.rerun()

    else:

        st.caption(
            "Henüz kayıtlı bilgi yok."
        )


    st.divider()


    # ========================================================
    # WARDROBE
    # ========================================================

    st.subheader("👕 Gardırop")

    try:

        wardrobe = get_wardrobe(
            supabase,
            session_id,
        )

    except Exception:

        wardrobe = []


    st.caption(
        f"{len(wardrobe)} parça"
    )


    for item in wardrobe[:10]:

        name = item.get(
            "name",
            "Kıyafet",
        )

        category = item.get(
            "category",
            "",
        )

        color = item.get(
            "color",
            "",
        )

        st.markdown(
            f"""
            <div class="wardrobe-item">

            <b>{name}</b>

            <br>

            <span class="small-muted">
            {category}
            """

            + (
                f" · {color}"
                if color
                else ""
            )

            + """
            </span>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# WELCOME
# ============================================================

if not st.session_state.messages:

    st.markdown(
        '<div class="main-logo">✦</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Kenz</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Nasıl yardımcı olabilirim?'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    with st.chat_message(role):

        file_name = message.get(
            "file_name"
        )

        file_type = message.get(
            "file_type"
        )

        file_url = message.get(
            "file_url"
        )


        # ----------------------------------------------------
        # FILE
        # ----------------------------------------------------

        if file_name:

            if file_type:

                if file_type.startswith(
                    "image/"
                ):

                    if file_url:

                        st.image(
                            file_url,
                            use_container_width=True,
                        )

                    else:

                        st.caption(
                            f"📎 {file_name}"
                        )

                elif file_type.startswith(
                    "audio/"
                ):

                    if file_url:

                        st.audio(
                            file_url
                        )

                    else:

                        st.caption(
                            f"🎵 {file_name}"
                        )

                elif file_type.startswith(
                    "video/"
                ):

                    if file_url:

                        st.video(
                            file_url
                        )

                    else:

                        st.caption(
                            f"🎥 {file_name}"
                        )

                else:

                    st.caption(
                        f"📎 {file_name}"
                    )

            else:

                st.caption(
                    f"📎 {file_name}"
                )


        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        if content:

            st.markdown(
                content
            )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Kenz'e bir şey yaz...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "gif",
        "pdf",
        "txt",
        "csv",
        "docx",
        "xlsx",
        "mp3",
        "wav",
        "m4a",
        "ogg",
        "opus",
        "mp4",
        "mov",
        "mkv",
        "webm",
        "avi",
    ],
    max_upload_size=200,
)


# ============================================================
# MESSAGE
# ============================================================

if prompt:

    user_text = (
        getattr(
            prompt,
            "text",
            "",
        )
        or ""
    ).strip()


    uploaded_file = getattr(
        prompt,
        "file",
        None,
    )


    # --------------------------------------------------------
    # FILE DATA
    # --------------------------------------------------------

    file_bytes = None
    file_name = None
    mime_type = None


    if uploaded_file:

        file_bytes = uploaded_file.getvalue()

        file_name = uploaded_file.name

        mime_type = (
            uploaded_file.type
            or mimetypes.guess_type(
                file_name
            )[0]
            or "application/octet-stream"
        )


    if not user_text and not file_bytes:

        st.stop()


    # ========================================================
    # SHOW USER MESSAGE
    # ========================================================

    with st.chat_message("user"):

        if file_bytes:

            if mime_type.startswith(
                "image/"
            ):

                st.image(
                    file_bytes,
                    use_container_width=True,
                )

            elif mime_type.startswith(
                "audio/"
            ):

                st.audio(
                    file_bytes
                )

            elif mime_type.startswith(
                "video/"
            ):

                st.video(
                    file_bytes
                )

            else:

                st.caption(
                    f"📎 {file_name}"
                )


        if user_text:

            st.markdown(
                user_text
            )


    # ========================================================
    # MEMORY
    # ========================================================

    lower = user_text.lower()


    memory_phrases = [
        "bunu hatırla",
        "bunu hafızana al",
        "hafızanda tut",
        "aklında tut",
        "bundan sonra",
    ]


    should_save_memory = any(
        phrase in lower
        for phrase in memory_phrases
    )


    if should_save_memory:

        memory_text = user_text


        for phrase in memory_phrases:

            memory_text = re.sub(
                re.escape(phrase),
                "",
                memory_text,
                flags=re.IGNORECASE,
            )


        memory_text = memory_text.strip()


        if memory_text:

            try:

                save_memory(
                    supabase,
                    session_id,
                    memory_text,
                )

            except Exception as e:

                st.warning(
                    "Hafıza kaydedilemedi."
                )


    # ========================================================
    # FORGET
    # ========================================================

    forget_phrases = [
        "bunu unut",
        "şunu unut",
        "hafızadan sil",
    ]


    if any(
        phrase in lower
        for phrase in forget_phrases
    ):

        target = user_text


        for phrase in forget_phrases:

            target = re.sub(
                re.escape(phrase),
                "",
                target,
                flags=re.IGNORECASE,
            )


        target = target.strip().lower()


        current_memories = get_memories(
            supabase,
            session_id,
        )


        for memory in current_memories:

            text = memory.get(
                "memory",
                "",
            )


            if (
                not target
                or target in text.lower()
            ):

                delete_memory(
                    supabase,
                    session_id,
                    memory["id"],
                )


    # ========================================================
    # WARDROBE
    # ========================================================

    wardrobe_command = any(
        phrase in lower
        for phrase in [
            "gardırobuma ekle",
            "gardıroba ekle",
            "dolabıma ekle",
        ]
    )


    if (
        file_bytes
        and wardrobe_command
    ):

        try:

            with st.spinner(
                "Kıyafeti analiz ediyorum..."
            ):

                item = extract_wardrobe_item(
                    file_bytes,
                    mime_type,
                )


                add_wardrobe_item(
                    supabase,
                    session_id,
                    item,
                )


            st.success(
                "Kıyafeti gardırobuna ekledim."
            )


            st.rerun()


        except Exception as e:

            st.error(
                "Gardırop işlemi başarısız."
            )

            st.code(
                str(e)
            )


    # ========================================================
    # URL CONVERSION
    # ========================================================

    url_match = re.search(
        r"https?://[^\s]+",
        user_text,
        re.IGNORECASE,
    )


    formats = [
        "mp3",
        "wav",
        "flac",
        "m4a",
        "aac",
        "opus",
        "ogg",
        "mp4",
        "mkv",
        "webm",
        "mov",
        "avi",
        "gif",
    ]


    selected_format = None


    for fmt in formats:

        if re.search(
            rf"\b{fmt}\b",
            lower,
        ):

            selected_format = fmt

            break


    conversion_words = [
        "çevir",
        "dönüştür",
        "indir",
        "yap",
        "format",
    ]


    if (
        url_match
        and selected_format
        and any(
            word in lower
            for word in conversion_words
        )
    ):

        url = url_match.group(0)


        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                f"{selected_format.upper()} hazırlanıyor..."
            ):

                try:

                    result = convert_media_url(
                        url,
                        selected_format,
                    )


                    st.success(
                        "Hazır."
                    )


                    st.download_button(
                        (
                            f"📥 "
                            f"{selected_format.upper()} "
                            f"indir"
                        ),
                        result["bytes"],
                        file_name=result["file_name"],
                        mime=result["mime_type"],
                        use_container_width=True,
                    )


                    answer = (
                        "Tamamdır. Medyayı "
                        f"**{selected_format.upper()}** "
                        "formatına dönüştürdüm."
                    )


                    st.markdown(
                        answer
                    )


                    save_message(
                        supabase,
                        session_id,
                        "user",
                        user_text,
                        file_name,
                        file_bytes,
                        mime_type,
                        "user",
                    )


                    save_message(
                        supabase,
                        session_id,
                        "assistant",
                        answer,
                        provider="converter",
                    )


                    st.session_state.messages = (
                        get_messages(
                            supabase,
                            session_id,
                            100,
                        )
                    )


                    st.stop()


                except Exception as e:

                    st.error(
                        "Bu bağlantı dönüştürülemedi."
                    )

                    st.caption(
                        str(e)
                    )

                    st.stop()


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    save_message(
        supabase,
        session_id,
        "user",
        user_text,
        file_name,
        file_bytes,
        mime_type,
        "user",
    )


    # ========================================================
    # GET CONTEXT
    # ========================================================

    history = get_messages(
        supabase,
        session_id,
        30,
    )


    memories = get_memories(
        supabase,
        session_id,
    )


    wardrobe = get_wardrobe(
        supabase,
        session_id,
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

                answer = chat_with_kenz(
                    user_text=user_text,
                    file_bytes=file_bytes,
                    file_name=file_name,
                    mime_type=mime_type,
                    history=history,
                    memories=memories,
                    wardrobe=wardrobe,
                )


                st.markdown(
                    answer
                )


                provider = st.session_state.get(
                    "last_provider",
                    "gemini",
                )


                save_message(
                    supabase,
                    session_id,
                    "assistant",
                    answer,
                    provider=provider,
                )


                # ------------------------------------------------
                # AUTOMATIC TITLE
                # ------------------------------------------------

                conversations = get_conversations(
                    supabase,
                    session_id,
                )


                current_id = (
                    st.session_state.get(
                        "kenz_conversation_id"
                    )
                )


                if (
                    current_id
                    and user_text
                ):

                    current = next(
                        (
                            c
                            for c in conversations
                            if str(
                                c["id"]
                            )
                            == str(
                                current_id
                            )
                        ),
                        None,
                    )


                    if current:

                        current_title = (
                            current.get(
                                "title"
                            )
                            or ""
                        )


                        if (
                            current_title
                            == "Yeni sohbet"
                        ):

                            clean_title = (
                                user_text
                                .replace(
                                    "\n",
                                    " ",
                                )
                                .strip()
                            )


                            if len(
                                clean_title
                            ) > 60:

                                clean_title = (
                                    clean_title[:60]
                                    + "..."
                                )


                            (
                                supabase
                                .table(
                                    "conversations"
                                )
                                .update({
                                    "title":
                                        clean_title,
                                    "updated_at":
                                        "now()",
                                })
                                .eq(
                                    "id",
                                    current_id,
                                )
                                .execute()
                            )


                # ------------------------------------------------
                # REFRESH
                # ------------------------------------------------

                st.session_state.messages = (
                    get_messages(
                        supabase,
                        session_id,
                        100,
                    )
                )


            except Exception as e:

                st.error(
                    "Kenz cevap verirken hata oluştu."
                )

                st.code(
                    str(e)
                )
