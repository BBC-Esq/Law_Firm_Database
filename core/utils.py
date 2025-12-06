from PySide6.QtCore import QDate
from datetime import date

def date_to_qdate(d) -> QDate:
    if isinstance(d, str):
        parts = d.split("-")
        if len(parts) == 3:
            return QDate(int(parts[0]), int(parts[1]), int(parts[2]))
    elif isinstance(d, date):
        return QDate(d.year, d.month, d.day)
    return QDate.currentDate()

def qdate_to_date(qd: QDate) -> date:
    return date(qd.year(), qd.month(), qd.day())