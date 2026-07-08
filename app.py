from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

from database import (
    add_employee,
    add_meeting,
    delete_employee,
    get_employees,
    get_meetings,
    get_meetings_between_dates,
    get_meetings_by_date,
    has_meeting_conflict,
    init_db,
    update_employee_department,
)


def meetings_to_dataframe(meetings):
    return pd.DataFrame(
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


def build_day_schedule(meetings, employees):
    time_slots = [
        f"{hour:02d}:00"
        for hour in range(8, 21)
    ]

    employee_names = [employee["name"] for employee in employees]

    schedule = pd.DataFrame(
        "",
        index=time_slots,
        columns=employee_names,
    )

    for meeting in meetings:
        _, participant_1, participant_2, _, start_time, end_time = meeting

        start_hour = int(start_time.split(":")[0])
        end_hour = int(end_time.split(":")[0])

        if end_time.split(":")[1] != "00":
            end_hour += 1

        for hour in range(start_hour, end_hour):
            slot = f"{hour:02d}:00"

            if slot in schedule.index:
                schedule.loc[slot, participant_1] = "Занят"
                schedule.loc[slot, participant_2] = "Занят"

    return schedule


def highlight_busy_cells(value):
    if value == "Занят":
        return "background-color: #F4C2C2; color: #4A4A4A; font-weight: 600;"
    return "background-color: #FFFFFF;"


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

    with st.expander("Управление сотрудниками"):
        selected_employee_label = st.selectbox(
            "Выберите сотрудника",
            options=employee_labels,
            index=None,
            key="employee_management_selectbox",
        )

        selected_employee = (
            employee_by_label[selected_employee_label]
            if selected_employee_label
            else None
        )

        if selected_employee:
            st.write(
                f"Выбран сотрудник: "
                f"{selected_employee['name']} · {selected_employee['department']}"
            )

            new_department = st.text_input(
                "Новый отдел",
                placeholder="Например: Продажи",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Изменить отдел"):
                    if not new_department.strip():
                        st.error("Введите новый отдел.")
                    else:
                        update_employee_department(
                            selected_employee["id"],
                            new_department,
                        )
                        st.success("Отдел сотрудника обновлён.")
                        st.rerun()

            with col2:
                if st.button("Удалить сотрудника"):
                    delete_employee(selected_employee["id"])
                    st.success("Сотрудник удалён из справочника.")
                    st.rerun()
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

st.subheader("Расписание встреч")

tab_day, tab_week, tab_all = st.tabs(
    [
        "День",
        "Неделя",
        "Все встречи",
    ]
)

with tab_day:
    selected_day = st.date_input(
        "Выберите день",
        value=date.today(),
        key="day_schedule_date",
    )

    day_meetings = get_meetings_by_date(selected_day.isoformat())

    st.markdown("### Список встреч на день")

    if day_meetings:
        day_df = meetings_to_dataframe(day_meetings)
        st.dataframe(day_df, use_container_width=True, hide_index=True)
    else:
        st.info("На выбранный день встреч нет.")

    st.markdown("### Занятость сотрудников по времени")

    if employees:
        schedule_df = build_day_schedule(day_meetings, employees)
        st.dataframe(
            schedule_df.style.applymap(highlight_busy_cells),
            use_container_width=True,
        )
    else:
        st.info("Сначала добавьте сотрудников в справочник.")

with tab_week:
    selected_week_start = st.date_input(
        "Выберите начало недели",
        value=date.today(),
        key="week_schedule_start",
    )

    selected_week_end = selected_week_start + timedelta(days=6)

    st.caption(
        f"Период: {selected_week_start.isoformat()} — {selected_week_end.isoformat()}"
    )

    week_meetings = get_meetings_between_dates(
        selected_week_start.isoformat(),
        selected_week_end.isoformat(),
    )

    if week_meetings:
        week_df = meetings_to_dataframe(week_meetings)
        st.dataframe(week_df, use_container_width=True, hide_index=True)
    else:
        st.info("На выбранную неделю встреч нет.")

with tab_all:
    all_meetings = get_meetings()

    if all_meetings:
        all_df = meetings_to_dataframe(all_meetings)
        st.dataframe(all_df, use_container_width=True, hide_index=True)
    else:
        st.info("Пока встреч нет.")