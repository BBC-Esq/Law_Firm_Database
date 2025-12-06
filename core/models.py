from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Client:
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    billing_rate_cents: int = 30000
    created_at: Optional[datetime] = None

    @property
    def billing_rate(self) -> float:
        return self.billing_rate_cents / 100.0

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
class Judge:
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    created_at: Optional[datetime] = None

@dataclass
class CourtStaff:
    id: Optional[int] = None
    judge_id: Optional[int] = None
    name: str = ""
    job_title: str = ""
    phone: str = ""
    email: str = ""
    created_at: Optional[datetime] = None

@dataclass
class OpposingAttorney:
    id: Optional[int] = None
    name: str = ""
    firm_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    created_at: Optional[datetime] = None

@dataclass
class OpposingStaff:
    id: Optional[int] = None
    attorney_id: Optional[int] = None
    name: str = ""
    job_title: str = ""
    phone: str = ""
    email: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Case:
    id: Optional[int] = None
    client_id: Optional[int] = None
    judge_id: Optional[int] = None
    opposing_attorney_id: Optional[int] = None
    case_number: str = ""
    court_type: str = ""
    county: str = ""
    case_name: str = ""
    created_at: Optional[datetime] = None

@dataclass
class BillingEntry:
    id: Optional[int] = None
    case_id: Optional[int] = None
    entry_date: Optional[date] = None
    hours: float = 0.0
    description: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Payment:
    id: Optional[int] = None
    client_id: Optional[int] = None
    case_id: Optional[int] = None
    payment_date: Optional[date] = None
    amount_cents: int = 0
    payment_method: str = ""
    reference_number: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    
    @property
    def amount(self) -> float:
        return self.amount_cents / 100.0