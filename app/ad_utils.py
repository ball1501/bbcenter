import os
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL

# โหลดค่าต่างๆ จากไฟล์ .env เข้ามาในระบบ
load_dotenv()

# ==========================================
# 🛑 ดึงค่าเซิร์ฟเวอร์ AD จาก Environment Variables 🛑
# ==========================================
AD_SERVER = os.getenv('AD_SERVER')
AD_DOMAIN = os.getenv('AD_DOMAIN')
SEARCH_BASE = os.getenv('SEARCH_BASE')

def check_ad_login(username, password):
    """
    ฟังก์ชันเช็กรหัสผ่านกับ AD และดึงข้อมูลพื้นฐานกลับมา
    """
    # 1. กำหนดเป้าหมาย Server
    server = Server(AD_SERVER, get_info=ALL)
    
    # 2. จัดรูปแบบ Username สำหรับล็อกอินเข้า AD (มักใช้รูปแบบ user@domain.local)
    ad_user_login = f"{username}@{AD_DOMAIN}"
    
    try:
        # 3. พยายามเชื่อมต่อและ Bind (ล็อกอิน)
        conn = Connection(server, user=ad_user_login, password=password, auto_bind=True)
        
        # 4. ค้นหาข้อมูลของ User คนนี้เพิ่มเติม (เช่น ชื่อ-นามสกุล, อีเมล, แผนก)
        conn.search(
            search_base=SEARCH_BASE,
            search_filter=f'(sAMAccountName={username})',
            attributes=['cn', 'mail', 'department']
        )
        
        user_info = {
            'full_name': username,
            'email': None,
            'department': None
        }
        
        if conn.entries:
            entry = conn.entries[0]
            if 'cn' in entry: user_info['full_name'] = str(entry.cn.value)
            if 'mail' in entry: user_info['email'] = str(entry.mail.value)
            if 'department' in entry: user_info['department'] = str(entry.department.value)
            
        conn.unbind()
        return True, user_info

    except Exception as e:
        print(f"AD Error for user {username}: {e}")
        return False, None