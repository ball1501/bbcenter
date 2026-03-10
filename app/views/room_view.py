from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db, RoomBooking

room_bp = Blueprint('room', __name__)

# ชื่อห้องและสีรวมไว้ที่เดียว — แก้ที่นี่ที่เดียวพอ
ROOM_COLORS = {
    'ห้องประชุมเล็ก': '#2563EB',
    'ห้องประชุมใหญ่': '#F59E0B',
}
ROOM_CHOICES = list(ROOM_COLORS.keys())


@room_bp.route('/room')
@login_required
def index():
    bookings = RoomBooking.query.order_by(RoomBooking.start_time.asc()).all()
    return render_template('room/room.html', bookings=bookings, room_choices=ROOM_CHOICES)


@room_bp.route('/room/book', methods=['POST'])
@login_required
def book_room():
    room_name  = request.form.get('room_name')
    title      = request.form.get('title')
    start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
    end_time   = datetime.strptime(request.form.get('end_time'),   '%Y-%m-%dT%H:%M')

    if start_time >= end_time:
        flash('เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น', 'danger')
        return redirect(url_for('room.index'))

    overlap = RoomBooking.query.filter(
        RoomBooking.room_name  == room_name,
        RoomBooking.start_time < end_time,
        RoomBooking.end_time   > start_time
    ).first()

    if overlap:
        flash(f'ไม่สามารถจองได้! {room_name} เวลานี้ถูกจองแล้วโดย {overlap.user.full_name or overlap.user.username}', 'danger')
    else:
        new_booking = RoomBooking(
            user_id    = current_user.id,
            room_name  = room_name,
            title      = title,
            start_time = start_time,
            end_time   = end_time
        )
        db.session.add(new_booking)
        db.session.commit()
        flash('จองห้องประชุมสำเร็จ!', 'success')

    return redirect(url_for('room.index'))


@room_bp.route('/room/edit/<int:id>', methods=['POST'])
@login_required
def edit_room(id):
    booking = RoomBooking.query.get_or_404(id)

    if booking.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขการจองนี้', 'danger')
        return redirect(url_for('room.index'))

    room_name  = request.form.get('room_name')
    title      = request.form.get('title')
    start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
    end_time   = datetime.strptime(request.form.get('end_time'),   '%Y-%m-%dT%H:%M')

    if start_time >= end_time:
        flash('เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น', 'danger')
        return redirect(url_for('room.index'))

    overlap = RoomBooking.query.filter(
        RoomBooking.id         != booking.id,
        RoomBooking.room_name  == room_name,
        RoomBooking.start_time < end_time,
        RoomBooking.end_time   > start_time
    ).first()

    if overlap:
        flash('ไม่สามารถแก้ไขได้ เวลาชนกับการจองอื่น', 'danger')
    else:
        booking.room_name  = room_name
        booking.title      = title
        booking.start_time = start_time
        booking.end_time   = end_time
        db.session.commit()
        flash('อัปเดตข้อมูลสำเร็จ', 'success')

    return redirect(url_for('room.index'))


@room_bp.route('/room/delete/<int:id>', methods=['POST'])
@login_required
def delete_room(id):
    booking = RoomBooking.query.get_or_404(id)

    if booking.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบการจองนี้', 'danger')
        return redirect(url_for('room.index'))

    db.session.delete(booking)
    db.session.commit()
    flash('ยกเลิกการจองห้องประชุมแล้ว', 'success')
    return redirect(url_for('room.index'))


@room_bp.route('/api/room/bookings')
@login_required
def api_room_bookings():
    bookings = RoomBooking.query.all()
    events = []
    for b in bookings:
        events.append({
            'id':    b.id,
            'title': f"{b.title} ({b.user.full_name or b.user.username})",
            'start': b.start_time.isoformat(),
            'end':   b.end_time.isoformat(),
            'color': ROOM_COLORS.get(b.room_name, '#6B7280'),
            'extendedProps': {'room': b.room_name}
        })
    return jsonify(events)