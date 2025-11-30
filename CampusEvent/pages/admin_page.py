import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog, filedialog
from services import db_sqlite as db
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AdminPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.admin_logged_in = None
        self.build_ui()

    def build_ui(self):
        # ========== TOP: STATUS LOGIN ==========
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=(12, 6))
        
        self.admin_status_label = ctk.CTkLabel(
            top, 
            text="Admin: belum login", 
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.admin_status_label.pack(side="left", padx=6)
        
        ctk.CTkButton(
            top, 
            text="Logout", 
            command=self.logout_admin, 
            width=120,
            fg_color="#E74C3C",
            hover_color="#C0392B"
        ).pack(side="right", padx=6)
        
        ctk.CTkButton(
            top, 
            text="Login Admin", 
            command=self.login_admin, 
            width=120,
            fg_color="#3498DB",
            hover_color="#2980B9"
        ).pack(side="right", padx=6)

        # ========== MAIN CONTENT: 2 COLUMN ==========
        tabs_frame = ctk.CTkFrame(self)
        tabs_frame.pack(fill="both", expand=True, padx=12, pady=6)

        # ---------- LEFT COLUMN: FORM TAMBAH + PESERTA (scrollable) ----------
        # Buat sebuah container dengan Canvas + Scrollbar agar isi kiri bisa discroll
        import tkinter as tk

        left_container = ctk.CTkFrame(tabs_frame, width=400)
        left_container.pack(side="left", fill="y", padx=(0, 12), pady=(8, 8))
        left_container.pack_propagate(False)

        # Canvas standar untuk scrollable region
        left_canvas = tk.Canvas(left_container, borderwidth=0, highlightthickness=0)
        vsb_left = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=vsb_left.set)

        vsb_left.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        # Frame CTk di dalam canvas — semua widget kiri akan ditambahkan ke `left`
        left = ctk.CTkFrame(left_canvas)
        left_window = left_canvas.create_window((0, 0), window=left, anchor="nw")

        # Update scrollregion saat isi frame berubah
        def _on_left_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        left.bind("<Configure>", _on_left_configure)

        # Pastikan lebar anak menyesuaikan lebar canvas
        def _on_canvas_configure(event):
            try:
                left_canvas.itemconfig(left_window, width=event.width)
            except Exception:
                pass

        left_canvas.bind("<Configure>", _on_canvas_configure)

        # Enable mouse wheel scrolling (Windows)
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ===== FORM TAMBAH KEGIATAN =====
        ctk.CTkLabel(
            left,
            text="Tambah Kegiatan",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="center", pady=(4, 6))

        form_frame = ctk.CTkFrame(left)
        form_frame.pack(fill="x", padx=8, pady=(0, 8))

        # ========== INPUT: NAMA ==========
        ctk.CTkLabel(form_frame, text="Nama Kegiatan:", anchor="w").pack(anchor="w", padx=6, pady=(3, 1))
        self.admin_entry_nama_keg = ctk.CTkEntry(form_frame, width=360, placeholder_text="Contoh: Seminar AI")
        self.admin_entry_nama_keg.pack(padx=6, pady=(0, 4))

        # ========== INPUT: DESKRIPSI ==========
        ctk.CTkLabel(form_frame, text="Deskripsi:", anchor="w").pack(anchor="w", padx=6, pady=(3, 1))
        try:
            self.admin_entry_desk = ctk.CTkTextbox(form_frame, height=70, width=360)
        except Exception:
            import tkinter as tk
            self.admin_entry_desk = tk.Text(form_frame, height=4, width=45)
        self.admin_entry_desk.pack(padx=6, pady=(0, 4))

        # ========== INPUT: KUOTA ==========
        ctk.CTkLabel(form_frame, text="Kuota Peserta:", anchor="w").pack(anchor="w", padx=6, pady=(3, 1))
        self.admin_entry_kuota = ctk.CTkEntry(form_frame, width=120, placeholder_text="Contoh: 100")
        self.admin_entry_kuota.pack(padx=6, pady=(0, 4), anchor="w")

        # ========== INPUT: TANGGAL ==========
        ctk.CTkLabel(form_frame, text="Tanggal Kegiatan (YYYY-MM-DD):", anchor="w").pack(anchor="w", padx=6, pady=(3, 1))
        self.admin_entry_tanggal = ctk.CTkEntry(form_frame, width=180, placeholder_text="2025-12-31")
        self.admin_entry_tanggal.pack(padx=6, pady=(0, 4), anchor="w")

        # ========== INPUT: TANGGAL TUTUP ==========
        ctk.CTkLabel(form_frame, text="Tanggal Tutup Pendaftaran (Opsional):", anchor="w").pack(anchor="w", padx=6, pady=(3, 1))
        self.admin_entry_tanggal_tutup = ctk.CTkEntry(form_frame, width=180, placeholder_text="2025-12-20")
        self.admin_entry_tanggal_tutup.pack(padx=6, pady=(0, 4), anchor="w")

        # ========== BUTTON TAMBAH ==========
        ctk.CTkButton(
            left,
            text="➕ Tambah Kegiatan",
            command=self.tambah_kegiatan,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            height=32,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(padx=10, pady=(6, 10))

        # ========== SEPARATOR ==========
        ttk.Separator(left, orient="horizontal").pack(fill="x", padx=10, pady=(4, 6))

        # ===== LIHAT PESERTA =====
        ctk.CTkLabel(
            left,
            text="Lihat Peserta per Kegiatan",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="center", pady=(4, 6))

        peserta_frame = ctk.CTkFrame(left)
        peserta_frame.pack(fill="x", padx=8, pady=(0, 6))

        ctk.CTkLabel(peserta_frame, text="ID Kegiatan:", anchor="w").pack(anchor="w", padx=6, pady=(2, 1))
        self.admin_entry_idpeserta = ctk.CTkEntry(peserta_frame, width=120, placeholder_text="Contoh: 1")
        self.admin_entry_idpeserta.pack(padx=6, pady=(0, 6), anchor="w")

        # ========== BUTTON LIHAT PESERTA ==========
        ctk.CTkButton(
            left,
            text="👥 Tampilkan Peserta",
            command=self.tampilkan_peserta,
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(padx=10, pady=(6, 8))

        # ---------- RIGHT COLUMN: TABEL KEGIATAN + BUTTONS ----------
        right = ctk.CTkFrame(tabs_frame)
        right.pack(side="left", fill="both", expand=True, pady=6)

        ctk.CTkLabel(
            right, 
            text="Daftar Kegiatan (Admin)", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=8, pady=(8, 8))

        # ===== TREEVIEW DENGAN SCROLLBAR =====
        table_frame = ctk.CTkFrame(right)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        self.admin_keg_tree = ttk.Treeview(
            table_frame,
            columns=("id", "nama", "deskripsi", "tanggal", "tanggal_tutup", "kuota", "peserta"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        
        vsb.config(command=self.admin_keg_tree.yview)
        hsb.config(command=self.admin_keg_tree.xview)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Headings
        headers = {
            "id": "ID",
            "nama": "Nama Kegiatan",
            "deskripsi": "Deskripsi",
            "tanggal": "Tanggal",
            "tanggal_tutup": "Tutup Daftar",
            "kuota": "Kuota",
            "peserta": "Peserta"
        }

        for col, txt in headers.items():
            self.admin_keg_tree.heading(col, text=txt, anchor="center")

        # Column widths
        self.admin_keg_tree.column("id", width=50, anchor="center")
        self.admin_keg_tree.column("nama", width=200, anchor="w")
        self.admin_keg_tree.column("deskripsi", width=300, anchor="w")
        self.admin_keg_tree.column("tanggal", width=100, anchor="center")
        self.admin_keg_tree.column("tanggal_tutup", width=100, anchor="center")
        self.admin_keg_tree.column("kuota", width=70, anchor="center")
        self.admin_keg_tree.column("peserta", width=70, anchor="center")

        self.admin_keg_tree.pack(fill="both", expand=True)

        # ===== ACTION BUTTONS =====
        btnframe_admin = ctk.CTkFrame(right)
        btnframe_admin.pack(fill="x", padx=8, pady=10)

        buttons = [
            ("🗑️ Hapus", self.hapus_kegiatan, "#E74C3C", "#C0392B"),
            ("✏️ Edit", self.edit_kegiatan, "#3498DB", "#2980B9"),
            ("📥 Export", self.export_peserta, "#2ECC71", "#27AE60"),
            ("📊 Dashboard", self.show_dashboard, "#1ABC9C", "#16A085")
        ]

        for text, cmd, fg, hover in buttons:
            ctk.CTkButton(
                btnframe_admin, 
                text=text, 
                width=160, 
                height=35,
                fg_color=fg, 
                hover_color=hover,
                command=cmd,
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left", padx=4)

        # Refresh tabel
        self.refresh_admin_kegiatan()

    # ==================== LOGIN/LOGOUT ADMIN ====================
    def login_admin(self):
        """Login admin dengan password tersembunyi"""
        # Custom dialog untuk login
        dialog = ctk.CTkToplevel(self)
        dialog.title("Login Admin")
        dialog.geometry("400x300")
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        ctk.CTkLabel(
            dialog,
            text="🔐 Login Admin",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 20))
        
        # Form frame
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(padx=30, pady=10)
        
        # Username
        ctk.CTkLabel(
            form_frame,
            text="Username:",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="e", padx=(10, 10), pady=10)
        
        entry_username = ctk.CTkEntry(
            form_frame,
            width=220,
            placeholder_text="Masukkan username"
        )
        entry_username.grid(row=0, column=1, pady=10)
        entry_username.focus()  # Auto focus
        
        # Password
        ctk.CTkLabel(
            form_frame,
            text="Password:",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="e", padx=(10, 10), pady=10)
        
        entry_password = ctk.CTkEntry(
            form_frame,
            width=220,
            show="*",  # PENTING! Ini yang bikin password tersembunyi
            placeholder_text="Masukkan password"
        )
        entry_password.grid(row=1, column=1, pady=10)
        
        # Variable untuk hasil
        login_result = {"success": False}
        
        def do_login():
            username = entry_username.get().strip()
            password = entry_password.get().strip()
            
            if not username or not password:
                messagebox.showwarning("Input Kurang", "Username dan password harus diisi!")
                return
            
            admin = db.get_admin(username)
            if not admin:
                messagebox.showerror("Gagal", "Admin tidak ditemukan!")
                return
            
            if not db.verify_password(password, admin.get("password")):
                messagebox.showerror("Gagal", "Password salah!")
                return
            
            # Login berhasil
            self.admin_logged_in = username
            self.admin_status_label.configure(
                text=f"Admin: {admin.get('username', username)}"
            )
            login_result["success"] = True
            dialog.destroy()
            messagebox.showinfo(
                "Sukses", 
                f"Selamat datang, {admin.get('username', username)}!"
            )
            self.refresh_admin_kegiatan()
        
        # Button frame
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Login",
            command=do_login,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            width=120,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Batal",
            command=dialog.destroy,
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            width=120,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=5)
        
        # Bind Enter key untuk login
        entry_username.bind('<Return>', lambda e: entry_password.focus())
        entry_password.bind('<Return>', lambda e: do_login())
        
        # Wait for dialog to close
        dialog.wait_window()
    def logout_admin(self):
        """Logout admin"""
        if self.admin_logged_in:
            self.admin_logged_in = None
            self.admin_status_label.configure(text="Admin: belum login")
            messagebox.showinfo("Logout", "Anda telah logout.")
        else:
            messagebox.showinfo("Info", "Anda belum login.")

    # ==================== CRUD KEGIATAN ====================
    def tambah_kegiatan(self):
        """Tambah kegiatan baru"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return

        nama = self.admin_entry_nama_keg.get().strip()
        try:
            desk = self.admin_entry_desk.get("0.0", "end").strip()
        except Exception:
            desk = self.admin_entry_desk.get("1.0", "end").strip()

        kuota = self.admin_entry_kuota.get().strip()
        tanggal = self.admin_entry_tanggal.get().strip()
        tanggal_tutup = self.admin_entry_tanggal_tutup.get().strip()

        if not all([nama, kuota, tanggal]):
            messagebox.showwarning("Input Kurang", "Nama, Kuota, dan Tanggal wajib diisi!")
            return

        try:
            kuota_int = int(kuota)
            if kuota_int <= 0:
                raise ValueError("Kuota harus lebih dari 0")
        except ValueError as e:
            messagebox.showerror("Error", f"Kuota tidak valid: {e}")
            return

        # Validasi format tanggal
        import datetime
        try:
            datetime.datetime.strptime(tanggal, "%Y-%m-%d")
            if tanggal_tutup:
                datetime.datetime.strptime(tanggal_tutup, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Format tanggal salah! Gunakan YYYY-MM-DD")
            return

        try:
            db.insert_kegiatan(
                nama, desk, kuota_int, tanggal, 
                tanggal_tutup if tanggal_tutup else None
            )
            messagebox.showinfo("Sukses", "Kegiatan berhasil ditambahkan!")
            
            # Clear form
            self.admin_entry_nama_keg.delete(0, "end")
            self.admin_entry_desk.delete("0.0", "end")
            self.admin_entry_kuota.delete(0, "end")
            self.admin_entry_tanggal.delete(0, "end")
            self.admin_entry_tanggal_tutup.delete(0, "end")
            
            self.refresh_admin_kegiatan()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menambah kegiatan: {e}")

    def edit_kegiatan(self):
        """Edit kegiatan"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return

        sel = self.admin_keg_tree.selection()
        if not sel:
            messagebox.showwarning("Pilih", "Pilih kegiatan yang ingin diedit!")
            return

        item = self.admin_keg_tree.item(sel[0])["values"]
        id_keg = int(item[0])
        keg = db.get_kegiatan_by_id(id_keg)
        
        if not keg:
            messagebox.showerror("Error", "Kegiatan tidak ditemukan!")
            return

        # Dialog edit
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Kegiatan")
        dialog.geometry("500x550")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="✏️ Edit Kegiatan",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 15))

        form = ctk.CTkFrame(dialog)
        form.pack(padx=20, pady=10, fill="both", expand=True)

        # Nama
        ctk.CTkLabel(form, text="Nama:", anchor="w").pack(anchor="w", padx=10, pady=(5,2))
        entry_nama = ctk.CTkEntry(form, width=440)
        entry_nama.insert(0, keg["nama"])
        entry_nama.pack(padx=10, pady=(0,8))

        # Deskripsi
        ctk.CTkLabel(form, text="Deskripsi:", anchor="w").pack(anchor="w", padx=10, pady=(5,2))
        entry_desk = ctk.CTkTextbox(form, width=440, height=100)
        entry_desk.insert("0.0", keg.get("deskripsi", ""))
        entry_desk.pack(padx=10, pady=(0,8))

        # Kuota
        ctk.CTkLabel(form, text="Kuota:", anchor="w").pack(anchor="w", padx=10, pady=(5,2))
        entry_kuota = ctk.CTkEntry(form, width=150)
        entry_kuota.insert(0, str(keg["kuota"]))
        entry_kuota.pack(padx=10, pady=(0,8), anchor="w")

        # Tanggal
        ctk.CTkLabel(form, text="Tanggal (YYYY-MM-DD):", anchor="w").pack(anchor="w", padx=10, pady=(5,2))
        entry_tanggal = ctk.CTkEntry(form, width=180)
        entry_tanggal.insert(0, keg["tanggal_kegiatan"])
        entry_tanggal.pack(padx=10, pady=(0,8), anchor="w")

        # Tanggal Tutup
        ctk.CTkLabel(form, text="Tanggal Tutup (Opsional):", anchor="w").pack(anchor="w", padx=10, pady=(5,2))
        entry_tutup = ctk.CTkEntry(form, width=180)
        if keg.get("tanggal_tutup"):
            entry_tutup.insert(0, keg["tanggal_tutup"])
        entry_tutup.pack(padx=10, pady=(0,8), anchor="w")

        def simpan():
            try:
                kuota_baru = int(entry_kuota.get())
                db.update_kegiatan(
                    id_keg,
                    entry_nama.get(),
                    entry_desk.get("0.0", "end").strip(),
                    kuota_baru,
                    entry_tanggal.get(),
                    entry_tutup.get() if entry_tutup.get() else None
                )
                messagebox.showinfo("Sukses", "Kegiatan berhasil diupdate!")
                self.refresh_admin_kegiatan()
                dialog.destroy()
            except ValueError:
                messagebox.showwarning("Input", "Kuota harus angka!")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal update: {e}")

        # Buttons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Simpan",
            command=simpan,
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

    def hapus_kegiatan(self):
        """Hapus kegiatan"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return
        
        sel = self.admin_keg_tree.selection()
        if not sel:
            messagebox.showwarning("Pilih", "Pilih kegiatan yang ingin dihapus!")
            return
        
        item = self.admin_keg_tree.item(sel[0])["values"]
        id_keg = int(item[0])
        nama_keg = item[1]
        
        if messagebox.askyesno(
            "Konfirmasi", 
            f"Yakin ingin hapus kegiatan '{nama_keg}'?\n\nSemua data pendaftaran terkait akan ikut terhapus!"
        ):
            if db.delete_kegiatan(id_keg):
                messagebox.showinfo("Sukses", "Kegiatan berhasil dihapus!")
                self.refresh_admin_kegiatan()
            else:
                messagebox.showerror("Gagal", "Gagal menghapus kegiatan!")

    # ==================== PESERTA & DASHBOARD ====================
    def tampilkan_peserta(self):
        """Tampilkan peserta per kegiatan dengan scrollbar"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return
        
        idtxt = self.admin_entry_idpeserta.get().strip()
        if not idtxt:
            messagebox.showwarning("Input", "Masukkan ID kegiatan!")
            return
        
        try:
            idk = int(idtxt)
        except ValueError:
            messagebox.showwarning("Input", "ID harus angka!")
            return

        kegiatan = db.get_kegiatan_by_id(idk)
        if not kegiatan:
            messagebox.showerror("Error", "Kegiatan tidak ditemukan!")
            return

        peserta = db.get_peserta_per_kegiatan(idk)
        if not peserta:
            messagebox.showinfo("Peserta", "Belum ada peserta untuk kegiatan ini.")
            return

        # Window baru
        win = ctk.CTkToplevel(self)
        win.title(f"Peserta: {kegiatan['nama']}")
        win.geometry("1000x600")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text=f"👥 Daftar Peserta (Total: {len(peserta)})",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            win,
            text=f"Kegiatan: {kegiatan['nama']}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 10))

        # Frame untuk treeview dengan scrollbar
        table_frame = ctk.CTkFrame(win)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars (PENTING!)
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        tree = ttk.Treeview(
            table_frame,
            columns=("no", "nim", "nama", "fakultas", "jurusan", "tanggal", "kode"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=20  # Set height
        )
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        headers = [
            ("no", "No", 50),
            ("nim", "NIM", 100),
            ("nama", "Nama", 200),
            ("fakultas", "Fakultas", 150),
            ("jurusan", "Jurusan", 150),
            ("tanggal", "Tanggal Daftar", 130),
            ("kode", "Kode Tiket", 100)
        ]

        for col, txt, w in headers:
            tree.heading(col, text=txt, anchor="center")
            tree.column(col, anchor="center" if col in ["no", "nim", "kode", "tanggal"] else "w", width=w)

        # Pack scrollbars SEBELUM tree
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # Insert data
        for i, p in enumerate(peserta, 1):
            tree.insert("", "end", values=(
                i,
                p["nim"],
                p["nama"],
                p.get("fakultas", "-"),
                p.get("jurusan", "-"),
                p["tanggal_daftar"],
                p["kode_tiket"]
            ))

        ctk.CTkButton(
            win,
            text="Tutup",
            command=win.destroy,
            fg_color="#95A5A6",
            width=150
        ).pack(pady=15)

    def export_peserta(self):
        """Export peserta (pilih: per kegiatan atau semua kegiatan)"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return

        # Dialog pilih mode
        mode_dialog = ctk.CTkToplevel(self)
        mode_dialog.title("Pilih Mode Export")
        mode_dialog.geometry("450x300")
        mode_dialog.grab_set()

        # Center
        mode_dialog.update_idletasks()
        x = (mode_dialog.winfo_screenwidth() // 2) - (mode_dialog.winfo_width() // 2)
        y = (mode_dialog.winfo_screenheight() // 2) - (mode_dialog.winfo_height() // 2)
        mode_dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            mode_dialog,
            text="📥 Pilih Mode Export",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 15))

        def export_satu_kegiatan():
            mode_dialog.destroy()
            
            # Cek apakah ada kegiatan yang dipilih
            sel = self.admin_keg_tree.selection()
            if not sel:
                messagebox.showwarning("Pilih", "Pilih kegiatan terlebih dahulu dari tabel!")
                return
            
            item = self.admin_keg_tree.item(sel[0])["values"]
            id_keg = int(item[0])
            nama_keg = item[1]

            # Dialog pilih format
            self.show_format_dialog(id_keg, nama_keg, mode="single")

        def export_semua_kegiatan():
            mode_dialog.destroy()
            self.show_format_dialog(None, None, mode="all")

        # Buttons
        ctk.CTkButton(
            mode_dialog,
            text="📄 Export Satu Kegiatan\n(Pilih dari tabel dulu)",
            command=export_satu_kegiatan,
            fg_color="#3498DB",
            hover_color="#2980B9",
            width=300,
            height=60,
            font=ctk.CTkFont(size=13)
        ).pack(pady=10)

        ctk.CTkButton(
            mode_dialog,
            text="📚 Export Semua Kegiatan\n(Gabungan semua peserta)",
            command=export_semua_kegiatan,
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            width=300,
            height=60,
            font=ctk.CTkFont(size=13)
        ).pack(pady=10)

        ctk.CTkButton(
            mode_dialog,
            text="Batal",
            command=mode_dialog.destroy,
            fg_color="#95A5A6",
            width=150
        ).pack(pady=15)

    def show_format_dialog(self, id_keg, nama_keg, mode="single"):
        """Dialog pilih format export (CSV/PDF)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pilih Format File")
        dialog.geometry("400x250")
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="📥 Pilih Format Export",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))

        if mode == "single":
            ctk.CTkLabel(
                dialog,
                text=f"Kegiatan: {nama_keg}",
                font=ctk.CTkFont(size=12)
            ).pack(pady=(0, 20))
        else:
            ctk.CTkLabel(
                dialog,
                text="Mode: Semua Kegiatan",
                font=ctk.CTkFont(size=12)
            ).pack(pady=(0, 20))

        def export_csv():
            if mode == "single":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    initialfile=f"peserta_kegiatan_{id_keg}.csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Simpan Data Peserta (CSV)"
                )
                if not filename:
                    return

                if db.export_peserta_csv(id_keg, filename):
                    messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                    dialog.destroy()
                else:
                    messagebox.showwarning("Kosong", "Tidak ada peserta untuk kegiatan ini!")
            else:
                # Export semua kegiatan
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    initialfile=f"peserta_semua_kegiatan.csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Simpan Data Peserta Semua Kegiatan (CSV)"
                )
                if not filename:
                    return

                if self.export_all_csv(filename):
                    messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                    dialog.destroy()
                else:
                    messagebox.showwarning("Kosong", "Tidak ada peserta di semua kegiatan!")

        def export_pdf():
            if mode == "single":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    initialfile=f"peserta_kegiatan_{id_keg}.pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Simpan Data Peserta (PDF)"
                )
                if not filename:
                    return

                if db.export_peserta_pdf(id_keg, filename):
                    messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                    dialog.destroy()
                else:
                    messagebox.showwarning("Kosong", "Tidak ada peserta untuk kegiatan ini!")
            else:
                # Export semua kegiatan
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    initialfile=f"peserta_semua_kegiatan.pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Simpan Data Peserta Semua Kegiatan (PDF)"
                )
                if not filename:
                    return

                if self.export_all_pdf(filename):
                    messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                    dialog.destroy()
                else:
                    messagebox.showwarning("Kosong", "Tidak ada peserta di semua kegiatan!")

        # Buttons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="📄 CSV",
            command=export_csv,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            width=150,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="📕 PDF",
            command=export_pdf,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=150,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            dialog,
            text="Batal",
            command=dialog.destroy,
            fg_color="#95A5A6",
            width=150
        ).pack(pady=10)

    def export_all_csv(self, filename):
        """Export semua peserta dari semua kegiatan ke CSV"""
        import csv
        try:
            kegiatan_list = db.get_kegiatan()
            all_data = []

            for keg in kegiatan_list:
                peserta = db.get_peserta_per_kegiatan(keg["id_kegiatan"])
                for p in peserta:
                    all_data.append({
                        "kegiatan": keg["nama"],
                        "nim": p["nim"],
                        "nama": p["nama"],
                        "fakultas": p.get("fakultas", "-"),
                        "jurusan": p.get("jurusan", "-"),
                        "tanggal_daftar": p["tanggal_daftar"],
                        "kode_tiket": p["kode_tiket"]
                    })

            if not all_data:
                return False

            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Kegiatan", "NIM", "Nama", "Fakultas", "Jurusan", "Tanggal Daftar", "Kode Tiket"])
                for row in all_data:
                    writer.writerow([
                        row["kegiatan"], row["nim"], row["nama"],
                        row["fakultas"], row["jurusan"],
                        row["tanggal_daftar"], row["kode_tiket"]
                    ])
            return True
        except Exception as e:
            print(f"Error export all CSV: {e}")
            return False

    def export_all_pdf(self, filename):
        """Export semua peserta dari semua kegiatan ke PDF"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            kegiatan_list = db.get_kegiatan()
            all_data = []

            for keg in kegiatan_list:
                peserta = db.get_peserta_per_kegiatan(keg["id_kegiatan"])
                for p in peserta:
                    all_data.append({
                        "kegiatan": keg["nama"],
                        "nim": p["nim"],
                        "nama": p["nama"],
                        "fakultas": p.get("fakultas", "-"),
                        "jurusan": p.get("jurusan", "-"),
                        "tanggal_daftar": p["tanggal_daftar"],
                        "kode_tiket": p["kode_tiket"]
                    })

            if not all_data:
                return False

            doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                                    rightMargin=20, leftMargin=20,
                                    topMargin=30, bottomMargin=30)

            styles = getSampleStyleSheet()
            style_cell = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            )

            elements = []

            # Title
            title = Paragraph("<b>Daftar Peserta Semua Kegiatan</b>", styles["Title"])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Table data
            data = [["No", "Kegiatan", "NIM", "Nama", "Fakultas", "Jurusan", "Tanggal Daftar", "Kode Tiket"]]
            for i, row in enumerate(all_data, 1):
                data.append([
                    str(i),
                    Paragraph(row["kegiatan"], style_cell),
                    Paragraph(row["nim"], style_cell),
                    Paragraph(row["nama"], style_cell),
                    Paragraph(row["fakultas"], style_cell),
                    Paragraph(row["jurusan"], style_cell),
                    Paragraph(row["tanggal_daftar"], style_cell),
                    Paragraph(row["kode_tiket"], style_cell)
                ])

            col_widths = [30, 110, 70, 110, 120, 120, 90, 70]
            table = Table(data, colWidths=col_widths, repeatRows=1)

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ]))

            elements.append(table)
            doc.build(elements)

            return True
        except Exception as e:
            print(f"Error export all PDF: {e}")
            return False

        def export_csv():
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"peserta_{id_keg}.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Simpan Data Peserta (CSV)"
            )
            if not filename:
                return

            if db.export_peserta_csv(id_keg, filename):
                messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                dialog.destroy()
            else:
                messagebox.showwarning("Kosong", "Tidak ada peserta untuk kegiatan ini!")

        def export_pdf():
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=f"peserta_{id_keg}.pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Simpan Data Peserta (PDF)"
            )
            if not filename:
                return

            if db.export_peserta_pdf(id_keg, filename):
                messagebox.showinfo("Sukses", f"Data berhasil diekspor ke:\n{filename}")
                dialog.destroy()
            else:
                messagebox.showwarning("Kosong", "Tidak ada peserta untuk kegiatan ini!")

        # Buttons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="📄 Export CSV",
            command=export_csv,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            width=150,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="📕 Export PDF",
            command=export_pdf,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=150,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            dialog,
            text="Batal",
            command=dialog.destroy,
            fg_color="#95A5A6",
            width=150
        ).pack(pady=10)

    def show_dashboard(self):
        """Tampilkan dashboard statistik"""
        if not self.admin_logged_in:
            messagebox.showwarning("Login", "Login terlebih dahulu!")
            return

        win = ctk.CTkToplevel(self)
        win.title("Dashboard Statistik")
        win.geometry("900x650")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="📊 Dashboard Statistik Kegiatan",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        stats = db.dashboard() or []
        
        if not stats:
            ctk.CTkLabel(
                win,
                text="Belum ada data kegiatan",
                font=ctk.CTkFont(size=14)
            ).pack(pady=50)
            return

        # Text statistik
        txtbox = ctk.CTkTextbox(win, height=150)
        txtbox.pack(fill="x", padx=15, pady=10)

        total_kegiatan = len(stats)
        total_peserta = sum(s['jumlah_peserta'] for s in stats)
        total_kuota = sum(s['kuota'] for s in stats)

        txtbox.insert("0.0", f"📌 Ringkasan:\n")
        txtbox.insert("end", f"   Total Kegiatan: {total_kegiatan}\n")
        txtbox.insert("end", f"   Total Peserta: {total_peserta}\n")
        txtbox.insert("end", f"   Total Kuota: {total_kuota}\n")
        txtbox.insert("end", f"\n{'='*60}\n\n")

        for s in stats:
            sisa = s['kuota'] - s['jumlah_peserta']
            persen = (s['jumlah_peserta'] / s['kuota'] * 100) if s['kuota'] > 0 else 0
            txtbox.insert("end", f"Kegiatan: {s['nama']}\n")
            txtbox.insert("end", f"  📊 Peserta: {s['jumlah_peserta']} / {s['kuota']} ({persen:.1f}%)\n")
            txtbox.insert("end", f"  📍 Sisa Kuota: {sisa}\n")
            txtbox.insert("end", f"  📅 Tanggal: {s['tanggal_kegiatan']}\n\n")

        txtbox.configure(state="disabled")

        # Chart dengan matplotlib
        chart_frame = ctk.CTkFrame(win)
        chart_frame.pack(fill="both", expand=True, padx=15, pady=10)

        try:
            kegiatan_names = [s["nama"][:25] for s in stats]  # Truncate
            peserta_counts = [s["jumlah_peserta"] for s in stats]
            kuota_counts = [s["kuota"] for s in stats]

            fig = Figure(figsize=(9, 4.5), dpi=100)
            ax = fig.add_subplot(111)

            x = range(len(kegiatan_names))
            width = 0.35

            # Bar untuk peserta
            bars1 = ax.bar([i - width/2 for i in x], peserta_counts, width, 
                          label='Peserta', color='#2ECC71', edgecolor='black')
            
            # Bar untuk kuota
            bars2 = ax.bar([i + width/2 for i in x], kuota_counts, width,
                          label='Kuota', color='#3498DB', edgecolor='black', alpha=0.7)

            # Label nilai di atas bar
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom', fontsize=9, fontweight='bold')

            ax.set_xlabel('Kegiatan', fontsize=11, fontweight='bold')
            ax.set_ylabel('Jumlah', fontsize=11, fontweight='bold')
            ax.set_title('Perbandingan Peserta vs Kuota per Kegiatan', 
                        fontsize=13, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(kegiatan_names, rotation=30, ha='right', fontsize=9)
            ax.legend(loc='upper right')
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            fig.tight_layout()

            # Embed ke tkinter
            canvas_widget = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas_widget.draw()
            canvas_widget.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            ctk.CTkLabel(
                chart_frame,
                text=f"⚠️ Gagal membuat grafik: {e}",
                font=ctk.CTkFont(size=12)
            ).pack(pady=30)

        # Tombol tutup
        ctk.CTkButton(
            win,
            text="Tutup",
            command=win.destroy,
            fg_color="#95A5A6",
            width=150
        ).pack(pady=15)

    # ==================== REFRESH TABLE ====================
    def refresh_admin_kegiatan(self):
        """Refresh tabel kegiatan"""
        for r in self.admin_keg_tree.get_children():
            self.admin_keg_tree.delete(r)
        
        try:
            kegs = db.get_kegiatan() or []
            
            for k in kegs:
                # Truncate deskripsi
                desc = k.get("deskripsi", "")
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                
                # Admin lihat kuota ASLI, bukan sisa
                peserta = k.get("peserta_terdaftar", 0)
                kuota_asli = k.get("kuota") + peserta  # Hitung balik kuota asli
                
                self.admin_keg_tree.insert(
                    "", "end",
                    values=(
                        k["id_kegiatan"],
                        k["nama"],
                        desc,
                        k["tanggal_kegiatan"],
                        k.get("tanggal_tutup", "-"),
                        kuota_asli,  # Kuota maksimal (asli)
                        peserta      # Jumlah peserta terdaftar
                    )
                )
        except Exception as e:
            messagebox.showerror("Error DB", f"Gagal mengambil data kegiatan: {e}")