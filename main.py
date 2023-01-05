import sqlite3
import re
import subprocess
import time


def convert_to_seconds(string_time):
    string_time = string_time.split(":")
    seconds = (
        int(string_time[0]) * 3600 + int(string_time[1]) * 60 + int(string_time[2])
    )
    return seconds


def get_current_activity():
    focused_window = subprocess.check_output(
        "xdotool getwindowfocus getwindowname", shell=True
    )
    focused_window = focused_window.decode("utf-8").strip()
    focused_window = focused_window.replace(" – ", " - ")
    focused_window = focused_window.split(" - ")
    if len(focused_window) == 1:
        focused_window = ["", focused_window[0]]
    elif len(focused_window) == 2:
        focused_window = [focused_window[0], focused_window[1]]
    else:
        app = focused_window[-1]
        window = " ".join(focused_window[:-1])
        focused_window = [window, app]

    focused_window = [
        re.sub(r"[^a-zA-Z0-9а-яА-Я -.,/|]+", "", focused_window[0]),
        re.sub(r"[^a-zA-Z0-9а-яА-Я -]+", "", focused_window[1]),
    ]
    focused_window[0] = focused_window[0].strip()
    return focused_window


class Database:
    def __init__(self, db_file):
        self.conn = None
        self.db_file = db_file

    def create_connection(self, db_file):
        """create a database connection to a SQLite database"""
        try:
            self.conn = sqlite3.connect(db_file)
        except sqlite3.Error as error:
            raise error

    def create_table(self, create_table_sql):
        """create a table from the create_table_sql statement"""
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except sqlite3.Error as error:
            raise error

    def insert(self, insert_sql):
        """insert a row into a table"""
        try:
            c = self.conn.cursor()
            c.execute(insert_sql)
            self.conn.commit()
        except sqlite3.Error as error:
            raise error

    def select(self, select_sql):
        """select a row from a table"""
        try:
            c = self.conn.cursor()
            c.execute(select_sql)
            return c.fetchall()
        except sqlite3.Error as error:
            raise error

    def close(self):
        """close the connection to the database"""
        try:
            self.conn.close()
        except sqlite3.Error as error:
            raise error


class Activity:
    def __init__(self, activity_name, activity_time):
        self.name = activity_name
        self.time = activity_time

    def __str__(self):
        return f"{self.name} - {self.time}"

    def __repr__(self):
        return f"{self.name} - {self.time}"


class Timer:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.end_time - self.start_time))

    def __repr__(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.end_time - self.start_time))

    def __add__(self, other):
        return Timer(self.start_time, self.end_time + other.end_time - other.start_time)


def main():
    db = Database("main.db")
    db.create_connection(db.db_file)
    prev_activity = None
    activity_table = """
        CREATE TABLE IF NOT EXISTS activity (
            id integer PRIMARY KEY,
            app text NOT NULL,
            window text NOT NULL,
            time text NOT NULL,
            date_id integer NOT NULL,
            FOREIGN KEY (date_id) REFERENCES date (id)
        )
    """
    date_table = """
        CREATE TABLE IF NOT EXISTS date (
            id integer PRIMARY KEY,
            date text NOT NULL
        )
    """
    db.create_table(date_table)
    db.create_table(activity_table)
    date = time.strftime("%Y-%m-%d")
    if not db.select(f"SELECT * FROM date WHERE date='{date}'"):
        db.insert(f"INSERT INTO date (date) VALUES ('{date}')")
    date_id = db.select(f"SELECT id FROM date WHERE date='{date}'")[0][0]
    time_start = time.time()
    while True:
        time.sleep(1)
        current_activity = get_current_activity()
        if current_activity != prev_activity:
            if prev_activity:
                time_end = time.time()
                timer = Timer(time_start, time_end)
                time_start = time.time()
                app, window = prev_activity
                if db.select(
                    f"SELECT * FROM activity WHERE app='{app}' AND window='{window}' AND date_id='{date_id}'"
                ):
                    db_time = db.select(
                        f"SELECT time FROM activity WHERE app='{app}' AND window='{window}' AND date_id='{date_id}'"
                    )[0][0]
                    print(db_time)
                    db_time = Timer(0, convert_to_seconds(db_time))
                    timer = timer + db_time
                    db.insert(
                        f"UPDATE activity SET time='{timer}' WHERE app='{app}' AND window='{window}' AND date_id='{date_id}'"
                    )
                    print(timer, prev_activity)
            prev_activity = current_activity
            app, window = current_activity
            if not db.select(
                f"SELECT * FROM activity WHERE app='{app}' AND window='{window}' AND date_id='{date_id}'"
            ):
                db.insert(
                    f"INSERT INTO activity (app, window, time, date_id) VALUES ('{app}', '{window}', '00:00:00', '{date_id}')"
                )


if __name__ == "__main__":
    main()
