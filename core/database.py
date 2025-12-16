import sqlite3


class Database:
    def __init__(self, db_path="law_billing.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()

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
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                middle_name TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                billing_rate_cents INTEGER DEFAULT 30000 CHECK(billing_rate_cents >= 0),
                firm_name TEXT,
                job_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT,
                case_name TEXT,
                is_litigation INTEGER DEFAULT 0,
                court_type TEXT,
                county TEXT,
                status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'Closed')),
                billing_rate_cents INTEGER DEFAULT 30000 CHECK(billing_rate_cents >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN (
                    'client',
                    'opposing_party',
                    'opposing_counsel',
                    'opposing_staff',
                    'judge',
                    'judge_staff',
                    'court_staff',
                    'guardian_ad_litem',
                    'co_counsel'
                )),
                party_designation TEXT CHECK(party_designation IN (
                    'plaintiff',
                    'defendant',
                    NULL
                )),
                represents_person_id INTEGER,
                is_pro_se BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
                FOREIGN KEY (represents_person_id) REFERENCES people(id) ON DELETE SET NULL,
                UNIQUE(case_id, person_id, role)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                entry_date DATE NOT NULL,
                hours REAL CHECK(hours >= 0 OR hours IS NULL),
                is_expense INTEGER DEFAULT 0,
                amount_cents INTEGER CHECK(amount_cents >= 0 OR amount_cents IS NULL),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                case_id INTEGER,
                payment_date DATE NOT NULL,
                amount_cents INTEGER NOT NULL DEFAULT 0 CHECK(amount_cents >= 0),
                expense_amount_cents INTEGER NOT NULL DEFAULT 0 CHECK(expense_amount_cents >= 0),
                payment_method TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_people_case ON case_people(case_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_people_person ON case_people(person_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_billing_case ON billing_entries(case_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_person ON payments(person_id)
        """)

        self.connection.commit()

    def execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        self.connection.commit()
        return cursor

    def fetchall(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()

    def fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchone()