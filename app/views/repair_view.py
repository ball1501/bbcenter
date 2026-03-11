import os
import time
from datetime import datetime
from calendar import month_name
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, RepairTicket
from sqlalchemy import extract

repair_bp = Blueprint('repair', __name__)


def is_repair_admin():
    """เช็คว่า user คนนี้มีสิทธิ์ admin ระบบซ่อมหรือเปล่า"""
    return current_user.role_repair == 'admin' or current_user.is_superadmin


def get_repair_summary():
    """คำนวณ summary ของเดือนปัจจุบันสำหรับ admin"""
    now = datetime.now()
    month_tickets = RepairTicket.query.filter(
        extract('year',  RepairTicket.created_at) == now.year,
        extract('month', RepairTicket.created_at) == now.month
    ).all()

    by_category = {}
    for t in month_tickets:
        by_category[t.category] = by_category.get(t.category, 0) + 1

    th_months = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

    return {
        'month_label': f"{th_months[now.month]} {now.year + 543}",
        'total':       len(month_tickets),
        'pending':     sum(1 for t in month_tickets if t.status == 'pending'),
        'in_progress': sum(1 for t in month_tickets if t.status == 'in_progress'),
        'done':        sum(1 for t in month_tickets if t.status == 'done'),
        'urgent':      sum(1 for t in month_tickets if t.urgency == 'ด่วนมาก'),
        'by_category': by_category,
    }


@repair_bp.route('/repair', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':

        # 🟢 1. จัดการเรื่องไฟล์รูปภาพ
        image_file = request.files.get('image')
        filename = None

        if image_file and image_file.filename != '':
            upload_folder = os.path.join('static', 'uploads', 'repair')
            os.makedirs(upload_folder, exist_ok=True)

            safe_name = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{safe_name}"

            filepath = os.path.join(upload_folder, filename)
            image_file.save(filepath)

        # 🟢 2. บันทึกข้อมูลลง Database
        new_ticket = RepairTicket(
            user_id=current_user.id,
            category=request.form.get('category'),
            urgency=request.form.get('urgency'),
            asset_tag=request.form.get('asset_tag'),
            location=request.form.get('location'),
            subject=request.form.get('subject'),
            image_file=filename
        )
        db.session.add(new_ticket)
        db.session.commit()

        flash('แจ้งซ่อมสำเร็จ! ข้อมูลของคุณถูกส่งเข้าระบบเรียบร้อยแล้ว', 'success')
        return redirect(url_for('repair.index'))

    tickets = RepairTicket.query.order_by(RepairTicket.created_at.desc()).all()
    summary = get_repair_summary() if is_repair_admin() else None
    return render_template('repair/repair.html', tickets=tickets, summary=summary)


# 🟢 Route สำหรับแก้ไข (Update) — เฉพาะเจ้าของ 
@repair_bp.route('/repair/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    ticket = RepairTicket.query.get_or_404(id)

    if ticket.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์เข้าถึงหรือแก้ไขรายการนี้', 'danger')
        return redirect(url_for('repair.index'))

    if request.method == 'POST':
        ticket.category = request.form.get('category')
        ticket.urgency = request.form.get('urgency')
        ticket.asset_tag = request.form.get('asset_tag')
        ticket.location = request.form.get('location')
        ticket.subject = request.form.get('subject')

        db.session.commit()
        flash('อัปเดตข้อมูลแจ้งซ่อมเรียบร้อยแล้ว', 'success')
        return redirect(url_for('repair.index'))

    tickets = RepairTicket.query.order_by(RepairTicket.created_at.desc()).all()
    summary = get_repair_summary() if is_repair_admin() else None
    return render_template('repair/repair.html', tickets=tickets, edit_ticket=ticket, summary=summary)


# 🟢 Route สำหรับลบ — เฉพาะเจ้าของ
@repair_bp.route('/repair/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    ticket = RepairTicket.query.get_or_404(id)

    if ticket.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์เข้าถึงหรือลบรายการนี้', 'danger')
        return redirect(url_for('repair.index'))

    db.session.delete(ticket)
    db.session.commit()
    flash('ลบรายการแจ้งซ่อมเรียบร้อยแล้ว', 'success')
    return redirect(url_for('repair.index'))


# 🆕 Route สำหรับ Admin — อัปเดตสถานะ (รับงาน / ปิดงาน)
@repair_bp.route('/repair/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    # เฉพาะ admin เท่านั้น
    if not is_repair_admin():
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'danger')
        return redirect(url_for('repair.index'))

    ticket = RepairTicket.query.get_or_404(id)
    action = request.form.get('action')

    if action == 'accept':
        # รับงาน: pending → in_progress
        if ticket.status != 'pending':
            flash('ไม่สามารถรับงานได้ เนื่องจากสถานะไม่ใช่ "รอดำเนินการ"', 'warning')
            return redirect(url_for('repair.index'))

        ticket.status = 'in_progress'
        new_urgency = request.form.get('urgency', '').strip()
        if new_urgency:
            ticket.urgency = new_urgency
        flash(f'รับงาน #{ ticket.id } เรียบร้อยแล้ว กำลังดำเนินการซ่อม', 'success')

    elif action == 'close':
        # ปิดงาน: in_progress → done
        if ticket.status != 'in_progress':
            flash('ไม่สามารถปิดงานได้ เนื่องจากสถานะไม่ใช่ "กำลังซ่อม"', 'warning')
            return redirect(url_for('repair.index'))

        resolved_note = request.form.get('resolved_note', '').strip()
        if not resolved_note:
            flash('กรุณากรอกบันทึกผลการซ่อมก่อนปิดงาน', 'warning')
            return redirect(url_for('repair.index'))

        ticket.status = 'done'
        ticket.resolved_note = resolved_note
        ticket.resolved_at = datetime.now()
        flash(f'ปิดงาน #{ ticket.id } เรียบร้อยแล้ว', 'success')

    else:
        flash('คำสั่งไม่ถูกต้อง', 'danger')
        return redirect(url_for('repair.index'))

    db.session.commit()
    return redirect(url_for('repair.index'))