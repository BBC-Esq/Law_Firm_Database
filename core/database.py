import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path="law_billing.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()
        self.run_migrations()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self):
        if self.connection:
            self.connection.close()

    def create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                middle_name TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                billing_rate_cents INTEGER DEFAULT 30000 CHECK(billing_rate_cents >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS judges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS court_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judge_id INTEGER,
                name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (judge_id) REFERENCES judges(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opposing_attorneys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                firm_name TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opposing_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attorney_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attorney_id) REFERENCES opposing_attorneys(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                judge_id INTEGER,
                opposing_attorney_id INTEGER,
                case_number TEXT,
                court_type TEXT CHECK(court_type IN ('Superior Court', 'Magistrate Court', 'State Court')),
                county TEXT,
                case_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (judge_id) REFERENCES judges(id) ON DELETE SET NULL,
                FOREIGN KEY (opposing_attorney_id) REFERENCES opposing_attorneys(id) ON DELETE SET NULL,
                UNIQUE(case_number, court_type, county)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                entry_date DATE NOT NULL,
                hours REAL NOT NULL CHECK(hours > 0),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                case_id INTEGER,
                payment_date DATE NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                payment_method TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_counties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                county_name TEXT NOT NULL UNIQUE,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

    def run_migrations(self):
        cursor = self.connection.cursor()

        cursor.execute("PRAGMA table_info(court_staff)")
        columns = cursor.fetchall()

        for col in columns:
            if col[1] == 'judge_id' and col[3] == 1:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS court_staff_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        judge_id INTEGER,
                        name TEXT NOT NULL,
                        job_title TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (judge_id) REFERENCES judges(id) ON DELETE CASCADE
                    )
                """)

                cursor.execute("""
                    INSERT INTO court_staff_new (id, judge_id, name, job_title, phone, email, created_at)
                    SELECT id, judge_id, name, job_title, phone, email, created_at FROM court_staff
                """)

                cursor.execute("DROP TABLE court_staff")
                cursor.execute("ALTER TABLE court_staff_new RENAME TO court_staff")
                
                self.connection.commit()
                break

    def _execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor

    def execute(self, query, params=None):
        cursor = self._execute(query, params)
        self.connection.commit()
        return cursor

    def fetchall(self, query, params=None):
        return self._execute(query, params).fetchall()

    def fetchone(self, query, params=None):
        return self._execute(query, params).fetchone()