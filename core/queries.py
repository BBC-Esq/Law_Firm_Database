from core.base_queries import BaseQueries
from core.models import Person, Case, CasePerson, BillingEntry, Payment
from typing import List
import calendar


PERSON_COLUMNS = """
    id, first_name, last_name, middle_name, phone, email, address,
    billing_rate_cents, firm_name, job_title, created_at
"""

CASE_COLUMNS = "id, case_number, case_name, is_litigation, court_type, county, status, billing_rate_cents, created_at"

CASE_PERSON_COLUMNS = "id, case_id, person_id, role, party_designation, represents_person_id, is_pro_se, created_at"

BILLING_COLUMNS = "id, case_id, entry_date, hours, is_expense, amount_cents, description, sort_order, created_at"

PAYMENT_COLUMNS = "id, person_id, case_id, payment_date, amount_cents, expense_amount_cents, payment_method, reference_number, notes, created_at"


class PersonQueries(BaseQueries[Person]):
    table_name = "people"
    model_class = Person
    columns = PERSON_COLUMNS
    order_by = "last_name, first_name"

    def create(self, person: Person) -> int:
        cursor = self.db.execute("""
            INSERT INTO people (
                first_name, last_name, middle_name,
                phone, email, address, billing_rate_cents, firm_name, job_title
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            person.first_name, person.last_name, person.middle_name,
            person.phone, person.email, person.address,
            person.billing_rate_cents, person.firm_name, person.job_title
        ))
        return cursor.lastrowid

    def update(self, person: Person):
        self.db.execute("""
            UPDATE people SET
                first_name=?, last_name=?, middle_name=?,
                phone=?, email=?, address=?, billing_rate_cents=?, firm_name=?, job_title=?
            WHERE id=?
        """, (
            person.first_name, person.last_name, person.middle_name,
            person.phone, person.email, person.address,
            person.billing_rate_cents, person.firm_name, person.job_title,
            person.id
        ))

    def find_duplicates(self, first_name: str, last_name: str) -> List[Person]:
        rows = self.db.fetchall(f"""
            SELECT {PERSON_COLUMNS} FROM people 
            WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)
            ORDER BY last_name, first_name
        """, (first_name, last_name))
        return [Person(**dict(row)) for row in rows]

    def get_all_clients(self) -> List[Person]:
        rows = self.db.fetchall(f"""
            SELECT DISTINCT p.id, p.first_name, p.last_name, p.middle_name, p.phone, p.email, 
                   p.address, p.billing_rate_cents, p.firm_name, p.job_title, p.created_at
            FROM people p
            JOIN case_people cp ON p.id = cp.person_id
            WHERE cp.role = 'client'
            ORDER BY p.last_name, p.first_name
        """)
        return [Person(**dict(row)) for row in rows]

    def get_phone_contacts(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT 
                p.phone,
                p.first_name,
                p.last_name,
                GROUP_CONCAT(DISTINCT cp.role) as roles
            FROM people p
            LEFT JOIN case_people cp ON p.id = cp.person_id
            WHERE p.phone IS NOT NULL AND p.phone != ''
            GROUP BY p.id
        """)
        return [dict(row) for row in rows]


