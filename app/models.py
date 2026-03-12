from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

# 🟢 สร้างฟังก์ชันดึงเวลาปัจจุบันของไทย (UTC + 7 ชั่วโมง)
def get_bkk_time():
    return datetime.utcnow() + timedelta(hours=7)

# ==========================================
# 1. ตาราง User (ต้องอยู่บนสุดเสมอ)
# ==========================================
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    department = db.Column(db.String(100))
    
    role_repair = db.Column(db.String(20), default='user')
    role_maintenance = db.Column(db.String(20), default='user')
    role_vehicle = db.Column(db.String(20), default='user')
    role_room = db.Column(db.String(20), default='user')
    is_superadmin = db.Column(db.Boolean, default=False)

    # 🛑 ย้าย Relationship มาไว้ฝั่ง User ให้มันรู้ตัวว่ามีตาราง RepairTicket เชื่อมอยู่
    repair_tickets = db.relationship('RepairTicket', backref='user', lazy=True)
    maintenance_tickets = db.relationship('MaintenanceTicket', backref='user', lazy=True)
    vehicle_bookings = db.relationship('VehicleBooking', backref='user', lazy=True)
    room_bookings = db.relationship('RoomBooking', backref='user', lazy=True)
    


# ==========================================
# 2. ตาราง RepairTicket (ระบบแจ้งซ่อม)
# ==========================================
class RepairTicket(db.Model):
    __tablename__ = 'repair_ticket'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    urgency = db.Column(db.String(20), nullable=False)
    asset_tag = db.Column(db.String(50))
    location = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    
    # 🟢 เพิ่มคอลัมน์นี้สำหรับเก็บชื่อไฟล์รูป (อนุญาตให้เป็นค่าว่างได้ เพราะบางเคสอาจไม่มีรูป)
    image_file = db.Column(db.String(255), nullable=True) 
    
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=get_bkk_time)

    # 🆕 เพิ่มสำหรับ Admin
    resolved_note = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, onupdate=get_bkk_time, nullable=True)




# ==========================================
# 3. ตาราง MaintenanceTicket (ระบบแจ้งซ่อมทั่วไป/อาคาร)
# ==========================================
class MaintenanceTicket(db.Model):
    __tablename__ = 'maintenance_ticket'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    category = db.Column(db.String(50), nullable=False) # ประปา, ไฟฟ้า, แอร์ ฯลฯ
    urgency = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False) # 🟢 เบอร์ติดต่อกลับ (สำคัญสำหรับช่างอาคาร)
    subject = db.Column(db.String(150), nullable=False)
    image_file = db.Column(db.String(255), nullable=True)
    
    status = db.Column(db.String(20), default='pending')
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=get_bkk_time)

    resolved_note   = db.Column(db.Text, nullable=True)
    resolved_at     = db.Column(db.DateTime, nullable=True)
    updated_at      = db.Column(db.DateTime, nullable=True)
    repair_cost     = db.Column(db.Numeric(10, 2), nullable=True)
    technician_type = db.Column(db.String(20), nullable=True)
    scheduled_date  = db.Column(db.Date, nullable=True)
    image_after     = db.Column(db.String(255), nullable=True)


# ==========================================
# 4. ตาราง Vehicle (ข้อมูลรถในบริษัท)
# ==========================================
class Vehicle(db.Model):
    __tablename__ = 'vehicle'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)       # ยี่ห้อ เช่น Toyota
    model = db.Column(db.String(50), nullable=False)       # รุ่น เช่น Commuter
    license_plate = db.Column(db.String(20), unique=True, nullable=False) # ทะเบียนรถ (ห้ามซ้ำ)
    capacity = db.Column(db.Integer, nullable=False)       # จำนวนที่นั่งสูงสุด
    status = db.Column(db.String(20), default='active')    # สถานะ: active (พร้อมใช้งาน), maintenance (ซ่อมบำรุง)
    fuel_rate = db.Column(db.Float, default=10.0)          # อัตราสิ้นเปลือง กม./ลิตร


# ==========================================
# 5.0 ตาราง คนขับ
# ==========================================
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # ผูกกับ User account
    linked_user = db.relationship('User', foreign_keys=[user_id])


# ==========================================
# 5. ตาราง VehicleBooking (ตั๋วการจองรถ/เจ้าภาพทริป)
# ==========================================
class VehicleBooking(db.Model):
    __tablename__ = 'vehicle_booking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)       # ใครเป็นคนจอง (ผู้ตั้งทริป)
    start_datetime = db.Column(db.DateTime, nullable=False) # วัน-เวลาที่เริ่มใช้รถ
    end_datetime = db.Column(db.DateTime, nullable=False)   # วัน-เวลาที่คืนรถ
    
    destination = db.Column(db.String(200), nullable=False) # สถานที่ปลายทาง เช่น "นิคมอุตสาหกรรมชลบุรี"
    purpose = db.Column(db.String(200), nullable=False)     # วัตถุประสงค์ เช่น "พบลูกค้า"
    
    need_driver = db.Column(db.Boolean, default=True)       # ต้องการพนักงานขับรถไหม? (True/False)
    passenger_count = db.Column(db.Integer, nullable=False) # จำนวนคนไปในทริปนี้ (ตัวตั้งต้น)
    allow_join = db.Column(db.Boolean, default=True)        # 🟢 ยอมให้คนอื่นขอติดรถไปด้วยไหม?

    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    # driver = db.relationship('Driver', backref='bookings')
    driver  = db.relationship('Driver', foreign_keys=[driver_id],  backref='bookings')
    
    status = db.Column(db.String(20), default='pending')    # pending, approved, rejected, completed
    created_at = db.Column(db.DateTime, default=get_bkk_time)

    trip_group          = db.Column(db.String(50), nullable=True)   # เช่น "TRP-001"
    assigned_vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)
    assigned_vehicle    = db.relationship('Vehicle', foreign_keys='VehicleBooking.assigned_vehicle_id')

    assigned_vehicle2_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)
    assigned_vehicle2    = db.relationship('Vehicle', foreign_keys=[assigned_vehicle2_id])

    driver2_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    # driver2    = db.relationship('Driver', foreign_keys=[driver2_id])
    driver2 = db.relationship('Driver', foreign_keys=[driver2_id])

    telegram_message_id = db.Column(db.Integer, nullable=True)

    expense_type      = db.Column(db.String(20), nullable=True)
    central_category  = db.Column(db.String(50), nullable=True)




# ==========================================
# 6. ตาราง RoomBooking (จองห้องประชุม)
# ==========================================
class RoomBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_name = db.Column(db.String(50), nullable=False) # เก็บชื่อ "ห้อง 1" หรือ "ห้อง 2"
    title = db.Column(db.String(255), nullable=False) # หัวข้อการประชุม
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=get_bkk_time)
    


# ==========================================
# 7. ตาราง VehicleMileage (การจดกม.)
# ==========================================
class VehicleMileage(db.Model):
    __tablename__    = 'vehicle_mileage'
    id               = db.Column(db.Integer, primary_key=True)
    booking_id       = db.Column(db.Integer, db.ForeignKey('vehicle_booking.id'), nullable=False)
    odometer_start   = db.Column(db.Integer, nullable=True)
    odometer_end     = db.Column(db.Integer, nullable=True)
    actual_start     = db.Column(db.DateTime, nullable=True)
    actual_end       = db.Column(db.DateTime, nullable=True)
    fuel_cost        = db.Column(db.Float, default=0)
    noted_by         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.now)

    booking          = db.relationship('VehicleBooking', backref='mileage')
    noter            = db.relationship('User', foreign_keys=[noted_by])

    # ข้อ 1: รูปหน้าปัด
    odometer_start_img = db.Column(db.String(255), nullable=True)
    odometer_end_img   = db.Column(db.String(255), nullable=True)

    # ข้อ 2: เติมน้ำมันระหว่างทาง
    refuel        = db.Column(db.Boolean, default=False)
    refuel_amount = db.Column(db.Float, default=0)
    refuel_img    = db.Column(db.String(255), nullable=True)


# ==========================================
# 8. ตาราง SystemConfig (ค่า config กลาง)
# ==========================================
class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    key   = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(100), nullable=False)

    @staticmethod
    def get(key, default=None):
        row = SystemConfig.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = SystemConfig.query.get(key)
        if row:
            row.value = str(value)
        else:
            db.session.add(SystemConfig(key=key, value=str(value)))
        db.session.commit()