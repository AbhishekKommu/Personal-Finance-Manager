from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'finance-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    transactions = db.relationship('Transaction', backref='owner', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'date': self.date.strftime('%Y-%m-%d')
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Page Routes ---
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html', username=current_user.username)

# --- Authentication APIs ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_pw = generate_password_hash(data.get('password'), method='scrypt')
    user = User(username=data.get('username'), password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if not user or not check_password_hash(user.password, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401

    login_user(user)
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

# --- Financial Transaction REST APIs ---
@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    total_income = sum(t.amount for t in txs if t.type == 'income')
    total_expense = sum(t.amount for t in txs if t.type == 'expense')
    balance = total_income - total_expense

    return jsonify({
        'transactions': [t.to_dict() for t in txs],
        'summary': {
            'balance': round(balance, 2),
            'income': round(total_income, 2),
            'expense': round(total_expense, 2)
        }
    }), 200

@app.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('amount') or not data.get('type'):
        return jsonify({'error': 'Missing required fields'}), 400

    tx = Transaction(
        title=data['title'],
        amount=float(data['amount']),
        type=data['type'],
        category=data.get('category', 'General'),
        user_id=current_user.id
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify(tx.to_dict()), 201

@app.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
@login_required
def delete_transaction(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()
    if not tx:
        return jsonify({'error': 'Transaction not found'}), 404

    db.session.delete(tx)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)