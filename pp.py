import sys
import os
import json
import csv
import re
import pymysql
from datetime import datetime
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QFrame, QStackedWidget, QListWidget, QListWidgetItem,QDialog,
    QFormLayout,QComboBox,QHeaderView,QCheckBox, QGridLayout, QWidget, QDateTimeEdit,QRadioButton,QDateEdit,QSizePolicy,
    QButtonGroup, QAbstractScrollArea,QFileDialog,QMenu,QToolButton,QAction,QGridLayout,QGroupBox,QStyledItemDelegate
)
from PyQt5.QtGui import QFont,QIntValidator,QDoubleValidator,QPixmap,QCursor,QPalette, QBrush, QLinearGradient, QColor,QRegExpValidator
from PyQt5.QtCore import QTimer,QTime, QDateTime,Qt,QDate,QRegExp,QObject, QEvent


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host="localhost",
            user="root",
            password="password",
            database="lottery"
        )
        self.cursor = self.connection.cursor()

    def verify_admin(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE name=%s AND pass=%s", (username, password))
        return self.cursor.fetchone()

    def add_user(self, username, password, company_name, incentive, email, rate, mor,day,eve):
        current_time = datetime.now()

        # ➕ INSERT user
        user_query = """
            INSERT INTO users 
            (name, company_name, phone_no, adress, incentive, email, pass, user_role, fk_user_id, active, rate, last_active, created_on) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        user_values = (
            username, company_name, None, None, incentive, email, password,
            2, 6, 1, rate, current_time, current_time
        )

        try:
            self.cursor.execute(user_query, user_values)
            user_id = self.cursor.lastrowid  # ✅ Get newly finserted user ID

            # ➕ INSERT 3 session-wise userrate rows
            rate_query = """
                INSERT INTO userrate (user_id, session_id, rate, created_by, tms)
                VALUES (%s, %s, %s, %s, %s)
            """

            for session_id, session_rate in [(1, mor), (2, day), (3, eve)]:
                self.cursor.execute(rate_query, (user_id, session_id, session_rate, 6, current_time))

            self.connection.commit()
            return True

        except pymysql.err.IntegrityError as e:
            print("Integrity Error:", e)
            return False

    def delete_user(self, userid):
        self.cursor.execute("DELETE FROM userrate WHERE user_id =%s", (userid))
        self.cursor.execute("DELETE FROM users WHERE id=%s", (userid))
        self.connection.commit()
        
    def delete_ticket(self, t_id):
        self.cursor.execute("DELETE FROM tickets WHERE id =%s", (t_id))
        self.cursor.execute("DELETE FROM ticket_session_names WHERE ticket_id=%s", (t_id))
        self.cursor.execute("DELETE FROM ticket_prizes WHERE ticket_id=%s", (t_id))
        self.connection.commit()
        
    def load_user(self):
        query = """SELECT             
                    u.id,
                    u.incentive,
                    u.rate,
                    u.email,
                    u.pass,
                    u.name,
                    u.company_name,
                    MAX(CASE WHEN r.session_id = 1 THEN r.rate END) AS MOR,
                    MAX(CASE WHEN r.session_id = 2 THEN r.rate END) AS DAY,
                    MAX(CASE WHEN r.session_id = 3 THEN r.rate END) AS EVE
                FROM userrate r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE u.user_role = 2
                GROUP BY u.id,
                    u.incentive,
                    u.rate,
                    u.email,
                    u.pass,
                    u.name,
                    u.company_name"""
                       
        self.cursor.execute(query)
        self.connection.commit()
        return self.cursor.fetchall()
        
    def load_ticket(self):
        query = """  
                SELECT 
                  t1.id AS ticket_id,
                  t1.name AS ticket_name,
                  t1.rate,

                  -- Session 1 info
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Sun'  THEN t2.name END) AS s1d1_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Mon'  THEN t2.name END) AS s1d2_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Tue'  THEN t2.name END) AS s1d3_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Wed'  THEN t2.name END) AS s1d4_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Thu'  THEN t2.name END) AS s1d5_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Fri'  THEN t2.name END) AS s1d6_name,
                  MAX(CASE WHEN t2.session_id = 1 and t2.day='Sat'  THEN t2.name END) AS s1d7_name,
                  
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Sun'  THEN t2.name END) AS s2d1_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Mon'  THEN t2.name END) AS s2d2_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Tue'  THEN t2.name END) AS s2d3_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Wed'  THEN t2.name END) AS s2d4_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Thu'  THEN t2.name END) AS s2d5_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Fri'  THEN t2.name END) AS s2d6_name,
                  MAX(CASE WHEN t2.session_id = 2 and t2.day='Sat'  THEN t2.name END) AS s2d7_name,
                  
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Sun'  THEN t2.name END) AS s3d1_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Mon'  THEN t2.name END) AS s3d2_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Tue'  THEN t2.name END) AS s3d3_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Wed'  THEN t2.name END) AS s3d4_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Thu'  THEN t2.name END) AS s3d5_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Fri'  THEN t2.name END) AS s3d6_name,
                  MAX(CASE WHEN t2.session_id = 3 and t2.day='Sat'  THEN t2.name END) AS s3d7_name
                  

                FROM tickets AS t1
                LEFT JOIN ticket_session_names AS t2 ON t1.id = t2.ticket_id
                -- LEFT JOIN ticket_prizes AS t3 ON t1.id = t3.ticket_id AND t2.session_id = t3.session_id

                GROUP BY 
                  t1.id, t1.name, t1.rate
                """
                       
        self.cursor.execute(query)
        self.connection.commit()
        return self.cursor.fetchall()
        
        
    def add_ticket(self,name,rate,da,p):
        self.cursor.execute(""" insert into tickets (user_id,name,is_active,rate,created_at,updated_at) values(%s,%s,%s,%s,CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) """,(6,name,1,rate))
        t_id = self.cursor.lastrowid
        
        day_query = """
                INSERT INTO ticket_session_names (ticket_id, session_id, day,name, created_at, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
        prize_query = """
                INSERT INTO ticket_prizes (ticket_id, session_id,sr_no, amount,super_amount,special_amount, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s,%s,CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """

        k=1
        for i in da:
            for day,v in i.items():
                self.cursor.execute(day_query, (t_id, k, day,v))
            k=k+1
                
        for i in range(1,4):
            for j in range(6):
                self.cursor.execute(prize_query, (t_id, i,j, p[i-1]['pvt'][j],p[i-1]['bonus'][j],p[i-1]['inc'][j]))
                
        self.connection.commit()
        
    def update_ticket(self, ticket_id, name, rate, da, p):
        # 1. Update the ticket's main details
        update_ticket_query = """
            UPDATE tickets SET name = %s, rate = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """
        self.cursor.execute(update_ticket_query, (name, rate, ticket_id))

        # 2. Delete existing session names and prizes
        self.cursor.execute("DELETE FROM ticket_session_names WHERE ticket_id = %s", (ticket_id,))
        self.cursor.execute("DELETE FROM ticket_prizes WHERE ticket_id = %s", (ticket_id,))

        # 3. Re-insert updated session names (days)
        day_query = """
            INSERT INTO ticket_session_names (ticket_id, session_id, day, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        k = 1
        for session_data in da:
            for day, val in session_data.items():
                self.cursor.execute(day_query, (ticket_id, k, day, val))
            k += 1

        # 4. Re-insert updated prizes
        prize_query = """
            INSERT INTO ticket_prizes (ticket_id, session_id, sr_no, amount, super_amount, special_amount, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        for i in range(1, 4):  # session_id: 1 = MOR, 2 = DAY, 3 = EVE
            for j in range(6):  # PVT1 to PVT6
                self.cursor.execute(prize_query, (
                    ticket_id,
                    i,
                    j,
                    p[i-1]['pvt'][j],
                    p[i-1]['bonus'][j],
                    p[i-1]['inc'][j]
                ))

        self.connection.commit()

        
    def update_user(self, uid,name,password,company_name,incentive,username,rate,mor,day,eve):
        query_user = """
        UPDATE users 
        SET name = %s, company_name = %s, email = %s,rate = %s,incentive=%s,pass=%s
        WHERE id = %s 
        """
        values_user = (name, company_name, username, rate,incentive,password, uid)
        
        query_dis = """
        UPDATE userrate
        SET rate = %s
        where user_id = %s and session_id = %s
        """
       

        try:
            self.cursor.execute(query_user, values_user)
            
            for session_id, session_rate in [(1, mor), (2, day), (3, eve)]:
                self.cursor.execute(query_dis, (session_rate, uid, session_id))
            
            self.connection.commit()
            print(f"User {name} updated successfully!")
            return True
                
        except Exception as e:
            print(f"Error updating user: {e}")
            return False



class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Page")
        self.setFixedSize(1000, 500)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)

        # === Left Panel ===
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #ffb2f3, stop:1 #ffd6fd);
        """)
        left_layout = QVBoxLayout(left_panel)

        image_label = QLabel()
        pixmap = QPixmap("game_image.png")  # Replace with your image file
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)

        left_layout.addStretch()
        left_layout.addWidget(image_label)
        left_layout.addStretch()

        # === Right Panel ===
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #8d4b8c; color: white;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(60, 40, 60, 40)

        title = QLabel("Welcome Back!")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))

        subtitle = QLabel("Don’t have an account yet? <a href='#' style='color:#d0bfff;'>Sign Up</a>")
        subtitle.setOpenExternalLinks(True)
        subtitle.setFont(QFont("Segoe UI", 10))

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("background-color: white; color: black; padding: 12px; border-radius: 8px; font-size: 14px;")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("background-color: white; color: black; padding: 12px; border-radius: 8px; font-size: 14px;")

        # Options row (checkbox + link)
        self.checkbox = QCheckBox("Keep me logged in")
        self.checkbox.setStyleSheet("color: white;")

        forgot = QLabel("<a href='#' style='color:#d0bfff;'>Forgot Password?</a>")
        forgot.setOpenExternalLinks(True)
        forgot.setFont(QFont("Segoe UI", 10))
        options_row = QHBoxLayout()
        options_row.addWidget(self.checkbox)
        options_row.addStretch()
        options_row.addWidget(forgot)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.check_login)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #98a3ff;
                color: white;
                padding: 12px;
                font-size: 16px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7c8dff;
            }
        """)

        right_layout.addWidget(title)
        right_layout.addWidget(subtitle)
        right_layout.addSpacing(15)
        right_layout.addWidget(self.username)
        right_layout.addWidget(self.password)
        right_layout.addLayout(options_row)
        right_layout.addSpacing(10)
        right_layout.addWidget(login_btn)
        right_layout.addStretch()

        # Add both panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # In init_ui of LoginPage
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    session = json.load(f)
                    if session.get("keep_logged_in"):
                        self.username.setText(session.get("username", ""))
                        self.password.setText(session.get("password", ""))
                        self.checkbox.setChecked(True)
            except Exception as e:
                print("Error reading session file:", e)


    def check_login(self):
        username = self.username.text()
        password = self.password.text()
        data = self.db.verify_admin(username, password)

        if data is not None:
            # ✅ Save credentials if checkbox is checked
            if self.checkbox.isChecked():
                with open("session.json", "w") as f:
                    json.dump({
                        "username": username,
                        "password": password,
                        "keep_logged_in": True
                    }, f)
            else:
                if os.path.exists("session.json"):
                    os.remove("session.json")

            self.hide()
            self.admin_panel = AdminPanel(username, data)
            self.admin_panel.show()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid credentials")

        
class AddDistributorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Distributor")
        self.setFixedSize(900, 600)
        self.setStyleSheet("background-color: #e6ccff;")  # 🌸 Light Purple BG
        self.db = Database()
        self.setup_ui()

    def setup_ui(self):
        

        # 🌟 Main layout
        main_layout = QVBoxLayout(self)

        # 🟨 White Box Form
        white_box = QWidget()
        white_box.setStyleSheet("background-color: #e6ccff; border-radius: 5px;")
        white_layout = QVBoxLayout(white_box)

        # 🔷 Heading
        heading = QLabel("The Field Labels Marked With * Are Required Input Fields.")
        heading.setFont(QFont("Segoe UI", 10, QFont.Bold))
        heading.setStyleSheet("color: #333; margin-top: 10px;")
        white_layout.addWidget(heading)

        # 📋 Grid layout for form
        grid = QGridLayout()
        grid.setSpacing(10)

        def field(label, default_text=""):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #222;")
            line = QLineEdit()
            line.setText(default_text)
            line.setStyleSheet("background-color: white; padding: 5px; color: black;")
            return lbl, line

        # First row
        name_lbl, self.name_input = field("Name *", "Type Name")
        comp_lbl, self.comp_input = field("Company Name *")
        grid.addWidget(name_lbl, 0, 0)
        grid.addWidget(self.name_input, 0, 1)
        grid.addWidget(comp_lbl, 0, 2)
        grid.addWidget(self.comp_input, 0, 3)

        # Second row
        inc_lbl, self.inc_input = field("Incentive *")
        rate_lbl, self.rate_input = field("Rate *")
        grid.addWidget(inc_lbl, 1, 0)
        grid.addWidget(self.inc_input, 1, 1)
        grid.addWidget(rate_lbl, 1, 2)
        grid.addWidget(self.rate_input, 1, 3)

        white_layout.addLayout(grid)

        # 🔹 Sub-heading
        sub_heading = QLabel("Create the dealer credentials:")
        sub_heading.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        white_layout.addWidget(sub_heading)

        # Third row
        cred_grid = QGridLayout()
        user_lbl, self.user_input = field("User *", "nagaland@gmail.com")
        pass_lbl, self.pass_input = field("Password *")
        self.pass_input.setEchoMode(QLineEdit.Password)
        cred_grid.addWidget(user_lbl, 2, 0)
        cred_grid.addWidget(self.user_input, 2, 1)
        cred_grid.addWidget(pass_lbl, 2, 2)
        cred_grid.addWidget(self.pass_input, 2, 3)

        white_layout.addLayout(cred_grid)

        # 🔘 Session Wise Report Label
        session_label = QLabel("Session Wise Report *")
        session_label.setStyleSheet("color: #333; font-weight: bold; margin-top: 10px;")
        white_layout.addWidget(session_label)

        # Fourth row: MOR / DAY / EVE
        session_grid = QGridLayout()
        mor_lbl, self.mor_input = field("MOR *")
        day_lbl, self.day_input = field("DAY *")
        eve_lbl, self.eve_input = field("EVE *")
        session_grid.addWidget(mor_lbl, 0, 0)
        session_grid.addWidget(self.mor_input, 0, 1)
        session_grid.addWidget(day_lbl, 0, 2)
        session_grid.addWidget(self.day_input, 0, 3)
        session_grid.addWidget(eve_lbl, 1, 0)
        session_grid.addWidget(self.eve_input, 1, 1)

        white_layout.addLayout(session_grid)
        main_layout.addWidget(white_box)

        # Validators
        int_validator = QDoubleValidator(0.00, 9999.99, 2)
        self.rate_input.setValidator(int_validator)
        self.inc_input.setValidator(int_validator)
        self.mor_input.setValidator(int_validator)
        self.day_input.setValidator(int_validator)
        self.eve_input.setValidator(int_validator)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        create_btn = QPushButton("Create")
        close_btn.setStyleSheet("padding: 6px 16px;")
        create_btn.setStyleSheet("padding: 6px 16px; background-color: #28a745; color: white;")
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(create_btn)
        close_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.create_distributor)

        main_layout.addLayout(btn_layout)

    def create_distributor(self):
        import re
        name = self.name_input.text()
        password = self.pass_input.text()
        company_name = self.comp_input.text()
        incentive = self.inc_input.text()
        username = self.user_input.text()
        rate = self.rate_input.text()
        mor = self.mor_input.text()
        day = self.day_input.text()
        eve = self.eve_input.text()


        # Validate required fields
        fields = [
            name,password,company_name,incentive,username,rate,mor,day,eve
        ]
        for field in fields:
            if not field:
                QMessageBox.warning(self, "Missing Field", "All fields are required.")
                return
        
        if not re.match(r"^[a-zA-Z0-9()\s]*$", name.strip()):
            QMessageBox.warning(self, "Input Error", "Name can only contain letters, numbers, spaces, and parentheses.")
            return

        if not re.match(r"^[a-zA-Z0-9@.]+$", username.strip()) or ' ' in username.strip():
            QMessageBox.warning(self, "Input Error", "User must contain only letters, numbers, '@', and '.' without spaces.")
            return
        
        self.db.add_user(name,password,company_name,incentive,username,rate,mor,day,eve)
        QMessageBox.information(self, "Success", "User added successfully!")
        self.accept()
 
