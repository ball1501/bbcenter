import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN     = "8630024542:AAFR-VaVpp75CwE2u_0IJY1U43oTFzq9rLM"
TELEGRAM_GROUP_CHAT_ID = "-5275480755"

TH_MONTHS = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
             'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


def _fmt_date(dt):
    if not dt: return '-'
    return f"{dt.day} {TH_MONTHS[dt.month]} {dt.year + 543}"

def _fmt_time(dt):
    if not dt: return '-'
    return dt.strftime('%H:%M')

def _send(text: str) -> int | None:
    """ส่งข้อความ — คืนค่า message_id ถ้าสำเร็จ หรือ None ถ้าล้มเหลว"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_GROUP_CHAT_ID,
            "text":       text,
            "parse_mode": "HTML",
        }, timeout=5)
        if resp.ok:
            return resp.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[Telegram] Send error: {e}")
    return None


def delete_old_message(booking):
    """ลบข้อความเก่าออกจาก group (ถ้ามี message_id เก็บไว้)"""
    if not booking.telegram_message_id:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
        requests.post(url, json={
            "chat_id":    TELEGRAM_GROUP_CHAT_ID,
            "message_id": booking.telegram_message_id,
        }, timeout=5)
    except Exception as e:
        print(f"[Telegram] Delete error: {e}")


def _save_message_id(booking, message_id):
    """บันทึก message_id ลง DB"""
    if message_id:
        from models import db
        booking.telegram_message_id = message_id
        db.session.commit()


def _car_lines(booking):
    v1, v2 = booking.assigned_vehicle, booking.assigned_vehicle2
    lines = []
    if v1: lines.append(f"🚐  <b>{v1.brand} {v1.model}</b>  ·  <code>{v1.license_plate}</code>")
    if v2: lines.append(f"🚐  <b>{v2.brand} {v2.model}</b>  ·  <code>{v2.license_plate}</code>")
    return "\n".join(lines) if lines else "🚐  ยังไม่กำหนดรถ"

def _driver_lines(booking):
    if not booking.need_driver:
        return "\n🚗  ขับรถด้วยตัวเอง"
    lines = []
    if booking.driver:  lines.append(f"👨‍✈️  <b>{booking.driver.name}</b>  📞 {booking.driver.phone}")
    if booking.driver2: lines.append(f"👨‍✈️  <b>{booking.driver2.name}</b>  📞 {booking.driver2.phone}")
    return "\n" + "\n".join(lines) if lines else ""

def _time_line(booking):
    d1, d2 = booking.start_datetime, booking.end_datetime
    if _fmt_date(d1) == _fmt_date(d2):
        return f"🗓  {_fmt_date(d1)}\n     {_fmt_time(d1)} → {_fmt_time(d2)} น."
    return (f"🗓  ไป    {_fmt_date(d1)}  {_fmt_time(d1)} น.\n"
            f"🗓  กลับ  {_fmt_date(d2)}  {_fmt_time(d2)} น.")

def _expense_line(booking):
    exp = booking.expense_type
    if exp == 'central':
        cat = f"  ({booking.central_category})" if booking.central_category else ""
        return f"\n💰  ค่าใช้จ่าย: <b>ส่วนกลาง</b>{cat}"
    elif exp == 'department':
        return f"\n💰  ค่าใช้จ่าย: <b>หน่วยงาน</b>"
    elif exp == 'personal':
        return f"\n💰  ค่าใช้จ่าย: <b>ผู้จองออกเอง</b>"
    return ""


# ─────────────────────────────────────────
# 1. Admin อนุมัติทันที
# ─────────────────────────────────────────
def notify_approved(booking):
    delete_old_message(booking)
    group_line = f"\n🔗  กลุ่ม <code>{booking.trip_group}</code>" if booking.trip_group else ""
    text = (
        f"✅  <b>อนุมัติการจองรถ</b>  —  <code>#{booking.id}</code>\n\n"
        f"👤  <b>{booking.user.full_name or booking.user.username}</b>  |  {booking.user.department or '-'}\n"
        f"📍  <b>{booking.destination}</b>\n"
        f"🎯  {booking.purpose or '-'}  ·  👥 {booking.passenger_count} คน"
        f"{_expense_line(booking)}\n\n"
        f"{_time_line(booking)}\n\n"
        f"{_car_lines(booking)}"
        f"{_driver_lines(booking)}"
        f"{group_line}"
    )
    _save_message_id(booking, _send(text))


# ─────────────────────────────────────────
# 2. Admin ส่งต่อให้ Approver
# ─────────────────────────────────────────
def notify_forwarded_to_approver(booking):
    delete_old_message(booking)
    text = (
        f"📨  <b>รอ Approver อนุมัติ</b>  —  <code>#{booking.id}</code>\n\n"
        f"👤  <b>{booking.user.full_name or booking.user.username}</b>  |  {booking.user.department or '-'}\n"
        f"⚠️  <i>Approver แผนก <b>{booking.user.department or '-'}</b> โปรดพิจารณา</i>\n"
        f"📍  <b>{booking.destination}</b>\n"
        f"🎯  {booking.purpose or '-'}  ·  👥 {booking.passenger_count} คน"
        f"{_expense_line(booking)}\n\n"
        f"{_time_line(booking)}\n\n"
        f"{_car_lines(booking)}"
        f"{_driver_lines(booking)}"
    )
    _save_message_id(booking, _send(text))


# ─────────────────────────────────────────
# 3. Approver อนุมัติปิดท้าย
# ─────────────────────────────────────────
def notify_approver_approved(booking, approver):
    delete_old_message(booking)
    text = (
        f"🎉  <b>พร้อมเดินทาง!</b>  —  <code>#{booking.id}</code>\n\n"
        f"👤  <b>{booking.user.full_name or booking.user.username}</b>  |  {booking.user.department or '-'}\n"
        f"📍  <b>{booking.destination}</b>\n"
        f"🎯  {booking.purpose or '-'}  ·  👥 {booking.passenger_count} คน"
        f"{_expense_line(booking)}\n\n"
        f"{_time_line(booking)}\n\n"
        f"{_car_lines(booking)}"
        f"{_driver_lines(booking)}\n\n"
        f"✍️  อนุมัติโดย <b>{approver.full_name or approver.username}</b>"
    )
    _save_message_id(booking, _send(text))


# ─────────────────────────────────────────
# 4. ไม่อนุมัติ
# ─────────────────────────────────────────
def notify_rejected(booking, rejected_by):
    delete_old_message(booking)
    text = (
        f"❌  <b>ไม่อนุมัติ</b>  —  <code>#{booking.id}</code>\n\n"
        f"👤  <b>{booking.user.full_name or booking.user.username}</b>  |  {booking.user.department or '-'}\n"
        f"📍  {booking.destination}\n"
        f"🗓  {_fmt_date(booking.start_datetime)}  {_fmt_time(booking.start_datetime)} น.\n\n"
        f"✍️  ปฏิเสธโดย <b>{rejected_by.full_name or rejected_by.username}</b>"
    )
    _save_message_id(booking, _send(text))