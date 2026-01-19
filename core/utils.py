from PySide6.QtCore import QDate
from datetime import date, datetime
from typing import Optional, Union


def parse_date(value: Union[str, date, datetime, None]) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def parse_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def date_to_qdate(d: Union[str, date, None]) -> QDate:
    parsed = parse_date(d)
    if parsed:
        return QDate(parsed.year, parsed.month, parsed.day)
    return QDate.currentDate()


def qdate_to_date(qd: QDate) -> date:
    return date(qd.year(), qd.month(), qd.day())


def format_matter_display(matter: dict, include_client: bool = False) -> str:
    matter_name = matter.get('case_name') or ''
    client_name = matter.get('client_name') or 'No Client'
    
    if matter.get('is_litigation'):
        county = matter.get('county') or ''
        court_type = matter.get('court_type') or ''
        case_number = matter.get('case_number') or ''
        
        if county and court_type:
            court_display = f"{county} County {court_type}"
        else:
            court_display = court_type or county or 'Litigation'
        
        if case_number:
            suffix = f"{court_display} ({case_number})"
        else:
            suffix = court_display
    else:
        suffix = "Non-Litigation"
    
    if include_client:
        return f"{client_name} - {matter_name} - {suffix}"
    return f"{matter_name} - {suffix}"