class ModifyDistributorDialog(QDialog):
    def __init__(self, parent,user_data):
        super().__init__(parent)
        self.setWindowTitle("Modify Distributor")
        self.setFixedSize(900, 600)
        self.setStyleSheet("background-color: #e6ccff;")  # 🌸 Light Purple BG
        self.db = Database()
        self.uid,self.inc,self.rate,self.user,self.password,self.name,self.cname,self.mor,self.day,self.eve =user_data
        self.setup_ui()

    def setup_ui(self):
        

        # 🌟 Main layout
        main_layout = QVBoxLayout(self)

        # 🟨 White Box Form
        white_box = QWidget()
        white_box.setStyleSheet("background-color: #e6ccff; border-radius: 5px;")
        white_layout = QVBoxLayout(white_box)

        # 🔷 Heading
        heading = QLabel("The Field Labels Marked With * Are Required Input Fields.")
        heading.setFont(QFont("Segoe UI", 10, QFont.Bold))
        heading.setStyleSheet("color: #333; margin-top: 10px;")
        white_layout.addWidget(heading)

        # 📋 Grid layout for form
        grid = QGridLayout()
        grid.setSpacing(10)

        def field(label, default_text=""):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #222;")
            line = QLineEdit()
            line.setText(default_text)
            line.setStyleSheet("background-color: white; padding: 5px; color: black;")
            return lbl, line

        # First row
        name_lbl, self.name_input = field("Name *", self.name)
        comp_lbl, self.comp_input = field("Company Name *",self.cname)
        grid.addWidget(name_lbl, 0, 0)
        grid.addWidget(self.name_input, 0, 1)
        grid.addWidget(comp_lbl, 0, 2)
        grid.addWidget(self.comp_input, 0, 3)

        # Second row
        inc_lbl, self.inc_input = field("Incentive *",str(self.inc))
        rate_lbl, self.rate_input = field("Rate *",str(self.rate))
        grid.addWidget(inc_lbl, 1, 0)
        grid.addWidget(self.inc_input, 1, 1)
        grid.addWidget(rate_lbl, 1, 2)
        grid.addWidget(self.rate_input, 1, 3)

        white_layout.addLayout(grid)

        # 🔹 Sub-heading
        sub_heading = QLabel("Create the dealer credentials:")
        sub_heading.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        white_layout.addWidget(sub_heading)

        # Third row
        cred_grid = QGridLayout()
        user_lbl, self.user_input = field("User *",self.user)
        pass_lbl, self.pass_input = field("Password *",self.password)
        self.pass_input.setEchoMode(QLineEdit.Password)
        cred_grid.addWidget(user_lbl, 2, 0)
        cred_grid.addWidget(self.user_input, 2, 1)
        cred_grid.addWidget(pass_lbl, 2, 2)
        cred_grid.addWidget(self.pass_input, 2, 3)

        white_layout.addLayout(cred_grid)

        # 🔘 Session Wise Report Label
        session_label = QLabel("Session Wise Report *")
        session_label.setStyleSheet("color: #333; font-weight: bold; margin-top: 10px;")
        white_layout.addWidget(session_label)

        # Fourth row: MOR / DAY / EVE
        session_grid = QGridLayout()
        mor_lbl, self.mor_input = field("MOR *",str(self.mor))
        day_lbl, self.day_input = field("DAY *",str(self.day))
        eve_lbl, self.eve_input = field("EVE *",str(self.eve))
        session_grid.addWidget(mor_lbl, 0, 0)
        session_grid.addWidget(self.mor_input, 0, 1)
        session_grid.addWidget(day_lbl, 0, 2)
        session_grid.addWidget(self.day_input, 0, 3)
        session_grid.addWidget(eve_lbl, 1, 0)
        session_grid.addWidget(self.eve_input, 1, 1)

        white_layout.addLayout(session_grid)
        main_layout.addWidget(white_box)

        # Validators
        int_validator = QDoubleValidator(0.00, 9999.99, 2)
        self.rate_input.setValidator(int_validator)
        self.inc_input.setValidator(int_validator)
        self.mor_input.setValidator(int_validator)
        self.day_input.setValidator(int_validator)
        self.eve_input.setValidator(int_validator)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        create_btn = QPushButton("Update")
        close_btn.setStyleSheet("padding: 6px 16px;")
        create_btn.setStyleSheet("padding: 6px 16px; background-color: orange; color: black;")
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(create_btn)
        close_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.update_distributor)

        main_layout.addLayout(btn_layout) 
        
    def update_distributor(self):
        import re
        name = self.name_input.text()
        password = self.pass_input.text()
        company_name = self.comp_input.text()
        incentive = self.inc_input.text()
        username = self.user_input.text()
        rate = self.rate_input.text()
        mor = self.mor_input.text()
        day = self.day_input.text()
        eve = self.eve_input.text()


        # Validate required fields
        fields = [
            name,password,company_name,incentive,username,rate,mor,day,eve
        ]
        for field in fields:
            if not field:
                QMessageBox.warning(self, "Missing Field", "All fields are required.")
                return
        
        if not re.match(r"^[a-zA-Z0-9()\s]*$", name.strip()):
            QMessageBox.warning(self, "Input Error", "Name can only contain letters, numbers, spaces, and parentheses.")
            return

        if not re.match(r"^[a-zA-Z0-9@.]+$", username.strip()) or ' ' in username.strip():
            QMessageBox.warning(self, "Input Error", "User must contain only letters, numbers, '@', and '.' without spaces.")
            return
        
        self.db.update_user(self.uid,name,password,company_name,incentive,username,rate,mor,day,eve)
        QMessageBox.information(self, "Success", "User updated successfully!")
        self.accept()

