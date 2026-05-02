import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import pyodbc

# Database connection
def connect_db():
    try:
        conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                    r'DBQ=C:\Users\pc\Desktop\New folder\billing.system.accdb')  # Update with your database path
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")

# Function to get all product names from the database
def get_all_product_names():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT product_name FROM PRODUCTS")
            products = cursor.fetchall()
            return [product[0] for product in products]  # Return only the product names
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Error fetching product names:\n{e}")
        finally:
            conn.close()
    return []

# Function to filter product names based on user input
def get_filtered_product_names(filter_text=""):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            query = "SELECT product_name FROM PRODUCTS WHERE product_name LIKE ?"
            cursor.execute(query, (filter_text + '%',))
            products = cursor.fetchall()
            return [product[0] for product in products]  # Return filtered product names
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Error fetching product names:\n{e}")
        finally:
            conn.close()
    return []

# Function to update product names in the combobox based on input
def on_product_name_change(event):
    input_text = product_combobox.get()
    if input_text:
        filtered_products = get_filtered_product_names(input_text)  # Fetch products matching the input text
        product_combobox.configure(values=filtered_products)  # Update combobox with filtered values
    else:
        product_combobox.configure(values=all_product_names)  # Set to all products if input is empty

# Function to get product price based on product name
def get_product_price(product_name):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT product_price FROM PRODUCTS WHERE product_name = ?", (product_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                messagebox.showwarning("Not Found", "Product not found in PRODUCTS table.")
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Error fetching product price:\n{e}")
        finally:
            conn.close()
    return 0

# Function to add a new product purchase
def add_purchase():
    purchase_id = entry_purchase_id.get()
    customer_id = entry_customer_id.get()
    customer_name = entry_customer_name.get()
    product_name = product_combobox.get()
    quantity = entry_quantity.get()

    if purchase_id and customer_id and customer_name and product_name and quantity:
        product_price = get_product_price(product_name)
        if product_price == 0:
            return

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO PURCHASES (purchase_id, customer_id, customer_name, product_name, quantity, product_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (purchase_id, customer_id, customer_name, product_name, int(quantity), product_price)
                )

                conn.commit()
                messagebox.showinfo("Success", "Purchase details added successfully!")
                clear_fields()  # Clear only specific fields
            except pyodbc.Error as e:
                if "23000" in str(e):  # Handle duplicate purchase_id
                    messagebox.showerror("Database Error", "Purchase ID already exists. Please use a unique ID.")
                else:
                    messagebox.showerror("Database Error", f"Failed to add data to database:\n{e}")
            finally:
                conn.close()
    else:
        messagebox.showwarning("Input Error", "Please enter all purchase details.")

# Function to generate payment receipt with date and individual item details
def generate_receipt():
    customer_id = entry_receipt_customer_id.get()
    if customer_id:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(""" 
                    SELECT product_name, quantity, product_price 
                    FROM PURCHASES WHERE customer_id = ?
                """, (customer_id,))
                purchases = cursor.fetchall()

                if purchases:
                    cursor.execute("SELECT customer_name FROM PURCHASES WHERE customer_id = ?", (customer_id,))
                    customer_name = cursor.fetchone()[0]

                    date_today = datetime.now().strftime("%Y-%m-%d")
                    receipt = f"Date: {date_today}\nCustomer ID: {customer_id}\nCustomer Name: {customer_name}\n\n"
                    receipt += "Items Purchased:\n"
                    receipt += "-" * 50 + "\n"
                    receipt += "{:<25} {:<10} {:>12}\n".format("Product", "Quantity", "Total Price")
                    receipt += "-" * 50 + "\n"

                    total = 0
                    for product_name, quantity, product_price in purchases:
                        item_total = int(quantity) * float(product_price)
                        total += item_total
                        receipt += "{:<25} {:<10} ${:>11.2f}\n".format(product_name, quantity, item_total)

                    discount = 0.05 if total >= 2000 else 0
                    discount_amount = total * discount
                    total_after_discount = total - discount_amount

                    receipt += "-" * 50 + "\n"
                    receipt += "{:<25} {:<10} ${:>11.2f}\n".format("Total Bill", "", total)
                    receipt += "{:<25} {:<10} ${:>11.2f}\n".format("Discount", "", discount_amount)
                    receipt += "{:<25} {:<10} ${:>11.2f}".format("Total After Discount", "", total_after_discount)

                    text_receipt.delete(1.0, ctk.END)
                    text_receipt.insert(ctk.END, receipt)
                else:
                    messagebox.showwarning("Not Found", "No purchases found for the provided Customer ID.")
            except pyodbc.Error as e:
                messagebox.showerror("Database Error", f"Error fetching data:\n{e}")
            finally:
                conn.close()
    else:
        messagebox.showwarning("Input Error", "Please enter a Customer ID.")

