import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from streamlit_oauth import OAuth2Component

# -------------------------
# OAuth設定
# -------------------------

CLIENT_ID = st.secrets["client_id"]
CLIENT_SECRET = st.secrets["client_secret"]

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

REDIRECT_URI = "https://original01meet-link-generator-humgvp4oikdy4li46kgupw.streamlit.app/component/streamlit_oauth.authorize_button"

SCOPE = "https://www.googleapis.com/auth/calendar"

oauth2 = OAuth2Component(
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZE_URL,
    TOKEN_URL
)

st.title("📅 Meetリンク作成")

# -------------------------
# ログイン
# -------------------------

if "token" not in st.session_state:

    result = oauth2.authorize_button(
        name="Googleでログイン",
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        key="google",
        extras_params={
            "access_type": "offline",
            "prompt": "consent",
        }
    )

    if result:
        st.session_state.token = result["token"]
        st.rerun()

else:
    st.success("ログイン済み")

# -------------------------
# Meet生成
# -------------------------

if "token" in st.session_state:

    token = st.session_state.token

    creds = Credentials(token["access_token"])

    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    summary = st.text_input("ミーティング名")

    date = st.date_input("日付")

    # スマホ用時間選択
    times = [
        "09:00","09:30","10:00","10:30",
        "11:00","11:30","12:00","12:30",
        "13:00","13:30","14:00","14:30",
        "15:00","15:30","16:00","16:30",
        "17:00","17:30","18:00","18:30",
        "19:00","19:30","20:00","20:30"
    ]

    start_time = st.selectbox("開始時間", times)
    end_time = st.selectbox("終了時間", times)

    if st.button("Meetリンク生成"):

        start = f"{date}T{start_time}:00+09:00"
        end = f"{date}T{end_time}:00+09:00"

        event = {
            "summary": summary,
            "start": {
                "dateTime": start,
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": end,
                "timeZone": "Asia/Tokyo",
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": "meet123456",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1,
        ).execute()

        meet_link = created_event.get("hangoutLink")

        if meet_link:

            st.success("Meetリンク作成完了")

            st.code(meet_link)

        else:

            st.error("Meetリンク取得失敗")
