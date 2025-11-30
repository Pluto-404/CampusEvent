import customtkinter as ctk
from pages.mahasiswa_page import MahasiswaPage
from pages.admin_page import AdminPage
from PIL import Image
import os

class App(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Window settings
        self.title("Sistem Pendaftaran Kegiatan Kampus - GUI")
        self.geometry("1100x700")
        self.minsize(1000, 650)

        # Container utama
        self.container = ctk.CTkFrame(self, corner_radius=8)
        self.container.pack(fill="both", expand=True, padx=12, pady=12)

        # Sidebar
        sidebar = ctk.CTkFrame(self.container, width=220)
        sidebar.pack(side="left", fill="y", padx=(0, 12), pady=6)

        self.main_area = ctk.CTkFrame(self.container)
        self.main_area.pack(side="right", fill="both", expand=True, pady=6)

        # ========== LOGO DI SIDEBAR (PALING ATAS) ==========
        try:
            # Load logo dari folder assets
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
            logo_img = Image.open(logo_path)
            
            # Resize logo (misalnya 150x150)
            logo_img = logo_img.resize((150, 150))
            
            # Convert ke CTkImage
            self.logo_photo = ctk.CTkImage(
                light_image=logo_img, 
                dark_image=logo_img, 
                size=(100, 100)
                
            )
            
            # Tampilkan logo
            logo_label = ctk.CTkLabel(sidebar, image=self.logo_photo, text="")
            logo_label.pack(pady=(10, 5))
            
        except Exception as e:
            print(f"⚠️ Gagal load logo: {e}")
            # Jika logo tidak ada, tampilkan teks sebagai gantinya
            ctk.CTkLabel(
                sidebar, 
                text="🎓",
                font=ctk.CTkFont(size=60)
            ).pack(pady=(10, 5))
        
        # Title di bawah logo
        ctk.CTkLabel(
            sidebar, 
            text="Campus Event",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color= "#4e93ca"
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            sidebar, 
            text="Management System",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 15))

        
        # ====================================================

        # Sidebar buttons
        ctk.CTkLabel(sidebar, text="Menu", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(8,16))
        ctk.CTkButton(sidebar, text="🏠 Home", command=self.show_home).pack(fill="x", padx=8, pady=(0,8))
        ctk.CTkButton(sidebar, text="👨‍🎓 Mahasiswa", command=self.show_mahasiswa).pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(sidebar, text="👨‍💼 Admin", command=self.show_admin).pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(sidebar, text="🌙/☀️ Mode", command=self.toggle_mode).pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(sidebar, text="🔄 Refresh Data", command=self.refresh_all).pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(sidebar, text="🚪 Keluar", fg_color="#D9534F", hover_color="#C9302C",
                      command=self.on_exit).pack(side="bottom", fill="x", padx=8, pady=8)

        # Pages
        self.pages = {}
        self.pages["mahasiswa"] = MahasiswaPage(self.main_area, self)
        self.pages["admin"] = AdminPage(self.main_area, self)

        # Show default
        self.show_home()

    # -------------------
    def clear_main(self):
        for child in self.main_area.winfo_children():
            child.pack_forget()

    def show_home(self):
        self.clear_main()
        frame = ctk.CTkFrame(self.main_area)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Title
        ctk.CTkLabel(
            frame, 
            text="🎓 Sistem Pendaftaran Kegiatan Kampus",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(30, 10))
        
        # Subtitle
        ctk.CTkLabel(
            frame, 
            text="Selamat Datang!",
            font=ctk.CTkFont(size=16)
        ).pack(pady=10)
        
        # Description
        desc_frame = ctk.CTkFrame(frame)
        desc_frame.pack(pady=20, padx=50, fill="x")
        
        ctk.CTkLabel(
            desc_frame,
            text="Gunakan menu sidebar untuk mengakses:",
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)
        
        info_text = """
        👨‍🎓 Mahasiswa: Registrasi, Login, Daftar Kegiatan, Cetak E-Ticket
        
        👨‍💼 Admin: Kelola Kegiatan, Lihat Peserta, Dashboard, Export CSV
        
        🌙/☀️ Mode: Toggle Dark/Light Mode
        """
        
        ctk.CTkLabel(
            desc_frame,
            text=info_text,
            font=ctk.CTkFont(size=13),
            justify="left"
        ).pack(pady=10)
        
        # Footer
        ctk.CTkLabel(
            frame,
            text="Campus Event | Dibuat Oleh Kelompok 3",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="bottom", pady=20)

    def show_mahasiswa(self):
        self.clear_main()
        self.pages["mahasiswa"].pack(fill="both", expand=True)

    def show_admin(self):
        self.clear_main()
        self.pages["admin"].pack(fill="both", expand=True)

    def toggle_mode(self):
        mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(mode)

    def refresh_all(self):
        """Refresh tampilan data mahasiswa dan admin tanpa login ulang."""
        try:
            # Cek dan refresh tabel mahasiswa (kalau halaman ada)
            if "mahasiswa" in self.pages:
                self.pages["mahasiswa"].refresh_kegiatan()

            # Cek dan refresh tabel admin
            if "admin" in self.pages:
                self.pages["admin"].refresh_admin_kegiatan()

            # Tampilkan notifikasi cepat
            from tkinter import messagebox
            messagebox.showinfo("Refresh", "✅ Data berhasil diperbarui.")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Gagal Refresh", f"❌ Terjadi kesalahan: {e}")


    def on_exit(self):
        import tkinter.messagebox as messagebox
        if messagebox.askokcancel("Keluar", "Anda yakin ingin keluar?"):
            self.destroy()

