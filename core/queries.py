from core.database import Database
from core.models import Client, Judge, CourtStaff, Case, BillingEntry, OpposingAttorney, OpposingStaff, Payment
from typing import List, Optional, TypeVar, Generic, Type
from dataclasses import fields
from datetime import date

T = TypeVar('T')

class BaseQueries(Generic[T]):
    table_name: str = ""
    model_class: Type[T] = None
    order_by: str = "id"

    def __init__(self, db: Database):
        self.db = db

    def _get_field_names(self) -> List[str]:
        excluded = {'id', 'created_at'}
        return [f.name for f in fields(self.model_class) if f.name not in excluded]

    def _get_field_values(self, entity: T) -> tuple:
        field_names = self._get_field_names()
        return tuple(getattr(entity, f) for f in field_names)

    def create(self, entity: T) -> int:
        field_names = self._get_field_names()
        placeholders = ', '.join(['?'] * len(field_names))
        columns = ', '.join(field_names)
        values = self._get_field_values(entity)
        cursor = self.db.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            values
        )
        return cursor.lastrowid

    def update(self, entity: T):
        field_names = self._get_field_names()
        set_clause = ', '.join(f"{f}=?" for f in field_names)
        values = self._get_field_values(entity) + (entity.id,)
        self.db.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id=?",
            values
        )

    def delete(self, entity_id: int):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE id=?", (entity_id,))

    def get_all(self) -> List[T]:
        rows = self.db.fetchall(f"SELECT * FROM {self.table_name} ORDER BY {self.order_by}")
        return [self.model_class(**dict(row)) for row in rows]

    def get_by_id(self, entity_id: int) -> Optional[T]:
        row = self.db.fetchone(f"SELECT * FROM {self.table_name} WHERE id=?", (entity_id,))
        return self.model_class(**dict(row)) if row else None


