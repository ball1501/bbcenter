# views/auth_view.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, RepairTicket, MaintenanceTicket, RoomBooking, VehicleBooking
from ad_utils import check_ad_login
from datetime import datetime, date

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        is_valid, user_info = check_ad_login(username, password)

        if is_valid:
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(
                    username=username,
                    full_name=user_info['full_name'],
                    email=user_info['email'],
                    department=user_info['department']
                )
                db.session.add(user)
                db.session.commit()

            login_user(user)
            return redirect(url_for('auth.dashboard'))
        else:
            flash("User หรือ Password ไม่ถูกต้อง!", "danger")

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user_count = User.query.count()
    today = date.today()

    # ---- Stats จริงจาก DB ----
    # ระบบซ่อม IT
    repair_pending     = RepairTicket.query.filter_by(status='pending').count()
    repair_in_progress = RepairTicket.query.filter_by(status='in_progress').count()
    repair_done_total  = RepairTicket.query.filter_by(status='done').count()

    # ระบบซ่อมอาคาร
    maint_pending     = MaintenanceTicket.query.filter_by(status='pending').count()
    maint_in_progress = MaintenanceTicket.query.filter_by(status='in_progress').count()
    maint_done_total  = MaintenanceTicket.query.filter_by(status='done').count()

    # ระบบจองยานพาหนะ
    vehicle_pending     = VehicleBooking.query.filter_by(status='pending').count()
    vehicle_waiting_approver = VehicleBooking.query.filter_by(status='waiting_approver').count()
    vehicle_approved  = VehicleBooking.query.filter_by(status='approved').count()

    # งานรอดำเนินการรวม (สำหรับ alert badge)
    total_pending = repair_pending + maint_pending + vehicle_pending

    # Ticket ของ user คนนี้ที่ยังไม่เสร็จ
    my_repair_open = RepairTicket.query.filter(
        RepairTicket.user_id == current_user.id,
        RepairTicket.status != 'done'
    ).count()
    my_maint_open = MaintenanceTicket.query.filter(
        MaintenanceTicket.user_id == current_user.id,
        MaintenanceTicket.status != 'done'
    ).count()

    # ยานพาหนะ — จองรออนุมัติ
    vehicle_pending          = VehicleBooking.query.filter_by(status='pending').count()
    vehicle_waiting_approver = VehicleBooking.query.filter_by(status='waiting_approver').count()
    vehicle_approved         = VehicleBooking.query.filter_by(status='approved').count()
    my_vehicle_pending       = VehicleBooking.query.filter_by(
        user_id=current_user.id, status='pending'
    ).count()

    # recent vehicle bookings สำหรับ admin
    recent_vehicle = VehicleBooking.query.order_by(
        VehicleBooking.created_at.desc()
    ).limit(5).all()

    # ห้องประชุม — จองวันนี้
    today_start = datetime.combine(today, datetime.min.time())
    today_end   = datetime.combine(today, datetime.max.time())
    room_today  = RoomBooking.query.filter(
        RoomBooking.start_time >= today_start,
        RoomBooking.start_time <= today_end
    ).count()

    # จองของ user วันนี้
    my_room_today = RoomBooking.query.filter(
        RoomBooking.user_id    == current_user.id,
        RoomBooking.start_time >= today_start,
        RoomBooking.start_time <= today_end
    ).all()

    # recent room bookings
    recent_room = RoomBooking.query.order_by(
        RoomBooking.start_time.asc()
    ).filter(RoomBooking.start_time >= today_start).limit(5).all()
    recent_repair = RepairTicket.query.order_by(
        RepairTicket.created_at.desc()
    ).limit(5).all()
    recent_maint = MaintenanceTicket.query.order_by(
        MaintenanceTicket.created_at.desc()
    ).limit(5).all()

    stats = {
        # ภาพรวม
        'total_pending':      total_pending,
        'user_count':         user_count,

        # IT Repair
        'repair_pending':     repair_pending,
        'repair_in_progress': repair_in_progress,
        'repair_done_total':  repair_done_total,

        # Maintenance
        'maint_pending':      maint_pending,
        'maint_in_progress':  maint_in_progress,
        'maint_done_total':   maint_done_total,

        # งานของ user ปัจจุบัน
        'my_repair_open':     my_repair_open,
        'my_maint_open':      my_maint_open,

        # ยานพาหนะ
        'vehicle_pending':    vehicle_pending,
        'vehicle_waiting_approver': vehicle_waiting_approver,
        'vehicle_approved':   vehicle_approved,
        'my_vehicle_pending': my_vehicle_pending,

        # ห้องประชุม
        'room_today':     room_today,
        'my_room_today':  my_room_today,
    }

    return render_template(
        'dashboard/dashboard.html',
        stats=stats,
        recent_repair=recent_repair,
        recent_maint=recent_maint,
        recent_room=recent_room,
        recent_vehicle=recent_vehicle,
    )


@auth_bp.route('/manage_users')
@login_required
def manage_users():
    if not current_user.is_superadmin:
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้าจัดการผู้ใช้งาน", "danger")
        return redirect(url_for('auth.dashboard'))

    users = User.query.all()
    return render_template('usermng/manage_users.html', users=users)


@auth_bp.route('/update_user/<int:id>', methods=['POST'])
@login_required
def update_user(id):
    if not current_user.is_superadmin:
        return redirect(url_for('auth.dashboard'))

    user = User.query.get_or_404(id)
    user.department    = request.form.get('department')
    user.role_repair   = request.form.get('role_repair')
    user.role_maintenance = request.form.get('role_maintenance')
    user.role_vehicle  = request.form.get('role_vehicle')
    user.role_room     = request.form.get('role_room')
    user.is_superadmin = True if request.form.get('is_superadmin') else False

    db.session.commit()
    flash(f"อัปเดตสิทธิ์ของ {user.full_name or user.username} เรียบร้อยแล้ว!", "success")
    return redirect(url_for('auth.manage_users'))