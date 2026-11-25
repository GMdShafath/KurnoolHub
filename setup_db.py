"""Creates the local MySQL database + sample data for Kurnool Hub (safe to re-run)."""
import os
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
DB = os.environ.get("MYSQLDATABASE", "kurnool_hub")
conn = mysql.connector.connect(
    host=os.environ.get("MYSQLHOST", "localhost"),
    port=int(os.environ.get("MYSQLPORT", 3306)),
    user=os.environ.get("MYSQLUSER", "root"),
    password=os.environ.get("MYSQLPASSWORD", ""),
)
c = conn.cursor()
c.execute(f"CREATE DATABASE IF NOT EXISTS `{DB}` CHARACTER SET utf8mb4")
c.execute(f"USE `{DB}`")

for ddl in [
 "CREATE TABLE IF NOT EXISTS categories (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, icon VARCHAR(255))",
 "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
 "CREATE TABLE IF NOT EXISTS admins (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL)",
 "CREATE TABLE IF NOT EXISTS businesses (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(150) NOT NULL, category_id INT, description TEXT, address VARCHAR(255), phone VARCHAR(30), rating DECIMAL(3,1) DEFAULT 0, image VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
 "CREATE TABLE IF NOT EXISTS business_categories (business_id INT NOT NULL, category_id INT NOT NULL, PRIMARY KEY (business_id, category_id))",
 "CREATE TABLE IF NOT EXISTS places (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(150) NOT NULL, description TEXT, location VARCHAR(255), image VARCHAR(255))",
 "CREATE TABLE IF NOT EXISTS events (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(150) NOT NULL, description TEXT, event_date DATE, location VARCHAR(255), image VARCHAR(255))",
 "CREATE TABLE IF NOT EXISTS favorites (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, business_id INT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY uq_fav (user_id, business_id))",
 "CREATE TABLE IF NOT EXISTS reviews (id INT AUTO_INCREMENT PRIMARY KEY, business_id INT NOT NULL, user_id INT NOT NULL, rating INT NOT NULL, comment TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
 "CREATE TABLE IF NOT EXISTS login_activity (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
]:
    c.execute(ddl)

c.execute("SELECT COUNT(*) FROM categories")
if c.fetchone()[0] == 0:
    c.executemany("INSERT INTO categories (name, description, icon) VALUES (%s,%s,%s)", [
        ("Restaurants", "Cafes, biryani and local food", "Forza_cafe.jpg"),
        ("Shopping", "Malls and markets", "Tgv_mall.jpg"),
        ("Healthcare", "Hospitals and clinics", "city_care_hospital.jpg"),
        ("Education", "Schools and colleges", "education.jpg"),
    ])
    c.executemany("INSERT INTO businesses (name, category_id, description, address, phone, rating, image) VALUES (%s,%s,%s,%s,%s,%s,%s)", [
        ("Forza Cafe", 1, "Cozy cafe with great coffee and snacks.", "Nandyal Road, Kurnool", "9876500001", 4.4, "Forza_cafe.jpg"),
        ("Pista House", 1, "Famous for Hyderabadi biryani and haleem.", "Bellary Road, Kurnool", "9876500002", 4.6, "pista_house.png"),
        ("TGV Mall", 2, "Shopping, food court and cinema.", "Budhwarpet, Kurnool", "9876500003", 4.3, "Tgv_mall.jpg"),
        ("City Care Hospital", 3, "Multi-speciality hospital, 24x7 emergency.", "Gayatri Estate, Kurnool", "9876500004", 4.5, "city_care_hospital.jpg"),
        ("St. Joseph School", 4, "Well-regarded English medium school.", "Kurnool", "9876500005", 4.2, "st.joseph_school.png"),
    ])
    c.executemany("INSERT INTO places (name, description, location, image) VALUES (%s,%s,%s,%s)", [
        ("Konda Reddy Fort", "Historic fort in the heart of Kurnool.", "Kurnool", "konda_reddy_fort.jpg"),
        ("Orvakal Rock Gardens", "Natural rock formations and scenic views.", "Orvakal", "orvakal_rock_gardens.jpg"),
        ("Rollapadu Wildlife Sanctuary", "Home of the Great Indian Bustard.", "Rollapadu", "rollapadu_wildlife_sanctuary.jpg"),
    ])
    c.execute("INSERT INTO events (title, description, event_date, location, image) VALUES (%s,%s,%s,%s,%s)",
        ("Kurnool Utsav", "Annual cultural festival with food, music and crafts.", "2026-12-20", "Kurnool", "kurnool_utsav.jpg"))

c.execute("SELECT COUNT(*) FROM admins")
if c.fetchone()[0] == 0:
    admin_pw = os.environ.get("ADMIN_PASSWORD")
    if admin_pw:
        c.execute("INSERT INTO admins (name, email, password) VALUES (%s,%s,%s)",
            ("Admin", os.environ.get("ADMIN_EMAIL", "admin@kurnoolhub.com"), generate_password_hash(admin_pw)))
    else:
        print("No ADMIN_PASSWORD set in .env - admin account not created.")

conn.commit()
print(f"Database '{DB}' ready.")
