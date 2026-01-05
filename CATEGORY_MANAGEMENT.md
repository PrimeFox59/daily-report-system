# Category Management Feature

## Overview
Admin dapat mengatur kategori laporan melalui menu **Settings** di navigation bar.

## Fitur Utama

### 1. Menu Settings (Admin Only)
- Lokasi: Navigation bar → **Settings** (ikon gear)
- Akses: Hanya untuk user dengan `is_admin = True`
- Route: `/admin/categories`

### 2. Halaman Category Management
File: `templates/admin_categories.html`

**Fitur:**
- ✅ View semua kategori dalam tabel
- ✅ Add kategori baru
- ✅ Edit kategori yang sudah ada
- ✅ Delete kategori
- ✅ Toggle Active/Inactive status
- ✅ Pilih warna (Bootstrap color classes)
- ✅ Pilih icon (Bootstrap Icons)

**Kolom Kategori:**
- **Name**: Nama kategori (unique)
- **Color**: Warna badge (primary, success, warning, danger, info, secondary)
- **Icon**: Bootstrap icon class (e.g., bi-check-circle, bi-graph-up)
- **Status**: Active atau Inactive

### 3. Default Categories
Setelah migration, sistem memiliki 4 kategori default:

| Category | Color | Icon | Status |
|----------|-------|------|--------|
| Quality | success (green) | bi-check-circle | Active |
| Cost | warning (yellow) | bi-currency-dollar | Active |
| Delivery | danger (red) | bi-truck | Active |
| Productivity | info (cyan) | bi-graph-up | Active |

### 4. Dynamic Form Dropdowns
Form laporan di dashboard sekarang menggunakan kategori dari database:
- **New Report Form**: Dropdown otomatis terisi dari Category.query.filter_by(is_active=True)
- **Edit Report Modal**: Dropdown juga dinamis
- Hanya kategori dengan status Active yang muncul di form

## API Routes (Admin Only)

### GET /admin/categories
Menampilkan halaman management kategori

### POST /admin/category/add
Menambah kategori baru
**Parameters:**
- name: string (required, unique)
- color: string (required, Bootstrap color class)
- icon: string (required, Bootstrap icon class)

**Response:** JSON `{success: true/false, message: '...'}`

### POST /admin/category/<id>/edit
Mengupdate kategori
**Parameters:**
- name: string
- color: string
- icon: string

**Response:** JSON `{success: true/false, message: '...'}`

### POST /admin/category/<id>/delete
Menghapus kategori

**Response:** JSON `{success: true/false, message: '...'}`

### POST /admin/category/<id>/toggle
Mengaktifkan/nonaktifkan kategori

**Response:** JSON `{success: true/false, message: '...'}`

## Database Model

```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(20), nullable=False, default='primary')
    icon = db.Column(db.String(50), nullable=False, default='bi-tag')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Migration

File: `migrate_categories.py`

**Cara menjalankan:**
```bash
python migrate_categories.py
```

**Output:**
```
✓ Default categories created successfully!
Total categories: 4
```

## Cara Penggunaan

### Untuk Admin:
1. Login sebagai admin
2. Klik menu **Settings** di navigation bar
3. Halaman Category Settings akan terbuka
4. **Add Category**: Klik tombol "+ Add Category"
   - Isi nama kategori
   - Pilih warna dari dropdown
   - Isi icon class (lihat https://icons.getbootstrap.com/)
   - Klik "Save Category"
5. **Edit Category**: Klik tombol pencil
   - Update nama, warna, atau icon
   - Klik "Save Changes"
6. **Toggle Status**: Klik tombol toggle untuk aktifkan/nonaktifkan
7. **Delete Category**: Klik tombol trash (konfirmasi required)

### Untuk User:
- Dropdown kategori di form otomatis ter-update
- Hanya kategori Active yang muncul
- User tidak perlu melakukan apa-apa

## File yang Dimodifikasi

1. **models.py** - Added Category model
2. **app.py** - Added 5 admin routes + updated dashboard route
3. **templates/base.html** - Added Settings menu for admin
4. **templates/dashboard.html** - Dynamic category dropdowns
5. **templates/admin_categories.html** - NEW: Category management UI
6. **migrate_categories.py** - NEW: Migration script

## Bootstrap Icons Reference
Lihat: https://icons.getbootstrap.com/

**Contoh icon yang umum:**
- bi-check-circle (Quality)
- bi-currency-dollar (Cost)
- bi-truck (Delivery)
- bi-graph-up (Productivity)
- bi-shield-check (Safety)
- bi-tools (Maintenance)
- bi-people (HR)
- bi-tag (General)

## Bootstrap Color Classes
- **primary**: Blue
- **success**: Green
- **warning**: Yellow/Orange
- **danger**: Red
- **info**: Cyan/Light Blue
- **secondary**: Gray

## Security
- Semua admin routes memiliki check: `if not current_user.is_admin`
- Unauthorized access akan redirect ke dashboard dengan flash message
- API routes return 403 untuk non-admin

## Status
✅ **Fully Implemented and Tested**
- Migration completed
- All routes working
- UI fully functional
- Security implemented
