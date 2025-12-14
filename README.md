# 💸 Expenza Core (Expense Tracker CLI)

**Expenza Core** is a robust, production-grade command-line expense tracker built with **Python 3**. It is designed for reliability and data safety, featuring atomic file saving, budget alerts, and precise financial calculations.

Unlike simple scripts, this tool focuses on **data integrity**, offering built-in backups, undo functionality, and CSV import/export capabilities.

## 📂 Repository Content

This project is contained within a powerful single-file application:

* **`expense_tracker.py`:** The main executable script. It handles:
    * **Data Persistence:** Stores records in `expenses.json` with **atomic saving** to prevent corruption during crashes.
    * **Logic & Math:** Uses Python's `Decimal` class for high-precision monetary calculations (avoiding floating-point errors).
    * **Interactive CLI:** A robust menu loop for managing transactions, budgets, and settings.

---

## ✨ Key Features

### 📊 Financial Management
* **Smart Budgeting:** Set monthly budgets and receive immediate alerts if an expense pushes you over the limit.
* **Deep Analytics:** View monthly summaries, calculate averages, and identify top spending categories.
* **Category Management:** Dynamically add, remove, or reassign expense categories.

### 🛡️ Data Safety & Power Tools
* **Atomic Saves & Backups:** Prevents data loss by writing to a temporary file first. Includes automatic backup creation.
* **Undo Capability:** Made a mistake? Instantly revert the last operation using the backup file.
* **Import/Export:** Seamlessly migrate data using standard CSV files for integration with Excel or Google Sheets.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.6 or higher.

### Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/pushtikadia/Expenza-Core.git](https://github.com/pushtikadia/Expenza-Core.git)
    ```
2.  **Navigate to the directory:**
    ```bash
    cd Expenza-Core
    ```
3.  **Run the tracker:**
    ```bash
    python expense_tracker.py
    ```
4.  **Follow the menu:**
    Type `add` to record an expense, `stats` for insights, or `help` to see all commands.

---

## 🛠️ Technologies Used

* **Language:** Python 3
* **Core Libraries:** `json`, `csv`, `decimal`, `datetime`, `shutil` (File Ops)

---

<p align="center">
  <b>Expenza Core</b> • Created by <a href="https://github.com/pushtikadia"><b>Pushti Kadia</b></a>
</p>




