import sqlite3
from pathlib import Path


DB_PATH = Path("meetings.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                meeting_type TEXT NOT NULL,
                description TEXT,
                materials_link TEXT,
                meeting_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meeting_participants (
                meeting_id INTEGER NOT NULL,
                employee_name TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                UNIQUE(name, department)
            )
            """
        )

        conn.commit()


def add_meeting(
    title,
    meeting_type,
    description,
    materials_link,
    participants,
    meeting_date,
    start_time,
    end_time,
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meetings (
                title,
                meeting_type,
                description,
                materials_link,
                meeting_date,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                meeting_type,
                description,
                materials_link,
                meeting_date,
                start_time,
                end_time,
            ),
        )

        meeting_id = cursor.lastrowid

        for participant in participants:
            conn.execute(
                """
                INSERT INTO meeting_participants (
                    meeting_id,
                    employee_name
                )
                VALUES (?, ?)
                """,
                (
                    meeting_id,
                    participant,
                ),
            )

        conn.commit()


def get_meetings():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                m.id,
                m.title,
                m.meeting_type,
                m.description,
                m.materials_link,
                m.meeting_date,
                m.start_time,
                m.end_time,
                GROUP_CONCAT(mp.employee_name, ', ') AS participants
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            GROUP BY m.id
            ORDER BY m.meeting_date, m.start_time
            """
        )
        return cursor.fetchall()


def has_meeting_conflict(participants, meeting_date, start_time, end_time):
    normalized_participants = {
        participant.strip().lower()
        for participant in participants
    }

    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                m.start_time,
                m.end_time,
                mp.employee_name
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE m.meeting_date = ?
            """,
            (meeting_date,),
        )

        existing_records = cursor.fetchall()

    for existing_start, existing_end, existing_employee in existing_records:
        has_same_participant = existing_employee.strip().lower() in normalized_participants
        has_time_overlap = start_time < existing_end and end_time > existing_start

        if has_same_participant and has_time_overlap:
            return True

    return False


def add_employee(name, department):
    normalized_name = name.strip()
    normalized_department = department.strip()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO employees (name, department)
            VALUES (?, ?)
            """,
            (normalized_name, normalized_department),
        )
        conn.commit()


def get_employees():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, name, department
            FROM employees
            ORDER BY department, name
            """
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "department": row[2],
                "label": f"{row[1]} · {row[2]}",
            }
            for row in cursor.fetchall()
        ]
    

def delete_employee(employee_id):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        )
        conn.commit()


def update_employee_department(employee_id, new_department):
    normalized_department = new_department.strip()

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE employees
            SET department = ?
            WHERE id = ?
            """,
            (normalized_department, employee_id),
        )
        conn.commit()


def get_meetings_by_date(meeting_date):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                m.id,
                m.title,
                m.meeting_type,
                m.description,
                m.materials_link,
                m.meeting_date,
                m.start_time,
                m.end_time,
                GROUP_CONCAT(mp.employee_name, ', ') AS participants
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE m.meeting_date = ?
            GROUP BY m.id
            ORDER BY m.start_time
            """,
            (meeting_date,),
        )
        return cursor.fetchall()


def get_meetings_between_dates(start_date, end_date):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                m.id,
                m.title,
                m.meeting_type,
                m.description,
                m.materials_link,
                m.meeting_date,
                m.start_time,
                m.end_time,
                GROUP_CONCAT(mp.employee_name, ', ') AS participants
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE m.meeting_date BETWEEN ? AND ?
            GROUP BY m.id
            ORDER BY m.meeting_date, m.start_time
            """,
            (start_date, end_date),
        )
        return cursor.fetchall()


def get_meetings_for_employees_by_date(employee_names, meeting_date):
    if not employee_names:
        return []

    placeholders = ", ".join(["?"] * len(employee_names))

    with get_connection() as conn:
        cursor = conn.execute(
            f"""
            SELECT DISTINCT
                m.id,
                m.title,
                m.meeting_type,
                m.description,
                m.materials_link,
                m.meeting_date,
                m.start_time,
                m.end_time,
                GROUP_CONCAT(mp_all.employee_name, ', ') AS participants
            FROM meetings m
            JOIN meeting_participants mp_filter ON m.id = mp_filter.meeting_id
            JOIN meeting_participants mp_all ON m.id = mp_all.meeting_id
            WHERE m.meeting_date = ?
              AND mp_filter.employee_name IN ({placeholders})
            GROUP BY m.id
            ORDER BY m.start_time
            """,
            [meeting_date] + employee_names,
        )
        return cursor.fetchall()