class CaseQueries(BaseQueries[Case]):
    table_name = "cases"
    model_class = Case
    columns = CASE_COLUMNS
    order_by = "created_at DESC"

    def _build_case_query(self, select_clause: str, include_closed: bool, order_by: str) -> str:
        query = f"""
            SELECT {select_clause}
            FROM cases c
            LEFT JOIN case_people cp ON c.id = cp.case_id AND cp.role = 'client'
            LEFT JOIN people p ON cp.person_id = p.id
        """
        if not include_closed:
            query += " WHERE c.status = 'Open'"
        query += f" ORDER BY {order_by}"
        return query

    def generate_matter_number(self, last_name: str) -> str:
        clean_name = "".join(c for c in last_name if c.isalnum())
        if not clean_name:
            clean_name = "Matter"

        rows = self.db.fetchall("""
            SELECT case_name FROM cases 
            WHERE case_name LIKE ?
            ORDER BY case_name
        """, (f"{clean_name}-%",))

        existing_numbers = []
        for row in rows:
            case_name = row["case_name"]
            if "-" in case_name:
                try:
                    num_part = case_name.split("-")[-1]
                    existing_numbers.append(int(num_part))
                except ValueError:
                    pass

        next_number = 1
        if existing_numbers:
            next_number = max(existing_numbers) + 1

        return f"{clean_name}-{next_number:03d}"

    def create(self, case: Case) -> int:
        cursor = self.db.execute("""
            INSERT INTO cases (case_number, case_name, is_litigation, court_type, county, status, billing_rate_cents)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (case.case_number, case.case_name, case.is_litigation, case.court_type, case.county, case.status, case.billing_rate_cents))
        return cursor.lastrowid

    def create_with_client(self, case: Case, client_id: int, party_designation: str = None) -> int:
        case_id = self.create(case)
        self.db.execute("""
            INSERT INTO case_people (case_id, person_id, role, party_designation)
            VALUES (?, ?, 'client', ?)
        """, (case_id, client_id, party_designation))
        return case_id

    def update(self, case: Case):
        self.db.execute("""
            UPDATE cases SET case_number=?, case_name=?, is_litigation=?, court_type=?, county=?, status=?, billing_rate_cents=?
            WHERE id=?
        """, (case.case_number, case.case_name, case.is_litigation, case.court_type, case.county, case.status, case.billing_rate_cents, case.id))

    def get_all_with_client(self, include_closed: bool = True) -> List[dict]:
        select_clause = """
            c.id, c.case_number, c.case_name, c.is_litigation, c.court_type, c.county, 
            c.status, c.billing_rate_cents, c.created_at,
            p.first_name || ' ' || p.last_name as client_name,
            p.id as client_id
        """
        query = self._build_case_query(select_clause, include_closed, "c.created_at DESC")
        rows = self.db.fetchall(query)
        return [dict(row) for row in rows]

    def get_matters_for_invoice(self, include_closed: bool = True) -> List[dict]:
        select_clause = """
            c.id, c.case_name, c.case_number, c.billing_rate_cents,
            c.is_litigation, c.court_type, c.county, c.status,
            p.first_name, p.last_name, p.address, p.email,
            p.id as client_id,
            p.first_name || ' ' || p.last_name as client_name
        """
        query = self._build_case_query(select_clause, include_closed, "c.case_name")
        rows = self.db.fetchall(query)
        return [dict(row) for row in rows]

    def get_by_client(self, client_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT c.id, c.case_number, c.case_name, c.is_litigation, c.court_type, c.county,
                   c.status, c.billing_rate_cents, c.created_at,
                   p.first_name || ' ' || p.last_name as client_name
            FROM cases c
            JOIN case_people cp ON c.id = cp.case_id AND cp.role = 'client'
            JOIN people p ON cp.person_id = p.id
            WHERE p.id = ?
            ORDER BY c.created_at DESC
        """, (client_id,))
        return [dict(row) for row in rows]

    def get_cases_for_person(self, person_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT c.id, c.case_number, c.case_name, c.is_litigation, c.court_type, c.county,
                   c.status, c.billing_rate_cents, c.created_at,
                   GROUP_CONCAT(DISTINCT cp.role) as roles,
                   client.first_name || ' ' || client.last_name as client_name
            FROM cases c
            JOIN case_people cp ON c.id = cp.case_id
            LEFT JOIN case_people client_cp ON c.id = client_cp.case_id AND client_cp.role = 'client'
            LEFT JOIN people client ON client_cp.person_id = client.id
            WHERE cp.person_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (person_id,))
        return [dict(row) for row in rows]


