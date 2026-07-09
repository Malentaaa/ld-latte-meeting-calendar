import base64
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
    get_meetings_for_employees_by_date,
)


def load_css(file_path):
    with open(file_path, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True,
        )


def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()
    

def meetings_to_dataframe(meetings):
    return pd.DataFrame(
        meetings,
        columns=[
            "ID",
            "Тема",
            "Тип",
            "Повестка",
            "Материалы",
            "Дата",
            "Начало",
            "Окончание",
            "Участники",
        ],
    )


def time_to_minutes(time_value):
    hour, minute = map(int, time_value.split(":"))
    return hour * 60 + minute


def minutes_to_time(minutes):
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def find_common_free_slots(meetings, selected_employee_names):
    workday_start = 8 * 60
    workday_end = 20 * 60
    step = 15

    busy_slots = {
        employee: set()
        for employee in selected_employee_names
    }

    for meeting in meetings:
        (
            _,
            _title,
            _meeting_type,
            _description,
            _materials_link,
            _meeting_date,
            start_time,
            end_time,
            participants_text,
        ) = meeting

        meeting_participants = [
            participant.strip()
            for participant in participants_text.split(",")
        ]

        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)

        for participant in meeting_participants:
            if participant not in busy_slots:
                continue

            for minute in range(start_minutes, end_minutes, step):
                busy_slots[participant].add(minute)

    free_points = []

    for minute in range(workday_start, workday_end, step):
        all_free = all(
            minute not in busy_slots[employee]
            for employee in selected_employee_names
        )

        if all_free:
            free_points.append(minute)

    if not free_points:
        return []

    free_intervals = []

    interval_start = free_points[0]
    previous_point = free_points[0]

    for point in free_points[1:]:
        if point == previous_point + step:
            previous_point = point
        else:
            free_intervals.append(
                f"{minutes_to_time(interval_start)}–{minutes_to_time(previous_point + step)}"
            )
            interval_start = point
            previous_point = point

    free_intervals.append(
        f"{minutes_to_time(interval_start)}–{minutes_to_time(previous_point + step)}"
    )

    return free_intervals


def build_day_schedule(meetings, selected_employee_names):
    time_slots = [f"{hour:02d}:00" for hour in range(8, 21)]

    schedule = pd.DataFrame(
        "Свободен",
        index=time_slots,
        columns=selected_employee_names,
    )

    for meeting in meetings:
        (
            _,
            title,
            meeting_type,
            _description,
            _materials_link,
            _meeting_date,
            start_time,
            end_time,
            participants_text,
        ) = meeting

        meeting_participants = [
            participant.strip()
            for participant in participants_text.split(",")
        ]

        start_hour = int(start_time.split(":")[0])
        end_hour = int(end_time.split(":")[0])

        if end_time.split(":")[1] != "00":
            end_hour += 1

        for hour in range(start_hour, end_hour):
            slot = f"{hour:02d}:00"

            if slot not in schedule.index:
                continue

            for participant in meeting_participants:
                if participant in schedule.columns:
                    schedule.loc[slot, participant] = f"{meeting_type}\n{title}"

    return schedule


def build_week_calendar(week_meetings, week_start_date):
    time_slots = [f"{hour:02d}:00" for hour in range(8, 21)]

    week_days = [
        week_start_date + timedelta(days=day)
        for day in range(7)
    ]

    columns = [
        format_weekday_ru(day)
        for day in week_days
    ]

    calendar = pd.DataFrame(
        "",
        index=time_slots,
        columns=columns,
    )

    for meeting in week_meetings:
        (
            _,
            title,
            meeting_type,
            _description,
            _materials_link,
            meeting_date,
            start_time,
            end_time,
            _participants_text,
        ) = meeting

        meeting_date_obj = datetime.fromisoformat(meeting_date).date()

        if meeting_date_obj not in week_days:
            continue

        day_column = format_weekday_ru(meeting_date_obj)

        start_hour = int(start_time.split(":")[0])
        end_hour = int(end_time.split(":")[0])

        if end_time.split(":")[1] != "00":
            end_hour += 1

        meeting_text = (
            f"{start_time}–{end_time}\n"
            f"{meeting_type}\n"
            f"{title}"
        )

        for hour in range(start_hour, end_hour):
            slot = f"{hour:02d}:00"

            if slot not in calendar.index:
                continue

            if calendar.loc[slot, day_column]:
                calendar.loc[slot, day_column] += f"\n\n{meeting_text}"
            else:
                calendar.loc[slot, day_column] = meeting_text

    return calendar


