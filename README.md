# PCare Prolanis Automation

Automation GUI untuk mengisi form di PCare eClaim BPJS, Komdat Kemkes, dan ePuskesmas. Mendukung 4 jenis automation:

1. **Pendaftaran Kegiatan Prolanis** — mendaftarkan pasien ke kegiatan (Senam/Edukasi)
2. **Pendaftaran Peserta Prolanis** — mendaftarkan pasien sebagai peserta Prolanis
3. **Komdat Posyandu** — mengisi form kegiatan posyandu bulanan di microsite Kemkes
4. **Update Alamat CSV** — mengambil alamat (kelurahan) dari ePuskesmas dan update file CSV

## Cara Pakai (GUI)

### 1. Siapkan file CSV _(hanya untuk Prolanis & Update Alamat)_

Taruh file CSV di folder `file/`.

**Format CSV — Pendaftaran Kegiatan:**

```csv
NO_BPJS,TB_BB,LP,TD
00000XXXXX635,167/70,98,120/79
00001XXXXX161,150/67,86,110/70
```

| Kolom | Keterangan | Contoh |
|-------|-----------|--------|
| NO_BPJS | Nomor BPJS peserta | 00000XXXXX635 |
| TB_BB | Tinggi badan / Berat badan | 167/70 |
| LP | Lingkar perut | 98 |
| TD | Tekanan darah (sistole/diastole) | 120/79 |

**Format CSV — Pendaftaran Peserta:**

```csv
NO_BPJS,TELEPON,ALAMAT
0001315950759,081514710526,KP. SUKAMANTRI
```

| Kolom | Keterangan | Contoh |
|-------|-----------|--------|
| NO_BPJS | Nomor BPJS peserta | 0001315950759 |
| TELEPON | No. HP (jika kosong/invalid, pakai default) | 081514710526 |
| ALAMAT | Alamat peserta | KP. SUKAMANTRI |

**Komdat Posyandu** — tidak perlu CSV, data diambil langsung dari tabel di website.

**Update Alamat CSV** — gunakan file CSV dengan format Pendaftaran Peserta (kolom ALAMAT akan di-update).

### 2. Jalankan GUI

- **Mac**: `./run.sh`
- **Windows**: double-click `run.bat`

### 3. Pilih pengaturan di GUI

- **Automation** — pilih jenis automation
- **Kegiatan** — pilih Senam (037) atau Edukasi (036) _(hanya untuk Pendaftaran Kegiatan)_
- **Bulan** — pilih bulan target _(hanya untuk Komdat Posyandu)_
- **Mode** — Test (isi form tanpa simpan) atau Submit (simpan data)
- **Browse** — pilih file CSV _(hanya untuk Prolanis & Update Alamat)_

### 4. Mulai

1. Klik **Mulai Automation**
2. Browser terbuka → **Login manual** ke situs terkait
3. Klik **OK** di dialog untuk memulai
4. Pantau progress di log area
5. Klik **Stop** kapan saja untuk menghentikan

### 5. Log

Setelah selesai, log otomatis disimpan di folder `logs/` dengan format:
```
logs/2026-06-18_191852_peserta.txt
logs/2026-06-18_143000_kegiatan.txt
logs/2026-06-22_220000_komdat.txt
logs/2026-08-03_170000_update_alamat.txt
```

## Setup

- **Mac**: `~/pcare-venv/bin/python` (sudah ada)
- **Windows**: Lihat `SETUP_WINDOWS.md` atau double-click `setup.bat`

## Catatan — Prolanis

- Script akan skip pasien yang alert/warning muncul setelah klik Cari
- Script akan skip pasien yang sudah terdaftar Prolanis (ada label "- Prolanis")
- Script akan skip jika tombol Simpan disabled
- Pendaftaran Peserta: email konstan `upttamansari@gmail.com`, keterangan konstan `riwayat hipertensi`
- Pendaftaran Peserta: telepon yang kosong/hanya nol/kurang dari 8 digit akan diganti `089526585949`
- `respRate` dan `heartRate` diisi konstan (20 dan 80) untuk Pendaftaran Kegiatan
- Turnstile token expired setiap ~5 pasien — otomatis retry klik Cari (8x, interval 8 detik)
- Jika Cloudflare minta klik checkbox "Verify you are human" — notifikasi muncul, automation menunggu (max 10 menit)
- "Verifikasi keamanan gagal" — otomatis retry 1x sebelum skip

## Catatan — Komdat Posyandu

- URL: `https://microsite.kemkes.go.id/med_mci_si12/web/site/login`
- Script otomatis navigasi ke Kegiatan Posyandu → Edit → iterasi semua posyandu
- Skip posyandu yang sudah diisi (tombol UPDATE berwarna hijau)
- Hanya klik tombol UPDATE yang berwarna abu-abu (belum diisi)
- Form diisi otomatis:
  - Melakukan Kegiatan Hari Buka (semua layanan + 3 sub-checkbox bayi/balita)
  - Melakukan Penyuluhan Kesehatan dan Gizi (semua)
  - Melakukan Pemberian PMT → Sesuai Standar
  - Melakukan Layanan Kunjungan Rumah
  - Bimbingan Teknis: Sudah → Pendamping: PUSKESMAS
  - Lapor ke UPKDK: Sudah → Periode: 1 Kali/Minggu
  - Supervisi: Sudah
- Sumber Pembiayaan tidak diisi (dibiarkan kosong)
- Mode Test: form diisi tapi modal ditutup tanpa simpan
- Mode Submit: form diisi dan klik UPDATE untuk menyimpan

## Catatan — Update Alamat CSV

- URL: `https://bogor.epuskesmas.id/login`
- Cari nomor BPJS di halaman Pasien ePuskesmas
- Ambil **kelurahan** dari tabel hasil pencarian (kolom Kelurahan)
- Jika pasien tidak ditemukan atau kelurahan kosong → alamat diisi random dari: SUKAMANTRI, TAMANSARI, PASIREURIH, SIRNAGALIH
- Mode Test: cari dan tampilkan di log, file CSV tidak diubah
- Mode Submit: cari dan update kolom ALAMAT di file CSV