class AddTicketDialog(QDialog):
    def __init__(self, parent=None):
        super(AddTicketDialog, self).__init__(parent)
        self.setWindowTitle("Add Ticket")
        self.setMinimumWidth(500)
        self.setStyleSheet("background-color: #e6ccff;")
        self.db = Database()

        self.session_stack = QStackedWidget()
        self.session_forms = {}  # To hold widgets per session
        self.layout = QVBoxLayout()
        self.title = QLabel("The Field Labels Marked With * Are Required Input Fields.")
        self.title.setStyleSheet("color: Red; font-weight: bold;")
        self.layout.addWidget(self.title)
        self.build_form()
        self.setLayout(self.layout)

    def build_form(self):
        # Basic user input
        form = QGridLayout()
        self.name_input = QLineEdit()
        rate_validator = QDoubleValidator(0.0, 999999.99, 2)
        self.rate_input = QLineEdit()
        self.rate_input.setValidator(rate_validator)
        name_validator = QRegExpValidator(QRegExp("^[A-Za-z0-9 ]+$"))
        self.name_input.setPlaceholderText("Enter Your Name")
        self.name_input.setValidator(name_validator)
        self.rate_input.setPlaceholderText("Enter Rate")
        self.name_input.setStyleSheet("background-color: white; padding: 5px; color: black;")
        self.rate_input.setStyleSheet("background-color: white; padding: 5px; color: black;")

        form.addWidget(QLabel("Name *"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Rate *"), 0, 2)
        form.addWidget(self.rate_input, 0, 3)
        self.layout.addLayout(form)

        # Session buttons
        session_btns = QHBoxLayout()
        session_btns.addSpacing(0)
        for idx, (label, color) in enumerate([("MOR", "#FF4500"), ("DAY", "#FFA500"), ("EVE", "#DC143C")]):
            btn = QPushButton(label)
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold;")
            btn.setFixedSize(80, 30)
            btn.clicked.connect(lambda _, i=idx: self.session_stack.setCurrentIndex(i))
            session_btns.addWidget(btn)

        all_btn = QPushButton("ALL")
        all_btn.setStyleSheet("background-color: #32CD32; color: white; font-weight: bold;")
        all_btn.setFixedSize(80, 30) 
        all_btn.clicked.connect(self.copy_all_to_all_sessions)
        session_btns.addWidget(all_btn)
        self.layout.addLayout(session_btns)
        
        self.t = QLabel("Days")
        self.t.setStyleSheet("color: black; font-weight: bold;font-size: 21px;")
        self.layout.addWidget(self.t)

        # Stack for each session form (MOR, DAY, EVE)
        for session in ["MOR", "DAY", "EVE"]:
            widget = self.build_session_form(session)
            self.session_stack.addWidget(widget)
            self.session_forms[session] = widget

        self.layout.addWidget(self.session_stack)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Close")
        create_btn = QPushButton("Create")
        create_btn.setStyleSheet("padding: 6px 16px; background-color: #28a745; color: white;")
        close_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.collect_and_save)
        bottom_layout.addWidget(close_btn)
        bottom_layout.addWidget(create_btn)
        self.layout.addLayout(bottom_layout)

    def build_session_form(self, session):
        frame = QWidget()
        layout = QVBoxLayout()

        # Day entries
        name_validator = QRegExpValidator(QRegExp("^[A-Za-z0-9 ]+$"))
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        day_inputs = {}
        day_grid = QGridLayout()
        for i, day in enumerate(days):
            lbl = QLabel(day)
            inp = QLineEdit()
            inp.setValidator(name_validator)
            inp.setPlaceholderText("Enter")
            inp.setStyleSheet("background-color: white; padding: 5px; color: black;")
            day_inputs[day] = inp
            row, col = divmod(i, 4)
            day_grid.addWidget(lbl, row, col*2)
            day_grid.addWidget(inp, row, col*2 + 1)

        layout.addLayout(day_grid)
        c=QHBoxLayout()
        title = QLabel("Prizes")
        title.setStyleSheet("color: black; font-weight: bold;font-size: 21px;")
        c.addWidget(title)
        c.addWidget(QLabel("PVT"))
        c.addWidget(QLabel("Bonus"))
        c.addWidget(QLabel("Incentive"))
        layout.addLayout(c)
        # Prize inputs
        
        prize_validator = QDoubleValidator(0.0, 999999.99, 2)

        
        prize_grid = QGridLayout()
        prize_inputs = {}
        for i in range(6):
            pvt = QLineEdit(); pvt.setPlaceholderText("PVT")
            bonus = QLineEdit(); bonus.setPlaceholderText("Bonus")
            incentive = QLineEdit(); incentive.setPlaceholderText("Incentive")
            for field in (pvt, bonus, incentive):
                field.setStyleSheet("background-color: white; padding: 5px; color: black;")
                field.setValidator(prize_validator)
            prize_grid.addWidget(QLabel(f"PVT{i+1}"), i, 0)
            prize_grid.addWidget(pvt, i, 1)
            prize_grid.addWidget(bonus, i, 2)
            prize_grid.addWidget(incentive, i, 3)
            prize_inputs[f"PVT{i+1}"] = pvt
            prize_inputs[f"Bonus{i+1}"] = bonus
            prize_inputs[f"Incentive{i+1}"] = incentive

        layout.addLayout(prize_grid)

        frame.setLayout(layout)
        frame.day_inputs = day_inputs
        frame.prize_inputs = prize_inputs
        return frame

    def copy_all_to_all_sessions(self):
        base = self.session_forms["MOR"]
        for session in ["DAY", "EVE"]:
            target = self.session_forms[session]
            for day, inp in base.day_inputs.items():
                target.day_inputs[day].setText(inp.text())
            for key, inp in base.prize_inputs.items():
                target.prize_inputs[key].setText(inp.text())

    def collect_and_save(self):
        # Collect input and save logic here
        s=[]
        da=[]
        pr=[]
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
        if not self.rate_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Rate is required.")
            return
        for session, widget in self.session_forms.items():
            s.append(session)
            days={}
            for d, i in widget.day_inputs.items():
                if not i.text().strip():
                    QMessageBox.warning(self, "Validation Error", f"All days must be filled for session {session}.")
                    return
                days[d]=i.text()
            da.append(days)
                
            p={'pvt':[],'bonus':[],'inc':[]}
            for k, i in widget.prize_inputs.items():
                if not i.text().strip():
                    QMessageBox.warning(self, "Validation Error", f"All prize fields must be filled for session {session}.")
                    return
                if 'PVT' in k: 
                    p['pvt'].append(i.text())
                elif 'Bon' in k:
                    p['bonus'].append(i.text())
                else:
                    p['inc'].append(i.text())
            pr.append(p)
            
        # print(pr)
            
        self.db.add_ticket(self.name_input.text(),float(self.rate_input.text()),da,pr)
        QMessageBox.information(self, "Success", "ticket added successfully!")
        self.accept()

class ModifyTicketDialog(QDialog):
    def __init__(self, parent=None,ticket_data=None):
        super(ModifyTicketDialog, self).__init__(parent)
        self.setWindowTitle("Update Ticket")
        self.setMinimumWidth(500)
        self.setStyleSheet("background-color: #e6ccff;")
        self.db = Database()
        self.ticket_data = ticket_data
        
        self.session_stack = QStackedWidget()
        self.session_forms = {}  # To hold widgets per session
        self.layout = QVBoxLayout()
        self.title = QLabel("The Field Labels Marked With * Are Required Input Fields.")
        self.title.setStyleSheet("color: Red; font-weight: bold;")
        self.layout.addWidget(self.title)
        self.build_form()
        self.setLayout(self.layout)

    def build_form(self):
        # Basic user input
        form = QGridLayout()
        self.name_input = QLineEdit()
        rate_validator = QDoubleValidator(0.0, 999999.99, 2)
        self.rate_input = QLineEdit()
        self.rate_input.setValidator(rate_validator)
        name_validator = QRegExpValidator(QRegExp("^[A-Za-z0-9 ]+$"))
        self.name_input.setText(self.ticket_data['name'])
        self.name_input.setValidator(name_validator)
        self.rate_input.setText(str(self.ticket_data['rate']))
        self.name_input.setStyleSheet("background-color: white; padding: 5px; color: black;")
        self.rate_input.setStyleSheet("background-color: white; padding: 5px; color: black;")

        form.addWidget(QLabel("Name *"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Rate *"), 0, 2)
        form.addWidget(self.rate_input, 0, 3)
        self.layout.addLayout(form)

        # Session buttons
        session_btns = QHBoxLayout()
        for idx, (label, color) in enumerate([("MOR", "#FF4500"), ("DAY", "#FFA500"), ("EVE", "#DC143C")]):
            btn = QPushButton(label)
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold;")
            btn.setFixedSize(80, 30)
            btn.clicked.connect(lambda _, i=idx: self.session_stack.setCurrentIndex(i))
            session_btns.addWidget(btn)

        all_btn = QPushButton("ALL")
        all_btn.setStyleSheet("background-color: #32CD32; color: white; font-weight: bold;")
        all_btn.setFixedSize(80, 30)
        all_btn.clicked.connect(self.copy_all_to_all_sessions)
        session_btns.addWidget(all_btn)
        self.layout.addLayout(session_btns)
        
        self.t = QLabel("Days")
        self.t.setStyleSheet("color: black; font-weight: bold;font-size: 21px;")
        self.layout.addWidget(self.t)

        # Stack for each session form (MOR, DAY, EVE)
        for session in ['MOR', 'DAY', 'EVE']:
            widget = self.build_session_form(session)
            self.session_stack.addWidget(widget)
            self.session_forms[session] = widget

        self.layout.addWidget(self.session_stack)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Close")
        create_btn = QPushButton("Update")
        create_btn.setStyleSheet("padding: 6px 16px; background-color: orange; color: black;")
        close_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.collect_and_save)
        bottom_layout.addWidget(close_btn)
        bottom_layout.addWidget(create_btn)
        self.layout.addLayout(bottom_layout)

    def build_session_form(self, session):
        frame = QWidget()
        layout = QVBoxLayout()

        # Day entries
        name_validator = QRegExpValidator(QRegExp("^[A-Za-z0-9 ]+$"))
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        day_inputs = {}
        day_grid = QGridLayout()
        for i, day in enumerate(days):
            lbl = QLabel(day)
            inp = QLineEdit()
            inp.setValidator(name_validator)
            inp.setText(self.ticket_data['sessions'][session]['days'][day])
            inp.setStyleSheet("background-color: white; padding: 5px; color: black;")
            day_inputs[day] = inp
            row, col = divmod(i, 4)
            day_grid.addWidget(lbl, row, col*2)
            day_grid.addWidget(inp, row, col*2 + 1)

        layout.addLayout(day_grid)
         
        c=QHBoxLayout()
        title = QLabel("Prizes")
        title.setStyleSheet("color: black; font-weight: bold;font-size: 21px;")
        c.addWidget(title)
        c.addWidget(QLabel("PVT"))
        c.addWidget(QLabel("Bonus"))
        c.addWidget(QLabel("Incentive"))
        layout.addLayout(c)
        # Prize inputs
        
        prize_validator = QDoubleValidator(0.0, 999999.99, 2)

        
        prize_grid = QGridLayout()
        prize_inputs = {}
        for i in range(6):
            
            pvt = QLineEdit(); pvt.setText(self.ticket_data['sessions'][session]['prizes']['pvt'][i])
            bonus = QLineEdit(); bonus.setText(self.ticket_data['sessions'][session]['prizes']['bonus'][i])
            incentive = QLineEdit(); incentive.setText(self.ticket_data['sessions'][session]['prizes']['inc'][i])
            for field in (pvt, bonus, incentive):
                field.setStyleSheet("background-color: white; padding: 5px; color: black;")
                field.setValidator(prize_validator)
            prize_grid.addWidget(QLabel(f"PVT{i+1}"), i, 0)
            prize_grid.addWidget(pvt, i, 1)
            prize_grid.addWidget(bonus, i, 2)
            prize_grid.addWidget(incentive, i, 3)
            prize_inputs[f"PVT{i+1}"] = pvt
            prize_inputs[f"Bonus{i+1}"] = bonus
            prize_inputs[f"Incentive{i+1}"] = incentive

        layout.addLayout(prize_grid)

        frame.setLayout(layout)
        frame.day_inputs = day_inputs
        frame.prize_inputs = prize_inputs
        return frame

    def copy_all_to_all_sessions(self):
        base = self.session_forms["MOR"]
        for session in ["DAY", "EVE"]:
            target = self.session_forms[session]
            for day, inp in base.day_inputs.items():
                target.day_inputs[day].setText(inp.text())
            for key, inp in base.prize_inputs.items():
                target.prize_inputs[key].setText(inp.text())

    def collect_and_save(self):
        # Collect input and save logic here
        s=[]
        da=[]
        pr=[]
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
        if not self.rate_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Rate is required.")
            return
        for session, widget in self.session_forms.items():
            s.append(session)
            days={}
            for d, i in widget.day_inputs.items():
                if not i.text().strip():
                    QMessageBox.warning(self, "Validation Error", f"All days must be filled for session {session}.")
                    return
                days[d]=i.text()
            da.append(days)
                
            p={'pvt':[],'bonus':[],'inc':[]}
            for k, i in widget.prize_inputs.items():
                if not i.text().strip():
                    QMessageBox.warning(self, "Validation Error", f"All prize fields must be filled for session {session}.")
                    return
                if 'PVT' in k: 
                    p['pvt'].append(i.text())
                elif 'Bon' in k:
                    p['bonus'].append(i.text())
                else:
                    p['inc'].append(i.text())
            pr.append(p)
            
        # print(pr)
            
        self.db.update_ticket(self.ticket_data['id'],self.name_input.text(),float(self.rate_input.text()),da,pr)
        QMessageBox.information(self, "Success", "ticket updated successfully!")
        self.accept()
        
class TrackingLineEdit(QLineEdit):
    def __init__(self, table, row, col, value_store, parent=None):
        super().__init__(parent)
        self.table = table
        self.row = row
        self.col = col
        self.value_store = value_store

    def focusOutEvent(self, event):
        self.value_store[self.col] = self.text()
        super().focusOutEvent(event)


# 🔹 Custom Delegate that installs TrackingLineEdit and listens for Enter
class EditDelegate(QStyledItemDelegate):
    def __init__(self, table, value_store,admin_panel, parent=None):
        super().__init__(parent)
        self.table = table
        self.value_store = value_store
        self.admin_panel = admin_panel

    def createEditor(self, parent, option, index):
        row = index.row()
        col = index.column()

        editor = TrackingLineEdit(self.table, row, col, self.value_store, parent)

        def commit_and_save():
            # print("enter pressed cs")
            self.value_store[col] = editor.text()
            self.commitData.emit(editor)
            self.closeEditor.emit(editor)
            QTimer.singleShot(0, lambda: self.save_row(row))

        editor.returnPressed.connect(commit_and_save)
        return editor

    # def save_row(self, row):
        # # print("enter pressed")
        # print(self.value_store)
        # self.table.clearSelection()
        
    def save_row(self, row):
        self.table.clearSelection()
        
        try:
            uid_item = self.table.item(row, 0)
            uid = uid_item.data(Qt.UserRole) if uid_item else None
            if uid is None:
                raise ValueError("User ID not found")

            # uid_item = self.table.item(row, 0)
            # uid = int(uid_item.text()) if uid_item and uid_item.text().isdigit() else None
            # if uid is None:
                # raise ValueError("Invalid user ID")

            name = self.table.item(row, 2).text().strip()
            company_name = self.table.item(row, 3).text().strip()

            mor_text = self.table.item(row, 4).text().strip()
            day_text = self.table.item(row, 5).text().strip()
            eve_text = self.table.item(row, 6).text().strip()

            # Validate float conversion
            try:
                mor = float(mor_text)
                day = float(day_text)
                eve = float(eve_text)
            except ValueError:
                QMessageBox.warning(self.table, "Input Error", "MOR, DAY, and EVE values must be numbers.")
                return

            # Fetch required fields from DB
            db = Database()
            db.cursor.execute("SELECT email, pass, rate, incentive FROM users WHERE id=%s", (uid,))
            result = db.cursor.fetchone()
            if not result:
                raise ValueError("User not found in database")

            email, password, rate, incentive = result

            success = db.update_user(uid, name, password, company_name, incentive, email, rate, mor, day, eve)

            if success:
                print(" Reloading user table manually")
                # self.table.setRowCount(0)
                
                self.admin_panel.load_users()
                



        except Exception as e:
            QMessageBox.critical(self.table, "Update Error", f"Failed to update user: {e}")
            print(f"Error in save_row: {e}")


        
class FiveDigitDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMaxLength(5)
        editor.setValidator(QIntValidator(0, 99999, editor))
        editor.editingFinished.connect(lambda: self.auto_complete_to(editor, index))
        return editor

    def auto_complete_to(self, editor, index):
        if index.column() == 2:
            model_parent = index.model().parent()

            if not isinstance(model_parent, QTableWidget):
                print("Unexpected model parent:", model_parent)
                return

            table = model_parent
            row = index.row()
            to_val = editor.text().strip()

            if len(to_val) == 2:
                from_item = table.item(row, 1)
                if from_item and len(from_item.text()) == 5:
                    from_val = from_item.text()
                    completed = from_val[:3] + to_val

                    if int(completed) <= int(from_val):
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("TO must be greater than FROM.")
                        msg.setWindowTitle("Invalid TO Entry")
                        msg.exec_()
                        table.blockSignals(True)
                        table.setItem(row, 2, QTableWidgetItem(""))
                        table.blockSignals(False)
                        return

                    table.blockSignals(True)
                    table.setItem(row, 2, QTableWidgetItem(completed))
                    table.blockSignals(False)

                    # Manually trigger your row calc
                    table.cellChanged.emit(row, 2)



class AdminPanel(QWidget):
    def __init__(self, name, data):
        super().__init__()
        self.setWindowTitle("Admin Panel")
        self.setGeometry(200, 100, 1000, 600)
        self.db = Database()
        self.resize(1200, 800)
        self.name = name
        self.data = data
        if self.data[8] == 1:
            self.role = 'Admin'
        elif self.data[8] == 2:
            self.role = 'Distributer'
        elif self.data[8] == 3:
            self.role = 'Dealer'
        else:
            return

        self.page_widgets = {}
        self.value_store = {}
        

        self.init_ui()

    def init_ui(self):
        # 🌈 Gradient Background
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#00d6ff"))  # Soft sky blue
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        main_layout = QVBoxLayout()

        # 👤 Header Info
        self.header_label = QLabel(f"👤 {self.name} ({self.role})")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: white;
        """)
        # header_layout = QHBoxLayout()
        # header_layout.addWidget(self.header_label)
        # header_widget = QWidget()
        # header_widget.setLayout(header_layout)

        # 🌟 Menu Bar
        self.nav_bar_layout = QHBoxLayout()
        self.nav_bar_layout.setSpacing(20)
        self.nav_bar_layout.setContentsMargins(10, 10, 10, 10)
        simple_style = """
            QToolButton {
                background-color: blue;
                border: none;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 12px;
                color: white;
            }
            QToolButton::menu-indicator {
                image: none;
            }
            QToolButton::hover {
                color: #007ACC;
            }
        """

        # 🔽 Master Menu
        master_btn = QToolButton()
        master_btn.setText("Master Data")
        master_btn.setPopupMode(QToolButton.InstantPopup)
        master_menu = QMenu()
        add_distributer_action = QAction("Add Distributer", self)
        add_tickets_action = QAction("Add Tickets", self)
        master_menu.addAction(add_distributer_action)
        master_menu.addAction(add_tickets_action)
        master_btn.setMenu(master_menu)
        master_btn.setStyleSheet(simple_style)
        self.nav_bar_layout.addWidget(master_btn)

        # 🔽 Transactions Menu
        trans_btn = QToolButton()
        trans_btn.setText("Transactions")
        trans_btn.setPopupMode(QToolButton.InstantPopup)
        trans_menu = QMenu()
        credit_action = QAction("Credit Purchase", self)
        sale_action = QAction("Sale List", self)
        unsold_action = QAction("Unsold", self)
        trans_menu.addAction(credit_action)
        trans_menu.addAction(sale_action)
        trans_menu.addAction(unsold_action)
        trans_btn.setMenu(trans_menu)
        trans_btn.setStyleSheet(simple_style)
        self.nav_bar_layout.addWidget(trans_btn)
        self.nav_bar_layout.addStretch() 
        self.nav_bar_layout.addWidget(self.header_label)
        

        # 🚪 Exit Button
        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; background: none; border: none; }")
        exit_btn.clicked.connect(self.confirm_exit)
        exit_btn.setShortcut("Esc")
        # self.nav_bar_layout.addStretch()
        self.nav_bar_layout.addWidget(exit_btn)

        nav_bar_widget = QWidget()
        nav_bar_widget.setLayout(self.nav_bar_layout)
        nav_bar_widget.setStyleSheet("background-color: blue")

        # 🔄 Stackable Content
        self.pages = QStackedWidget()
        self.add_page("home", self.create_user_management_page())
        self.add_page("add_distributer", self.create_user_management_page())
        self.add_page("add_tickets", self.create_ticket_management_page())
        self.add_page("credit",self.credit_purchase())
        self.add_page("sale", self.sale_list())
        self.add_page("unsold", QLabel("📦 Unsold Tickets Page"))

        # 🔗 Connect Menus to Pages
        add_distributer_action.triggered.connect(lambda: self.switch_page("add_distributer"))
        add_tickets_action.triggered.connect(lambda: self.switch_page("add_tickets"))
        credit_action.triggered.connect(lambda: self.switch_page("credit"))
        sale_action.triggered.connect(lambda: self.switch_page("sale"))
        unsold_action.triggered.connect(lambda: self.switch_page("unsold"))

        # 🧩 Final Layout
        # main_layout.addWidget(header_widget)
        main_layout.addWidget(nav_bar_widget)
        main_layout.addWidget(self.pages, stretch=1)

        self.setLayout(main_layout)
        self.switch_page("home")  # default
    def confirm_exit(self):
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.close()

    def add_page(self, name, widget):
        # widget.setAlignment(Qt.AlignCenter)
        self.pages.addWidget(widget)
        self.page_widgets[name] = widget

    def switch_page(self, name):
        if name in self.page_widgets:
            self.pages.setCurrentWidget(self.page_widgets[name])
        else:
            print(f"[Error] Page '{name}' not found.")
            
    
            
            
    def create_user_management_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.add_user_btn = QPushButton(" + Add Distributer")
        self.add_user_btn.setObjectName("openPopupButton")
        self.add_user_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
        self.add_user_btn.clicked.connect(self.open_add_user_dialog)
        
        layout.addWidget(self.add_user_btn,alignment=Qt.AlignLeft)
 
    
        self.user_table = QTableWidget(0, 8)
        self.user_table.setMaximumWidth(1178)
        self.user_table.setHorizontalHeaderLabels(["SrNo", "Code", "Name", "Company Name", "MOR", "DAY", "EVE", "Action"])
        self.user_table.setObjectName("userTable")

        # ✅ Set full table editable by default
        self.user_table.setEditTriggers(QTableWidget.AllEditTriggers)

        # ✅ Set selection behavior: row-based
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)

        # ✅ Table styling
        self.user_table.setStyleSheet("""
                QTableWidget {
                    background-color:#c8ffe0;  /* Light sky blue table background */
                    border: none;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background-color: #fffdd0;  /* Cream color */
                    color: #0055aa;             /* Blue text */
                    font-weight: bold;
                    padding: 4px;
                    border: 1px solid #ccc;
                }
                QTableWidget::item {
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: red;
                    color: white;
                }
                QTableWidget::item:focus {
                    background-color: white;
                    color: black;
                }
            """)

        # Allow users to manually resize columns
        
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.user_table.setItemDelegate(EditDelegate(self.user_table, self.value_store))
        self.user_table.setItemDelegate(EditDelegate(self.user_table, self.value_store, self))

        
        

        header = self.user_table.horizontalHeader()
        header.setStretchLastSection(False) 

        ratios = [4, 10,40, 25,8, 8, 8, 13] 
        total = sum(ratios)

        for i, val in enumerate(ratios):
            self.user_table.setColumnWidth(i, val * 10)
        
        
        table_container = QHBoxLayout()
        
        table_container.addWidget(self.user_table)
       
        # Add this to your main layout
        layout.addLayout(table_container)
        info_layout = QHBoxLayout()
        button_defs = [
            "Save (Enter)", "Import (F4)", "Exit (Esc)"
        ]

        for text in button_defs:
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(30)
            label.setFont(QFont("Arial", 9, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    background-color: #fffdd0;
                    border: 1px solid black;
                    
                    color: black;
                }
            """)
            label.setFixedWidth(150)
            info_layout.addWidget(label)

        layout.addLayout(info_layout)
        widget.setLayout(layout)
        
       
        self.user_table.blockSignals(True)
        self.load_users()
        self.user_table.blockSignals(False)
          
        return widget
        
    
        
       
    
        
    def create_ticket_management_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.add_ticket_btn = QPushButton(" + Add Ticket")
        self.add_ticket_btn.setObjectName("openPopupButton")
        self.add_ticket_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
        self.add_ticket_btn.clicked.connect(self.open_add_ticket_dialog)
        layout.addWidget(self.add_ticket_btn,alignment=Qt.AlignLeft)
 
    
        self.ticket_table = QTableWidget(0, 3)
        self.ticket_table.setMaximumWidth(590)
        self.ticket_table.setHorizontalHeaderLabels([ "SrNo","Ticket Name", "Action"])
        self.ticket_table.setObjectName("ticketTable")
        self.ticket_table.setEditTriggers(QTableWidget.AllEditTriggers)

        # ✅ Set selection behavior: row-based
        self.ticket_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ticket_table.setStyleSheet("""
                QTableWidget {
                    background-color:#c8ffe0;  /* Light sky blue table background */
                    border: none;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background-color: #fffdd0;  /* Cream color */
                    color: #0055aa;             /* Blue text */
                    font-weight: bold;
                    padding: 4px;
                    border: 1px solid #ccc;
                }
                QTableWidget::item {
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: red;
                    color: white;
                }
                QTableWidget::item:focus {
                    background-color: white;
                    color: black;
                }
            """)


        self.ticket_table.verticalHeader().setVisible(False)
        self.ticket_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.ticket_table.setItemDelegate(EditDelegate(self.user_table, self.value_store))
        
        

        header = self.ticket_table.horizontalHeader()
        header.setStretchLastSection(False) 

        ratios = [4,40, 13] 
        total = sum(ratios)

        for i, val in enumerate(ratios):
            self.ticket_table.setColumnWidth(i, val * 10)

        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(self.ticket_table)
        table_container.addStretch()


        layout.addLayout(table_container)
        info_layout = QHBoxLayout()
        button_defs = [
            "Save (Enter)", "Import (F4)", "Exit (Esc)"
        ]

        for text in button_defs:
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(30)
            label.setFont(QFont("Arial", 9, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    background-color: #fffdd0;
                    border: 1px solid black;
                    
                    color: black;
                }
            """)
            label.setFixedWidth(150)
            info_layout.addWidget(label)

        layout.addLayout(info_layout)

        widget.setLayout(layout)
        self.load_tickets()
        return widget
        
    

        
    def credit_purchase(self):
        
        session_timer = QTimer(self)
        session_end_time = None  # Needs to be accessible by both nested functions

        def start_session_countdown():
            session = session_dropdown.currentText().lower()

            selected_date = date_edit.date()
            current_date = QDate.currentDate()

            # ✅ Only run countdown if selected date is today
            if selected_date != current_date:
                session_timer.stop()
                session_timer_label.setText("Session Ends")
                return

            now = QDateTime.currentDateTime()

            if session == "m":
                end_time = QTime(13, 0, 0)  # 1 PM
            elif session == "d":
                end_time = QTime(16, 0, 0)  # 4 PM
            elif session == "e":
                end_time = QTime(20, 0, 0)  # 8 PM
            else:
                session_timer.stop()
                session_timer_label.setText("Session Ends In: --:--:--")
                return

            # Set session end datetime for today
            nonlocal session_end_time
            session_end_time = QDateTime(now.date(), end_time)

            if now > session_end_time:
                session_timer_label.setText("Session Over")
                session_timer.stop()
                return

            session_timer.start(1000)


        def update_session_countdown():
            nonlocal session_end_time
            if not session_end_time:
                return

            now = QDateTime.currentDateTime()
            remaining = now.secsTo(session_end_time)

            if remaining <= 0:
                session_timer.stop()
                session_timer_label.setText("Session Over")
                return

            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            session_timer_label.setText(f"Session Ends In: {hours:02}:{minutes:02}:{seconds:02}")

        session_timer.timeout.connect(update_session_countdown)

        def fetch_distributor_rates(self):
            query = """
                SELECT u.name, r.session_id, r.rate
                FROM userrate r
                JOIN users u ON r.user_id = u.id
                WHERE r.created_by = %s
                ORDER BY u.name, r.session_id
            """
            
            self.db.cursor.execute(query, [self.data[0]])  # assuming self.data[0] is current user ID
            results = self.db.cursor.fetchall()

            distributors = {}
           

            session_map = {1: 'm', 2: 'd', 3: 'e'}

            for name, session_id, rate in results:
                if name not in distributors:
                    distributors[name] = {}
                key = session_map.get(session_id)
                if key:
                    distributors[name][key] = float(rate)

            return distributors
        window = QWidget()
        window.setWindowTitle("Sales Return")
        window.setStyleSheet("background-color:  #ccf2ff;")

        distributors = fetch_distributor_rates(self)
        # print(distributors)
        layout = QVBoxLayout(window)

       
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Date widgets
        date_label = QLabel("Date:")
        # date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_label.setFixedWidth(40)

        date_edit = QDateEdit(calendarPopup=True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setFixedWidth(120)

        # Party widgets
        party_label = QLabel("Party Name: ")
        party_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        party_label.setFixedWidth(120)

        party_dropdown = QComboBox()
        party_dropdown.addItems(["Select"] + list(distributors.keys()))
        # party_dropdown.setFixedHeight(24)
        party_dropdown.setFixedWidth(300)
        
        
        session={'M':1,'D':2,'E':3}
        session_label = QLabel("Session: ")
        session_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        session_label.setFixedWidth(80)
        session_dropdown = QComboBox()
        session_dropdown.addItems(["Select"] + list(session.keys()))
        # party_dropdown.setFixedHeight(24)
        session_dropdown.setFixedWidth(80)
        session_dropdown.currentIndexChanged.connect(start_session_countdown)
        date_edit.dateChanged.connect(start_session_countdown)
        
        
        session_timer_label = QLabel("Session Ends In: --:--:--")
        session_timer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        session_timer_label.setFixedWidth(300)
        session_timer_label.setStyleSheet("font-weight: bold; color: darkblue;")
        


        # Add widgets directly to the top layout
        top_layout.addWidget(date_label)
        top_layout.addWidget(date_edit)
        top_layout.addSpacing(10)
        top_layout.addWidget(party_label)
        top_layout.addWidget(party_dropdown)
        top_layout.addSpacing(10)
        top_layout.addWidget(session_label)
        top_layout.addWidget(session_dropdown)
        top_layout.addWidget(session_timer_label)

        
        layout.addLayout(top_layout)
        layout.addSpacing(0)

        # --- Table ---
        table = QTableWidget(0, 9)
        table.setHorizontalHeaderLabels([
            "Item", "From", "To", "Lottery", "Group",
            "Count", "Quantity", "Rate", "Amount"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("""
                QTableWidget {
                    background-color:#c8ffe0;  /* Light sky blue table background */
                    border: none;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background-color: #fffdd0;  /* Cream color */
                    color: #0055aa;             /* Blue text */
                    font-weight: bold;
                    padding: 4px;
                    border: 1px solid #ccc;
                }
                QTableWidget::item {
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: red;
                    color: white;
                }
                QTableWidget::item:focus {
                    background-color: white;
                    color: black;
                }
            """)
            
        
                   
        
        # layout.addWidget(table)
        
        table_totals_layout = QHBoxLayout()

        # Left: the table
        table_totals_layout.addWidget(table, stretch=8)

        # Right: vertical layout for totals
        totals_column = QVBoxLayout()
        totals_column.setAlignment(Qt.AlignTop)  # Top-align the totals
        totals_column.setContentsMargins(10, 0, 0, 0)  # Add left margin

        total_qty_label = QLabel("Total Qty: 0")
        total_amount_label = QLabel("Total Amount: 0.00")
        total_entries_label = QLabel("Total Entries: 0")

        for lbl in [total_qty_label, total_amount_label, total_entries_label]:
            lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
            totals_column.addWidget(lbl)
            totals_column.addSpacing(10)

        table_totals_layout.addLayout(totals_column, stretch=2)

        layout.addLayout(table_totals_layout)

        # Totals Area
        # total_layout = QHBoxLayout()
        # total_qty_label = QLabel("Total Qty: 0")
        # total_amount_label = QLabel("Total Amount: 0.00")
        # total_entries_label = QLabel("Total Entries: 0")
        # for lbl in [total_qty_label, total_amount_label, total_entries_label]:
            # total_layout.addWidget(lbl)
        # layout.addLayout(total_layout)
        
        

        # Set delegate for From and To columns (2 and 3)
        delegate = FiveDigitDelegate()
        table.setItemDelegateForColumn(1, delegate)
        table.setItemDelegateForColumn(2, delegate)

        
        

        
        def is_valid_5digit(text):
            return text.isdigit() and len(text) == 5

        def parse_same_from_item(item_text):
            match = re.findall(r'(?:[med])?(\d+)', item_text.lower())
            if match:
                values = list(set(match))
                return int(values[0]) if len(values) == 1 else None
            return None

        def calculate_totals():
            total_qty = 0
            total_amount = 0.0
            entry_count = 0
            for row in range(table.rowCount()):
                qty_item = table.item(row, 6)
                amt_item = table.item(row, 8)
                if qty_item and amt_item:
                    try:
                        qty = int(qty_item.text())
                        amt = float(amt_item.text())
                        total_qty += qty
                        total_amount += amt
                        entry_count += 1
                    except:
                        continue
            total_qty_label.setText(f"Total Qty: {total_qty}")
            total_amount_label.setText(f"Total Amount: {total_amount:.2f}")
            total_entries_label.setText(f"Total Entries: {entry_count}")

        def calculate_row(row):
            try:
                from_val = table.item(row, 1).text().strip()
                to_val = table.item(row, 2).text().strip()
                item_text = table.item(row, 0).text().strip().lower()

                if not (is_valid_5digit(from_val) and is_valid_5digit(to_val)):
                    return

                if int(to_val) <= int(from_val):
                    from PyQt5.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("TO must be greater than FROM.")
                    msg.setWindowTitle("Invalid TO Entry")
                    msg.exec_()
                    table.blockSignals(True)
                    table.setItem(row, 2, QTableWidgetItem(""))
                    table.blockSignals(False)
                    return

                # Prevent duplicate From-To for same Item
                for r in range(table.rowCount()):
                    if r != row:
                        other_item = table.item(r, 0)
                        other_from = table.item(r, 1)
                        other_to = table.item(r, 2)
                        if all([other_item, other_from, other_to]):
                            if (item_text == other_item.text().strip().lower() and
                                from_val == other_from.text().strip() and
                                to_val == other_to.text().strip()):
                                from PyQt5.QtWidgets import QMessageBox
                                msg = QMessageBox()
                                msg.setIcon(QMessageBox.Warning)
                                msg.setText("Duplicate From-To range for same Item is not allowed.")
                                msg.setWindowTitle("Duplicate Entry")
                                msg.exec_()
                                table.blockSignals(True)
                                table.setItem(row, 1, QTableWidgetItem(""))
                                table.setItem(row, 2, QTableWidgetItem(""))
                                table.blockSignals(False)
                                return
                sid=0               
                day_name = date_edit.date().toString("ddd")
                if item_text[0] =='m' :
                    sid=1
                elif item_text[0] =='d':
                    sid=2
                elif item_text[0] =='e':
                    sid=3
                
                                
                qf='''
                SELECT tn.name
                FROM  users u 
                inner JOIN (select distinct user_id from userrate where created_by=%s) r  ON r.user_id = u.id
                left join tickets as t
                on t.rate=u.rate
                left join ticket_session_names as tn
                on tn.ticket_id = t.id
                where tn.session_id=%s
                and tn.day=%s
                and u.name=%s
                '''
                self.db.cursor.execute(qf, [self.data[0],sid,day_name,party_dropdown.currentText()])  # assuming self.data[0] is current user ID
                lottery = self.db.cursor.fetchone()
                if lottery:
                    lottery_name = lottery[0]  # tn.name
                    print("Lottery Name:", lottery_name)
                else:
                    print("No result found.")
                same_val = parse_same_from_item(item_text)
                if same_val is None:
                    return

                count = (int(to_val) - int(from_val)) + 1
                qty = count * same_val
                rate = distributors[party_dropdown.currentText()][item_text[0]]
                amount = qty * rate
                table.blockSignals(True)
                for col, val in zip([3,5,6,7,8], [lottery_name,count, qty, rate, f"{amount:.2f}"]):
                    table.setItem(row, col, QTableWidgetItem(str(val)))
                table.blockSignals(False)

                calculate_totals()
            except Exception as e:
                print("Error calculating row:", e)


        def add_row():
            row = table.rowCount()
            table.insertRow(row)
            table.blockSignals(True)
            for col in range(9):
                table.setItem(row, col, QTableWidgetItem(""))
            table.blockSignals(False)

        def handle_cell_change(row, col):
            if party_dropdown.currentText() == "Select":
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Party Not Selected")
                msg.setText("Please select a Party Name before entering items.")
                msg.exec_()
                table.blockSignals(True)
                for c in range(table.columnCount()):
                    table.setItem(row, c, QTableWidgetItem(""))
                table.blockSignals(False)
                return
            if col == 0:  # Validate Item column
                item = table.item(row, 0)
                if item:
                    text = item.text().strip().lower()
                    selected_session = session_dropdown.currentText().lower()
                    if text[0].isdigit():
                        if selected_session == "m" :
                            # item.setText(f"M{text}")  # Add 'm' if it's not there already
                            table.blockSignals(True)
                            table.setItem(row, 0, QTableWidgetItem(f"M{text}"))
                            table.blockSignals(False)
                        elif selected_session == "d" :
                            # item.setText(f"D{text}")  # Add 'd'
                            table.blockSignals(True)
                            table.setItem(row, 0, QTableWidgetItem(f"D{text}"))
                            table.blockSignals(False)
                        elif selected_session == "e" :
                            # item.setText(f"E{text}")  # Add 'e'
                            table.blockSignals(True)
                            table.setItem(row, 0, QTableWidgetItem(f"E{text}"))
                            table.blockSignals(False)
                    t=table.item(row, 0).text().strip().lower()
                    print(t)
                    if not re.match(r"^[med][0-9]+$", t):  # Validate pattern: m5, d20, e15, etc.
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Item must start with 'm', 'e', or 'd' followed by digits (e.g., m10, e5).")
                        msg.setWindowTitle("Invalid Item Format")
                        msg.exec_()
                        table.blockSignals(True)
                        table.setItem(row, 0, QTableWidgetItem(""))
                        table.blockSignals(False)
                        return
                    
            if col==1:    
                item = table.item(row, 1)
                if item and len(item.text().strip())!=5:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("enter 5 digits")
                    msg.setWindowTitle("Invalid from")
                    msg.exec_()
                    table.blockSignals(True)
                    table.setItem(row, 1, QTableWidgetItem(""))
                    table.blockSignals(False)
                    return
                    
                    
            if col ==2:
                print(row)
                calculate_row(row)

            if row == table.rowCount() - 1:
                if all(table.item(row, c) and table.item(row, c).text().strip() != "" for c in range(3)):
                    add_row()

        table.cellChanged.connect(handle_cell_change)
        
        def clear_form(self):
            date_edit.setDate(QDate.currentDate())
            party_dropdown.setCurrentIndex(0)
            
            # table.setRowCount(15)
            # for col in range(table.columnCount()):
                # table.blockSignals(True)
                # table.setItem(0, col, QTableWidgetItem(""))
                # table.blockSignals(False)
            table.clearContents()
            calculate_totals()

        def save_entries():
            entries = []
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                if any(row_data[1:5]):
                    entries.append(row_data)
                    
            for e in entries:
                sid=0               
                day_name = date_edit.date().toString("ddd")
                if e[0][0].lower() =='m' :
                    sid=1
                elif e[0][0].lower() =='d':
                    sid=2
                elif e[0][0].lower() =='e':
                    sid=3
                qf1='''
                SELECT tn.name,tn.id as tid,u.id as uid
                FROM  users u 
                inner JOIN (select distinct user_id from userrate where created_by=%s) r  ON r.user_id = u.id
                left join tickets as t
                on t.rate=u.rate
                left join ticket_session_names as tn
                on tn.ticket_id = t.id
                where tn.session_id=%s
                and tn.day=%s
                and u.name=%s
                '''
                self.db.cursor.execute(qf1, [self.data[0],sid,day_name,party_dropdown.currentText()])  # assuming self.data[0] is current user ID
                lottery = self.db.cursor.fetchone()
                qf = '''
                    INSERT INTO lcm_sales
                    (fk_user, session, fk_tickets, same, `group`, from_ticket, to_ticket, count, qty, price, date, created_by, user_role, created_at)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''

                # Convert QDate to Python date or string
                sales_date = date_edit.date().toString("yyyy-MM-dd")
                created_date = QDate.currentDate().toString("yyyy-MM-dd")

                # Assuming e is a list like: [same, from_ticket, to_ticket, ..., count, qty, ..., price]
                self.db.cursor.execute(qf, [
                    lottery[2],     # fk_user
                    sid,            # session
                    lottery[1],     # fk_tickets
                    e[0][1:],       # same (strip first char if needed)
                    30,             # group
                    e[1],           # from_ticket
                    e[2],           # to_ticket
                    e[5],           # count
                    e[6],           # qty
                    e[8],           # price
                    sales_date,     # date (from QDateEdit)
                    self.data[0],   # created_by
                    self.data[8],   # user_role
                    created_date    # created_at
                ])
                self.db.connection.commit()
                table.clearContents()
            
            
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(save_entries)
        save_btn.setStyleSheet("padding: 6px 16px; background-color: orange; color: white;")

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(clear_form)
        reset_btn.setStyleSheet("padding: 6px 16px; background-color: grey; color: white;")

        # Add buttons to horizontal layout
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)

        # Add the horizontal layout to the main layout
        layout.addLayout(button_layout)
        info_layout = QHBoxLayout()
        button_defs = [
            "Save (Enter)", "Import (F4)", "Exit (Esc)"
        ]

        for text in button_defs:
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(30)
            label.setFont(QFont("Arial", 9, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    background-color: #fffdd0;
                    border: 1px solid black;
                    
                    color: black;
                }
            """)
            label.setFixedWidth(150)
            info_layout.addWidget(label)

        layout.addLayout(info_layout)

        for row in range(15):
            add_row()
        window.resize(1100, 550)
        window.show()
        return window
        
        
    def sale_list(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.add_sales_btn = QPushButton(" + Add Sales")
        self.add_sales_btn.setObjectName("openPopupButton")
        self.add_sales_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
        self.add_sales_btn.clicked.connect(lambda: self.switch_page("credit"))
        


        
        layout.addWidget(self.add_sales_btn,alignment=Qt.AlignLeft)
 
    
        self.user_table = QTableWidget(0, 11)
        self.user_table.setMaximumWidth(1489)
        self.user_table.setHorizontalHeaderLabels(["SrNo","Date", "Customer", "Ticket", "From", "To", "Item", "Groups", "Total ticket Qty","Price","Action"])
        self.user_table.setObjectName("SaleList")

        # ✅ Set full table editable by default
        self.user_table.setEditTriggers(QTableWidget.AllEditTriggers)

        # ✅ Set selection behavior: row-based
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)

        # ✅ Table styling
        self.user_table.setStyleSheet("""
                QTableWidget {
                    background-color:#c8ffe0;  /* Light sky blue table background */
                    border: none;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background-color: #fffdd0;  /* Cream color */
                    color: #0055aa;             /* Blue text */
                    font-weight: bold;
                    padding: 4px;
                    border: 1px solid #ccc;
                }
                QTableWidget::item {
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: red;
                    color: white;
                }
                QTableWidget::item:focus {
                    background-color: white;
                    color: black;
                }
            """)

        # Allow users to manually resize columns
        
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.user_table.setItemDelegate(EditDelegate(self.user_table, self.value_store))
        # self.user_table.setItemDelegate(EditDelegate(self.user_table, self.value_store, self))

        
        

        header = self.user_table.horizontalHeader()
        header.setStretchLastSection(False) 

        ratios = [4, 10,40, 25,8, 8, 8,8,15,8, 13] 
        total = sum(ratios)

        for i, val in enumerate(ratios):
            self.user_table.setColumnWidth(i, val * 10)
        
        
        table_container = QHBoxLayout()
        
        table_container.addWidget(self.user_table)
       
        # Add this to your main layout
        layout.addLayout(table_container)
        info_layout = QHBoxLayout()
        button_defs = [
            "Save (Enter)", "Import (F4)", "Exit (Esc)"
        ]

        for text in button_defs:
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(30)
            label.setFont(QFont("Arial", 9, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    background-color: #fffdd0;
                    border: 1px solid black;
                    
                    color: black;
                }
            """)
            label.setFixedWidth(150)
            info_layout.addWidget(label)

        layout.addLayout(info_layout)
        widget.setLayout(layout)
        
       
        # self.user_table.blockSignals(True)
        # self.load_users()
        # self.user_table.blockSignals(False)
          
        return widget
     
    def load_tickets(self):
        self.ticket_table.setRowCount(0)
        users = self.db.load_ticket()
        self.ticket_table.setRowCount(len(users))
        for row, user in enumerate(users):
            for col, data in enumerate(user[1:2]):
                item = QTableWidgetItem(str(row + 1))
                item.setTextAlignment(Qt.AlignCenter)
                
                self.ticket_table.setItem(row, 0, item)
                item1 = QTableWidgetItem(str(data))
                item1.setTextAlignment(Qt.AlignCenter)
                self.ticket_table.setItem(row, col+1,item1 )
                
            modify_button = QPushButton("M")
            modify_button.setFixedSize(28, 28)
            modify_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;  /* Amber warning */
                    color: black;
                    font-weight: bold;
                    border: 1px solid #e0a800;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            modify_button.clicked.connect(lambda _, u=user[0]: self.open_modify_ticket_dialog(u))


            delete_button = QPushButton("D")
            delete_button.setFixedSize(28, 28)
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;  /* Danger red */
                    color: white;
                    font-weight: bold;
                    border: 1px solid #bd2130;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #bd2130;
                }
            """)
            delete_button.clicked.connect(lambda _, u=user[0]: self.delete_ticket(u))

            action_layout = QHBoxLayout()
            action_layout.addWidget(modify_button)
            action_layout.addWidget(delete_button)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.ticket_table.setCellWidget(row, 2, action_widget)
        
    def load_users(self):
        print("loading")
        self.user_table.blockSignals(True)
        self.user_table.setRowCount(0)
        users = self.db.load_user()
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            uid = user[0]  # This is the user ID from DB
            sr_item = QTableWidgetItem(str(row + 1))  # Displayed serial number
            sr_item.setTextAlignment(Qt.AlignCenter)
            sr_item.setData(Qt.UserRole, uid)  # Hidden actual UID

            self.user_table.setItem(row, 0, sr_item)
            
            # item = QTableWidgetItem(str(row + 1))
            
            
            # self.user_table.setItem(row, 0, item)
            
            
            self.user_table.setItem(row, 1, QTableWidgetItem(str("")))
            
            for col, data in enumerate(user[5:]):
                item=QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)
                self.user_table.setItem(row, col+2,item )
                
                
            modify_button = QPushButton("M")
            modify_button.setFixedSize(28, 28)  # Square shape
            modify_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;  /* Amber warning */
                    color: black;
                    font-weight: bold;
                    border: 1px solid #e0a800;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            modify_button.clicked.connect(lambda _, u=user: self.open_modify_user_dialog(u))


            delete_button = QPushButton("D")
            delete_button.setFixedSize(28, 28)
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;  /* Danger red */
                    color: white;
                    font-weight: bold;
                    border: 1px solid #bd2130;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #bd2130;
                }
            """)
            delete_button.clicked.connect(lambda _, u=user: self.delete_user(u))


            action_layout = QHBoxLayout()
            action_layout.addWidget(modify_button)
            action_layout.addWidget(delete_button)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.user_table.setCellWidget(row, 7, action_widget)
        self.user_table.blockSignals(False)
            
    def open_add_user_dialog(self):
        dialog = AddDistributorDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.load_users()  
            
    def open_add_ticket_dialog(self):
        dialog = AddTicketDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.load_tickets()

    def delete_user(self,u):
        if u:
            self.db.delete_user(u[0])
            QMessageBox.information(self, "Success", f"{u[5]} deleted successfully")
            self.load_users()       
        else:
            QMessageBox.warning(self, "Error", "failed to delete")  

    def delete_ticket(self,t):
        if t:
            self.db.delete_ticket(t)
            QMessageBox.information(self, "Success"," deleted successfully")
            self.load_tickets()       
        else:
            QMessageBox.warning(self, "Error")       

    def open_modify_user_dialog(self, user_data):
        dialog = ModifyDistributorDialog(self, user_data)
        if dialog.exec_():
            print("User modified, refreshing table...")
            self.load_users()   


    def open_modify_ticket_dialog(self, tid):
        t_data=self.get_ticket_by_id(tid)
        # print(t_data)
        dialog = ModifyTicketDialog(self, t_data)
        if dialog.exec_():
            print("ticket modified, refreshing table...")
            self.load_tickets()     
    
    def get_ticket_by_id(self, ticket_id):
        ticket_query = "SELECT id, name, rate FROM tickets WHERE id = %s"
        self.db.cursor.execute(ticket_query, (ticket_id,))
        ticket_row = self.db.cursor.fetchone()
        if not ticket_row:
            return None

        ticket_data = {
            'id': ticket_row[0],
            'name': ticket_row[1],
            'rate': float(ticket_row[2]),
            'sessions': {}
        }

        # Step 1: Load session IDs
        session_ids = {'MOR': 1, 'DAY': 2, 'EVE': 3}  # If you're using IDs this way

        # Step 2: Fetch ticket_session_names (Days)
        day_query = "SELECT session_id, day, name FROM ticket_session_names WHERE ticket_id = %s"
        self.db.cursor.execute(day_query, (ticket_id,))
        for session_id, day, name in self.db.cursor.fetchall():
            session_name = [k for k, v in session_ids.items() if v == session_id][0]
            if session_name not in ticket_data['sessions']:
                ticket_data['sessions'][session_name] = {'days': {}, 'prizes': {'pvt': [], 'bonus': [], 'inc': []}}
            ticket_data['sessions'][session_name]['days'][day] = name

        # Step 3: Fetch ticket_prizes
        prize_query = """SELECT session_id, sr_no, amount, special_amount, super_amount 
                         FROM ticket_prizes WHERE ticket_id = %s ORDER BY session_id, sr_no"""
        self.db.cursor.execute(prize_query, (ticket_id,))
        for session_id, line, pvt, bonus, incentive in self.db.cursor.fetchall():
            session_name = [k for k, v in session_ids.items() if v == session_id][0]
            if session_name not in ticket_data['sessions']:
                ticket_data['sessions'][session_name] = {'days': {}, 'prizes': {'pvt': [], 'bonus': [], 'inc': []}}
            ticket_data['sessions'][session_name]['prizes']['pvt'].append(str(pvt))
            ticket_data['sessions'][session_name]['prizes']['bonus'].append(str(bonus))
            ticket_data['sessions'][session_name]['prizes']['inc'].append(str(incentive))

        return ticket_data
    
        


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = LoginPage()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        print("🔥 Unhandled Exception:")
        traceback.print_exc()
