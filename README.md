# PCare Prolanis Automation

Automation script untuk mengisi form pendaftaran kegiatan Prolanis (Dokter Kelompok) di PCare eClaim BPJS.

## Cara Pakai

### 1. Siapkan file CSV

Buat file CSV dengan format:

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

### 2. Ubah nama file CSV di script

Buka `pcare_automation_test_one.py`, ubah baris:

```python
CSV_FILE = "pcare_test_one_data.csv"
```

Ganti dengan nama file CSV yang mau diproses.

### 3. Ubah kegiatan (jika perlu)

```python
DEFAULT_KEGIATAN = "037"  # 037 = Senam, 036 = Edukasi
```

### 4. Jalankan

- **Mac**: `./run.sh`
- **Windows**: double-click `run.bat`

### 5. Submit

Setelah yakin form terisi benar, ubah:

```python
SUBMIT_FORM = True
```

## Setup

- **Mac**: `~/pcare-venv/bin/python` (sudah ada)
- **Windows**: Lihat `SETUP_WINDOWS.md` atau double-click `setup.bat`

## Catatan

- Script akan skip pasien yang alert/warning muncul setelah klik Cari
- Script akan skip jika tombol Simpan disabled
- Hasil ditampilkan di terminal: SUCCESS / SKIPPED / ERROR
- `respRate` dan `heartRate` diisi konstan (20 dan 80)
