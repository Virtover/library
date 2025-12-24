from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20))
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    publisher = db.Column(db.String(200))
    year = db.Column(db.Integer)
    signature = db.Column(db.String(100))
    description = db.Column(db.Text)
    keywords = db.Column(db.String(500))  # comma-separated

    def to_dict(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'year': self.year,
            'signature': self.signature,
            'description': self.description,
            'keywords': self.keywords
        }