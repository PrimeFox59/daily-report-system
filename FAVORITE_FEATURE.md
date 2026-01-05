# Fitur Favorite/Bookmark User - Daily Report System

## Deskripsi
Fitur ini memungkinkan admin untuk menandai user sebagai favorit (bookmark) di halaman Monitoring. User yang ditandai favorit akan selalu muncul di bagian atas daftar user, memudahkan akses cepat ke user yang sering dimonitor.

## Fitur Utama
- ✨ Bisa menandai lebih dari 1 user sebagai favorit
- ⭐ User favorit otomatis muncul di bagian atas daftar (sorted by favorite, then by name)
- 🎯 Toggle favorite dengan sekali klik (icon star)
- 🔄 Auto re-sort list setelah toggle tanpa reload halaman
- 💫 Visual indicator: star icon kuning di sebelah nama user yang favorit

## Cara Menggunakan
1. Buka halaman **Monitoring** (hanya admin)
2. Di daftar "Select User", setiap user memiliki ikon star di sebelah kanan
3. Klik ikon star untuk menandai/unmark user sebagai favorit:
   - ⭐ Star kosong (outline) = belum favorit
   - ⭐ Star terisi (solid) = sudah favorit
4. User favorit akan langsung berpindah ke bagian atas daftar
5. User favorit juga memiliki star icon kuning di sebelah nama mereka

## Perubahan Teknis

### 1. Database
- Tabel `user` ditambah kolom baru: `is_favorite` (BOOLEAN, default=0)
- Migration script: `migrate_favorites.py`

### 2. Backend (app.py)
- Route baru: `POST /api/users/<user_id>/toggle-favorite`
  - Toggle status favorite user
  - Return JSON: {success, message, is_favorite}
- Update route `monitoring()`:
  - Sorting user: `User.query.order_by(User.is_favorite.desc(), User.name).all()`
  - User favorit muncul pertama, lalu diurutkan berdasarkan nama

### 3. Frontend (monitoring.html)
- Tombol star di setiap user card dengan data attribute:
  - `data-user-id`: ID user
  - `data-is-favorite`: status favorite saat ini
- JavaScript function `toggleFavorite()`:
  - AJAX POST ke backend untuk toggle
  - Update UI (icon, badge, re-sorting) tanpa reload
- CSS untuk styling tombol star (hover effect, transition)

### 4. Model (models.py)
- Class `User` ditambah field: `is_favorite = db.Column(db.Boolean, default=False)`

## Contoh Penggunaan
```
Sebelum favorit:
- A. Kasir
- A. Sakuri
- A. Syahroni
- Aan Khusnul Ma'Arif

Setelah A. Sakuri dan Aan Khusnul Ma'Arif difavoritkan:
- ⭐ A. Sakuri (favorit)
- ⭐ Aan Khusnul Ma'Arif (favorit)
- A. Kasir
- A. Syahroni
```

## Catatan
- Fitur ini bersifat **global** (semua admin melihat favorit yang sama)
- Tidak ada batasan jumlah user yang bisa difavoritkan
- Favorit tetap tersimpan di database (persistent)
- Search functionality tetap bekerja dengan daftar yang sudah di-sort
