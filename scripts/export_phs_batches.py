import openpyxl
import re
import csv
import os

wb = openpyxl.load_workbook("file/PHS 2026 (Jawaban) (2).xlsx", data_only=True)
sheet = wb.active

rows = []
for r in sheet.iter_rows(min_row=3, values_only=False):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        rows.append([c.value for c in r])

def map_job(j):
    s = str(j).strip().lower()
    if not s or s == "none":
        return "Belum/Tidak Bekerja"
    if any(k in s for k in ["irt", "ibu", "rumah tangga", "mengurus rumah tangga"]):
        return "Ibu Rumah Tangga"
    if any(k in s for k in ["pegawai", "pegawe", "karyawan", "fnb"]):
        return "Karyawan Swasta/ Tenaga Kerja"
    if any(k in s for k in ["pensiun", "belum", "tidak", "blum", "blm", "blom"]):
        return "Belum/Tidak Bekerja"
    if any(k in s for k in ["buruh", "biruh", "marbot"]):
        return "Buruh"
    if any(k in s for k in ["pelajar", "sekolah", "mahasiswa"]):
        return "Pelajar/Mahasiswa"
    if "pns" in s or "asn" in s:
        return "ASN"
    if "guru" in s or "dosen" in s:
        return "Guru/Dosen"
    if any(k in s for k in ["wira", "dagang"]):
        return "Wiraswasta"
    if "petani" in s:
        return "Petani"
    return "Belum/Tidak Bekerja"

def map_gender(j):
    s = str(j).strip().lower()
    if any(k in s for k in ["irt", "ibu", "rumah tangga", "mengurus rumah tangga"]):
        return "Perempuan"
    return "Laki - Laki"

def map_edu(e):
    s = str(e).strip()
    if "SD" in s:
        return "SD Sederajat"
    if "SMA" in s:
        return "SMA Sederajat"
    if "SMP" in s:
        return "SMP Sederajat"
    if "D4" in s or "S1" in s:
        return "D4/S1"
    if "D3" in s:
        return "D3"
    if "S2" in s:
        return "S2"
    if "Belum" in s or "tidak" in s.lower():
        return "Tidak Sekolah/ Tidak Tamat Sekolah"
    return "Tidak diketahui"

def map_age(v, cat):
    m = re.search(r"(\d+)", str(v))
    age = int(m.group(1)) if m else 0
    if age >= 15 or "> 15" in str(cat):
        return age, "≥ 15 tahun"
    else:
        return age, "10 s.d 14 Tahun"

def map_place(p):
    s = str(p).strip().lower()
    if "posyandu" in s:
        return "Posyandu/ Posbindu"
    if "puskesmas" in s:
        return "Puskesmas"
    if "fasilitas" in s:
        return "Fasilitas kesehatan lainnya"
    if "mandiri" in s:
        return "Mandiri/ Sendiri"
    return "Posyandu/ Posbindu"

def clean_num(val):
    s = str(val).strip() if val is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    return s

records = []
for idx, r in enumerate(rows, 1):
    job_mapped = map_job(r[12])
    gender_mapped = map_gender(r[12])
    edu_mapped = map_edu(r[11])
    age, rentang_usia = map_age(r[13], r[14])
    place_td = map_place(r[22])
    place_gd = map_place(r[24])
    buah_sayur = str(r[20]).strip() if r[20] else "3 Porsi"
    if buah_sayur not in ["> 3 Porsi", "3 Porsi", "< 3 Porsi"]:
        buah_sayur = "3 Porsi"

    rw = clean_num(r[5])
    rt = clean_num(r[6])
    nik = clean_num(r[10])

    rec = {
        "No": idx,
        "Kecamatan": "Tamansari",
        "Desa": str(r[4]).strip() if r[4] else "Tamansari",
        "Puskesmas": "Puskesmas Sirnagalih",
        "Pendata": "Kader",
        "RW": rw,
        "RT": rt,
        "NIK": nik,
        "Nama": str(r[9]).strip() if r[9] else "",
        "Jenis Kelamin": gender_mapped,
        "Rentang Usia": rentang_usia,
        "Usia": age,
        "Pendidikan Terakhir": edu_mapped,
        "Pekerjaan": job_mapped,
        "Cek Tekanan Darah": "Ya",
        "Tempat Tekanan Darah": place_td,
        "Cek Gula Darah": "Ya",
        "Tempat Gula Darah": place_gd,
        "Aktivitas Fisik": "Ya",
        "Cuci Tangan": "Ya",
        "Buah dan Sayur": buah_sayur,
        "Perokok Aktif": "Tidak",
        "Pernah Merokok": "Tidak",
        "Lama Berhenti Merokok": ""
    }
    records.append(rec)

batch_size = 100
total_batches = (len(records) + batch_size - 1) // batch_size
fieldnames = list(records[0].keys())

print(f"Total records: {len(records)}, Splitting into {total_batches} batches:")
for b in range(total_batches):
    start_idx = b * batch_size
    end_idx = min(start_idx + batch_size, len(records))
    batch_records = records[start_idx:end_idx]
    batch_file = f"file/phs_batch_{b+1}.csv"
    with open(batch_file, "w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(batch_records)
    print(f"  Batch {b+1}: {batch_file} ({len(batch_records)} records, index {start_idx+1} to {end_idx})")
