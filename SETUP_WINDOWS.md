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
pip install pandas playwright
playwright install chromium
```

## Step 6: Jalankan Script

```cmd
python pcare_automation_test_one.py
```

## Step 7: Cara Pakai

1. Browser Chromium akan terbuka otomatis
2. **Login manual** ke PCare dan set tanggal
3. Tekan **Enter** di Command Prompt untuk mulai mengisi form
4. Script akan mengisi data dari file `pcare_test_one_data.csv`
5. Setelah selesai, tekan **Enter** lagi untuk menutup browser

## Catatan

- Untuk submit form sungguhan, buka `pcare_automation_test_one.py` dan ubah `SUBMIT_FORM = False` menjadi `SUBMIT_FORM = True`
- Tambah data pasien di file `pcare_test_one_data.csv` dengan format:
  ```
  NO_BPJS,TB_BB,LP,TD,KEGIATAN
  0000059117635,167/70,98,120/79,037
  ```
- Untuk menjalankan ulang tanpa activate venv setiap kali, bisa pakai:
  ```cmd
  pcare-venv\Scripts\python pcare_automation_test_one.py
  ```

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `python` not recognized | Reinstall Python, pastikan centang "Add to PATH" |
| `playwright install` gagal | Pastikan internet stabil, coba ulang |
| Browser tidak muncul | Jalankan `playwright install chromium` ulang |
| Permission error | Jalankan Command Prompt sebagai Administrator |
