from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = mysql.connector.connect(host="localhost", user=username, password=password)
            if conn.is_connected():
                session['user'] = username
                session['pass'] = password
                session['username'] = username  # 👈 Add this for navbar logic
                return redirect(url_for('index'))
        except Error:
            return render_template("login.html", error="Invalid credentials or MySQL server error.")
    return render_template("login.html")

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user=session['user'],
        password=session['pass']
    )

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route('/add_book', methods=['POST'])
def add_book():
    if 'user' not in session:
        return redirect(url_for('login'))

    data = request.json
    title = data['title']
    author = data['author']
    genre = data['genre']
    year = data['year']
    description = data.get('description', '')

    if not str(year).isdigit():
        return jsonify(message="Year must be numeric."), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS library")
        cursor.execute("USE library")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                author VARCHAR(255),
                genre VARCHAR(100),
                year INT,
                description TEXT
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("ALTER TABLE books AUTO_INCREMENT = 1")

        cursor.execute(
            "INSERT INTO books (title, author, genre, year, description) VALUES (%s, %s, %s, %s, %s)",
            (title, author, genre, int(year), description)
        )
        conn.commit()
        return jsonify(message="Book added successfully!")
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/show_books')
def show_books():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE library")
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        return jsonify(books=books)
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_book', methods=['POST'])
def delete_book():
    if 'user' not in session:
        return redirect(url_for('login'))

    title = request.json['title']
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("USE library")
        cursor.execute("DELETE FROM books WHERE title = %s", (title,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify(message="No book found with that title.")

        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE books AUTO_INCREMENT = 1")

        return jsonify(message="Book deleted successfully!")
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/search_books')
def search_books():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE library")
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", (f"%{query}%", f"%{query}%"))
        books = cursor.fetchall()
        return jsonify(books=books)
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/filter_genre')
def filter_genre():
    if 'user' not in session:
        return redirect(url_for('login'))
    genre = request.args.get('genre', '')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE library")
        cursor.execute("SELECT * FROM books WHERE genre = %s", (genre,))
        books = cursor.fetchall()
        return jsonify(books=books)
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/latest_books')
def latest_books():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE library")
        cursor.execute("SELECT * FROM books ORDER BY year DESC")
        books = cursor.fetchall()
        return jsonify(books=books)
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/export_books')
def export_books():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE library")
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        return jsonify(books=books)
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/import_books', methods=['POST'])
def import_books():
    if 'user' not in session:
        return redirect(url_for('login'))
    books = request.get_json()
    if not isinstance(books, list):
        return jsonify(message="Invalid JSON format. Expected a list of book objects."), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("USE library")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                author VARCHAR(255),
                genre VARCHAR(100),
                year INT,
                description TEXT
            )
        """)
        for book in books:
            cursor.execute(
                "INSERT INTO books (title, author, genre, year, description) VALUES (%s, %s, %s, %s, %s)",
                (
                    book.get('title', ''),
                    book.get('author', ''),
                    book.get('genre', ''),
                    int(book.get('year', 0)),
                    book.get('description', '')
                )
            )
        conn.commit()
        return jsonify(message="Books imported successfully.")
    except Error as e:
        return jsonify(message=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
