# Online bookstore project
# Olivia
# 2024/11/10
# description: The objective of this project is to develop an e-commerce platform for books that will enable users to search for their desired books, place orders, and receive an email containing a file that will work as a placeholder for an eBook. 



from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import sqlite3
import os

app = Flask(__name__)

# Configure Flask-Mail for email notifications
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Replace with your email password

mail = Mail(app)

# Create Database
DATABASE = "ecommerce.db"

def db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_database():
    conn = db_connection()
    cursor = conn.cursor()

    # Create Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Books (
            BookID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT,
            Author TEXT,
            Price REAL,
            Stock INTEGER
        )
    ''')

    # Create Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Orders (
            OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
            BookID INTEGER,
            CustomerEmail TEXT,
            Quantity INTEGER,
            TotalPrice REAL,
            FOREIGN KEY (BookID) REFERENCES Books(BookID)
        )
    ''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = db_connection()
    cursor = conn.cursor()

    books = [
        ("The Great Gatsby", "F. Scott Fitzgerald", 10.99, 100),
        ("To Kill a Mockingbird", "Harper Lee", 7.99, 50),
        ("1984", "George Orwell", 8.99, 75),
        ("Moby Dick", "Herman Melville", 11.99, 20)
    ]

    cursor.executemany('''
        INSERT INTO Books (Title, Author, Price, Stock)
        VALUES (?, ?, ?, ?)
    ''', books)
    conn.commit()
    conn.close()

# Search for books
@app.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('query', '')
    conn = db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM Books WHERE Title LIKE ? OR Author LIKE ?"
    cursor.execute(sql, (f'%{query}%', f'%{query}%'))
    books = cursor.fetchall()
    conn.close()

    return jsonify(books)

# Place an order
@app.route('/order', methods=['POST'])
def place_order():
    data = request.json
    book_id = data['book_id']
    customer_email = data['email']
    quantity = data['quantity']

    conn = db_connection()
    cursor = conn.cursor()

    # Book details
    cursor.execute("SELECT Price, Stock FROM Books WHERE BookID = ?", (book_id,))
    book = cursor.fetchone()

    if not book or book[1] < quantity:
        return jsonify({"error": "Book not available or insufficient stock"}), 400

    # Calculate total price and stock
    total_price = book[0] * quantity
    new_stock = book[1] - quantity
    cursor.execute("UPDATE Books SET Stock = ? WHERE BookID = ?", (new_stock, book_id))

    cursor.execute('''
        INSERT INTO Orders (BookID, CustomerEmail, Quantity, TotalPrice)
        VALUES (?, ?, ?, ?)
    ''', (book_id, customer_email, quantity, total_price))
    conn.commit()

    # Send confirmation email
    send_email(customer_email)

    conn.close()
    return jsonify({"message": "Order placed successfully"})

# Send emails
def send_email(to_email):
    placeholder_file = "ebook_placeholder.txt"

    if not os.path.exists(placeholder_file):
        with open(placeholder_file, "w") as f:
            f.write("Thank you for purchasing an eBook from our platform. This is your placeholder file for the eBook.")

    msg = Message("Your eBook Order Confirmation", sender="your_email@gmail.com", recipients=[to_email])
    msg.body = "Thank you for your order! Please find your eBook attached."
    with open(placeholder_file, "r") as ebook:
        msg.attach("ebook_placeholder.txt", "text/plain", ebook.read())
    mail.send(msg)


if __name__ == '__main__':
    
    create_database()

    insert_sample_data()

    app.run(debug=True)
