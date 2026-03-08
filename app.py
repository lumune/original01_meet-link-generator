import streamlit as st
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from streamlit_oauth import OAuth2Component


# -----------------------------
# OAuth設定
# -----------------------------

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

st.title("📅 Google Meet Link Generator")

st.write("GoogleログインしてMeetリンクを生成")


# -----------------------------
# ログイン処理
# -----------------------------

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

    st.success("Googleログイン済み")


# -----------------------------
# Meet生成
# -----------------------------

if "token" in st.session_state:

    token = st.session_state.token

    creds = Credentials(
        token["access_token"]
    )

    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    summary = st.text_input("ミーティング名")

    date = st.date_input("日付")

    start_time = st.time_input("開始時間")

    end_time = st.time_input("終了時間")

    if st.button("Meetリンク生成"):

        start = datetime.datetime.combine(date, start_time)
        end = datetime.datetime.combine(date, end_time)

        start = start.isoformat()
        end = end.isoformat()

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

            st.success("Meetリンク生成完了")

            st.code(meet_link)

        else:

            st.error("Meetリンクを取得できませんでした")
