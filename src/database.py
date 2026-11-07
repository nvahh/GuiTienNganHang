import sqlite3
import pandas as pd
from models import Customer, TermSaving, NonTermSaving

DB_NAME = "bank_savings.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            cccd TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone TEXT,
            address TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS savings (
            acc_id TEXT PRIMARY KEY,
            cccd TEXT NOT NULL,
            amount REAL NOT NULL,
            open_date TEXT NOT NULL,
            term_months INTEGER NOT NULL,
            interest_rate REAL NOT NULL,
            status TEXT DEFAULT 'Đang hoạt động',
            FOREIGN KEY (cccd) REFERENCES customers (cccd)
        )
    """)
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", [
            ("056204001234", "Nguyễn Văn An", "0905123456", "Nha Trang, Khánh Hòa"),
            ("056204005678", "Trần Thị Bình", "0914987654", "Cam Ranh, Khánh Hòa")
        ])
        cur.executemany("INSERT INTO savings VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("STK001", "056204001234", 50000000, "2026-01-15", 6, 5.2, "Đang hoạt động"),
            ("STK002", "056204005678", 120000000, "2026-09-01", 12, 6.0, "Đang hoạt động"),
            ("STK003", "056204001234", 20000000, "2026-08-10", 0, 0.5, "Đang hoạt động")
        ])
    conn.commit()
    conn.close()


def get_next_acc_id() -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT acc_id FROM savings")
    rows = cur.fetchall()
    conn.close()

    existing_numbers = set()
    for (acc_id,) in rows:
        if acc_id and acc_id.startswith("STK") and acc_id[3:].isdigit():
            existing_numbers.add(int(acc_id[3:]))

    next_num = 1
    while next_num in existing_numbers:
        next_num += 1

    return f"STK{next_num:03d}"


def get_customer_by_cccd(cccd: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cccd, full_name, phone, address FROM customers WHERE cccd = ?", (cccd,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"cccd": row[0], "full_name": row[1], "phone": row[2], "address": row[3]}
    return None


def get_customer_by_phone(phone: str, exclude_cccd: str = None):
    conn = get_connection()
    cur = conn.cursor()
    if exclude_cccd:
        cur.execute("SELECT cccd, full_name, phone FROM customers WHERE phone = ? AND cccd != ?", (phone, exclude_cccd))
    else:
        cur.execute("SELECT cccd, full_name, phone FROM customers WHERE phone = ?", (phone,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"cccd": row[0], "full_name": row[1], "phone": row[2]}
    return None


def check_cccd_exists(cccd: str) -> bool:
    return get_customer_by_cccd(cccd) is not None


def check_acc_id_exists(acc_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM savings WHERE acc_id = ?", (acc_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def add_customer(customer: Customer):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (cccd, full_name, phone, address)
        VALUES (?, ?, ?, ?)
    """, (customer.cccd, customer.full_name, customer.phone, customer.address))
    conn.commit()
    conn.close()


def add_saving(saving):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO savings (acc_id, cccd, amount, open_date, term_months, interest_rate, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (saving.acc_id, saving.cccd, saving.amount, saving.open_date, saving.term_months, saving.interest_rate, saving.status))
    conn.commit()
    conn.close()


def get_all_savings_df() -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT s.acc_id, s.cccd, c.full_name, c.phone, c.address, s.amount, s.open_date, 
               s.term_months, s.interest_rate, s.status
        FROM savings s
        JOIN customers c ON s.cccd = c.cccd
        ORDER BY s.acc_id ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_all_customers_df() -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT c.cccd, c.full_name, c.phone, c.address, COUNT(s.acc_id) as total_books
        FROM customers c
        LEFT JOIN savings s ON c.cccd = s.cccd
        GROUP BY c.cccd, c.full_name, c.phone, c.address
        ORDER BY c.full_name ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def update_customer(cccd: str, full_name: str, phone: str, address: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE customers 
        SET full_name = ?, phone = ?, address = ?
        WHERE cccd = ?
    """, (full_name, phone, address, cccd))
    conn.commit()
    conn.close()


def delete_saving_account(acc_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM savings WHERE acc_id = ?", (acc_id,))
    conn.commit()
    conn.close()


def get_saving_object(acc_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT acc_id, cccd, amount, open_date, term_months, interest_rate, status FROM savings WHERE acc_id = ?", (acc_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if row[4] == 0:
        return NonTermSaving(row[0], row[1], row[2], row[3], row[5], row[6])
    return TermSaving(row[0], row[1], row[2], row[3], row[4], row[5], row[6])


def close_saving_account(acc_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE savings SET status = 'Đã tất toán' WHERE acc_id = ?", (acc_id,))
    conn.commit()
    conn.close()