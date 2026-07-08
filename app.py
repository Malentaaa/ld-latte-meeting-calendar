from datetime import date, time

import streamlit as st

st.set_page_config(
    page_title="LD LATTE Meeting Calendar",
    page_icon="📅",
    layout="wide",
)

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
    if not participant_1 or not participant_2:
        st.error("Заполни обоих участников встречи.")
    elif participant_1.strip().lower() == participant_2.strip().lower():
        st.error("Участники должны быть разными.")
    elif start_time >= end_time:
        st.error("Время окончания должно быть позже времени начала.")
    else:
        st.success(
            f"Встреча добавлена: {participant_1} — {participant_2}, "
            f"{meeting_date}, {start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')}"
        )