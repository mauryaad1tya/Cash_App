import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QMessageBox, QStackedWidget, QFormLayout, QFrame,
                            QGraphicsDropShadowEffect, QDoubleSpinBox,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (QFont, QIcon, QPalette, QColor, QLinearGradient, 
                        QPainter, QDoubleValidator)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# Get the application directory
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (executable)
        return os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        return os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(get_app_dir(), 'cash_tracker.db')
print(f"Database path: {DB_PATH}")  # Debug print

# Initialize database
def init_db():
    print("Initializing database...")
    print(f"Using database at: {DB_PATH}")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create user table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_id TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    print("User table created/verified")
    
    # Create cash_transaction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cash_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
    ''')
    print("Transaction table created/verified")
    
    # Create transfer table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transfer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES user (id),
        FOREIGN KEY (receiver_id) REFERENCES user (id)
    )
    ''')
    print("Transfer table created/verified")
    
    conn.commit()
    conn.close()
    print("Database initialization complete")

def get_user_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN transaction_type = 'add' THEN amount ELSE -amount END), 0)
            FROM cash_transaction 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0
    finally:
        conn.close()

def transfer_money(sender_id, receiver_id, amount):
    if amount <= 0:
        raise ValueError("Amount must be positive")
        
    sender_balance = get_user_balance(sender_id)
    if sender_balance < amount:
        raise ValueError("Insufficient balance")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Add transfer record
        cursor.execute("""
            INSERT INTO transfer (amount, sender_id, receiver_id)
            VALUES (?, ?, ?)
        """, (amount, sender_id, receiver_id))
        
        # Add transaction for sender (remove money)
        cursor.execute("""
            INSERT INTO cash_transaction (amount, transaction_type, user_id)
            VALUES (?, 'remove', ?)
        """, (amount, sender_id))
        
        # Add transaction for receiver (add money)
        cursor.execute("""
            INSERT INTO cash_transaction (amount, transaction_type, user_id)
            VALUES (?, 'add', ?)
        """, (amount, receiver_id))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_username(username):
    print(f"Looking up user with username: {username}")  # Debug print
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, unique_id FROM user WHERE LOWER(username) = LOWER(?)", (username,))
        result = cursor.fetchone()
        print(f"Found user: {result}")  # Debug print
        return result
    except Exception as e:
        print(f"Error looking up user: {str(e)}")  # Debug print
        return None
    finally:
        conn.close()

# Global styles
STYLE_SHEET = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 #1a1b1e, stop:1 #2c2d31);
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #ffffff;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #7289da, stop:1 #5865f2);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    min-width: 120px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #5865f2, stop:1 #7289da);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #4752c4, stop:1 #5865f2);
    padding: 13px 23px 11px 25px;
}

QLineEdit, QDoubleSpinBox {
    padding: 12px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    font-size: 14px;
    background: rgba(26, 27, 30, 0.8);
    color: #ffffff;
    min-height: 20px;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: transparent;
    border: none;
    width: 20px;
}

QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 8px solid #7289da;
    width: 0px;
    height: 0px;
}

QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 8px solid #7289da;
    width: 0px;
    height: 0px;
}

QDoubleSpinBox::up-arrow:hover, QDoubleSpinBox::down-arrow:hover {
    border-bottom-color: #5865f2;
    border-top-color: #5865f2;
}

QLineEdit:focus, QDoubleSpinBox:focus {
    border: 2px solid #7289da;
    background: #1a1b1e;
}

QLabel {
    font-size: 14px;
    color: #ffffff;
}

QMessageBox {
    background-color: #2c2d31;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
    font-size: 14px;
    min-width: 300px;
    padding: 10px;
}

QMessageBox QPushButton {
    min-width: 100px;
    min-height: 30px;
    padding: 6px 12px;
}

.glass-container {
    background: rgba(44, 45, 49, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 25px;
    margin: 10px;
}

.title-label {
    font-size: 28px;
    font-weight: bold;
    color: #7289da;
    margin-bottom: 25px;
}

.balance-container {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 rgba(114, 137, 218, 0.1),
                               stop:1 rgba(88, 101, 242, 0.1));
    border: 1px solid rgba(114, 137, 218, 0.2);
    border-radius: 16px;
    padding: 30px;
    margin: 20px;
}

