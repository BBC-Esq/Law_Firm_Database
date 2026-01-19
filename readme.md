# ⚖️ Law Firm Billing System

A clean, intuitive desktop application for solo practitioners and small law firms to manage clients, cases, and billing.

---

## ✨ Features

**Client Management** — Store client contact information with support for multiple phone numbers and email addresses. Set individual hourly billing rates for each client.

**Case & Matter Tracking** — Link cases to clients, judges, and opposing counsel. Track case numbers, court types, and Georgia county venues with smart recent-county suggestions.

**Time Billing** — Log billable hours against specific matters with automatic amount calculation based on client rates. Filter entries by client or case.

**Payment Recording** — Record payments with flexible attribution to specific cases or as general client payments. Track payment methods and reference numbers.

**Court Directory** — Maintain a directory of judges and court staff. Associate staff members with specific judges or track general court personnel.

**Opposing Counsel Tracking** — Keep records of opposing attorneys, their firms, and staff members for easy reference across cases.

---

## 🚀 Installation

### Option 1: Run from Source

```
pip install PySide6
```
```
python main.py
```

## 💾 Data Storage

All data is stored in a SQLite database (`law_billing.db`) located in the same directory as the application. Back up this file regularly to protect your data.

---


## 🔧 Building the Executable

To create a standalone Windows executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "LawBilling" main.py
```

The executable will be created in the `dist` folder.
