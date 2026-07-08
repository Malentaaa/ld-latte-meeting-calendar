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