class ClientQueries(BaseQueries[Client]):
    table_name = "clients"
    model_class = Client
    order_by = "last_name, first_name"

    def search(self, query: str) -> List[Client]:
        rows = self.db.fetchall(
            """SELECT * FROM clients 
               WHERE first_name LIKE ? OR last_name LIKE ? OR middle_name LIKE ?
               ORDER BY last_name, first_name LIMIT 20""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        return [Client(**dict(row)) for row in rows]


class JudgeQueries(BaseQueries[Judge]):
    table_name = "judges"
    model_class = Judge
    order_by = "name"

    def get_staff_count(self, judge_id: int) -> int:
        row = self.db.fetchone(
            "SELECT COUNT(*) as count FROM court_staff WHERE judge_id = ?",
            (judge_id,)
        )
        return row["count"] if row else 0


class CourtStaffQueries(BaseQueries[CourtStaff]):
    table_name = "court_staff"
    model_class = CourtStaff
    order_by = "name"

    def get_by_judge(self, judge_id: int) -> List[CourtStaff]:
        rows = self.db.fetchall(
            "SELECT * FROM court_staff WHERE judge_id=? ORDER BY job_title, name",
            (judge_id,)
        )
        return [CourtStaff(**dict(row)) for row in rows]

    def get_general_staff(self) -> List[CourtStaff]:
        rows = self.db.fetchall(
            "SELECT * FROM court_staff WHERE judge_id IS NULL ORDER BY job_title, name"
        )
        return [CourtStaff(**dict(row)) for row in rows]

    def get_by_parent(self, parent_id: int) -> List[CourtStaff]:
        return self.get_by_judge(parent_id)


class OpposingAttorneyQueries(BaseQueries[OpposingAttorney]):
    table_name = "opposing_attorneys"
    model_class = OpposingAttorney
    order_by = "name"


class OpposingStaffQueries(BaseQueries[OpposingStaff]):
    table_name = "opposing_staff"
    model_class = OpposingStaff
    order_by = "name"

    def get_by_attorney(self, attorney_id: int) -> List[OpposingStaff]:
        rows = self.db.fetchall(
            "SELECT * FROM opposing_staff WHERE attorney_id=? ORDER BY job_title, name",
            (attorney_id,)
        )
        return [OpposingStaff(**dict(row)) for row in rows]

    def get_by_parent(self, parent_id: int) -> List[OpposingStaff]:
        return self.get_by_attorney(parent_id)


class CaseQueries(BaseQueries[Case]):
    table_name = "cases"
    model_class = Case
    order_by = "created_at DESC"

    def get_all(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT c.*, 
                   cl.first_name || ' ' || cl.last_name as client_name,
                   j.name as judge_name, 
                   oa.name as opposing_attorney_name
            FROM cases c
            LEFT JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN judges j ON c.judge_id = j.id
            LEFT JOIN opposing_attorneys oa ON c.opposing_attorney_id = oa.id
            ORDER BY c.created_at DESC
        """)
        return [dict(row) for row in rows]

    def get_by_client(self, client_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT c.*, 
                   cl.first_name || ' ' || cl.last_name as client_name,
                   j.name as judge_name, 
                   oa.name as opposing_attorney_name
            FROM cases c
            LEFT JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN judges j ON c.judge_id = j.id
            LEFT JOIN opposing_attorneys oa ON c.opposing_attorney_id = oa.id
            WHERE c.client_id = ?
            ORDER BY c.created_at DESC
        """, (client_id,))
        return [dict(row) for row in rows]

    def get_by_parent(self, parent_id: int) -> List[dict]:
        return self.get_by_client(parent_id)

    def search_matters(self, query: str) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT c.id, c.case_number, c.case_name, c.court_type, c.county,
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   cl.billing_rate_cents
            FROM cases c
            JOIN clients cl ON c.client_id = cl.id
            WHERE cl.first_name LIKE ? OR cl.last_name LIKE ? OR c.case_number LIKE ? OR c.case_name LIKE ?
            ORDER BY cl.last_name, cl.first_name
            LIMIT 20
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        return [dict(row) for row in rows]

    def get_matter_by_id(self, case_id: int) -> Optional[dict]:
        row = self.db.fetchone("""
            SELECT c.id, c.case_number, c.case_name, c.court_type, c.county,
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   cl.billing_rate_cents
            FROM cases c
            JOIN clients cl ON c.client_id = cl.id
            WHERE c.id = ?
        """, (case_id,))
        return dict(row) if row else None


class BillingQueries(BaseQueries[BillingEntry]):
    table_name = "billing_entries"
    model_class = BillingEntry
    order_by = "entry_date DESC"

    def get_by_case(self, case_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT be.*, c.case_number, c.case_name,
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   cl.billing_rate_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE be.case_id = ?
            ORDER BY be.entry_date DESC
        """, (case_id,))
        return [dict(row) for row in rows]

    def get_all_with_details(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT be.*, c.case_number, c.case_name, 
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   cl.billing_rate_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            ORDER BY be.entry_date DESC
        """)
        return [dict(row) for row in rows]

    def get_client_totals(self, client_id: int) -> dict:
        row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(be.hours), 0) as total_hours,
                COALESCE(SUM(be.hours * cl.billing_rate_cents), 0) as total_amount_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE cl.id = ?
        """, (client_id,))
        return dict(row) if row else {"total_hours": 0, "total_amount_cents": 0}

    def get_case_totals(self, case_id: int) -> dict:
        row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(be.hours), 0) as total_hours,
                COALESCE(SUM(be.hours * cl.billing_rate_cents), 0) as total_amount_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE c.id = ?
        """, (case_id,))
        return dict(row) if row else {"total_hours": 0, "total_amount_cents": 0}


class PaymentQueries(BaseQueries[Payment]):
    table_name = "payments"
    model_class = Payment
    order_by = "payment_date DESC"

    def get_all_with_details(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT p.*, 
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   c.case_number
            FROM payments p
            JOIN clients cl ON p.client_id = cl.id
            LEFT JOIN cases c ON p.case_id = c.id
            ORDER BY p.payment_date DESC
        """)
        return [dict(row) for row in rows]

    def get_by_client(self, client_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT p.*, 
                   cl.first_name || ' ' || cl.last_name as client_name, 
                   c.case_number
            FROM payments p
            JOIN clients cl ON p.client_id = cl.id
            LEFT JOIN cases c ON p.case_id = c.id
            WHERE p.client_id = ?
            ORDER BY p.payment_date DESC
        """, (client_id,))
        return [dict(row) for row in rows]

    def get_by_parent(self, parent_id: int) -> List[dict]:
        return self.get_by_client(parent_id)
    
    def get_client_total_cents(self, client_id: int) -> int:
        row = self.db.fetchone(
            "SELECT COALESCE(SUM(amount_cents), 0) as total FROM payments WHERE client_id = ?",
            (client_id,)
        )
        return row["total"] if row else 0


class RecentCountyQueries:
    def __init__(self, db: Database):
        self.db = db

    def add_recent(self, county_name: str):
        self.db.execute("""
            INSERT INTO recent_counties (county_name, last_used) 
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(county_name) DO UPDATE SET last_used = CURRENT_TIMESTAMP
        """, (county_name,))

    def get_recent(self, limit: int = 5) -> List[str]:
        rows = self.db.fetchall(
            "SELECT county_name FROM recent_counties ORDER BY last_used DESC LIMIT ?",
            (limit,)
        )
        return [row["county_name"] for row in rows]