from dataclasses import dataclass, fields
from datetime import date, datetime
from typing import Optional
from core.utils import parse_date, parse_datetime


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
PARTY_DESIGNATION_DISPLAY = {'plaintiff': 'Plaintiff', 'defendant': 'Defendant'}
MATTER_STATUSES = ('Open', 'Closed')


def _convert_field(obj, name, converter):
    """Convert a field value using the given converter."""
    value = getattr(obj, name)
    if value is not None:
        setattr(obj, name, converter(value))


def _post_init_common(obj, date_fields=None, datetime_fields=None, bool_fields=None):
    """Common post_init processing for date/datetime/bool fields."""
    for field in (date_fields or []):
        _convert_field(obj, field, parse_date)
    for field in (datetime_fields or []):
        _convert_field(obj, field, parse_datetime)
    for field in (bool_fields or []):
        val = getattr(obj, field)
        if isinstance(val, int):
            setattr(obj, field, bool(val))


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
        _post_init_common(self, datetime_fields=['created_at'])

    @property
    def full_name(self) -> str:
        parts = [self.first_name] + ([self.middle_name] if self.middle_name else []) + [self.last_name]
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        mid = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.last_name}, {self.first_name}{mid}"


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
        _post_init_common(self, datetime_fields=['created_at'], bool_fields=['is_litigation'])


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
        _post_init_common(self, datetime_fields=['created_at'], bool_fields=['is_pro_se'])


@dataclass
class BillingEntry:
    id: Optional[int] = None
    case_id: Optional[int] = None
    entry_date: Optional[date] = None
    hours: Optional[float] = None
    is_expense: bool = False
    amount_cents: Optional[int] = None
    description: str = ""
    sort_order: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        _post_init_common(self, date_fields=['entry_date'], datetime_fields=['created_at'], bool_fields=['is_expense'])

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
        _post_init_common(self, date_fields=['payment_date'], datetime_fields=['created_at'])

    @property
    def total_amount_cents(self) -> int:
        return self.amount_cents + self.expense_amount_cents