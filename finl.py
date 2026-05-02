import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import pyodbc

# ---------------- DATABASE ---------------- #
def connect_db():
    try:
        conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                    r'DBQ=C:\Users\pc\Desktop\New folder\billing.system.accdb')
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        messagebox.showerror("Database Error", f"Failed to connect:\n{e}")
        return None


def execute_query(query, params=(), fetch=False, one=False):
    conn = connect_db()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchone() if one else cursor.fetchall()
        conn.commit()
    except pyodbc.Error as e:
        messagebox.showerror("Database Error", f"{e}")
    finally:
        conn.close()


# ---------------- PRODUCT FUNCTIONS ---------------- #
def get_all_product_names():
    result = execute_query("SELECT product_name FROM PRODUCTS", fetch=True)
    return [r[0] for r in result] if result else []


def get_product_price(product_name):
    result = execute_query(
        "SELECT product_price FROM PRODUCTS WHERE product_name = ?",
        (product_name,),
        fetch=True,
        one=True
    )
    if result:
        return result[0]
    messagebox.showwarning("Not Found", "Product not found.")
    return None


def on_product_name_change(event):
    text = product_combobox.get().lower()
    filtered = [p for p in all_product_names if p.lower().startswith(text)]
    product_combobox.configure(values=filtered)


# ---------------- PURCHASE ---------------- #
def add_purchase():
    purchase_id = entry_purchase_id.get().strip()
    customer_id = entry_customer_id.get().strip()
    customer_name = entry_customer_name.get().strip()
    product_name = product_combobox.get().strip()

    # Validate quantity
    try:
        quantity = int(entry_quantity.get())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Quantity must be a positive number.")
        return

    if not (purchase_id and customer_id and customer_name and product_name):
        messagebox.showwarning("Input Error", "Fill all fields.")
        return

    product_price = get_product_price(product_name)
    if product_price is None:
        return

    try:
        execute_query(
            """
            INSERT INTO PURCHASES 
            (purchase_id, customer_id, customer_name, product_name, quantity, product_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (purchase_id, customer_id, customer_name, product_name, quantity, product_price)
        )
        messagebox.showinfo("Success", "Purchase added!")
        clear_fields()
    except Exception as e:
        if "23000" in str(e):
            messagebox.showerror("Error", "Duplicate Purchase ID.")
        else:
            messagebox.showerror("Error", str(e))


# ---------------- RECEIPT ---------------- #
def generate_receipt():
    customer_id = entry_receipt_customer_id.get().strip()
    if not customer_id:
        messagebox.showwarning("Input Error", "Enter Customer ID.")
        return

    purchases = execute_query(
        "SELECT product_name, quantity, product_price FROM PURCHASES WHERE customer_id = ?",
        (customer_id,),
        fetch=True
    )

    if not purchases:
        messagebox.showwarning("Not Found", "No purchases found.")
        return

    customer_name = execute_query(
        "SELECT customer_name FROM PURCHASES WHERE customer_id = ?",
        (customer_id,),
        fetch=True,
        one=True
    )[0]

    date_today = datetime.now().strftime("%Y-%m-%d")

    receipt = f"Date: {date_today}\nCustomer ID: {customer_id}\nCustomer Name: {customer_name}\n\n"
    receipt += "Items Purchased:\n"
    receipt += "-" * 50 + "\n"
    receipt += "{:<25} {:<10} {:>12}\n".format("Product", "Qty", "Total")
    receipt += "-" * 50 + "\n"

    total = 0
    for name, qty, price in purchases:
        item_total = qty * price
        total += item_total
        receipt += "{:<25} {:<10} PKR {:>10.2f}\n".format(name, qty, item_total)

    # Discount logic
    if total >= 5000:
        discount = 0.10
    elif total >= 2000:
        discount = 0.05
    else:
        discount = 0

    discount_amount = total * discount
    final_total = total - discount_amount

    receipt += "-" * 50 + "\n"
    receipt += "{:<25} {:<10} PKR {:>10.2f}\n".format("Total", "", total)
    receipt += "{:<25} {:<10} PKR {:>10.2f}\n".format("Discount", "", discount_amount)
    receipt += "{:<25} {:<10} PKR {:>10.2f}".format("Final Total", "", final_total)

    text_receipt.delete(1.0, ctk.END)
    text_receipt.insert(ctk.END, receipt)


# ---------------- CLEAR ---------------- #
def clear_fields():
    entry_purchase_id.delete(0, ctk.END)
    product_combobox.set('')
    entry_quantity.delete(0, ctk.END)


def clear_all_fields():
    entry_purchase_id.delete(0, ctk.END)
    entry_customer_id.delete(0, ctk.END)
    entry_customer_name.delete(0, ctk.END)
    product_combobox.set('')
    entry_quantity.delete(0, ctk.END)
    entry_receipt_customer_id.delete(0, ctk.END)
    text_receipt.delete(1.0, ctk.END)


# ---------------- UI ---------------- #
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Billing Program")
root.geometry("1400x800")

frame_input = ctk.CTkFrame(root)
frame_input.grid(row=0, column=0, sticky="nsew")

frame_receipt = ctk.CTkFrame(root)
frame_receipt.grid(row=0, column=1, sticky="nsew")

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=2)
root.grid_rowconfigure(0, weight=1)

# Input Fields
entry_purchase_id = ctk.CTkEntry(frame_input, width=300)
entry_customer_id = ctk.CTkEntry(frame_input, width=300)
entry_customer_name = ctk.CTkEntry(frame_input, width=300)
product_combobox = ctk.CTkComboBox(frame_input, width=300)
entry_quantity = ctk.CTkEntry(frame_input, width=300)

labels = ["Purchase ID", "Customer ID", "Customer Name", "Product Name", "Quantity"]
entries = [entry_purchase_id, entry_customer_id, entry_customer_name, product_combobox, entry_quantity]

for i, (label, entry) in enumerate(zip(labels, entries)):
    ctk.CTkLabel(frame_input, text=label).grid(row=i*2, column=0, padx=20, pady=5, sticky="w")
    entry.grid(row=i*2+1, column=0, pady=5)

product_combobox.bind("<KeyRelease>", on_product_name_change)

ctk.CTkButton(frame_input, text="Add Purchase", command=add_purchase).grid(row=10, column=0, pady=10)
ctk.CTkButton(frame_input, text="Clear All", command=clear_all_fields).grid(row=11, column=0, pady=10)

# Receipt
entry_receipt_customer_id = ctk.CTkEntry(frame_receipt, width=300)
entry_receipt_customer_id.grid(row=0, column=0, pady=10)

ctk.CTkButton(frame_receipt, text="Generate Receipt", command=generate_receipt).grid(row=1, column=0, pady=10)

text_receipt = ctk.CTkTextbox(frame_receipt, width=800, height=600, font=("Courier", 14))
text_receipt.grid(row=2, column=0, padx=20, pady=20)

# Load products once
all_product_names = get_all_product_names()
product_combobox.configure(values=all_product_names)

root.mainloop()

