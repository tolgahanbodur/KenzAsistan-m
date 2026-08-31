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
    color: #a1a1aa;
    font-size: 11px;
}

.main-logo {
    text-align: center;
    font-size: 48px;
    font-weight: 900;
    margin-top: 100px;
}

.main-title {
    text-align: center;
    font-size: 36px;
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

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# USER
# ============================================================

try:

    supabase, user_id = get_user_client()

except Exception as e:

    st.error(
        "Kenz başlatılamadı."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# SESSION
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = get_messages(
        supabase,
        user_id,
        100,
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

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
        Kullanıcı: {user_id[:10]}...
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    # ========================================================
    # MEMORY
    # ========================================================

    st.subheader("🧠 Hafıza")

    memories = get_memories(
        supabase,
        user_id,
    )

    if memories:

        for memory in memories[:15]:

            st.markdown(
                f"""
                <div class="memory-item">
                {memory.get("memory", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.caption(
            "Henüz hafıza yok."
        )

    if memories:

        if st.button(
            "🗑️ Hafızayı temizle",
            use_container_width=True,
        ):

            for memory in memories:

                delete_memory(
                    supabase,
                    user_id,
                    memory["id"],
                )

            st.rerun()

    st.divider()

    # ========================================================
    # WARDROBE
    # ========================================================

    st.subheader("👕 Gardırop")

    wardrobe = get_wardrobe(
        supabase,
        user_id,
    )

    st.caption(
        f"{len(wardrobe)} parça"
    )

    for item in wardrobe[:10]:

        st.markdown(
            f"""
            <div class="wardrobe-item">
            <b>{item.get("name", "Kıyafet")}</b><br>
            <span class="small-muted">
            {item.get("category", "")}
            ·
            {item.get("color", "")}
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

        file_data = message.get(
            "file_data"
        )

        if file_name and file_data:

            try:

                raw = base64.b64decode(
                    file_data
                )

                mime = mimetypes.guess_type(
                    file_name
                )[0] or ""

                if mime.startswith("image/"):

                    st.image(
                        raw,
                        use_container_width=True,
                    )

                elif mime.startswith("audio/"):

                    st.audio(raw)

                elif mime.startswith("video/"):

                    st.video(raw)

                else:

                    st.download_button(
                        "📎 Dosyayı görüntüle",
                        raw,
                        file_name=file_name,
                        mime=mime,
                    )

            except Exception:
                pass

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

            if mime_type.startswith("image/"):

                st.image(
                    file_bytes,
                    use_container_width=True,
                )

            elif mime_type.startswith("audio/"):

                st.audio(
                    file_bytes
                )

            elif mime_type.startswith("video/"):

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

            save_memory(
                supabase,
                user_id,
                memory_text,
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
            user_id,
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
                    user_id,
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

    if file_bytes and wardrobe_command:

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
                    user_id,
                    item,
                )

            with st.chat_message(
                "assistant"
            ):

                st.success(
                    "Kıyafeti gardırobuna ekledim."
                )

        except Exception as e:

            with st.chat_message(
                "assistant"
            ):

                st.error(
                    f"Gardırop işlemi başarısız: {e}"
                )

        st.rerun()


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
                        f"📥 {selected_format.upper()} indir",
                        result["bytes"],
                        file_name=result["file_name"],
                        mime=result["mime_type"],
                        use_container_width=True,
                    )

                    answer = (
                        f"Tamamdır. Medyayı "
                        f"**{selected_format.upper()}** "
                        f"formatına dönüştürdüm."
                    )

                    st.markdown(
                        answer
                    )

                    save_message(
                        supabase,
                        user_id,
                        "user",
                        user_text,
                        file_name,
                        file_bytes,
                    )

                    save_message(
                        supabase,
                        user_id,
                        "assistant",
                        answer,
                    )

                    st.session_state.messages = (
                        get_messages(
                            supabase,
                            user_id,
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
    # SAVE USER
    # ========================================================

    save_message(
        supabase,
        user_id,
        "user",
        user_text,
        file_name,
        file_bytes,
    )


    # ========================================================
    # AI
    # ========================================================

    history = get_messages(
        supabase,
        user_id,
        30,
    )

    memories = get_memories(
        supabase,
        user_id,
    )

    wardrobe = get_wardrobe(
        supabase,
        user_id,
    )


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

                save_message(
                    supabase,
                    user_id,
                    "assistant",
                    answer,
                )

                st.session_state.messages = (
                    get_messages(
                        supabase,
                        user_id,
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
