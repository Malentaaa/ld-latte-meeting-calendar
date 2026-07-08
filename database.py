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
                participant_1 TEXT NOT NULL,
                participant_2 TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
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

def add_meeting(participant_1, participant_2, meeting_date, start_time, end_time):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO meetings (
                participant_1,
                participant_2,
                meeting_date,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                participant_1,
                participant_2,
                meeting_date,
                start_time,
                end_time,
            ),
        )
        conn.commit()


def get_meetings():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                id,
                participant_1,
                participant_2,
                meeting_date,
                start_time,
                end_time
            FROM meetings
            ORDER BY meeting_date, start_time
            """
        )
        return cursor.fetchall()


def has_meeting_conflict(participant_1, participant_2, meeting_date, start_time, end_time):
    participants = {
        participant_1.strip().lower(),
        participant_2.strip().lower(),
    }

    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                participant_1,
                participant_2,
                start_time,
                end_time
            FROM meetings
            WHERE meeting_date = ?
            """,
            (meeting_date,),
        )
        meetings = cursor.fetchall()

    for existing_participant_1, existing_participant_2, existing_start, existing_end in meetings:
        existing_participants = {
            existing_participant_1.strip().lower(),
            existing_participant_2.strip().lower(),
        }

        has_same_participant = bool(participants & existing_participants)

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
                id,
                participant_1,
                participant_2,
                meeting_date,
                start_time,
                end_time
            FROM meetings
            WHERE meeting_date = ?
            ORDER BY start_time
            """,
            (meeting_date,),
        )
        return cursor.fetchall()


def get_meetings_between_dates(start_date, end_date):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                id,
                participant_1,
                participant_2,
                meeting_date,
                start_time,
                end_time
            FROM meetings
            WHERE meeting_date BETWEEN ? AND ?
            ORDER BY meeting_date, start_time
            """,
            (start_date, end_date),
        )
        return cursor.fetchall()