# Function to clear input fields
def clear_fields():
    product_combobox.set('')
    entry_quantity.delete(0, ctk.END)
    entry_purchase_id.delete(0, ctk.END)

# Function to clear all fields
def clear_all_fields():
    entry_purchase_id.delete(0, ctk.END)
    entry_customer_id.delete(0, ctk.END)
    entry_customer_name.delete(0, ctk.END)
    product_combobox.set('')
    entry_quantity.delete(0, ctk.END)
    entry_receipt_customer_id.delete(0, ctk.END)
    text_receipt.delete(1.0, ctk.END)

# Create main window with a dark theme using customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Billing Program")
root.geometry("1400x800")  # Adjusted for larger receipt frame

# Frames for layout
frame_input = ctk.CTkFrame(root)
frame_input.grid(row=0, column=0, sticky="nsew")

frame_receipt = ctk.CTkFrame(root)
frame_receipt.grid(row=0, column=1, sticky="nsew")

# Configure grid layout
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=2)  # More space for receipt frame
root.grid_rowconfigure(0, weight=1)

# Input Frame - New Customer Details
label_purchase_id = ctk.CTkLabel(frame_input, text="Purchase ID:", font=("Arial", 14))
label_purchase_id.grid(row=0, column=0, sticky="w", padx=20, pady=10)
entry_purchase_id = ctk.CTkEntry(frame_input, font=("Arial", 14), width=300)
entry_purchase_id.grid(row=1, column=0, pady=10)

label_customer_id = ctk.CTkLabel(frame_input, text="Customer ID:", font=("Arial", 14))
label_customer_id.grid(row=2, column=0, sticky="w", padx=20, pady=10)
entry_customer_id = ctk.CTkEntry(frame_input, font=("Arial", 14), width=300)
entry_customer_id.grid(row=3, column=0, pady=10)

label_customer_name = ctk.CTkLabel(frame_input, text="Customer Name:", font=("Arial", 14))
label_customer_name.grid(row=4, column=0, sticky="w", padx=20, pady=10)
entry_customer_name = ctk.CTkEntry(frame_input, font=("Arial", 14), width=300)
entry_customer_name.grid(row=5, column=0, pady=10)

# Product Name Combobox
label_product_name = ctk.CTkLabel(frame_input, text="Product Name:", font=("Arial", 14))
label_product_name.grid(row=6, column=0, sticky="w", padx=20, pady=10)
product_combobox = ctk.CTkComboBox(frame_input, font=("Arial", 14), width=300)
product_combobox.grid(row=7, column=0, pady=10)
product_combobox.bind("<KeyRelease>", on_product_name_change)

# Quantity Entry
label_quantity = ctk.CTkLabel(frame_input, text="Quantity:", font=("Arial", 14))
label_quantity.grid(row=8, column=0, sticky="w", padx=20, pady=10)
entry_quantity = ctk.CTkEntry(frame_input, font=("Arial", 14), width=300)
entry_quantity.grid(row=9, column=0, pady=10)

# Buttons
btn_add_purchase = ctk.CTkButton(frame_input, text="Add Purchase", font=("Arial", 14), command=add_purchase)
btn_add_purchase.grid(row=10, column=0, pady=10)

btn_clear_fields = ctk.CTkButton(frame_input, text="Clear All Fields", font=("Arial", 14), command=clear_all_fields)
btn_clear_fields.grid(row=11, column=0, pady=10)

# Receipt Frame
label_receipt_customer_id = ctk.CTkLabel(frame_receipt, text="Enter Customer ID for Receipt:", font=("Arial", 14))
label_receipt_customer_id.grid(row=0, column=0, padx=20, pady=10)
entry_receipt_customer_id = ctk.CTkEntry(frame_receipt, font=("Arial", 14), width=300)
entry_receipt_customer_id.grid(row=1, column=0, padx=20, pady=10)

btn_generate_receipt = ctk.CTkButton(frame_receipt, text="Generate Receipt", font=("Arial", 16), command=generate_receipt)
btn_generate_receipt.grid(row=2, column=0, padx=20, pady=10)

# Receipt Text Box
text_receipt = ctk.CTkTextbox(frame_receipt, font=("Courier", 14), wrap="none", width=800, height=600)  # Use monospace for alignment
text_receipt.grid(row=3, column=0, padx=20, pady=20)

# Fetch all product names for combobox
all_product_names = get_all_product_names()
product_combobox.configure(values=all_product_names)
root.mainloop()