def highlight_busy_cells(value):
    if value == "Свободен":
        return "background-color: #fffafb; color: #8d747b;"

    if "Инцидент / проблема" in value:
        return "background-color: #f2b8b5; color: #4a1f1f; font-weight: 700; white-space: pre-wrap;"

    if "Внешняя встреча" in value:
        return "background-color: #d8e3ea; color: #203947; font-weight: 700; white-space: pre-wrap;"

    if "Производство / швейный цех" in value:
        return "background-color: #f6c89f; color: #4a2a11; font-weight: 700; white-space: pre-wrap;"

    if "Контроль качества" in value:
        return "background-color: #e7b7c8; color: #4a2030; font-weight: 700; white-space: pre-wrap;"

    if "Дизайн / коллекция" in value:
        return "background-color: #ddd3ef; color: #34294a; font-weight: 700; white-space: pre-wrap;"

    if "Конструирование / лекала" in value:
        return "background-color: #cfc2e8; color: #30204a; font-weight: 700; white-space: pre-wrap;"

    if "Закупка тканей и фурнитуры" in value:
        return "background-color: #cfe4ef; color: #203947; font-weight: 700; white-space: pre-wrap;"

    if "Фото / контент" in value:
        return "background-color: #eadcf5; color: #3f2d4a; font-weight: 700; white-space: pre-wrap;"

    if "Карточки товара" in value:
        return "background-color: #e8cfd5; color: #3f3434; font-weight: 700; white-space: pre-wrap;"

    if "Маркетинг / реклама" in value:
        return "background-color: #f4e3a1; color: #4a3b11; font-weight: 700; white-space: pre-wrap;"

    if "Продажи / маркетплейсы" in value:
        return "background-color: #cfe8d6; color: #1f3f2a; font-weight: 700; white-space: pre-wrap;"

    if "Аналитика продаж" in value:
        return "background-color: #cfe8e3; color: #1f3f3a; font-weight: 700; white-space: pre-wrap;"

    if "Планирование" in value:
        return "background-color: #d8d8f0; color: #25254a; font-weight: 700; white-space: pre-wrap;"

    if "Логистика / отгрузки" in value:
        return "background-color: #c9dff2; color: #1f344a; font-weight: 700; white-space: pre-wrap;"

    if "Финансы / закупки" in value:
        return "background-color: #eadfd6; color: #3f3434; font-weight: 700; white-space: pre-wrap;"

    return "background-color: #eadfd6; color: #3f3434; font-weight: 700; white-space: pre-wrap;"


def highlight_calendar_cells(value):
    if not value:
        return "background-color: #fffafb; color: #8d747b;"

    if "Инцидент / проблема" in value:
        return "background-color: #f2b8b5; color: #4a1f1f; font-weight: 700; white-space: pre-wrap;"

    if "Внешняя встреча" in value:
        return "background-color: #d8e3ea; color: #203947; font-weight: 700; white-space: pre-wrap;"

    if "Производство / швейный цех" in value:
        return "background-color: #f6c89f; color: #4a2a11; font-weight: 700; white-space: pre-wrap;"

    if "Контроль качества" in value:
        return "background-color: #e7b7c8; color: #4a2030; font-weight: 700; white-space: pre-wrap;"

    if "Дизайн / коллекция" in value:
        return "background-color: #ddd3ef; color: #34294a; font-weight: 700; white-space: pre-wrap;"

    if "Конструирование / лекала" in value:
        return "background-color: #cfc2e8; color: #30204a; font-weight: 700; white-space: pre-wrap;"

    if "Закупка тканей и фурнитуры" in value:
        return "background-color: #cfe4ef; color: #203947; font-weight: 700; white-space: pre-wrap;"

    if "Фото / контент" in value:
        return "background-color: #eadcf5; color: #3f2d4a; font-weight: 700; white-space: pre-wrap;"

    if "Карточки товара" in value:
        return "background-color: #e8cfd5; color: #3f3434; font-weight: 700; white-space: pre-wrap;"

    if "Маркетинг / реклама" in value:
        return "background-color: #f4e3a1; color: #4a3b11; font-weight: 700; white-space: pre-wrap;"

    if "Продажи / маркетплейсы" in value:
        return "background-color: #cfe8d6; color: #1f3f2a; font-weight: 700; white-space: pre-wrap;"

    if "Аналитика продаж" in value:
        return "background-color: #cfe8e3; color: #1f3f3a; font-weight: 700; white-space: pre-wrap;"

    if "Планирование" in value:
        return "background-color: #d8d8f0; color: #25254a; font-weight: 700; white-space: pre-wrap;"

    if "Логистика / отгрузки" in value:
        return "background-color: #c9dff2; color: #1f344a; font-weight: 700; white-space: pre-wrap;"

    if "Финансы / закупки" in value:
        return "background-color: #eadfd6; color: #3f3434; font-weight: 700; white-space: pre-wrap;"

    return "background-color: #eadfd6; color: #3f3434; font-weight: 700; white-space: pre-wrap;"


