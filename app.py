import streamlit as st
import datetime
import json
import os

from googleapiclient.discovery import build
from streamlit_oauth import OAuth2Component


# -----------------------------
# Google OAuth設定
# -----------------------------

CLIENT_ID = st.secrets["client_id"]
CLIENT_SECRET = st.secrets["client_secret"]

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

REDIRECT_URI = "https://original01meet-link-generator-humgvp4oikdy4li46kgupw.streamlit.app"

SCOPES = "https://www.googleapis.com/auth/calendar"


# OAuthコンポーネント
oauth2 = OAuth2Component(
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZE_URL,
    TOKEN_URL,
)


# -----------------------------
# UI
# -----------------------------

st.title("📅 Google Meet Link Generator")

st.write("GoogleログインしてMeetリンクを生成できます")


# -----------------------------
# Googleログイン
# -----------------------------

result = oauth2.authorize_button(
    name="Googleでログイン",
    redirect_uri=REDIRECT_URI,
    scope=SCOPES,
    key="google",
    extras_params={
        "access_type": "offline",
        "prompt": "consent",
    }
)

if result:

    token = result["token"]

    # Google API接続
    service = build(
        "calendar",
        "v3",
        credentials=None,
        developerKey=None,
    )

    st.session_state.token = token


# -----------------------------
# Meet生成UI
# -----------------------------

if "token" in st.session_state:

    summary = st.text_input("ミーティング名")

    date = st.date_input("日付")

    start_time_input = st.time_input("開始時間")

    end_time_input = st.time_input("終了時間")


    if st.button("Meetを生成"):

        start_time = datetime.datetime.combine(date, start_time_input)
        end_time = datetime.datetime.combine(date, end_time_input)

        tz = datetime.timezone(datetime.timedelta(hours=9))

        start_time = start_time.replace(tzinfo=tz)
        end_time = end_time.replace(tzinfo=tz)

        service = build("calendar", "v3")

        event_body = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Asia/Tokyo",
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{start_time.timestamp():.0f}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
                conferenceDataVersion=1,
            )
            .execute()
        )

        meet_link = created.get("hangoutLink")

        if meet_link:

            st.success("Meetリンク作成完了")

            st.code(meet_link)

        else:

            st.error("Meetリンクを取得できませんでした")
