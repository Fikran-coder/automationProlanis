import openpyxl
import re

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
    # IRT
    if any(k in s for k in ["irt", "ibu", "rumah tangga", "mengurus rumah tangga"]):
        return "Ibu Rumah Tangga"
    # Pegawai / Karyawan
    if any(k in s for k in ["pegawai", "pegawe", "karyawan", "fnb"]):
        return "Karyawan Swasta/ Tenaga Kerja"
    # Pensiunan / Tidak bekerja
    if any(k in s for k in ["pensiun", "belum", "tidak", "blum", "blm", "blom"]):
        return "Belum/Tidak Bekerja"
    # Buruh / Marbot
    if any(k in s for k in ["buruh", "biruh", "marbot"]):
        return "Buruh"
    # Pelajar
    if any(k in s for k in ["pelajar", "sekolah", "mahasiswa"]):
        return "Pelajar/Mahasiswa"
    # Guru
    if "pns" in s or "asn" in s:
        return "ASN"
    if "guru" in s or "dosen" in s:
        return "Guru/Dosen"
    # Wiraswasta / dagang
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

# Test all 530 rows
mapped_records = []
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

    # RT / RW formatting
    rw = str(r[5]).strip() if r[5] is not None else "01"
    rt = str(r[6]).strip() if r[6] is not None else "01"
    # NIK
    nik = str(r[10]).strip() if r[10] is not None else ""
    if nik.endswith(".0"):
        nik = nik[:-2]

    rec = {
        "index": idx,
        "kader": str(r[1]).strip() if r[1] else "Kader",
        "desa": str(r[4]).strip() if r[4] else "Tamansari",
        "rw": rw,
        "rt": rt,
        "nama": str(r[9]).strip() if r[9] else "",
        "nik": nik,
        "pendidikan": edu_mapped,
        "pekerjaan": job_mapped,
        "jenis_kelamin": gender_mapped,
        "usia": age,
        "rentang_usia": rentang_usia,
        "aktivitas_fisik": "Ya",
        "cuci_tangan": "Ya",
        "buah_sayur": buah_sayur,
        "cek_tekanan_darah": "Ya",
        "tempat_tekanan_darah": place_td,
        "cek_gula_darah": "Ya",
        "tempat_gula_darah": place_gd,
        "perokok_aktif": "Tidak",
        "pernah_merokok": "Tidak",
    }
    mapped_records.append(rec)

print(f"Successfully mapped all {len(mapped_records)} records!")
print("Sample record 1:", mapped_records[0])
print("Sample record 250:", mapped_records[249])
