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