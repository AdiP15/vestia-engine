# matching/sjt.py
"""
Situational Judgment Test (SJT) — Logika Grading.

Cara kerja:
1. HRD membuat soal skenario + 4 pilihan jawaban
2. Tiap pilihan diberi bobot (0.0–1.0) oleh HRD sesuai kualitas respons
3. Pelamar memilih satu pilihan
4. Sistem menghitung skor gabungan:
   - 70% dari bobot pilihan yang dipilih (ditentukan HRD)
   - 30% dari cosine similarity teks pilihan vs pilihan terbaik (SBERT)
5. Hasil: skor per soal + skor total tes + profil kompetensi

Kenapa gabungan bobot + SBERT?
  Bobot saja = tidak ada peran AI, jadi cuma sistem kuis biasa.
  SBERT saja = tidak bisa bedain pilihan yang "benar" vs "salah" konteks kerja.
  Gabungan = bobot memastikan ketepatan, SBERT menambah nuansa semantik.
  Ini yang membuat SJT ini bisa disebut "AI-powered" secara valid di skripsi.
"""

from sklearn.metrics.pairwise import cosine_similarity
from . import ml_model


# Kompetensi yang diukur tiap soal (bisa dikustomisasi HRD)
KOMPETENSI_LIST = [
    'Teamwork',
    'Problem Solving',
    'Communication',
    'Leadership',
    'Adaptability',
    'Time Management',
    'Integrity',
    'Customer Focus',
]

# Batas grade (sama dengan Smart Grading esai)
GRADE_THRESHOLDS = {'A': 85.0, 'B': 70.0, 'C': 55.0, 'D': 40.0, 'E': 0.0}


def grade_satu_soal(pilihan_dipilih: str,
                    semua_pilihan: list[dict],
                    bobot_sbert: float = 0.30) -> dict:
    """
    Hitung skor untuk SATU soal SJT.

    Args:
        pilihan_dipilih : Huruf pilihan pelamar, contoh: 'B'
        semua_pilihan   : List dict pilihan, format:
                          [
                            {'huruf': 'A', 'teks': '...', 'bobot': 0.2},
                            {'huruf': 'B', 'teks': '...', 'bobot': 0.9},
                            {'huruf': 'C', 'teks': '...', 'bobot': 0.6},
                            {'huruf': 'D', 'teks': '...', 'bobot': 0.3},
                          ]
        bobot_sbert     : Porsi cosine similarity dalam skor akhir (default 30%)

    Returns:
        dict berisi skor, grade, cosine_raw, feedback, pilihan_terbaik
    """
    # Cari pilihan yang dipilih pelamar
    dipilih = next((p for p in semua_pilihan if p['huruf'] == pilihan_dipilih), None)
    if not dipilih:
        return {
            'skor': 0.0, 'grade': 'E',
            'cosine_raw': 0.0,
            'feedback': f'Pilihan "{pilihan_dipilih}" tidak ditemukan.',
            'pilihan_terbaik': '',
            'bobot_pilihan': 0.0,
        }

    # Cari pilihan terbaik (bobot tertinggi)
    terbaik = max(semua_pilihan, key=lambda p: p['bobot'])

    # Skor dari bobot pilihan (70%)
    skor_bobot = dipilih['bobot'] * 100

    # Skor dari cosine similarity teks pilihan vs teks terbaik (30%)
    embeddings   = ml_model.encode([dipilih['teks'], terbaik['teks']])
    cosine_raw   = float(cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0])
    skor_sbert   = max(0.0, min(100.0, cosine_raw * 100.0))

    # Skor akhir gabungan
    bobot_manual = 1.0 - bobot_sbert
    skor_akhir   = (bobot_manual * skor_bobot) + (bobot_sbert * skor_sbert)
    skor_akhir   = round(max(0.0, min(100.0, skor_akhir)), 2)

    grade    = _skor_ke_grade(skor_akhir)
    feedback = _generate_feedback(skor_akhir, dipilih, terbaik)

    return {
        'skor':           skor_akhir,
        'grade':          grade,
        'cosine_raw':     round(cosine_raw, 4),
        'skor_bobot':     round(skor_bobot, 2),
        'skor_sbert':     round(skor_sbert, 2),
        'feedback':       feedback,
        'pilihan_terbaik': terbaik['huruf'],
        'bobot_pilihan':  dipilih['bobot'],
    }


