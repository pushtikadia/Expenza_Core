import json
import uuid
import csv
import os
import shutil
import traceback
from datetime import datetime
from decimal import Decimal, InvalidOperation

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "expenses.backup.json")

def now_iso():
    return datetime.now().isoformat()

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"expenses": [], "budgets": {}, "categories": []}, f, indent=2)

def load_data():
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def atomic_save(data):
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
        try:
            shutil.copy(DATA_FILE, BACKUP_FILE)
        except Exception:
            pass
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def normalize_amount(val):
    if val is None:
        raise ValueError("Amount required")
    s = str(val).strip()
    if not s:
        raise ValueError("Amount required")
    s = s.replace(",", "").replace("$", "")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError("Invalid amount")
    return str(d)

def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    raise ValueError("Invalid date format. Use YYYY-MM-DD or ISO format.")

def mk_expense(amount, category, note="", date=None):
    if date:
        dt = parse_date(date)
        date_iso = dt.isoformat()
    else:
        date_iso = now_iso()
    return {
        "id": str(uuid.uuid4()),
        "amount": normalize_amount(amount),
        "category": category.strip() or "Misc",
        "note": note.strip(),
        "date": date_iso,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

def input_amount(prompt="Amount: "):
    while True:
        s = input(prompt).strip()
        if s.lower() in ("cancel", "c", "q", "quit"):
            return None
        try:
            return normalize_amount(s)
        except ValueError as e:
            print("Invalid amount:", e, "- type 'cancel' to abort")

def input_date(prompt="Date (YYYY-MM-DD or blank for today): "):
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        if s.lower() in ("cancel", "c", "q", "quit"):
            return "CANCELLED"
        try:
            return parse_date(s).isoformat()
        except ValueError as e:
            print(e, "- type 'cancel' to abort")

def input_text(prompt, allow_empty=True):
    s = input(prompt).strip()
    if not s and not allow_empty:
        return None
    return s

def add_interactive():
    try:
        amt = input_amount()
        if amt is None:
            print("Cancelled")
            return
        cat = input_text("Category (or blank for Misc): ")
        if not cat:
            cat = "Misc"
        note = input_text("Note (optional): ")
        date_iso = input_date()
        if date_iso == "CANCELLED":
            print("Cancelled")
            return
        exp = mk_expense(amt, cat, note or "", date_iso)
        data = load_data()
        if cat not in data.get("categories", []):
            data.setdefault("categories", []).append(cat)
        data.setdefault("expenses", []).append(exp)
        atomic_save(data)
        print("Saved", exp["id"])
        check_budget_alert_for_expense(data, exp)
    except ValueError as e:
        print("Error:", e)
    except Exception:
        print("Unexpected error:")
        traceback.print_exc()

def format_exp(e):
    try:
        dt = datetime.fromisoformat(e.get("date",""))
        date = dt.strftime("%Y-%m-%d")
    except Exception:
        date = e.get("date","")
    amt = Decimal(e["amount"])
    return f'{e["id"][:8]} | {date} | {e["category"][:12]:12} | {amt:>10,.2f} | {e["note"]}'

def list_interactive(limit=10, page_size=10):
    try:
        data = load_data()
        exps = sorted(data.get("expenses", []), key=lambda x: x.get("date",""), reverse=True)
        if not exps:
            print("No expenses"); return
        total = len(exps)
        if limit and limit < total:
            exps = exps[:limit]
        if page_size <= 0:
            page_size = len(exps)
        page = 0
        while True:
            start = page*page_size
            if start >= len(exps):
                print("End of list"); break
            end = min(start+page_size, len(exps))
            for e in exps[start:end]:
                print(format_exp(e))
            print(f"Showing {start+1}-{end} of {len(exps)}")
            cmd = input("[n]ext [p]rev [q]uit: ").strip().lower()
            if cmd in ("n","next",""):
                page += 1
                continue
            if cmd in ("p","prev"):
                page = max(0, page-1)
                continue
            break
    except Exception:
        print("Unexpected error while listing:")
        traceback.print_exc()

def find_by_prefix(prefix):
    data = load_data()
    for e in data.get("expenses", []):
        if e["id"].startswith(prefix):
            return e
    return None

def edit_interactive():
    try:
        prefix = input("ID prefix: ").strip()
        if not prefix:
            print("Prefix required"); return
        e = find_by_prefix(prefix)
        if not e:
            print("Not found"); return
        print("Current:", format_exp(e))
        new_amt = input_text(f"Amount [{e['amount']}] (blank to keep): ")
        new_cat = input_text(f"Category [{e['category']}] (blank to keep): ")
        new_note = input_text(f"Note [{e['note']}] (blank to keep): ")
        new_date = input_text(f"Date [{e['date'][:10]}] (blank to keep): ")
        if new_amt:
            try:
                e["amount"] = normalize_amount(new_amt)
            except ValueError:
                print("Invalid amount; skipping amount update.")
        if new_cat:
            e["category"] = new_cat
        if new_note:
            e["note"] = new_note
        if new_date:
            try:
                e["date"] = parse_date(new_date).isoformat()
            except ValueError:
                print("Invalid date; skipping date update.")
        e["updated_at"] = now_iso()
        data = load_data()
        for i,item in enumerate(data.get("expenses", [])):
            if item["id"] == e["id"]:
                data["expenses"][i] = e
                break
        if e["category"] not in data.get("categories", []):
            data.setdefault("categories", []).append(e["category"])
        atomic_save(data)
        print("Updated")
    except Exception:
        print("Unexpected error while editing:")
        traceback.print_exc()

def delete_interactive():
    try:
        prefix = input("ID prefix to delete (or prefix* for multiple): ").strip()
        if not prefix:
            print("Prefix required"); return
        data = load_data()
        exps = data.get("expenses", [])
        matches = [x for x in exps if x["id"].startswith(prefix)]
        if not matches:
            print("No matches"); return
        for m in matches:
            print(format_exp(m))
        conf = input(f"Delete {len(matches)} item(s)? Type 'yes' to confirm: ").strip().lower()
        if conf != "yes":
            print("Aborted"); return
        data["expenses"] = [x for x in exps if not x["id"].startswith(prefix)]
        atomic_save(data)
        print("Deleted")
    except Exception:
        print("Unexpected error while deleting:")
        traceback.print_exc()

def search_interactive():
    try:
        q = input("Search term (category/note/amount): ").strip().lower()
        if not q:
            print("Empty"); return
        data = load_data()
        results = []
        for e in data.get("expenses", []):
            if q in e["category"].lower() or q in e["note"].lower() or q in e["amount"]:
                results.append(e)
        if not results:
            print("No results"); return
        for r in sorted(results, key=lambda x: x.get("date",""), reverse=True):
            print(format_exp(r))
    except Exception:
        print("Unexpected error while searching:")
        traceback.print_exc()

def summary_by_month():
    try:
        data = load_data()
        totals = {}
        for e in data.get("expenses", []):
            try:
                key = datetime.fromisoformat(e.get("date","")).strftime("%Y-%m")
            except Exception:
                key = "unknown"
            amt = Decimal(e["amount"])
            totals.setdefault(key, Decimal(0))
            totals[key] += amt
        if not totals:
            print("No data"); return
        for k in sorted(totals.keys(), reverse=True):
            print(k, f"{totals[k]:,.2f}")
    except Exception:
        print("Unexpected error while summarizing:")
        traceback.print_exc()

def stats():
    try:
        data = load_data()
        exps = data.get("expenses", [])
        total = sum((Decimal(e["amount"]) for e in exps), Decimal(0))
        count = len(exps)
        avg = (total / count) if count else Decimal(0)
        cats = {}
        for e in exps:
            cats.setdefault(e["category"], Decimal(0))
            cats[e["category"]] += Decimal(e["amount"])
        top = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Count:", count)
        print("Total:", f"{total:,.2f}")
        print("Average:", f"{round(avg,2):,}")
        print("Top categories:")
        for k,v in top:
            print(" ", k, f"{v:,.2f}")
    except Exception:
        print("Unexpected error while calculating stats:")
        traceback.print_exc()

def export_csv():
    try:
        path = input("Export path [expenses_export.csv]: ").strip() or "expenses_export.csv"
        data = load_data()
        rows = data.get("expenses", [])
        if not rows:
            print("No data"); return
        keys = ["id","date","amount","category","note","created_at","updated_at"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k,"") for k in keys})
        print("Exported to", path)
    except Exception:
        print("Unexpected error while exporting CSV:")
        traceback.print_exc()

