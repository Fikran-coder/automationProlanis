# Setup Guide — Windows

## Prerequisites

- Windows 10 atau 11
- Koneksi internet

## Step 1: Install Python

1. Buka https://www.python.org/downloads/
2. Download Python 3.11 atau lebih baru
3. Saat install, **centang "Add python.exe to PATH"**
4. Klik "Install Now"

Verifikasi di Command Prompt:
```cmd
python --version
```

## Step 2: Download Project

Copy folder `automationProlanis` ke laptop Windows (via flashdisk, zip, atau Git).

Contoh lokasi: `C:\Users\NamaUser\automationProlanis`

## Step 3: Buat Virtual Environment

Buka Command Prompt, masuk ke folder project:
```cmd
cd C:\Users\NamaUser\automationProlanis
python -m venv pcare-venv
```

## Step 4: Aktifkan Virtual Environment

```cmd
pcare-venv\Scripts\activate
```

Akan muncul `(pcare-venv)` di awal baris.

## Step 5: Install Dependencies

```cmd
pip install pandas playwright customtkinter
playwright install chromium
```

## Step 6: Jalankan GUI

```cmd
python pcare_gui.py
```

Atau double-click `run.bat`.

## Step 7: Cara Pakai

1. Pilih **Automation** (Kegiatan atau Peserta)
2. Pilih **Kegiatan** (Senam/Edukasi) — hanya untuk Pendaftaran Kegiatan
3. Pilih **Mode** (Test atau Submit)
4. Klik **Browse** dan pilih file CSV dari folder `file/`
5. Klik **Mulai Automation**
6. Browser Chromium terbuka → **Login manual** ke PCare dan set tanggal
7. Klik **OK** untuk memulai
8. Pantau progress di log area
9. Klik **Stop** kapan saja untuk menghentikan

## Catatan

- File CSV taruh di folder `file/`
- Log hasil disimpan otomatis di folder `logs/`
- Untuk menjalankan tanpa activate venv setiap kali:
  ```cmd
  pcare-venv\Scripts\python pcare_gui.py
  ```

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `python` not recognized | Reinstall Python, pastikan centang "Add to PATH" |
| `playwright install` gagal | Pastikan internet stabil, coba ulang |
| Browser tidak muncul | Jalankan `playwright install chromium` ulang |
| Permission error | Jalankan Command Prompt sebagai Administrator |
| GUI tidak muncul | Pastikan `customtkinter` terinstall: `pip install customtkinter` |
