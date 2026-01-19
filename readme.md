# ⚖️ Law Firm Billing System

A clean, intuitive desktop application for solo practitioners and small law firms to manage clients, cases, and billing.

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