def grade_sesi_sjt(jawaban_pelamar: dict[str, str],
                   bank_soal: list[dict],
                   bobot_per_soal: list[float] | None = None) -> dict:
    """
    Hitung skor untuk SATU SESI SJT (banyak soal sekaligus).

    Args:
        jawaban_pelamar : {soal_id: huruf_pilihan}, contoh: {'1': 'B', '2': 'A', '3': 'C'}
        bank_soal       : List soal, tiap soal format:
                          {
                            'id': '1',
                            'skenario': 'Teks skenario situasi...',
                            'kompetensi': 'Teamwork',
                            'pilihan': [
                              {'huruf': 'A', 'teks': '...', 'bobot': 0.2},
                              ...
                            ]
                          }
        bobot_per_soal  : Bobot tiap soal (harus jumlah = 1.0).
                          None = semua soal bobot sama.

    Returns:
        dict lengkap: skor_per_soal, skor_total, grade_total,
                      profil_kompetensi, rekomendasi
    """
    n = len(bank_soal)
    if bobot_per_soal is None:
        bobot_per_soal = [1.0 / n] * n

    hasil_per_soal  = []
    skor_total      = 0.0
    profil          = {}   # {kompetensi: [skor, ...]}

    for i, soal in enumerate(bank_soal):
        soal_id   = str(soal['id'])
        dipilih   = jawaban_pelamar.get(soal_id, '')
        kompetensi = soal.get('kompetensi', 'Umum')

        hasil = grade_satu_soal(dipilih, soal['pilihan'])
        hasil['soal_id']    = soal_id
        hasil['skenario']   = soal['skenario'][:150] + '...'
        hasil['kompetensi'] = kompetensi

        hasil_per_soal.append(hasil)
        skor_total += hasil['skor'] * bobot_per_soal[i]

        # Akumulasi skor per kompetensi
        if kompetensi not in profil:
            profil[kompetensi] = []
        profil[kompetensi].append(hasil['skor'])

    # Rata-rata skor per kompetensi
    profil_rata = {k: round(sum(v) / len(v), 2) for k, v in profil.items()}

    skor_total  = round(skor_total, 2)
    grade_total = _skor_ke_grade(skor_total)
    rekomendasi = _generate_rekomendasi(skor_total, profil_rata)

    return {
        'hasil_per_soal':   hasil_per_soal,
        'skor_total':       skor_total,
        'grade_total':      grade_total,
        'profil_kompetensi': profil_rata,
        'rekomendasi':      rekomendasi,
        'jumlah_soal':      n,
    }


# ── Helper internal ──────────────────────────────────────────────────────────────

def _skor_ke_grade(skor: float) -> str:
    for grade, threshold in GRADE_THRESHOLDS.items():
        if skor >= threshold:
            return grade
    return 'E'


def _generate_feedback(skor: float, dipilih: dict, terbaik: dict) -> str:
    if dipilih['huruf'] == terbaik['huruf']:
        return 'Pilihan tepat! Respons ini mencerminkan pendekatan terbaik untuk situasi ini.'
    elif skor >= 70:
        return (f'Pilihan cukup baik. Respons "{terbaik["huruf"]}" akan lebih optimal '
                f'untuk situasi ini.')
    elif skor >= 40:
        return (f'Pilihan kurang tepat. Pertimbangkan respons "{terbaik["huruf"]}" '
                f'yang lebih sesuai konteks kerja profesional.')
    else:
        return (f'Pilihan tidak sesuai harapan. Pelajari kembali respons yang tepat '
                f'untuk situasi serupa di lingkungan kerja.')


def _generate_rekomendasi(skor_total: float, profil: dict) -> str:
    """Generate narasi rekomendasi otomatis berdasarkan profil kompetensi."""
    if not profil:
        return 'Data profil kompetensi tidak tersedia.'

    # Kompetensi terkuat dan terlemah
    terkuat  = max(profil, key=profil.get)
    terlemah = min(profil, key=profil.get)

    if skor_total >= 85:
        narasi = (f'Kandidat menunjukkan kesiapan kerja yang sangat baik. '
                  f'Kompetensi terkuat: {terkuat} ({profil[terkuat]:.1f}). '
                  f'Sangat direkomendasikan untuk tahap selanjutnya.')
    elif skor_total >= 70:
        narasi = (f'Kandidat memiliki kesiapan kerja yang baik. '
                  f'Kompetensi terkuat: {terkuat} ({profil[terkuat]:.1f}). '
                  f'Perlu pengembangan pada aspek {terlemah} ({profil[terlemah]:.1f}).')
    elif skor_total >= 55:
        narasi = (f'Kandidat cukup berpotensi namun perlu pengembangan lebih lanjut. '
                  f'Fokus pengembangan pada: {terlemah} ({profil[terlemah]:.1f}).')
    else:
        narasi = (f'Kandidat belum menunjukkan kesiapan kerja yang memadai. '
                  f'Disarankan untuk tidak melanjutkan ke tahap berikutnya.')

    return narasi