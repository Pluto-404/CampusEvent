from app import App
import customtkinter as ctk
from services import db_sqlite as db

if __name__ == "__main__":
    # Setup database
    db.create_tables()
    # Setup appearance
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    # Run app
    app = App()
    app.mainloop() 