def import_csv():
    try:
        path = input("CSV path: ").strip()
        if not path or not os.path.exists(path):
            print("File not found"); return
        with open(path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            imported = 0
            data = load_data()
            existing_keys = {(e.get("amount"), e.get("date"), e.get("category"), e.get("note")) for e in data.get("expenses", [])}
            for row in r:
                try:
                    amount = row.get("amount") or row.get("amt") or "0"
                    category = row.get("category") or "Imported"
                    note = row.get("note") or ""
                    date = row.get("date") or None
                    key = (normalize_amount(amount), date or "", category, note)
                    if key in existing_keys:
                        continue
                    e = mk_expense(amount, category, note, date)
                    data.setdefault("expenses", []).append(e)
                    existing_keys.add((e["amount"], e["date"], e["category"], e["note"]))
                    imported += 1
                except Exception:
                    continue
            atomic_save(data)
        print("Imported", imported)
    except Exception:
        print("Unexpected error while importing CSV:")
        traceback.print_exc()

def clear_all():
    try:
        conf = input("Type DELETE to confirm full reset: ").strip()
        if conf == "DELETE":
            atomic_save({"expenses": [], "budgets": {}, "categories": []})
            print("Cleared")
        else:
            print("Aborted")
    except Exception:
        print("Unexpected error while clearing:")
        traceback.print_exc()

def backup_now():
    try:
        data = load_data()
        path = input("Backup path [expenses.backup.json]: ").strip() or BACKUP_FILE
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Backup saved to", path)
    except Exception:
        print("Unexpected error while backing up:")
        traceback.print_exc()

def restore_backup():
    try:
        path = input("Backup path to restore [expenses.backup.json]: ").strip() or BACKUP_FILE
        if not os.path.exists(path):
            print("Backup not found"); return
        conf = input(f"This will replace current data with {path}. Type YES to confirm: ").strip()
        if conf != "YES":
            print("Aborted"); return
        try:
            shutil.copy(DATA_FILE, DATA_FILE + ".pre_restore.backup")
        except Exception:
            pass
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        atomic_save(data)
        print("Restored from", path)
    except Exception:
        print("Unexpected error while restoring:")
        traceback.print_exc()

def undo_last():
    try:
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            atomic_save(data)
            print("Undo successful")
        else:
            print("No backup to undo")
    except Exception:
        print("Unexpected error while undoing:")
        traceback.print_exc()

def manage_categories():
    try:
        data = load_data()
        cats = set(data.get("categories", []))
        while True:
            print("Categories:", ", ".join(sorted(cats)) if cats else "(none)")
            cmd = input("[a]dd [r]emove [q]uit: ").strip().lower()
            if cmd in ("a","add"):
                c = input("New category: ").strip()
                if c:
                    cats.add(c)
            elif cmd in ("r","remove"):
                c = input("Category to remove: ").strip()
                if c in cats:
                    linked = [e for e in data.get("expenses", []) if e["category"] == c]
                    if linked:
                        print(f"{len(linked)} expenses use this category.")
                        action = input("Type [d]elete to remove those expenses, [r]eassign to another category, or anything else to cancel: ").strip().lower()
                        if action in ("d","delete"):
                            data["expenses"] = [e for e in data.get("expenses", []) if e["category"] != c]
                            cats.remove(c)
                            print("Category and its expenses removed.")
                        elif action in ("r","reassign"):
                            newc = input("New category name: ").strip()
                            if newc:
                                for e in data.get("expenses", []):
                                    if e["category"] == c:
                                        e["category"] = newc
                                cats.discard(c)
                                cats.add(newc)
                                print("Reassigned expenses to", newc)
                            else:
                                print("No new category provided. Cancelled.")
                        else:
                            print("Cancelled removal.")
                    else:
                        cats.remove(c)
                        print("Category removed.")
                else:
                    print("Category not found.")
            else:
                break
        data["categories"] = sorted(list(cats))
        atomic_save(data)
        print("Updated categories")
    except Exception:
        print("Unexpected error while managing categories:")
        traceback.print_exc()

def set_budget():
    try:
        data = load_data()
        month = input("Budget month (YYYY-MM): ").strip()
        try:
            datetime.strptime(month+"-01", "%Y-%m-%d")
        except Exception:
            print("Invalid month"); return
        amt = input("Budget amount: ").strip()
        try:
            b = normalize_amount(amt)
        except ValueError:
            print("Invalid amount"); return
        data.setdefault("budgets", {})[month] = b
        atomic_save(data)
        print("Budget set")
    except Exception:
        print("Unexpected error while setting budget:")
        traceback.print_exc()

def budget_status():
    try:
        data = load_data()
        month = input("Month (YYYY-MM) or blank for current: ").strip()
        if not month:
            month = datetime.now().strftime("%Y-%m")
        total = Decimal(0)
        for e in data.get("expenses", []):
            try:
                if datetime.fromisoformat(e.get("date","")).strftime("%Y-%m") == month:
                    total += Decimal(e["amount"])
            except Exception:
                continue
        budget = data.get("budgets", {}).get(month)
        print("Month:", month)
        print("Spent:", f"{total:,.2f}")
        print("Budget:", budget if budget else "Not set")
        if budget:
            rem = Decimal(budget) - total
            print("Remaining:", f"{rem:,.2f}")
            if rem < 0:
                print("Alert: Budget exceeded by", f"{-rem:,.2f}")
    except Exception:
        print("Unexpected error while checking budget:")
        traceback.print_exc()

def check_budget_alert_for_expense(data, expense):
    try:
        month = datetime.fromisoformat(expense["date"]).strftime("%Y-%m")
    except Exception:
        return
    budget = data.get("budgets", {}).get(month)
    if not budget:
        return
    total = Decimal(0)
    for e in data.get("expenses", []):
        try:
            if datetime.fromisoformat(e.get("date","")).strftime("%Y-%m") == month:
                total += Decimal(e["amount"])
        except Exception:
            continue
    if total > Decimal(budget):
        print("Warning: month budget exceeded. Spent", f"{total:,.2f}", "budget", f"{Decimal(budget):,.2f}")

def report_text():
    try:
        data = load_data()
        totals = {}
        for e in data.get("expenses", []):
            try:
                k = datetime.fromisoformat(e.get("date","")).strftime("%Y-%m")
            except Exception:
                k = "unknown"
            totals.setdefault(k, Decimal(0))
            totals[k] += Decimal(e["amount"])
        lines = ["Expense Report", "=============="]
        for k in sorted(totals.keys(), reverse=True):
            lines.append(f"{k} : {totals[k]:,.2f}")
        path = input("Report file [report.txt]: ").strip() or "report.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("Report saved to", path)
    except Exception:
        print("Unexpected error while generating report:")
        traceback.print_exc()

def help_menu():
    print("Commands: add list edit delete search summary stats export import clear backup restore undo categories setbudget budget report help quit")

def main():
    ensure_data_file()
    print("Enhanced Expense Tracker")
    help_menu()
    while True:
        try:
            cmd = input(">> ").strip().lower()
            if cmd in ("q","quit","exit"):
                print("Goodbye"); break
            if cmd == "add":
                add_interactive()
            elif cmd == "list":
                list_interactive()
            elif cmd == "edit":
                edit_interactive()
            elif cmd == "delete":
                delete_interactive()
            elif cmd == "search":
                search_interactive()
            elif cmd == "summary":
                summary_by_month()
            elif cmd == "stats":
                stats()
            elif cmd == "export":
                export_csv()
            elif cmd == "import":
                import_csv()
            elif cmd == "clear":
                clear_all()
            elif cmd == "backup":
                backup_now()
            elif cmd == "restore":
                restore_backup()
            elif cmd == "undo":
                undo_last()
            elif cmd == "categories":
                manage_categories()
            elif cmd == "setbudget":
                set_budget()
            elif cmd == "budget":
                budget_status()
            elif cmd == "report":
                report_text()
            elif cmd == "help":
                help_menu()
            elif cmd == "":
                continue
            else:
                print("Unknown command. Type help")
        except KeyboardInterrupt:
            print("\nInterrupted. Type quit to exit")
        except Exception:
            print("Unexpected error in main loop:")
            traceback.print_exc()

if __name__ == "__main__":
    main()