class CasePersonQueries(BaseQueries[CasePerson]):
    table_name = "case_people"
    model_class = CasePerson
    columns = CASE_PERSON_COLUMNS
    order_by = "id"

    def add_person_to_case(self, case_person: CasePerson) -> int:
        cursor = self.db.execute("""
            INSERT INTO case_people (case_id, person_id, role, party_designation, represents_person_id, is_pro_se)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            case_person.case_id, case_person.person_id, case_person.role,
            case_person.party_designation, case_person.represents_person_id, case_person.is_pro_se
        ))
        return cursor.lastrowid

    def remove_person_from_case(self, case_person_id: int):
        self.delete(case_person_id)

    def get_people_for_case(self, case_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT cp.id, cp.case_id, cp.person_id, cp.role, cp.party_designation, 
                   cp.represents_person_id, cp.is_pro_se, cp.created_at,
                   p.first_name, p.last_name, p.middle_name,
                   p.phone, p.email, p.address, p.firm_name, p.job_title,
                   rep.first_name || ' ' || rep.last_name as represents_name
            FROM case_people cp
            JOIN people p ON cp.person_id = p.id
            LEFT JOIN people rep ON cp.represents_person_id = rep.id
            WHERE cp.case_id = ?
            ORDER BY 
                CASE cp.role
                    WHEN 'client' THEN 1
                    WHEN 'co_counsel' THEN 2
                    WHEN 'opposing_party' THEN 3
                    WHEN 'opposing_counsel' THEN 4
                    WHEN 'opposing_staff' THEN 5
                    WHEN 'judge' THEN 6
                    WHEN 'judge_staff' THEN 7
                    WHEN 'court_staff' THEN 8
                    WHEN 'guardian_ad_litem' THEN 9
                    ELSE 10
                END,
                p.last_name, p.first_name
        """, (case_id,))
        return [dict(row) for row in rows]

    def update_client(self, case_id: int, new_client_id: int, party_designation: str = None):
        self.db.execute(
            "DELETE FROM case_people WHERE case_id = ? AND role = 'client'",
            (case_id,)
        )
        self.db.execute("""
            INSERT INTO case_people (case_id, person_id, role, party_designation)
            VALUES (?, ?, 'client', ?)
        """, (case_id, new_client_id, party_designation))

    def update_client_designation(self, case_id: int, party_designation: str):
        self.db.execute("""
            UPDATE case_people 
            SET party_designation = ?
            WHERE case_id = ? AND role = 'client'
        """, (party_designation, case_id))

    def get_by_role(self, case_id: int, role: str) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT cp.id, cp.case_id, cp.person_id, cp.role, cp.party_designation,
                   cp.represents_person_id, cp.is_pro_se, cp.created_at,
                   p.first_name, p.last_name, p.middle_name,
                   p.phone, p.email, p.firm_name, p.job_title,
                   rep.first_name || ' ' || rep.last_name as represents_name
            FROM case_people cp
            JOIN people p ON cp.person_id = p.id
            LEFT JOIN people rep ON cp.represents_person_id = rep.id
            WHERE cp.case_id = ? AND cp.role = ?
            ORDER BY p.last_name, p.first_name
        """, (case_id, role))
        return [dict(row) for row in rows]

    def get_case_summary(self, case_id: int) -> dict:
        all_people = self.get_people_for_case(case_id)

        summary = {
            'client': None,
            'co_counsel': [],
            'judge': None,
            'judge_staff': [],
            'court_staff': [],
            'opposing_parties': [],
            'guardian_ad_litem': None
        }

        opposing_parties = {}
        attorney_to_party = {}

        for person in all_people:
            role = person['role']

            if role == 'client':
                summary['client'] = person
            elif role == 'co_counsel':
                summary['co_counsel'].append(person)
            elif role == 'judge':
                summary['judge'] = person
            elif role == 'judge_staff':
                summary['judge_staff'].append(person)
            elif role == 'court_staff':
                summary['court_staff'].append(person)
            elif role == 'opposing_party':
                opposing_parties[person['person_id']] = {
                    'party': person,
                    'attorneys': [],
                    'staff': []
                }
            elif role == 'opposing_counsel':
                rep_id = person['represents_person_id']
                if rep_id in opposing_parties:
                    opposing_parties[rep_id]['attorneys'].append(person)
                    attorney_to_party[person['person_id']] = rep_id
            elif role == 'opposing_staff':
                attorney_id = person['represents_person_id']
                party_id = attorney_to_party.get(attorney_id)
                if party_id and party_id in opposing_parties:
                    opposing_parties[party_id]['staff'].append(person)
            elif role == 'guardian_ad_litem':
                summary['guardian_ad_litem'] = person

        summary['opposing_parties'] = list(opposing_parties.values())

        return summary

    def clear_pro_se_for_party(self, case_id: int, person_id: int):
        self.db.execute("""
            UPDATE case_people 
            SET is_pro_se = 0
            WHERE case_id = ? AND person_id = ? AND role = 'opposing_party'
        """, (case_id, person_id))


class BillingQueries(BaseQueries[BillingEntry]):
    table_name = "billing_entries"
    model_class = BillingEntry
    columns = BILLING_COLUMNS
    order_by = "entry_date DESC, sort_order ASC"

    def get_next_sort_order(self, case_id: int, entry_date) -> int:
        row = self.db.fetchone("""
            SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order
            FROM billing_entries
            WHERE case_id = ? AND entry_date = ?
        """, (case_id, entry_date))
        return row["next_order"] if row else 0

    def create(self, entry: BillingEntry) -> int:
        sort_order = self.get_next_sort_order(entry.case_id, entry.entry_date)
        cursor = self.db.execute("""
            INSERT INTO billing_entries (case_id, entry_date, hours, is_expense, amount_cents, description, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.case_id, 
            entry.entry_date, 
            entry.hours, 
            1 if entry.is_expense else 0, 
            entry.amount_cents, 
            entry.description,
            sort_order
        ))
        return cursor.lastrowid

    def create_from_dict(self, entry_data: dict) -> int:
        case_id = entry_data['case_id']
        entry_date = entry_data['entry_date']
        sort_order = self.get_next_sort_order(case_id, entry_date)
        cursor = self.db.execute("""
            INSERT INTO billing_entries (case_id, entry_date, hours, is_expense, amount_cents, description, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            entry_date,
            entry_data.get('hours'),
            entry_data.get('is_expense', 0),
            entry_data.get('amount_cents'),
            entry_data.get('description', ''),
            sort_order
        ))
        return cursor.lastrowid

    def update(self, entry: BillingEntry):
        existing = self.get_by_id(entry.id)
        if existing and existing.entry_date != entry.entry_date:
            sort_order = self.get_next_sort_order(entry.case_id, entry.entry_date)
        else:
            sort_order = entry.sort_order
            
        self.db.execute("""
            UPDATE billing_entries SET case_id=?, entry_date=?, hours=?, is_expense=?, amount_cents=?, description=?, sort_order=?
            WHERE id=?
        """, (
            entry.case_id, 
            entry.entry_date, 
            entry.hours, 
            1 if entry.is_expense else 0, 
            entry.amount_cents, 
            entry.description,
            sort_order,
            entry.id
        ))

    def get_by_case(self, case_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT be.*,
                   c.case_number, c.case_name,
                   c.billing_rate_cents,
                   p.first_name || ' ' || p.last_name as client_name
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            LEFT JOIN case_people cp ON c.id = cp.case_id AND cp.role = 'client'
            LEFT JOIN people p ON cp.person_id = p.id
            WHERE be.case_id = ?
            ORDER BY be.entry_date DESC, be.sort_order ASC
        """, (case_id,))
        return [dict(row) for row in rows]

    def get_entries_for_period(self, case_id: int, year: int, month: int) -> List[dict]:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        rows = self.db.fetchall("""
            SELECT entry_date, hours, is_expense, amount_cents, description
            FROM billing_entries
            WHERE case_id = ? AND entry_date >= ? AND entry_date < ?
            ORDER BY entry_date ASC, sort_order ASC
        """, (case_id, start_date, end_date))
        return [dict(row) for row in rows]

    def get_entries_on_same_date(self, entry_id: int) -> List[dict]:
        entry = self.get_by_id(entry_id)
        if not entry:
            return []
        
        rows = self.db.fetchall("""
            SELECT id, sort_order
            FROM billing_entries
            WHERE case_id = ? AND entry_date = ?
            ORDER BY sort_order ASC
        """, (entry.case_id, entry.entry_date))
        return [dict(row) for row in rows]

    def move_entry_up(self, entry_id: int) -> bool:
        entries = self.get_entries_on_same_date(entry_id)
        if len(entries) < 2:
            return False
        
        current_idx = None
        for i, e in enumerate(entries):
            if e['id'] == entry_id:
                current_idx = i
                break
        
        if current_idx is None or current_idx == 0:
            return False
        
        prev_entry = entries[current_idx - 1]
        curr_entry = entries[current_idx]
        
        self.db.execute(
            "UPDATE billing_entries SET sort_order = ? WHERE id = ?",
            (prev_entry['sort_order'], entry_id)
        )
        self.db.execute(
            "UPDATE billing_entries SET sort_order = ? WHERE id = ?",
            (curr_entry['sort_order'], prev_entry['id'])
        )
        return True

    def move_entry_down(self, entry_id: int) -> bool:
        entries = self.get_entries_on_same_date(entry_id)
        if len(entries) < 2:
            return False
        
        current_idx = None
        for i, e in enumerate(entries):
            if e['id'] == entry_id:
                current_idx = i
                break
        
        if current_idx is None or current_idx == len(entries) - 1:
            return False
        
        next_entry = entries[current_idx + 1]
        curr_entry = entries[current_idx]
        
        self.db.execute(
            "UPDATE billing_entries SET sort_order = ? WHERE id = ?",
            (next_entry['sort_order'], entry_id)
        )
        self.db.execute(
            "UPDATE billing_entries SET sort_order = ? WHERE id = ?",
            (curr_entry['sort_order'], next_entry['id'])
        )
        return True

    def get_case_totals(self, case_id: int) -> dict:
        row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(CASE WHEN is_expense = 0 THEN hours ELSE 0 END), 0) as total_hours,
                COALESCE(SUM(CASE WHEN is_expense = 0 THEN hours * c.billing_rate_cents ELSE 0 END), 0) as total_time_cents,
                COALESCE(SUM(CASE WHEN is_expense = 1 THEN amount_cents ELSE 0 END), 0) as total_expense_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            WHERE be.case_id = ?
        """, (case_id,))
        result = dict(row) if row else {"total_hours": 0, "total_time_cents": 0, "total_expense_cents": 0}
        result["total_amount_cents"] = result["total_time_cents"] + result["total_expense_cents"]
        return result


class PaymentQueries(BaseQueries[Payment]):
    table_name = "payments"
    model_class = Payment
    columns = PAYMENT_COLUMNS
    order_by = "payment_date DESC"

    def create(self, payment: Payment) -> int:
        cursor = self.db.execute("""
            INSERT INTO payments (person_id, case_id, payment_date, amount_cents, 
                                  expense_amount_cents, payment_method, reference_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payment.person_id, payment.case_id, payment.payment_date,
            payment.amount_cents, payment.expense_amount_cents, 
            payment.payment_method, payment.reference_number, payment.notes
        ))
        return cursor.lastrowid

    def update(self, payment: Payment):
        self.db.execute("""
            UPDATE payments SET 
                person_id=?, case_id=?, payment_date=?, amount_cents=?,
                expense_amount_cents=?, payment_method=?, reference_number=?, notes=?
            WHERE id=?
        """, (
            payment.person_id, payment.case_id, payment.payment_date,
            payment.amount_cents, payment.expense_amount_cents,
            payment.payment_method, payment.reference_number,
            payment.notes, payment.id
        ))

    def get_by_case(self, case_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT p.*,
                   per.first_name || ' ' || per.last_name as client_name,
                   c.case_number
            FROM payments p
            JOIN people per ON p.person_id = per.id
            LEFT JOIN cases c ON p.case_id = c.id
            WHERE p.case_id = ?
            ORDER BY p.payment_date DESC
        """, (case_id,))
        return [dict(row) for row in rows]

    def get_case_payment_totals(self, case_id: int) -> dict:
        row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(amount_cents), 0) as total_fee_payments_cents,
                COALESCE(SUM(expense_amount_cents), 0) as total_expense_payments_cents
            FROM payments
            WHERE case_id = ?
        """, (case_id,))
        result = dict(row) if row else {"total_fee_payments_cents": 0, "total_expense_payments_cents": 0}
        result["total_payments_cents"] = result["total_fee_payments_cents"] + result["total_expense_payments_cents"]
        return result


