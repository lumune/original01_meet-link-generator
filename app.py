"""
Google Meet Link Generator (Streamlit版)
"""

import streamlit as st
import json
import datetime
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# -----------------------------
# credentials.json を生成
# -----------------------------
if not os.path.exists("credentials.json"):

    creds_dict = {
        "web": {
            "client_id": st.secrets["client_id"],
            "project_id": st.secrets["project_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["client_secret"],
            "redirect_uris": ["https://original01meet-link-generator-humgvp4oikdy4li46kgupw.streamlit.app/"]
        }
    }

    with open("credentials.json", "w") as f:
        json.dump(creds_dict, f)


# -----------------------------
# Google Calendar API
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar"]

SCRIPT_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"


# -----------------------------
# OAuth処理
# -----------------------------
def get_credentials():

    creds = None

    if "credentials" in st.session_state:
        return st.session_state.credentials

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri="https://original01meet-link-generator-humgvp4oikdy4li46kgupw.streamlit.app/"
    )

    auth_url, state = flow.authorization_url(prompt="consent")

    st.write("### Google認証")
    st.link_button("Googleでログイン", auth_url)

    code = st.text_input("認証コードを貼り付けてください")

    if code:
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state.credentials = creds
        return creds

    return None


# -----------------------------
# Meetイベント作成
# -----------------------------
def create_meet_event(service, summary, start_time, end_time):

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

    return created


# -----------------------------
# UI
# -----------------------------

st.title("📅 Google Meet Link Generator")

st.write("ミーティング情報を入力して **Meetリンクを生成**できます")

# ミーティング名
summary = st.text_input("ミーティング名")

# 日付
date = st.date_input("日付")

# 時間
start_time_input = st.time_input("開始時間")
end_time_input = st.time_input("終了時間")


# Meet生成
if st.button("Meetを生成"):

    creds = get_credentials()

    if not creds:
        st.stop()

    service = build("calendar", "v3", credentials=creds)

    start_time = datetime.datetime.combine(date, start_time_input)
    end_time = datetime.datetime.combine(date, end_time_input)

    tz = datetime.timezone(datetime.timedelta(hours=9))

    start_time = start_time.replace(tzinfo=tz)
    end_time = end_time.replace(tzinfo=tz)

    event = create_meet_event(service, summary, start_time, end_time)

    meet_link = event.get("hangoutLink")

    if meet_link:
        st.success("Meetリンク作成完了")
        st.code(meet_link)
    else:
        st.error("Meetリンクを取得できませんでした")
