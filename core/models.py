from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


ROLE_DISPLAY_NAMES = {
    'client': 'Client',
    'opposing_party': 'Opposing Party',
    'opposing_counsel': 'Opposing Counsel',
    'opposing_staff': 'Opposing Staff',
    'judge': 'Judge',
    'judge_staff': "Judge's Staff",
    'court_staff': 'Court Staff',
    'guardian_ad_litem': 'Guardian ad Litem',
    'co_counsel': 'Co-Counsel'
}

PARTY_DESIGNATIONS = ('plaintiff', 'defendant')

PARTY_DESIGNATION_DISPLAY = {
    'plaintiff': 'Plaintiff',
    'defendant': 'Defendant'
}

MATTER_STATUSES = ('Open', 'Closed')


def _parse_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    return None


def _parse_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d")
    return None


@dataclass
class Person:
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    billing_rate_cents: int = 30000
    firm_name: str = ""
    job_title: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.created_at = _parse_datetime(self.created_at)

    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"


@dataclass
class Case:
    id: Optional[int] = None
    case_number: str = ""
    case_name: str = ""
    is_litigation: bool = False
    court_type: str = ""
    county: str = ""
    status: str = "Open"
    billing_rate_cents: int = 30000
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.created_at = _parse_datetime(self.created_at)
        if isinstance(self.is_litigation, int):
            self.is_litigation = bool(self.is_litigation)


@dataclass
class CasePerson:
    id: Optional[int] = None
    case_id: Optional[int] = None
    person_id: Optional[int] = None
    role: str = ""
    party_designation: str = ""
    represents_person_id: Optional[int] = None
    is_pro_se: bool = False
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.created_at = _parse_datetime(self.created_at)
        if isinstance(self.is_pro_se, int):
            self.is_pro_se = bool(self.is_pro_se)


@dataclass
class BillingEntry:
    id: Optional[int] = None
    case_id: Optional[int] = None
    entry_date: Optional[date] = None
    hours: Optional[float] = None
    is_expense: bool = False
    amount_cents: Optional[int] = None
    description: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.entry_date = _parse_date(self.entry_date)
        self.created_at = _parse_datetime(self.created_at)
        if isinstance(self.is_expense, int):
            self.is_expense = bool(self.is_expense)


@dataclass
class Payment:
    id: Optional[int] = None
    person_id: Optional[int] = None
    case_id: Optional[int] = None
    payment_date: Optional[date] = None
    amount_cents: int = 0
    expense_amount_cents: int = 0
    payment_method: str = ""
    reference_number: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.payment_date = _parse_date(self.payment_date)
        self.created_at = _parse_datetime(self.created_at)
    
    @property
    def total_amount_cents(self) -> int:
        return self.amount_cents + self.expense_amount_cents