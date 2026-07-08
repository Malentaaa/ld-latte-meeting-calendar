from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from database import add_meeting, get_meetings, has_meeting_conflict, init_db


st.set_page_config(
    page_title="LD LATTE Meeting Calendar",
    page_icon="📅",
    layout="wide",
)

init_db()

st.title("LD LATTE Meeting Calendar")
st.write("Прототип календаря встреч компании")

st.divider()

st.subheader("Добавить встречу")

with st.form("meeting_form"):
    col1, col2 = st.columns(2)

    with col1:
        participant_1 = st.text_input("Участник 1", placeholder="Например: Анна")
        meeting_date = st.date_input("Дата встречи", value=date.today())

    with col2:
        participant_2 = st.text_input("Участник 2", placeholder="Например: Мария")
        start_time = st.time_input("Время начала", value=time(10, 0))
        end_time = st.time_input("Время окончания", value=time(11, 0))

    submitted = st.form_submit_button("Добавить встречу")

if submitted:
    meeting_start_datetime = datetime.combine(meeting_date, start_time)

    if not participant_1 or not participant_2:
        st.error("Заполни обоих участников встречи.")
    elif participant_1.strip().lower() == participant_2.strip().lower():
        st.error("Участники должны быть разными.")
    elif start_time >= end_time:
        st.error("Время окончания должно быть позже времени начала.")
    elif meeting_start_datetime <= datetime.now():
        st.error("Нельзя создать встречу в прошлом. Выбери дату и время позже текущего момента.")
    elif has_meeting_conflict(
        participant_1=participant_1,
        participant_2=participant_2,
        meeting_date=meeting_date.isoformat(),
        start_time=start_time.strftime("%H:%M"),
        end_time=end_time.strftime("%H:%M"),
    ):
        st.error("Слот занят: у одного из участников уже есть встреча в это время.")
    else:
        add_meeting(
            participant_1=participant_1.strip(),
            participant_2=participant_2.strip(),
            meeting_date=meeting_date.isoformat(),
            start_time=start_time.strftime("%H:%M"),
            end_time=end_time.strftime("%H:%M"),
        )
        st.success("Встреча добавлена.")

st.divider()

st.subheader("Список встреч")

meetings = get_meetings()

if meetings:
    df = pd.DataFrame(
        meetings,
        columns=[
            "ID",
            "Участник 1",
            "Участник 2",
            "Дата",
            "Начало",
            "Окончание",
        ],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Пока встреч нет.")