.balance-label {
    font-size: 18px;
    color: #a0a0a0;
    font-weight: 500;
}

.balance-value {
    font-size: 42px;
    font-weight: bold;
    color: #7289da;
}

.add-button {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #43b581, stop:1 #3ca374);
}

.add-button:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #3ca374, stop:1 #43b581);
}

.remove-button {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #f04747, stop:1 #d84040);
}

.remove-button:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #d84040, stop:1 #f04747);
}

.form-container {
    background: rgba(44, 45, 49, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 25px;
    margin: 15px;
}
"""

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Title with enhanced shadow effect
        title = QLabel("Cash Tracker")
        title.setProperty("class", "title-label")
        title.setAlignment(Qt.AlignCenter)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(114, 137, 218, 50))
        shadow.setOffset(0, 2)
        title.setGraphicsEffect(shadow)
        layout.addWidget(title)
        
        # Login form container with enhanced shadow
        form_container = QFrame()
        form_container.setProperty("class", "glass-container")
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Add enhanced shadow to form container
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(25)
        container_shadow.setColor(QColor(0, 0, 0, 60))
        container_shadow.setOffset(0, 4)
        form_container.setGraphicsEffect(container_shadow)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        
        form_container.setLayout(form_layout)
        layout.addWidget(form_container)
        
        # Login button with enhanced shadow
        login_btn = QPushButton("Login")
        login_btn.setCursor(Qt.PointingHandCursor)
        button_shadow = QGraphicsDropShadowEffect()
        button_shadow.setBlurRadius(15)
        button_shadow.setColor(QColor(114, 137, 218, 40))
        button_shadow.setOffset(0, 3)
        login_btn.setGraphicsEffect(button_shadow)
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)
        
        # Register link with enhanced styling
        register_container = QFrame()
        register_container.setProperty("class", "glass-container")
        register_layout = QHBoxLayout()
        register_layout.setContentsMargins(20, 15, 20, 15)
        
        register_label = QLabel("Don't have an account?")
        register_label.setStyleSheet("color: #a0a0a0;")
        register_btn = QPushButton("Register")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.parent.show_register)
        
        register_layout.addWidget(register_label)
        register_layout.addWidget(register_btn)
        register_container.setLayout(register_layout)
        
        # Add enhanced shadow to register container
        register_shadow = QGraphicsDropShadowEffect()
        register_shadow.setBlurRadius(20)
        register_shadow.setColor(QColor(0, 0, 0, 40))
        register_shadow.setOffset(0, 2)
        register_container.setGraphicsEffect(register_shadow)
        
        layout.addWidget(register_container)
        self.setLayout(layout)
        
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        print(f"Attempting login for user: {username}")
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, password_hash, unique_id FROM user WHERE username = ?", (username,))
            user = cursor.fetchone()
            print(f"Found user in database: {user is not None}")
            
            if user and check_password_hash(user[1], password):
                print("Password check successful")
                self.parent.user_id = user[0]
                self.parent.username = username
                self.parent.unique_id = user[2]  # Store the unique_id
                print(f"Set user_id to {self.parent.user_id} and username to {self.parent.username}")
                print(f"Set unique_id to {self.parent.unique_id}")  # Debug print
                self.parent.show_dashboard()
            else:
                print("Invalid username or password")
                QMessageBox.warning(self, "Error", "Invalid username or password")
        except Exception as e:
            print(f"Login error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
        finally:
            conn.close()

class RegisterWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("Register")
        title.setProperty("class", "title-label")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Register form container
        form_container = QFrame()
        form_container.setProperty("class", "form-container")
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        form_container.setLayout(form_layout)
        layout.addWidget(form_container)
        
        # Register button
        register_btn = QPushButton("Register")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn)
        
        # Login link
        login_layout = QHBoxLayout()
        login_layout.addStretch()
        login_label = QLabel("Already have an account?")
        login_btn = QPushButton("Login")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.parent.show_login)
        login_layout.addWidget(login_label)
        login_layout.addWidget(login_btn)
        login_layout.addStretch()
        
        layout.addLayout(login_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "All fields are required!")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
            
        # Check if username already exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        if cursor.fetchone():
            QMessageBox.warning(self, "Error", "Username already exists!")
            conn.close()
            return
            
        # Generate unique ID
        unique_id = str(uuid.uuid4())
        
        # Insert new user with unique ID
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO user (username, password_hash, unique_id) VALUES (?, ?, ?)",
            (username, password_hash, unique_id)
        )
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Success", "Registration successful!")
        self.parent.show_login()

class DashboardWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_user_id = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header with user info
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Cash Tracker")
        title.setProperty("class", "title-label")
        title.setAlignment(Qt.AlignLeft)
        
        # User info
        user_info_layout = QVBoxLayout()
        self.username_label = QLabel()
        self.username_label.setAlignment(Qt.AlignRight)
        self.username_label.setStyleSheet("color: #7289da; font-weight: 600; font-size: 14px;")
        
        # Unique ID container with copy button
        unique_id_container = QHBoxLayout()
        unique_id_label = QLabel("ID:")
        unique_id_label.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        self.unique_id_label = QLabel()
        self.unique_id_label.setStyleSheet("color: #a0a0a0; font-size: 12px; font-family: monospace;")
        self.unique_id_label.setCursor(Qt.PointingHandCursor)
        self.unique_id_label.setToolTip("Click to copy")
        self.unique_id_label.mousePressEvent = self.copy_unique_id
        
        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7289da;
                border: 1px solid #7289da;
                padding: 2px 8px;
                font-size: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(114, 137, 218, 0.1);
            }
        """)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_unique_id)
        
        unique_id_container.addWidget(unique_id_label)
        unique_id_container.addWidget(self.unique_id_label)
        unique_id_container.addWidget(copy_btn)
        unique_id_container.addStretch()
        
        user_info_layout.addWidget(self.username_label)
        user_info_layout.addLayout(unique_id_container)
        
        # Add logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.parent.logout)
        user_info_layout.addWidget(logout_btn)
        
        header_layout.addWidget(title)
        header_layout.addLayout(user_info_layout)
        layout.addLayout(header_layout)
        
        # Balance container with enhanced styling
        balance_container = QFrame()
        balance_container.setProperty("class", "balance-container")
        balance_layout = QVBoxLayout()
        
        balance_label = QLabel("Current Balance")
        balance_label.setProperty("class", "balance-label")
        balance_label.setAlignment(Qt.AlignCenter)
        
        self.balance_value = QLabel("₹0.00")
        self.balance_value.setProperty("class", "balance-value")
        self.balance_value.setAlignment(Qt.AlignCenter)
        
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.balance_value)
        balance_container.setLayout(balance_layout)
        
        # Add enhanced shadow to balance container
        balance_shadow = QGraphicsDropShadowEffect()
        balance_shadow.setBlurRadius(30)
        balance_shadow.setColor(QColor(114, 137, 218, 30))
        balance_shadow.setOffset(0, 4)
        balance_container.setGraphicsEffect(balance_shadow)
        
        layout.addWidget(balance_container)
        
        # Transfer container
        transfer_container = QFrame()
        transfer_container.setProperty("class", "form-container")
        transfer_layout = QVBoxLayout()
        
        transfer_label = QLabel("Transfer Money")
        transfer_label.setStyleSheet("color: #a0a0a0; font-size: 16px; margin-bottom: 15px;")
        transfer_layout.addWidget(transfer_label)
        
        # Recipient input
        recipient_layout = QHBoxLayout()
        recipient_label = QLabel("Recipient:")
        recipient_label.setStyleSheet("color: #a0a0a0;")
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Enter recipient's username")
        recipient_layout.addWidget(recipient_label)
        recipient_layout.addWidget(self.recipient_input)
        transfer_layout.addLayout(recipient_layout)
        
        # Amount input
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setStyleSheet("color: #a0a0a0;")
        self.transfer_amount_input = QDoubleSpinBox()
        self.transfer_amount_input.setRange(0.00, 999999.99)
        self.transfer_amount_input.setDecimals(2)
        self.transfer_amount_input.setSingleStep(1.00)
        self.transfer_amount_input.setPrefix("₹ ")
        self.transfer_amount_input.setFixedHeight(45)
        self.transfer_amount_input.setAlignment(Qt.AlignCenter)
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.transfer_amount_input)
        transfer_layout.addLayout(amount_layout)
        
        # Transfer button
        transfer_btn = QPushButton("Transfer")
        transfer_btn.setProperty("class", "add-button")
        transfer_btn.setCursor(Qt.PointingHandCursor)
        transfer_btn.clicked.connect(self.handle_transfer)
        transfer_layout.addWidget(transfer_btn)
        
        transfer_container.setLayout(transfer_layout)
        layout.addWidget(transfer_container)
        
        # Transaction form with enhanced styling
        form_container = QFrame()
        form_container.setProperty("class", "form-container")
        form_layout = QVBoxLayout()
        
        # Add label for amount input
        amount_label = QLabel("Enter amount in rupees:")
        amount_label.setStyleSheet("color: #a0a0a0; margin-bottom: 5px;")
        form_layout.addWidget(amount_label)
        
        # Configure QDoubleSpinBox for better number input handling
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.00, 999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(1.00)
        self.amount_input.setPrefix("₹ ")
        self.amount_input.setFixedHeight(45)
        self.amount_input.setAlignment(Qt.AlignCenter)
        self.amount_input.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Hide the up/down buttons
        self.amount_input.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 16px;
                font-weight: 500;
                padding-left: 15px;
                padding-right: 15px;
            }
        """)
        
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Cash")
        add_btn.setProperty("class", "add-button")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.handle_transaction('add'))
        
        remove_btn = QPushButton("Remove Cash")
        remove_btn.setProperty("class", "remove-button")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self.handle_transaction('remove'))
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        
        form_layout.addWidget(self.amount_input)
        form_layout.addLayout(button_layout)
        form_container.setLayout(form_layout)
        
        # Add enhanced shadow to form container
        form_shadow = QGraphicsDropShadowEffect()
        form_shadow.setBlurRadius(25)
        form_shadow.setColor(QColor(0, 0, 0, 50))
        form_shadow.setOffset(0, 4)
        form_container.setGraphicsEffect(form_shadow)
        
        layout.addWidget(form_container)

        # Transaction History Table
        history_label = QLabel("Transaction History")
        history_label.setStyleSheet("color: #a0a0a0; font-size: 16px; margin-top: 20px;")
        layout.addWidget(history_label)

        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(4)  # Add recipient column
        self.transaction_table.setHorizontalHeaderLabels(["Date", "Type", "Amount", "Recipient/Sender"])
        self.transaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transaction_table.setStyleSheet("""
            QTableWidget {
                background-color: #2c2d31;
                border: 1px solid #40444b;
                border-radius: 8px;
                color: #ffffff;
                gridline-color: #40444b;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #40444b;
            }
            QHeaderView::section {
                background-color: #36393f;
                color: #7289da;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #7289da;
            }
        """)
        layout.addWidget(self.transaction_table)
        
        self.setLayout(layout)

    def update_transaction_history(self):
        if not hasattr(self.parent, 'user_id'):
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Get regular transactions
            cursor.execute("""
                SELECT timestamp, transaction_type, amount, NULL as recipient
                FROM cash_transaction 
                WHERE user_id = ? 
                
                UNION ALL
                
                SELECT 
                    t.timestamp,
                    CASE 
                        WHEN t.sender_id = ? THEN 'transfer_out'
                        WHEN t.receiver_id = ? THEN 'transfer_in'
                    END as transaction_type,
                    t.amount,
                    CASE 
                        WHEN t.sender_id = ? THEN u2.username
                        WHEN t.receiver_id = ? THEN u1.username
                    END as recipient
                FROM transfer t
                JOIN user u1 ON t.sender_id = u1.id
                JOIN user u2 ON t.receiver_id = u2.id
                WHERE t.sender_id = ? OR t.receiver_id = ?
                
                ORDER BY timestamp DESC
            """, (self.parent.user_id, self.parent.user_id, self.parent.user_id, 
                  self.parent.user_id, self.parent.user_id, self.parent.user_id, self.parent.user_id))
            
            transactions = cursor.fetchall()
            
            self.transaction_table.setRowCount(len(transactions))
            self.transaction_table.setColumnCount(4)  # Add recipient column
            self.transaction_table.setHorizontalHeaderLabels(["Date", "Type", "Amount", "Recipient/Sender"])
            
            for row, (timestamp, trans_type, amount, recipient) in enumerate(transactions):
                # Format timestamp
                date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                
                # Create table items
                date_item = QTableWidgetItem(date_str)
                type_item = QTableWidgetItem()
                amount_item = QTableWidgetItem(f"₹{amount:.2f}")
                recipient_item = QTableWidgetItem(recipient if recipient else "")
                
                # Set text alignment
                date_item.setTextAlignment(Qt.AlignCenter)
                type_item.setTextAlignment(Qt.AlignCenter)
                amount_item.setTextAlignment(Qt.AlignCenter)
                recipient_item.setTextAlignment(Qt.AlignCenter)
                
                # Set text and color based on transaction type
                if trans_type == "add":
                    type_item.setText("Added")
                    type_item.setForeground(QColor("#43b581"))  # Green
                    amount_item.setForeground(QColor("#43b581"))
                elif trans_type == "remove":
                    type_item.setText("Removed")
                    type_item.setForeground(QColor("#f04747"))  # Red
                    amount_item.setForeground(QColor("#f04747"))
                elif trans_type == "transfer_out":
                    type_item.setText("Sent")
                    type_item.setForeground(QColor("#f04747"))  # Red
                    amount_item.setForeground(QColor("#f04747"))
                elif trans_type == "transfer_in":
                    type_item.setText("Received")
                    type_item.setForeground(QColor("#43b581"))  # Green
                    amount_item.setForeground(QColor("#43b581"))
                
                # Add items to table
                self.transaction_table.setItem(row, 0, date_item)
                self.transaction_table.setItem(row, 1, type_item)
                self.transaction_table.setItem(row, 2, amount_item)
                self.transaction_table.setItem(row, 3, recipient_item)
                
            # Resize columns to fit content
            self.transaction_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating transaction history: {str(e)}")
        finally:
            conn.close()

    def update_balance(self):
        if not hasattr(self.parent, 'user_id'):
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN transaction_type = 'add' THEN amount ELSE -amount END), 0) 
                FROM cash_transaction 
                WHERE user_id = ?
            """, (self.parent.user_id,))
            
            result = cursor.fetchone()
            balance = result[0] if result[0] is not None else 0
            self.balance_value.setText(f"₹{balance:.2f}")
        except Exception as e:
            print(f"Error updating balance: {str(e)}")
        finally:
            conn.close()

    def handle_transaction(self, transaction_type):
        amount = self.amount_input.value()
        if amount <= 0:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please enter a valid amount")
            msg.setIcon(QMessageBox.Warning)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2c2d31;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    min-width: 300px;
                }
                QMessageBox QPushButton {
                    min-width: 100px;
                    padding: 6px 12px;
                }
            """)
            msg.exec_()
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO cash_transaction (amount, transaction_type, user_id, timestamp) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (amount, transaction_type, self.parent.user_id))
            
            conn.commit()
            
            self.amount_input.setValue(0.00)
            self.update_balance()
            self.update_transaction_history()
            
            action = "added to" if transaction_type == "add" else "removed from"
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText(f"₹{amount:.2f} has been {action} your balance")
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2c2d31;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    min-width: 300px;
                }
                QMessageBox QPushButton {
                    min-width: 100px;
                    padding: 6px 12px;
                }
            """)
            msg.exec_()
        except Exception as e:
            print(f"Error handling transaction: {str(e)}")
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Transaction failed: {str(e)}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()
        finally:
            conn.close()

    def handle_transfer(self):
        recipient_username = self.recipient_input.text().strip()
        amount = self.transfer_amount_input.value()
        
        print(f"Attempting transfer to: {recipient_username}")  # Debug print
        
        if not recipient_username:
            QMessageBox.warning(self, "Error", "Please enter recipient's username")
            return
            
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid amount")
            return
            
        try:
            # Get recipient's user info
            recipient = get_user_by_username(recipient_username)
            print(f"Found recipient: {recipient}")  # Debug print
            
            if not recipient:
                QMessageBox.warning(self, "Error", f"Recipient '{recipient_username}' not found. Please check the username and try again.")
                return
                
            if recipient[0] == self.parent.user_id:
                QMessageBox.warning(self, "Error", "Cannot transfer to yourself")
                return
                
            # Get sender's balance
            sender_balance = get_user_balance(self.parent.user_id)
            print(f"Sender balance: {sender_balance}")  # Debug print
            
            if sender_balance < amount:
                QMessageBox.warning(self, "Error", f"Insufficient balance. Your current balance is ₹{sender_balance:.2f}")
                return
                
            # Perform transfer
            transfer_money(self.parent.user_id, recipient[0], amount)
            
            # Clear inputs
            self.recipient_input.clear()
            self.transfer_amount_input.setValue(0.00)
            
            # Update dashboard
            self.update_balance()
            self.update_transaction_history()
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Successfully transferred ₹{amount:.2f} to {recipient_username}"
            )
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            print(f"Transfer error: {str(e)}")  # Debug print
            QMessageBox.critical(self, "Error", f"Transfer failed: {str(e)}")

    def copy_unique_id(self, event=None):
        unique_id = self.unique_id_label.text().replace("ID: ", "")
        if unique_id:
            clipboard = QApplication.clipboard()
            clipboard.setText(unique_id)
            QMessageBox.information(self, "Copied", "Unique ID copied to clipboard!")
            
    def refresh_dashboard(self):
        if hasattr(self.parent, 'user_id') and self.parent.user_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            try:
                # Get user info including unique_id
                cursor.execute("SELECT username, unique_id FROM user WHERE id = ?", (self.parent.user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    self.username_label.setText(f"Welcome, {user_data[0]}")
                    self.unique_id_label.setText(user_data[1])  # Remove "ID: " prefix
                    print(f"Displaying unique ID: {user_data[1]}")  # Debug print
                else:
                    print("No user data found")  # Debug print
            except Exception as e:
                print(f"Error refreshing dashboard: {str(e)}")  # Debug print
            finally:
                conn.close()
            
            self.update_balance()
            self.update_transaction_history()
        else:
            print("No user_id found in parent")  # Debug print

class CashTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_id = None
        self.username = None
        self.unique_id = None  # Add unique_id property
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Cash Tracker")
        self.setGeometry(100, 100, 700, 600)
        self.setStyleSheet(STYLE_SHEET)
        
        # Create stacked widget for multiple screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create screens
        self.login_screen = LoginWindow(self)
        self.register_screen = RegisterWindow(self)
        self.dashboard_screen = DashboardWindow(self)
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.register_screen)
        self.stacked_widget.addWidget(self.dashboard_screen)
        
        # Show login screen by default
        self.show_login()
        
    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_screen)
        
    def show_register(self):
        self.stacked_widget.setCurrentWidget(self.register_screen)
        
    def show_dashboard(self):
        print(f"Showing dashboard for user: {self.username} (ID: {self.user_id}, Unique ID: {self.unique_id})")
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)
        self.dashboard_screen.username_label.setText(f"Welcome, {self.username}")
        self.dashboard_screen.unique_id_label.setText(f"ID: {self.unique_id}")
        self.dashboard_screen.refresh_dashboard()
        
    def logout(self):
        self.user_id = None
        self.username = None
        self.unique_id = None  # Clear unique_id on logout
        self.show_login()

def main():
    # Initialize database
    init_db()
    
    app = QApplication(sys.argv)
    window = CashTrackerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 