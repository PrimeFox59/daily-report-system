# Daily Report System

Sistem pelaporan harian untuk karyawan dengan fitur login menggunakan ID karyawan.

## Fitur
- ✅ Login dengan ID Karyawan (dari Excel)
- ✅ Dashboard untuk melihat laporan pribadi
- ✅ Form laporan dengan kategori (Quality, Cost, Delivery, Productivity)
- ✅ Monitoring untuk Admin (melihat laporan semua user)
- ✅ Edit/Delete laporan (maksimal 2 hari)
- ✅ Import data user otomatis dari Excel

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Import Data User dari Excel
Data user diambil dari file `User parin.xlsx` (sheet "ID karyawan").

Jalankan script import:
```bash
python init_db.py
```

Atau jalankan langsung script import:
```bash
python import_users_from_excel.py
```

Script akan:
- Membaca data dari Excel
- Membuat database baru
- Import semua user dengan status "approved"
- User dengan ID 344 akan menjadi Admin

### 3. Run Application
```bash
python app.py
```

Aplikasi akan berjalan di: http://127.0.0.1:8000

## Login Demo Accounts

Setelah import dari Excel, gunakan:
- **Admin**: ID `344` / Password `zzz`
- **User**: ID `368` / Password `zzz`
- Atau gunakan ID lain dari Excel dengan password `zzz`

## Struktur Database

### User Table
- employee_id: ID karyawan (dari Excel)
- name: Nama lengkap
- password_hash: Password terenkripsi
- department: Departemen
- section: Seksi
- job: Nama jabatan
- shift: Shift kerja
- is_admin: Status admin

### Report Table
- user_id: ID user pembuat laporan
- time: Waktu kejadian
- category: Kategori (Quality/Cost/Delivery/Productivity)
- title: Judul laporan
- notes: Catatan detail
- item_name: Nama item (optional)
- part_number: Nomor part (optional)
- customer: Nama customer (optional)

## Update Data User

Jika ada perubahan di Excel, jalankan ulang:
```bash
python import_users_from_excel.py
```

**PERHATIAN**: Ini akan menghapus semua data dan membuat database baru!

## File Penting
- `app.py` - Aplikasi utama Flask
- `models.py` - Database models
- `forms.py` - Form definitions
- `import_users_from_excel.py` - Script import dari Excel
- `init_db.py` - Initialize database
- `User parin.xlsx` - Data karyawan (sumber data)

## Teknologi
- Flask (Web Framework)
- SQLite (Database)
- Flask-Login (Authentication)
- Flask-WTF (Forms)
- openpyxl (Excel Reader)
- Bootstrap 5 (UI)
