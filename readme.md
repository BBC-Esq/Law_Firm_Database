# ⚖️ Law Firm Billing System

A clean, intuitive desktop application for solo practitioners and small law firms to manage clients, cases, and billing.

<img width="898" height="618" alt="image" src="https://github.com/user-attachments/assets/c19a6f01-26b0-4c74-ab2d-257a192562a7" />


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

```bash
# Clone the repository

# Install dependencies
pip install PySide6

# Run the application
python main.py
```

---

## 📖 Quick Start

1. **Add a client** — Go to the Clients tab and click "Add Client." Enter contact details and set the hourly billing rate.

2. **Create a case** — In the Cases/Matters tab, click "Add Case/Matter." Select the client, add case details, and optionally assign a judge and opposing counsel.

3. **Log time** — Switch to the Billing tab and click "Add Billing Entry." Search for the client/matter, enter hours and a description.

4. **Record payments** — In the Payments tab, click "Add Payment" to record client payments against specific cases or as general retainer payments.

5. **Manage court contacts** — Use the Court tab to add judges and their staff. The Opposing Counsel tab tracks attorneys you encounter on cases.

---

## 🎨 Interface

The application uses a tabbed interface with six main sections: Clients, Cases/Matters, Court, Opposing Counsel, Billing, and Payments. Tables support sorting by any column, and double-clicking any row opens it for editing.

---

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