MEETING_TYPES = [
    "Общее обсуждение",
    "Внешняя встреча",
    "Дизайн / коллекция",
    "Конструирование / лекала",
    "Закупка тканей и фурнитуры",
    "Производство / швейный цех",
    "Контроль качества",
    "Фото / контент",
    "Карточки товара",
    "Маркетинг / реклама",
    "Продажи / маркетплейсы",
    "Аналитика продаж",
    "Планирование",
    "Логистика / отгрузки",
    "Финансы / закупки",
    "Инцидент / проблема",
]


def format_weekday_ru(day):
    weekdays = {
        0: "Пн",
        1: "Вт",
        2: "Ср",
        3: "Чт",
        4: "Пт",
        5: "Сб",
        6: "Вс",
    }

    return f"{weekdays[day.weekday()]} {day.strftime('%d.%m')}"


st.set_page_config(
    page_title="Календарь внутренних встреч",
    page_icon="📅",
    layout="wide",
)

load_css("styles.css")

init_db()

logo_base64 = image_to_base64("assets/logo.png")

st.markdown(
    f"""
    <div class="app-header-centered">
        <img src="data:image/png;base64,{logo_base64}" class="app-logo">
        <div class="app-title">Календарь внутренних встреч</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

st.subheader("Справочник сотрудников")

with st.form("employee_form"):
    col1, col2 = st.columns(2)

    with col1:
        new_employee = st.text_input(
            "Имя сотрудника",
            placeholder="Например: Анна Иванова",
        )

    with col2:
        new_department = st.text_input(
            "Отдел",
            placeholder="Например: Производство",
        )

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
        meeting_title = st.text_input(
            "Тема встречи",
            placeholder="Например: Встреча с поставщиком тканей",
        )

        meeting_type = st.selectbox(
            "Тип встречи",
            options=MEETING_TYPES,
        )

        selected_participant_labels = st.multiselect(
            "Участники встречи",
            options=employee_labels,
            placeholder="Выберите одного или нескольких сотрудников",
        )

        meeting_date = st.date_input(
            "Дата встречи",
            value=date.today(),
        )

    with col2:
        start_time = st.time_input(
            "Время начала",
            value=time(10, 0),
            step=900,
        )

        end_time = st.time_input(
            "Время окончания",
            value=time(11, 0),
            step=900,
        )

        meeting_description = st.text_area(
            "Повестка / описание",
            placeholder=(
                "Например: обсудить сроки пошива партии, проблемные размеры, "
                "статус лекал, остатки ткани или подготовку карточек товара"
            ),
            height=100,
        )

        materials_link = st.text_input(
            "Ссылка на материалы",
            placeholder="Ссылка на таблицу, задачу, фото дефекта, карточку товара или макет коллекции",
        )

    submitted = st.form_submit_button("Добавить встречу")

if submitted:
    meeting_start_datetime = datetime.combine(meeting_date, start_time)

    selected_participants = [
        employee_by_label[label]["name"]
        for label in selected_participant_labels
    ]

    if not employees:
        st.error("Сначала добавьте сотрудников в справочник.")
    elif not meeting_title.strip():
        st.error("Введите тему встречи.")
    elif len(selected_participants) < 1:
        st.error("Выберите минимум одного участника встречи.")
    elif start_time >= end_time:
        st.error("Время окончания должно быть позже времени начала.")
    elif meeting_start_datetime <= datetime.now():
        st.error("Нельзя создать встречу в прошлом. Выбери дату и время позже текущего момента.")
    elif has_meeting_conflict(
        participants=selected_participants,
        meeting_date=meeting_date.isoformat(),
        start_time=start_time.strftime("%H:%M"),
        end_time=end_time.strftime("%H:%M"),
    ):
        st.error("Слот занят: у одного из участников уже есть встреча в это время.")
    else:
        add_meeting(
            title=meeting_title.strip(),
            meeting_type=meeting_type,
            description=meeting_description.strip(),
            materials_link=materials_link.strip(),
            participants=selected_participants,
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
    selected_schedule_labels = st.multiselect(
        "Чьё расписание показать",
        options=employee_labels,
        placeholder="Выберите одного или нескольких сотрудников",
        key="day_schedule_employees",
    )

    selected_schedule_employees = [
        employee_by_label[label]["name"]
        for label in selected_schedule_labels
    ]

    selected_day = st.date_input(
        "Выберите день",
        value=date.today(),
        key="day_schedule_date",
    )

    if selected_schedule_employees:
        day_meetings = get_meetings_for_employees_by_date(
            selected_schedule_employees,
            selected_day.isoformat(),
        )
    else:
        day_meetings = get_meetings_by_date(selected_day.isoformat())
    
    if selected_schedule_employees:
        if st.button("Найти свободные слоты"):
            free_slots = find_common_free_slots(
                day_meetings,
                selected_schedule_employees,
            )

            if free_slots:
                st.success("Общие свободные слоты:")
                for slot in free_slots:
                    st.write(f"• {slot}")
            else:
                st.warning("На выбранную дату общих свободных слотов не найдено.")

    st.markdown("### Список встреч на день")

    if day_meetings:
        day_df = meetings_to_dataframe(day_meetings)
        st.dataframe(day_df, use_container_width=True, hide_index=True)
    else:
        st.info("На выбранный день встреч нет.")

    st.markdown("### Занятость выбранных сотрудников")

    if not selected_schedule_employees:
        st.info("Выберите сотрудников, чтобы посмотреть их занятые и свободные слоты.")
    else:
        schedule_df = build_day_schedule(day_meetings, selected_schedule_employees)
        st.dataframe(
            schedule_df.style.applymap(highlight_busy_cells),
            use_container_width=True,
            height=500,
        )

with tab_week:
    selected_week_start = st.date_input(
        "Выберите начало недели",
        value=date.today(),
        key="week_schedule_start",
    )

    selected_week_end = selected_week_start + timedelta(days=6)

    selected_week_labels = st.multiselect(
        "Чьё недельное расписание показать",
        options=employee_labels,
        placeholder="Выберите одного или нескольких сотрудников",
        key="week_schedule_employees",
    )

    selected_week_employees = [
        employee_by_label[label]["name"]
        for label in selected_week_labels
    ]

    st.caption(
        f"Период: {selected_week_start.isoformat()} — {selected_week_end.isoformat()}"
    )

    if not selected_week_employees:
        st.info("Выберите сотрудника, чтобы посмотреть его недельное расписание.")
    else:
        week_meetings = []

        for day_offset in range(7):
            current_day = selected_week_start + timedelta(days=day_offset)
            day_records = get_meetings_for_employees_by_date(
                selected_week_employees,
                current_day.isoformat(),
            )
            week_meetings.extend(day_records)

        st.markdown("### Календарная сетка недели")

        if week_meetings:
            week_calendar_df = build_week_calendar(
                week_meetings,
                selected_week_start,
            )

            st.dataframe(
                week_calendar_df.style.applymap(highlight_calendar_cells),
                use_container_width=True,
                height=620,
            )
        else:
            st.info("У выбранных сотрудников нет встреч на эту неделю.")

        st.markdown("### Список встреч на неделю")

        if week_meetings:
            week_df = meetings_to_dataframe(week_meetings)
            st.dataframe(week_df, use_container_width=True, hide_index=True)
        else:
            st.info("Список встреч пуст.")

with tab_all:
    all_meetings = get_meetings()

    if all_meetings:
        all_df = meetings_to_dataframe(all_meetings)
        st.dataframe(all_df, use_container_width=True, hide_index=True)
    else:
        st.info("Пока встреч нет.")