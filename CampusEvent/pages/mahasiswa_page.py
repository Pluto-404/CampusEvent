import os
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
from services import db_sqlite as db
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import qrcode
import requests
from io import BytesIO


class MahasiswaPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.mahasiswa_nim_current = None
        self.build_ui()

    def build_ui(self):
        # ========== TOP SECTION: FORM & TABLE ==========
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=(12,6))

        # ---------- LEFT: FORM LOGIN/REGISTER ----------
        form = ctk.CTkFrame(top)
        form.pack(side="left", padx=12, pady=6, anchor="n")

        ctk.CTkLabel(
            form, 
            text="Registrasi / Login Mahasiswa",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(6,12))

        # Form entries
        self.entry_nim = ctk.CTkEntry(form, width=220, placeholder_text="NIM")
        self.entry_nama = ctk.CTkEntry(form, width=220, placeholder_text="Nama Lengkap")
        self.entry_fakultas = ctk.CTkEntry(form, width=220, placeholder_text="Fakultas")
        self.entry_jurusan = ctk.CTkEntry(form, width=220, placeholder_text="Jurusan")
        self.entry_password = ctk.CTkEntry(form, width=220, show="*", placeholder_text="Password")
        self.entry_password_confirm = ctk.CTkEntry(form, width=220, show="*", placeholder_text="Konfirmasi Password")

        labels = ["NIM:", "Nama:", "Fakultas:", "Jurusan:", "Password:", "Konfirmasi Password:"]
        entries = [
            self.entry_nim, self.entry_nama, self.entry_fakultas, 
            self.entry_jurusan, self.entry_password, self.entry_password_confirm
        ]

        for i, (lbl, ent) in enumerate(zip(labels, entries), start=1):
            ctk.CTkLabel(form, text=lbl, anchor="e").grid(
                row=i, column=0, sticky="e", padx=(6,4), pady=4
            )
            ent.grid(row=i, column=1, pady=4)

        ctk.CTkButton(
            form, 
            text="Registrasi / Masuk",
            command=self.register_or_login,
            fg_color="#4A90E2",
            hover_color="#357ABD"
        ).grid(row=7, column=0, columnspan=2, pady=(10,6))

        # ---------- RIGHT: TABLE KEGIATAN ----------
        right = ctk.CTkFrame(top)
        right.pack(side="left", fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(
            right, 
            text="Daftar Kegiatan",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(6,6), padx=6)

        # Treeview dengan scrollbar
        table_container = ctk.CTkFrame(right)
        table_container.pack(fill="both", expand=True, padx=6, pady=6)

        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient="vertical")
        hsb = ttk.Scrollbar(table_container, orient="horizontal")

        self.keg_tree = ttk.Treeview(
            table_container,
            columns=("id","nama","deskripsi","tanggal","tanggal_tutup","kuota"),
            show="headings",
            height=10,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.keg_tree.yview)
        hsb.config(command=self.keg_tree.xview)

        # Column headings
        headers = {
            "id": "ID",
            "nama": "Nama Kegiatan",
            "deskripsi": "Deskripsi",
            "tanggal": "Tanggal",
            "tanggal_tutup": "Tutup Daftar",
            "kuota": "Kuota"
        }

        for col, txt in headers.items():
            self.keg_tree.heading(col, text=txt, anchor="center")
            if col == "id":
                self.keg_tree.column(col, width=50, anchor="center")
            elif col == "nama":
                self.keg_tree.column(col, width=200, anchor="w")
            elif col == "deskripsi":
                self.keg_tree.column(col, width=300, anchor="w")
            elif col in ["tanggal", "tanggal_tutup"]:
                self.keg_tree.column(col, width=100, anchor="center")
            else:
                self.keg_tree.column(col, width=80, anchor="center")

        # Pack scrollbars and tree
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.keg_tree.pack(fill="both", expand=True)

        # ---------- BUTTONS ----------
        btnframe = ctk.CTkFrame(right)
        btnframe.pack(fill="x", padx=6, pady=6)

        buttons = [
            ("Daftar ke Kegiatan", self.daftar_kegiatan, "#4A90E2"),
            ("Lihat Status", self.lihat_status, "#9B59B6"),
            ("Batal Pendaftaran", self.batal, "#E67E22"),
            ("Cetak E-Ticket", self.cetak_ticket, "#2ECC71")
        ]

        for text, cmd, color in buttons:
            ctk.CTkButton(
                btnframe, 
                text=text, 
                command=cmd,
                fg_color=color,
                hover_color=color,
                width=140
            ).pack(side="left", padx=4)

        # ========== PROFIL SECTION ==========
        self.profil_frame = ctk.CTkFrame(self)
        self.profil_frame.pack(fill="x", padx=12, pady=(6,12))

        ctk.CTkLabel(
            self.profil_frame, 
            text="Profil Mahasiswa Aktif",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(6,6), padx=6)

        profil_inner = ctk.CTkFrame(self.profil_frame)
        profil_inner.pack(fill="x", padx=6, pady=6)

        # Avatar
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            avatar_path = os.path.join(base_dir, "assets", "avatar.png")
            avatar_img = Image.open(avatar_path).resize((100, 100))
            self.avatar_photo = ctk.CTkImage(
                light_image=avatar_img, 
                dark_image=avatar_img, 
                size=(100, 100)
            )
        except Exception as e:
            print(f"⚠️ Gagal load avatar: {e}")
            self.avatar_photo = None

        self.avatar_label = ctk.CTkLabel(profil_inner, image=self.avatar_photo, text="")
        self.avatar_label.pack(side="left", padx=8)

        # Info frame
        info_frame = ctk.CTkFrame(profil_inner)
        info_frame.pack(side="left", fill="both", expand=True, padx=8)

        self.label_nim = ctk.CTkLabel(info_frame, text="NIM: -", anchor="w")
        self.label_nama = ctk.CTkLabel(info_frame, text="Nama: -", anchor="w")
        self.label_fakultas = ctk.CTkLabel(info_frame, text="Fakultas: -", anchor="w")
        self.label_jurusan = ctk.CTkLabel(info_frame, text="Jurusan: -", anchor="w")

        for lbl in [self.label_nim, self.label_nama, self.label_fakultas, self.label_jurusan]:
            lbl.pack(anchor="w", pady=2)

        # Button Ubah Password
        # Logout button (baru)
        ctk.CTkButton(
            profil_inner,
            text="� Logout",
            command=self.logout_mahasiswa,
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            width=120
        ).pack(side="right", padx=8)

        # Button Ubah Password
        ctk.CTkButton(
            profil_inner,
            text="�🔒 Ubah Password",
            command=self.ubah_password,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=140
        ).pack(side="right", padx=8)

        # Refresh daftar kegiatan
        self.refresh_kegiatan()

    # ==================== HELPER FUNCTIONS ====================
    def refresh_kegiatan(self):
        """Refresh daftar kegiatan"""
        for r in self.keg_tree.get_children():
            self.keg_tree.delete(r)
        
        rows = db.get_kegiatan()
        for r in rows:
            # Truncate deskripsi jika terlalu panjang
            desc = r.get("deskripsi", "")
            if len(desc) > 50:
                desc = desc[:47] + "..."
            
            # Kuota sudah otomatis jadi sisa kuota dari database
            self.keg_tree.insert("", "end", values=(
                r["id_kegiatan"], 
                r["nama"], 
                desc,
                r["tanggal_kegiatan"], 
                r.get("tanggal_tutup", "-"),
                r["kuota"]  # Ini sudah sisa kuota
            ))
    def update_profil(self, mahasiswa_data):
        """Update profil display"""
        self.label_nim.configure(text=f"NIM: {mahasiswa_data['nim']}")
        self.label_nama.configure(text=f"Nama: {mahasiswa_data['nama']}")
        self.label_fakultas.configure(text=f"Fakultas: {mahasiswa_data.get('fakultas', '-')}")
        self.label_jurusan.configure(text=f"Jurusan: {mahasiswa_data.get('jurusan', '-')}")

        # ========== GENERATE AVATAR OTOMATIS BERDASARKAN NIM ==========
        try:
            seed = mahasiswa_data["nim"]

            # API Avatar DiceBear (style bisa diganti)
            url = f"https://api.dicebear.com/7.x/bottts/png?seed={seed}"

            # Download avatar
            response = requests.get(url)
            img = Image.open(BytesIO(response.content)).resize((100, 100))

            # Buat CTkImage
            self.avatar_photo = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(100, 100)
            )
            self.avatar_label.configure(image=self.avatar_photo)

        except Exception as e:
            print("Avatar gagal dimuat:", e)


    # ==================== REGISTRASI & LOGIN ====================
    def register_or_login(self):
        """Handle registrasi atau login"""
        nim = self.entry_nim.get().strip()
        nama = self.entry_nama.get().strip()
        fakultas = self.entry_fakultas.get().strip()
        jurusan = self.entry_jurusan.get().strip()
        pw = self.entry_password.get()
        pwc = self.entry_password_confirm.get()

        if not nim:
            messagebox.showwarning("Input Kurang", "NIM wajib diisi!")
            return

        existing = db.get_mahasiswa(nim)

        if existing is None:
            # ===== REGISTRASI BARU =====
            if not all([nama, fakultas, jurusan, pw, pwc]):
                messagebox.showwarning(
                    "Input Kurang", 
                    "Semua field wajib diisi untuk registrasi!"
                )
                return
            
            if pw != pwc:
                messagebox.showwarning("Password Salah", "Password tidak cocok!")
                return
            
            if db.insert_mahasiswa(nim, nama, fakultas, jurusan, password_plain=pw):
                messagebox.showinfo(
                    "Sukses", 
                    "Registrasi berhasil! Anda otomatis login."
                )
                existing = db.get_mahasiswa(nim)
            else:
                messagebox.showerror("Gagal", "Registrasi gagal! NIM mungkin sudah terdaftar.")
                return
        else:
            # ===== LOGIN =====
            if not pw:
                messagebox.showwarning("Input Kurang", "Password wajib diisi!")
                return
            
            if not db.verify_mahasiswa_password(nim, pw):
                messagebox.showerror("Gagal", "Password salah!")
                return
            
            messagebox.showinfo("Sukses", f"Selamat datang, {existing['nama']}!")

        # Update state & profil
        self.mahasiswa_nim_current = nim
        self.update_profil(existing)
        self.refresh_kegiatan()

    # ==================== UBAH PASSWORD ====================
    def ubah_password(self):
        """Ubah password mahasiswa"""
        if not self.mahasiswa_nim_current:
            messagebox.showwarning("Belum Login", "Login terlebih dahulu!")
            return

        # Dialog window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Ubah Password")
        dialog.geometry("400x300")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="🔒 Ubah Password",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 20))

        # Form
        form = ctk.CTkFrame(dialog)
        form.pack(padx=20, pady=10)

        ctk.CTkLabel(form, text="Password Lama:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        entry_old = ctk.CTkEntry(form, show="*", width=200)
        entry_old.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Password Baru:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        entry_new = ctk.CTkEntry(form, show="*", width=200)
        entry_new.grid(row=1, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Konfirmasi Baru:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        entry_confirm = ctk.CTkEntry(form, show="*", width=200)
        entry_confirm.grid(row=2, column=1, padx=5, pady=8)

        def simpan_password():
            pw_lama = entry_old.get()
            pw_baru = entry_new.get()
            pw_confirm = entry_confirm.get()

            if not all([pw_lama, pw_baru, pw_confirm]):
                messagebox.showwarning("Input Kurang", "Semua field harus diisi!")
                return

            # Verifikasi password lama
            if not db.verify_mahasiswa_password(self.mahasiswa_nim_current, pw_lama):
                messagebox.showerror("Gagal", "Password lama salah!")
                return

            # Cek konfirmasi
            if pw_baru != pw_confirm:
                messagebox.showerror("Gagal", "Konfirmasi password tidak cocok!")
                return

            # Cek password baru tidak sama dengan lama
            if pw_lama == pw_baru:
                messagebox.showwarning("Perhatian", "Password baru harus berbeda dengan yang lama!")
                return

            # Update password
            if db.update_mahasiswa_password(self.mahasiswa_nim_current, pw_baru):
                messagebox.showinfo("Sukses", "Password berhasil diubah!")
                dialog.destroy()
            else:
                messagebox.showerror("Gagal", "Gagal mengubah password!")

        # Buttons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Simpan",
            command=simpan_password,
            fg_color="#2ECC71",
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Batal",
            command=dialog.destroy,
            fg_color="#95A5A6",
            width=120
        ).pack(side="left", padx=5)

    def logout_mahasiswa(self):
        """Logout mahasiswa: reset state, clear profile and form entries"""
        if self.mahasiswa_nim_current:
            # Reset state
            self.mahasiswa_nim_current = None

            # Reset profile labels
            try:
                self.label_nim.configure(text="NIM: -")
                self.label_nama.configure(text="Nama: -")
                self.label_fakultas.configure(text="Fakultas: -")
                self.label_jurusan.configure(text="Jurusan: -")
            except Exception:
                pass

            # Clear form fields
            try:
                for e in [
                    self.entry_nim, self.entry_nama, self.entry_fakultas,
                    self.entry_jurusan, self.entry_password, self.entry_password_confirm
                ]:
                    e.delete(0, 'end')
            except Exception:
                pass

            # Refresh kegiatan (optional: show all but as non-logged user)
            try:
                self.refresh_kegiatan()
            except Exception:
                pass

            messagebox.showinfo("Logout", "Anda telah logout.")
        else:
            messagebox.showinfo("Info", "Anda belum login.")

    # ==================== DAFTAR KEGIATAN ====================
    def daftar_kegiatan(self):
        """Daftar ke kegiatan"""
        if not self.mahasiswa_nim_current:
            messagebox.showwarning("Belum Login", "Login terlebih dahulu!")
            return
        
        sel = self.keg_tree.selection()
        if not sel:
            messagebox.showwarning("Pilih Kegiatan", "Pilih kegiatan terlebih dahulu!")
            return
        
        id_keg = int(self.keg_tree.item(sel[0])['values'][0])
        ok, msg = db.daftar_event(self.mahasiswa_nim_current, id_keg)
        
        if ok:
            messagebox.showinfo("Sukses", msg)
            self.refresh_kegiatan()
        else:
            messagebox.showerror("Gagal", msg)

    # ==================== LIHAT STATUS ====================
    def lihat_status(self):
        """Lihat status pendaftaran"""
        if not self.mahasiswa_nim_current:
            messagebox.showwarning("Belum Login", "Login terlebih dahulu!")
            return
        
        rows = db.get_pendaftaran_mahasiswa(self.mahasiswa_nim_current)
        if not rows:
            messagebox.showinfo("Status", "Belum ada pendaftaran.")
            return
        
        # Window baru
        win = ctk.CTkToplevel(self)
        win.title("Status Pendaftaran")
        win.geometry("900x400")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="📋 Status Pendaftaran Anda",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        # Treeview
        tree = ttk.Treeview(
            win, 
            columns=("id","nama","deskripsi","tanggal","kode"), 
            show="headings"
        )
        
        tree.heading("id", text="ID", anchor="center")
        tree.heading("nama", text="Nama Kegiatan", anchor="center")
        tree.heading("deskripsi", text="Deskripsi", anchor="center")
        tree.heading("tanggal", text="Tanggal Daftar", anchor="center")
        tree.heading("kode", text="Kode Tiket", anchor="center")

        tree.column("id", width=50, anchor="center")
        tree.column("nama", width=250, anchor="w")
        tree.column("deskripsi", width=300, anchor="w")
        tree.column("tanggal", width=150, anchor="center")
        tree.column("kode", width=100, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        for r in rows:
            desc = r.get("deskripsi", "")
            if len(desc) > 40:
                desc = desc[:37] + "..."
            tree.insert("", "end", values=(
                r["id_kegiatan"], 
                r["nama"], 
                desc,
                r["tanggal_daftar"],
                r["kode_tiket"]
            ))

        ctk.CTkButton(
            win,
            text="Tutup",
            command=win.destroy,
            fg_color="#95A5A6"
        ).pack(pady=10)

    # ==================== BATAL PENDAFTARAN ====================
    def batal(self):
        """Batalkan pendaftaran"""
        if not self.mahasiswa_nim_current:
            messagebox.showwarning("Belum Login", "Login terlebih dahulu!")
            return
        
        sel = self.keg_tree.selection()
        if not sel:
            messagebox.showwarning("Pilih Kegiatan", "Pilih kegiatan terlebih dahulu!")
            return
        
        id_keg = int(self.keg_tree.item(sel[0])['values'][0])
        nama_keg = self.keg_tree.item(sel[0])['values'][1]
        
        if messagebox.askyesno("Konfirmasi", f"Yakin batal dari '{nama_keg}'?"):
            ok = db.batal_pendaftaran(self.mahasiswa_nim_current, id_keg)
            if ok:
                messagebox.showinfo("Sukses", "Berhasil dibatalkan!")
                self.refresh_kegiatan()
            else:
                messagebox.showerror("Gagal", "Tidak ada pendaftaran ditemukan!")

    # ==================== CETAK E-TICKET ====================
    def generate_ticket(self, filename, mahasiswa, kegiatan, kode_tiket):
        """Generate PDF ticket"""
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height-50, "BUKTI PENDAFTARAN KEGIATAN")
        
        # Line
        c.line(50, height-70, width-50, height-70)
        
        # Data Mahasiswa
        c.setFont("Helvetica-Bold", 14)
        c.drawString(80, height-110, "Data Mahasiswa:")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height-140, f"Nama     : {mahasiswa['nama']}")
        c.drawString(100, height-160, f"NIM      : {mahasiswa['nim']}")
        c.drawString(100, height-180, f"Fakultas : {mahasiswa.get('fakultas', '-')}")
        c.drawString(100, height-200, f"Jurusan  : {mahasiswa.get('jurusan', '-')}")
        
        # Data Kegiatan
        c.setFont("Helvetica-Bold", 14)
        c.drawString(80, height-240, "Data Kegiatan:")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height-270, f"Kegiatan : {kegiatan['nama']}")
        c.drawString(100, height-290, f"Tanggal  : {kegiatan['tanggal_kegiatan']}")
        
        # Kode Tiket
        c.setFont("Helvetica-Bold", 14)
        c.drawString(80, height-330, f"Kode Tiket: {kode_tiket}")
        
        # QR Code
        qr = qrcode.make(kode_tiket)
        qr_temp = "qr_temp.png"
        qr.save(qr_temp)
        c.drawImage(qr_temp, width-220, height-350, 150, 150)
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width/2, 50, "Tunjukkan tiket ini saat kegiatan berlangsung")
        c.drawCentredString(width/2, 35, "Campus Event Management System")
        
        c.save()
        
        # Cleanup
        if os.path.exists(qr_temp):
            os.remove(qr_temp)

    def cetak_ticket(self):
        """Cetak e-ticket"""
        if not self.mahasiswa_nim_current:
            messagebox.showwarning("Belum Login", "Login terlebih dahulu!")
            return

        rows = db.get_pendaftaran_mahasiswa(self.mahasiswa_nim_current)
        if not rows:
            messagebox.showinfo("Info", "Belum ada pendaftaran.")
            return

        # Dialog pilih kegiatan
        win = ctk.CTkToplevel(self)
        win.title("Pilih Kegiatan untuk Cetak Tiket")
        win.geometry("700x400")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="🎫 Pilih Kegiatan untuk Cetak Tiket",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        tree = ttk.Treeview(
            win,
            columns=("id","nama","tanggal","kode"),
            show="headings"
        )
        
        for col, txt, w in [("id","ID",50), ("nama","Nama Kegiatan",300), 
                             ("tanggal","Tanggal",150), ("kode","Kode Tiket",100)]:
            tree.heading(col, text=txt, anchor="center")
            tree.column(col, width=w, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for r in rows:
            tree.insert("", "end", values=(
                r["id_kegiatan"],
                r["nama"],
                r["tanggal_kegiatan"],
                r["kode_tiket"]
            ))

        def cetak_terpilih():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Pilih", "Pilih kegiatan terlebih dahulu!")
                return

            values = tree.item(sel[0])['values']
            id_keg = values[0]
            kode = values[3]

            kegiatan = db.get_kegiatan_by_id(id_keg)
            mahasiswa = db.get_mahasiswa(self.mahasiswa_nim_current)

            default_name = f"ticket_{mahasiswa['nim']}_{id_keg}.pdf"
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=default_name,
                filetypes=[("PDF files", "*.pdf")],
                title="Simpan E-Ticket"
            )

            if filename:
                self.generate_ticket(filename, mahasiswa, kegiatan, kode)
                messagebox.showinfo("Sukses", f"Tiket berhasil disimpan!\n{filename}")
                win.destroy()

        ctk.CTkButton(
            win,
            text="Cetak Tiket",
            command=cetak_terpilih,
            fg_color="#2ECC71",
            width=150
        ).pack(pady=10)