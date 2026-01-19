# ⚖️ Law Firm Billing System

A clean, intuitive desktop application for solo practitioners and small law firms to manage clients, cases, and billing.

## Features

| | Feature | Description |
|---|---|---|
| 📁 | **Matter Management** | Create and track litigation and non-litigation matters |
| 👥 | **Contact Management** | Unified database for all case participants |
| ⏱️ | **Time & Expense Tracking** | Log billable hours and expenses |
| 💰 | **Trust Accounting** | Separate fee and expense trust balances |
| 🧾 | **Invoice Generation** | Export professional invoices to Word |
| 📊 | **Reports** | Monthly and all-time billing summaries |
| 📞 | **Call Log Import** | Import CSV call logs, auto-match contacts |
| 📧 | **Email Log Import** | Import EML files, create billing entries |

## 🚀 Installation

### Option 1: Run from Source

```
pip install pyside6 python-docx
```
```
python main.py
```

## 💾 Data Storage

All data is stored in a SQLite database (`law_billing.db`) located in the same directory as the application. Back up this file regularly to protect your data.
