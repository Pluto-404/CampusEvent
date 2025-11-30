import sqlite3
import bcrypt
import csv
import uuid
import os
import datetime
from datetime import timezone, timedelta

# Path absolut ke database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eventcampus.db")

def get_wib_time():
    """Dapatkan waktu WIB (UTC+7)"""
    wib = datetime.datetime.now(timezone(timedelta(hours=7)))
    return wib.strftime("%Y-%m-%d %H:%M:%S")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ------------------ CREATE TABLES ------------------
def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS mahasiswa (
        nim TEXT PRIMARY KEY,
        nama TEXT NOT NULL,
        fakultas TEXT,
        jurusan TEXT,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS kegiatan (
        id_kegiatan INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        deskripsi TEXT,
        kuota INTEGER DEFAULT 0,
        tanggal_kegiatan DATE NOT NULL,
        tanggal_tutup DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pendaftaran (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nim TEXT NOT NULL,
        id_kegiatan INTEGER NOT NULL,
        tanggal_daftar TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        kode_tiket TEXT UNIQUE,
        FOREIGN KEY (nim) REFERENCES mahasiswa(nim) ON DELETE CASCADE,
        FOREIGN KEY (id_kegiatan) REFERENCES kegiatan(id_kegiatan) ON DELETE CASCADE,
        UNIQUE(nim, id_kegiatan)
    );
    """)
    conn.commit()

    # Seed admin
    admins = [
        ("Umar Adiwinata", "K3524068", "Administrator 1"),
        ("Fatih Nur Faiq", "K3524052", "Administrator 2"),
        ("Muhammad Raihan Faza", "K3524060", "Administrator 3"),
    ]
    for uname, pw, nama in admins:
        cur.execute("SELECT id FROM admin WHERE username=?", (uname,))
        if not cur.fetchone():
            pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            cur.execute("INSERT INTO admin (username, password, nama) VALUES (?, ?, ?)",
                        (uname, pw_hash, nama))
    conn.commit()
    conn.close()
    print("✅ Database SQLite berhasil dibuat!")

# ------------------ ADMIN ------------------
def get_admin(username):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def verify_password(password_plain, password_hashed):
    try:
        return bcrypt.checkpw(password_plain.encode(), password_hashed.encode())
    except Exception:
        return False

# ------------------ MAHASISWA ------------------
def insert_mahasiswa(nim, nama, fakultas, jurusan, password_plain=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        pw_hash = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt()).decode() if password_plain else None
        cur.execute("INSERT INTO mahasiswa (nim, nama, fakultas, jurusan, password) VALUES (?, ?, ?, ?, ?)",
                    (nim, nama, fakultas, jurusan, pw_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_mahasiswa(nim):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM mahasiswa WHERE nim=?", (nim,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_mahasiswa_password(nim, password_plain):
    m = get_mahasiswa(nim)
    if not m or not m.get("password"):
        return False
    return bcrypt.checkpw(password_plain.encode(), m["password"].encode())

def update_mahasiswa_password(nim, password_baru):
    """Update password mahasiswa"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        pw_hash = bcrypt.hashpw(password_baru.encode(), bcrypt.gensalt()).decode()
        cur.execute("UPDATE mahasiswa SET password=? WHERE nim=?", (pw_hash, nim))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# ------------------ KEGIATAN ------------------
def insert_kegiatan(nama, deskripsi, kuota, tanggal, tanggal_tutup=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO kegiatan (nama, deskripsi, kuota, tanggal_kegiatan, tanggal_tutup) VALUES (?, ?, ?, ?, ?)",
        (nama, deskripsi, kuota, tanggal, tanggal_tutup)
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def get_kegiatan():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            k.id_kegiatan,
            k.nama,
            k.deskripsi,
            k.kuota,
            k.tanggal_kegiatan,
            k.tanggal_tutup,
            k.created_at,
            (k.kuota - COUNT(p.nim)) as kuota_sisa,
            COUNT(p.nim) as peserta_terdaftar
        FROM kegiatan k
        LEFT JOIN pendaftaran p ON k.id_kegiatan = p.id_kegiatan
        GROUP BY k.id_kegiatan
        ORDER BY k.id_kegiatan
    """)
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        data = dict(r)
        # Ganti kuota dengan sisa kuota
        data['kuota'] = data['kuota_sisa']
        result.append(data)
    return result

def get_kegiatan_by_id(id_kegiatan):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM kegiatan WHERE id_kegiatan=?", (id_kegiatan,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_kegiatan(id_kegiatan, nama, deskripsi, kuota, tanggal, tanggal_tutup=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """UPDATE kegiatan 
               SET nama=?, deskripsi=?, kuota=?, tanggal_kegiatan=?, tanggal_tutup=? 
               WHERE id_kegiatan=?""",
            (nama, deskripsi, kuota, tanggal, tanggal_tutup, id_kegiatan)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def delete_kegiatan(id_kegiatan):
    """Hapus kegiatan beserta pendaftaran terkait (CASCADE)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM kegiatan WHERE id_kegiatan=?", (id_kegiatan,))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

# ------------------ PENDAFTARAN ------------------
def daftar_event(nim, id_kegiatan):
    """Daftar mahasiswa ke event dengan validasi lengkap"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ambil data kegiatan
    cur.execute("SELECT * FROM kegiatan WHERE id_kegiatan=?", (id_kegiatan,))
    keg = cur.fetchone()
    
    if not keg:
        conn.close()
        return False, "Kegiatan tidak ditemukan."

    hari_ini = datetime.date.today()

    # ✅ 1. Cek tanggal tutup pendaftaran
    if keg["tanggal_tutup"]:
        try:
            tanggal_tutup = datetime.datetime.strptime(keg["tanggal_tutup"], "%Y-%m-%d").date()
            if hari_ini > tanggal_tutup:
                conn.close()
                return False, f"Pendaftaran sudah ditutup sejak {tanggal_tutup}."
        except Exception:
            conn.close()
            return False, "Format tanggal tutup tidak valid!"

    # ✅ 2. Cek apakah kegiatan sudah lewat
    try:
        tanggal_kegiatan = datetime.datetime.strptime(keg["tanggal_kegiatan"], "%Y-%m-%d").date()
        if hari_ini > tanggal_kegiatan:
            conn.close()
            return False, "Kegiatan sudah dilaksanakan."
    except Exception:
        conn.close()
        return False, "Format tanggal kegiatan tidak valid!"

    #3. Cek kuota (REAL-TIME)
    cur.execute("SELECT COUNT(*) FROM pendaftaran WHERE id_kegiatan=?", (id_kegiatan,))
    jml = cur.fetchone()[0]
    sisa_kuota = keg["kuota"] - jml
    
    if sisa_kuota <= 0:
        conn.close()
        return False, "Kuota penuh."

    # ✅ 4. Cek apakah mahasiswa valid
    cur.execute("SELECT * FROM mahasiswa WHERE nim=?", (nim,))
    if not cur.fetchone():
        conn.close()
        return False, "Mahasiswa tidak terdaftar."

    # ✅ 5. Tambahkan pendaftaran
    # ✅ 5. Tambahkan pendaftaran
    kode = str(uuid.uuid4())[:8].upper()
    try:
        cur.execute(
            "INSERT INTO pendaftaran (nim, id_kegiatan, kode_tiket, tanggal_daftar) VALUES (?, ?, ?, ?)",
            (nim, id_kegiatan, kode, get_wib_time())
        )
        conn.commit()
        conn.close()
        return True, f"Berhasil daftar ke '{keg['nama']}'! Kode tiket: {kode}\nSisa kuota: {sisa_kuota - 1}"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Anda sudah terdaftar di kegiatan ini."

def batal_pendaftaran(nim, id_kegiatan):
    """Batalkan pendaftaran mahasiswa"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM pendaftaran WHERE nim=? AND id_kegiatan=?", (nim, id_kegiatan))
        conn.commit()
        ok = cur.rowcount > 0
        conn.close()
        return ok
    except Exception:
        conn.close()
        return False

def get_pendaftaran_mahasiswa(nim):
    """Ambil semua pendaftaran mahasiswa"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT k.id_kegiatan, k.nama, k.deskripsi, k.tanggal_kegiatan, 
               p.tanggal_daftar, p.kode_tiket
        FROM pendaftaran p
        JOIN kegiatan k ON p.id_kegiatan = k.id_kegiatan
        WHERE p.nim=?
        ORDER BY p.tanggal_daftar DESC
    """, (nim,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ------------------ PESERTA ------------------
def get_peserta_per_kegiatan(id_kegiatan):
    """Ambil daftar peserta untuk kegiatan tertentu"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT m.nim, m.nama, m.fakultas, m.jurusan, p.tanggal_daftar, p.kode_tiket
        FROM mahasiswa m
        JOIN pendaftaran p ON p.nim = m.nim
        WHERE p.id_kegiatan = ?
        ORDER BY p.tanggal_daftar
    """, (id_kegiatan,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ------------------ EXPORT ------------------
def export_peserta_csv(id_kegiatan, filename):
    """Export peserta ke CSV"""
    try:
        peserta = get_peserta_per_kegiatan(id_kegiatan)
        
        if not peserta:
            return False

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["NIM", "Nama", "Fakultas", "Jurusan", "Tanggal Daftar", "Kode Tiket"])
            for p in peserta:
                writer.writerow([
                    p['nim'], p['nama'], 
                    p.get('fakultas', '-'), 
                    p.get('jurusan', '-'),
                    p['tanggal_daftar'], 
                    p['kode_tiket']
                ])
        return True
    except Exception as e:
        print(f"[ERROR] Gagal ekspor CSV: {e}")
        return False

def export_peserta_pdf(id_kegiatan, filename):
    """Export peserta ke PDF"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        peserta = get_peserta_per_kegiatan(id_kegiatan)
        kegiatan = get_kegiatan_by_id(id_kegiatan)
        
        if not peserta:
            return False
        
        # Create PDF
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                                rightMargin=20, leftMargin=20, 
                                topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        style_cell = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            wordWrap='CJK'
        )
        
        elements = []
        
        # Title
        title = Paragraph(f"<b>Daftar Peserta: {kegiatan['nama']}</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Table data
        data = [["No", "NIM", "Nama", "Fakultas", "Jurusan", "Tanggal Daftar", "Kode Tiket"]]
        for i, p in enumerate(peserta, 1):
            data.append([
                str(i),
                Paragraph(p['nim'], style_cell),
                Paragraph(p['nama'], style_cell),
                Paragraph(p.get('fakultas', '-'), style_cell),
                Paragraph(p.get('jurusan', '-'), style_cell),
                Paragraph(p['tanggal_daftar'], style_cell),
                Paragraph(p['kode_tiket'], style_cell)
            ])
        
        # Create table
        col_widths = [30, 70, 120, 140, 140, 100, 80]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return True
    except ImportError:
        print("[ERROR] ReportLab tidak terinstall!")
        return False
    except Exception as e:
        print(f"[ERROR] Gagal ekspor PDF: {e}")
        return False

# ------------------ DASHBOARD ------------------
def dashboard():
    """Ambil statistik kegiatan"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            k.id_kegiatan,
            k.nama, 
            k.kuota, 
            k.tanggal_kegiatan,
            COUNT(p.nim) as jumlah_peserta
        FROM kegiatan k
        LEFT JOIN pendaftaran p ON k.id_kegiatan = p.id_kegiatan
        GROUP BY k.id_kegiatan, k.nama, k.kuota, k.tanggal_kegiatan
        ORDER BY k.id_kegiatan
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    create_tables()
