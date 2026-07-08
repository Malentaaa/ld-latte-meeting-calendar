from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from database import (
    add_employee,
    add_meeting,
    get_employees,
    get_meetings,
    has_meeting_conflict,
    init_db,
)


st.set_page_config(
    page_title="LD LATTE Meeting Calendar",
    page_icon="📅",
    layout="wide",
)

init_db()

st.title("LD LATTE Meeting Calendar")
st.write("Прототип календаря встреч компании")

st.divider()

st.subheader("Справочник сотрудников")

with st.form("employee_form"):
    col1, col2 = st.columns(2)

    with col1:
        new_employee = st.text_input("Имя сотрудника", placeholder="Например: Анна Иванова")

    with col2:
        new_department = st.text_input("Отдел", placeholder="Например: Маркетинг")

    employee_submitted = st.form_submit_button("Добавить сотрудника")

if employee_submitted:
    if not new_employee.strip():
        st.error("Введите имя сотрудника.")
    elif not new_department.strip():
        st.error("Введите отдел сотрудника.")
    else:
        try:
            add_employee(new_employee, new_department)
            st.success(f"Сотрудник добавлен: {new_employee.strip()} · {new_department.strip()}")
        except Exception:
            st.error("Такой сотрудник уже есть в этом отделе.")

employees = get_employees()

employee_labels = [employee["label"] for employee in employees]
employee_by_label = {employee["label"]: employee for employee in employees}

if employees:
    st.caption(f"В справочнике сотрудников: {len(employees)}")
else:
    st.info("Сначала добавьте сотрудников в справочник.")

st.divider()

st.subheader("Добавить встречу")

with st.form("meeting_form"):
    col1, col2 = st.columns(2)

    with col1:
        participant_1_label = st.selectbox("Участник 1", options=employee_labels, index=None)
        meeting_date = st.date_input("Дата встречи", value=date.today())

    with col2:
        participant_2_label = st.selectbox("Участник 2", options=employee_labels, index=None)
        start_time = st.time_input("Время начала", value=time(10, 0))
        end_time = st.time_input("Время окончания", value=time(11, 0))

    submitted = st.form_submit_button("Добавить встречу")

if submitted:
    meeting_start_datetime = datetime.combine(meeting_date, start_time)

    participant_1 = (
        employee_by_label[participant_1_label]["name"]
        if participant_1_label
        else None
    )
    participant_2 = (
        employee_by_label[participant_2_label]["name"]
        if participant_2_label
        else None
    )

    if not employees:
        st.error("Сначала добавьте сотрудников в справочник.")
    elif not participant_1 or not participant_2:
        st.error("Выберите обоих участников встречи.")
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