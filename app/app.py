import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import LoginManager,current_user
from models import db, User
from datetime import timedelta
from models import Vehicle # อย่าลืม import Vehicle ด้านบนด้วยนะถ้ายังไม่มี ชั่วคราว

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_super_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # จำ 7 วัน

# ผูก Database เข้ากับแอป
db.init_app(app)

# ตั้งค่า Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
# 🛑 จุดสำคัญ: ต้องบอก Flask ว่าหน้า Login ตอนนี้ย้ายไปอยู่ Blueprint 'auth' แล้ว
login_manager.login_view = 'auth.login' 
login_manager.login_message = "กรุณาเข้าสู่ระบบก่อน"  # เปลี่ยนเป็นภาษาไทย
login_manager.login_message_category = "danger"                   # บังคับให้เป็น error สีแดง

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# ลงทะเบียน Blueprints
# ==========================================
from views.auth_view import auth_bp
app.register_blueprint(auth_bp)

from views.repair_view import repair_bp  
app.register_blueprint(repair_bp)

from views.maintenance_view import maintenance_bp 
app.register_blueprint(maintenance_bp)

from views.vehicle_view import vehicle_bp, adminfleet_bp, admincost_bp
app.register_blueprint(vehicle_bp)
app.register_blueprint(adminfleet_bp)
app.register_blueprint(admincost_bp)

from views.room_view import room_bp
app.register_blueprint(room_bp)


# ==========================================

# Route หน้าแรกสุด (เวลาคนพิมพ์แค่ชื่อเว็บ) ให้โยนไปหน้า Login
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))  # ✅ login แล้ว → ไป dashboard
    return redirect(url_for('auth.login'))           # ยังไม่ login → ไปหน้า login

# 🛠️ Route ชั่วคราวสำหรับสร้างข้อมูลรถจำลอง (รันเสร็จแล้วลบทิ้งได้เลย)
@app.route('/mock-vehicles')
def mock_vehicles():
    # เช็คก่อนว่ามีรถในระบบหรือยัง จะได้ไม่สร้างซ้ำ
    if Vehicle.query.count() == 0:
        v1 = Vehicle(brand='TOYOTA', model='All New Commuter (รถตู้)', license_plate='1นจ9208', capacity=10)
        v2 = Vehicle(brand='TOYOTA', model='Hiace (รถตู้)', license_plate='ฮฉ 5064', capacity=10)
        v3 = Vehicle(brand='TOYOTA', model='Hiace (รถตู้ครัว)', license_plate='ฮข 3858', capacity=1)
        v4 = Vehicle(brand='ISUZU', model='D-MAX (รถกระบะ)', license_plate='ศม 139', capacity=4)
        v5 = Vehicle(brand='TOYOTA', model='VIGO (รถกระบะ)', license_plate='กร 7922', capacity=4)
        v6 = Vehicle(brand='FORD', model='RANGER (รถกระบะ)', license_plate='3ขข632', capacity=4)
        
        db.session.add_all([v1, v2, v3, v4, v5, v6])
        db.session.commit()
        return "เพิ่มข้อมูลรถจำลองสำเร็จ! <a href='/vehicle'>ไปหน้าระบบจองรถ</a>"
    return "มีข้อมูลรถในระบบอยู่แล้วครับ <a href='/vehicle'>ไปหน้าระบบจองรถ</a>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(host='0.0.0.0', port=5001, debug=True)