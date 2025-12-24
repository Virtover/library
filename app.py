from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Book
import pandas as pd
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/data/library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    # Filtering
    isbn = request.args.get('isbn', '')
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    publisher = request.args.get('publisher', '')
    year = request.args.get('year', '')
    signature = request.args.get('signature', '')
    keywords = request.args.get('keywords', '')

    query = Book.query

    if isbn:
        query = query.filter(Book.isbn.contains(isbn))
    if title:
        query = query.filter(Book.title.contains(title))
    if author:
        query = query.filter(Book.author.contains(author))
    if publisher:
        query = query.filter(Book.publisher.contains(publisher))
    if year:
        try:
            query = query.filter(Book.year == int(year))
        except ValueError:
            pass  # ignore invalid year input
    if signature:
        query = query.filter(Book.signature.contains(signature))
    if keywords:
        query = query.filter(Book.keywords.contains(keywords))

    books = query.all()

    if request.args.get('ajax'):
        return render_template('_books_list.html', books=books)

    return render_template('index.html', books=books, filters=request.args)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        book = Book(
            isbn=request.form['isbn'],
            title=request.form['title'],
            author=request.form['author'],
            publisher=request.form.get('publisher'),
            year=int(request.form.get('year')) if request.form.get('year') else None,
            signature=request.form.get('signature'),
            description=request.form.get('description'),
            keywords=request.form.get('keywords')
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully')
        return redirect(url_for('index'))
    return render_template('book_form.html', book=None)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.isbn = request.form['isbn']
        book.title = request.form['title']
        book.author = request.form['author']
        book.publisher = request.form.get('publisher')
        book.year = int(request.form.get('year')) if request.form.get('year') else None
        book.signature = request.form.get('signature')
        book.description = request.form.get('description')
        book.keywords = request.form.get('keywords')
        db.session.commit()
        flash('Book updated successfully')
        return redirect(url_for('index'))
    return render_template('book_form.html', book=book)

@app.route('/delete/<int:id>')
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_csv():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                book = Book(
                    isbn=str(row.get('ISBN', '')),
                    title=str(row.get('Title', '')),
                    author=str(row.get('Author', '')),
                    publisher=str(row.get('Publisher', '')),
                    year=int(row.get('Year')) if pd.notna(row.get('Year')) else None,
                    signature=str(row.get('Signature', '')),
                    description=str(row.get('Description', '')),
                    keywords=str(row.get('Keywords', ''))
                )
                db.session.add(book)
            db.session.commit()
            flash('CSV uploaded successfully')
            return redirect(url_for('index'))
        flash('Invalid file')
    return render_template('upload.html')

@app.route('/download')
def download_csv():
    # Apply same filters as index
    isbn = request.args.get('isbn', '')
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    publisher = request.args.get('publisher', '')
    year = request.args.get('year', '')
    signature = request.args.get('signature', '')
    keywords = request.args.get('keywords', '')

    query = Book.query

    if isbn:
        query = query.filter(Book.isbn.contains(isbn))
    if title:
        query = query.filter(Book.title.contains(title))
    if author:
        query = query.filter(Book.author.contains(author))
    if publisher:
        query = query.filter(Book.publisher.contains(publisher))
    if year:
        query = query.filter(Book.year == int(year))
    if signature:
        query = query.filter(Book.signature.contains(signature))
    if keywords:
        query = query.filter(Book.keywords.contains(keywords))

    books = query.all()
    df = pd.DataFrame([b.to_dict() for b in books])
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', download_name='books.csv', as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)