class RecentCountyQueries:
    def __init__(self, db):
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


class InvoiceQueries:
    def __init__(self, db):
        self.db = db

    def get_trust_balances(self, case_id: int, year: int, month: int) -> dict:
        last_day = calendar.monthrange(year, month)[1]
        cutoff_date = f"{year}-{month:02d}-{last_day:02d}"

        billing_row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(CASE WHEN is_expense = 0 THEN hours * c.billing_rate_cents ELSE 0 END), 0) as total_fees_cents,
                COALESCE(SUM(CASE WHEN is_expense = 1 THEN amount_cents ELSE 0 END), 0) as total_expenses_cents
            FROM billing_entries be
            JOIN cases c ON be.case_id = c.id
            WHERE be.case_id = ? AND be.entry_date <= ?
        """, (case_id, cutoff_date))
        billing = dict(billing_row) if billing_row else {'total_fees_cents': 0, 'total_expenses_cents': 0}

        payment_row = self.db.fetchone("""
            SELECT 
                COALESCE(SUM(amount_cents), 0) as total_fee_payments_cents,
                COALESCE(SUM(expense_amount_cents), 0) as total_expense_payments_cents
            FROM payments
            WHERE case_id = ? AND payment_date <= ?
        """, (case_id, cutoff_date))
        payments = dict(payment_row) if payment_row else {'total_fee_payments_cents': 0, 'total_expense_payments_cents': 0}

        total_fee_payments = payments['total_fee_payments_cents'] / 100.0
        total_expense_payments = payments['total_expense_payments_cents'] / 100.0
        total_fees_billed = billing['total_fees_cents'] / 100.0
        total_expenses_billed = billing['total_expenses_cents'] / 100.0

        fee_balance = total_fee_payments - total_fees_billed
        expense_balance = total_expense_payments - total_expenses_billed

        return {
            'fee_balance': fee_balance,
            'expense_balance': expense_balance,
            'total_fee_payments': total_fee_payments,
            'total_expense_payments': total_expense_payments,
            'total_fees_billed': total_fees_billed,
            'total_expenses_billed': total_expenses_billed
        }

    def get_billing_rate(self, case_id: int) -> float:
        row = self.db.fetchone("SELECT billing_rate_cents FROM cases WHERE id = ?", (case_id,))
        return (row['billing_rate_cents'] if row else 30000) / 100.0