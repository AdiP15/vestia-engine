# matching/services.py
"""
Logika bisnis utama untuk Skill Matching & Compatibility Score.

Alur kerja:
1. Terima teks resume/skill pelamar + teks deskripsi lowongan
2. Encode keduanya jadi vektor pakai SBERT
3. Hitung cosine similarity → normalize jadi skor 0-100
4. Tentukan label (No Fit / Potential Fit / Good Fit)
5. Lakukan Skill Gap Analysis (skill apa yang kurang)
"""

import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from . import ml_model


# ── Threshold label (sesuai distribusi dataset 0xnbk/resume-ats-score-v1-en) ──
THRESHOLD_NO_FIT        = 40.0   # < 40  → No Fit
THRESHOLD_POTENTIAL_FIT = 70.0   # 40-70 → Potential Fit
# >= 70 → Good Fit


def compute_compatibility(resume_text: str, job_description: str) -> dict:
    """
    Hitung compatibility score antara resume pelamar dan deskripsi lowongan.

    Args:
        resume_text     : Teks resume / skill pelamar (bisa panjang)
        job_description : Teks deskripsi + kualifikasi lowongan

    Returns:
        dict berisi:
            - score         : float, skor 0.0–100.0
            - label         : str, "No Fit" / "Potential Fit" / "Good Fit"
            - cosine_raw    : float, nilai cosine similarity mentah (0.0–1.0)
            - resume_preview: str, 300 karakter pertama resume (untuk tampilan)
    """
    if not resume_text or not job_description:
        return {
            'score': 0.0,
            'label': 'No Fit',
            'cosine_raw': 0.0,
            'resume_preview': '',
        }

    # Encode dua teks sekaligus dalam satu panggilan (lebih efisien)
    embeddings = ml_model.encode([resume_text, job_description])
    resume_vec = embeddings[0].reshape(1, -1)   # shape: (1, 384)
    job_vec    = embeddings[1].reshape(1, -1)   # shape: (1, 384)

    # Cosine similarity menghasilkan nilai -1 sampai 1
    # Untuk teks resume yang positif, biasanya hasilnya 0 sampai 1
    cosine_raw = float(cosine_similarity(resume_vec, job_vec)[0][0])

    # Normalisasi ke skala 0–100
    # Rumus: clamp cosine ke 0..1 lalu kali 100
    score = max(0.0, min(100.0, cosine_raw * 100.0))

    label = _score_to_label(score)

    return {
        'score': round(score, 2),
        'label': label,
        'cosine_raw': round(cosine_raw, 4),
        'resume_preview': resume_text[:300],
    }


def compute_skill_gap(resume_text: str, required_skills_csv: str) -> dict:
    """
    Analisis skill gap: bandingkan skill pelamar dengan skill yang dibutuhkan.

    Cara kerja sederhana:
    - Parse `required_skills_csv` jadi list skill yang dibutuhkan
    - Cek tiap skill apakah muncul (substring match) di resume_text
    - Kembalikan list skill yang ADA dan yang KURANG

    Catatan: substring match ini adalah pendekatan dasar.
    Nanti bisa ditingkatkan dengan cosine similarity per-skill
    kalau ada waktu untuk eksperimen.

    Args:
        resume_text         : Teks resume pelamar
        required_skills_csv : String skill dipisah koma, contoh: "Python, Django, SQL"

    Returns:
        dict berisi:
            - matched_skills  : list skill yang ditemukan di resume
            - missing_skills  : list skill yang tidak ada di resume
            - match_pct       : float, persentase skill yang cocok (0–100)
    """
    if not required_skills_csv:
        return {'matched_skills': [], 'missing_skills': [], 'match_pct': 0.0}

    # Parse skill yang dibutuhkan
    required = [s.strip() for s in required_skills_csv.split(',') if s.strip()]
    if not required:
        return {'matched_skills': [], 'missing_skills': [], 'match_pct': 0.0}

    resume_lower = resume_text.lower()
    matched  = []
    missing  = []

    for skill in required:
        # Cari skill sebagai kata (bukan substring di tengah kata lain)
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, resume_lower):
            matched.append(skill)
        else:
            missing.append(skill)

    match_pct = (len(matched) / len(required)) * 100 if required else 0.0

    return {
        'matched_skills': matched,
        'missing_skills': missing,
        'match_pct': round(match_pct, 1),
    }


def run_full_matching(resume_text: str, job_description: str,
                      required_skills_csv: str = '') -> dict:
    """
    Fungsi utama yang menggabungkan compatibility scoring + skill gap analysis.
    Ini yang dipanggil dari views.py.

    Args:
        resume_text         : Teks resume pelamar
        job_description     : Teks deskripsi lowongan
        required_skills_csv : Skill yang dibutuhkan lowongan (pisah koma)

    Returns:
        dict lengkap berisi hasil compatibility + skill gap
    """
    compat  = compute_compatibility(resume_text, job_description)
    gap     = compute_skill_gap(resume_text, required_skills_csv)

    return {
        # Compatibility Score
        'score':         compat['score'],
        'label':         compat['label'],
        'cosine_raw':    compat['cosine_raw'],
        'resume_preview': compat['resume_preview'],

        # Skill Gap Analysis
        'matched_skills': gap['matched_skills'],
        'missing_skills': gap['missing_skills'],
        'skill_match_pct': gap['match_pct'],

        # Teks input (untuk disimpan ke DB)
        'resume_text_input': resume_text,
        'job_desc_input':    job_description,
    }


# ── Helper internal ─────────────────────────────────────────────────────────────

def _score_to_label(score: float) -> str:
    """Konversi skor numerik ke label kategori."""
    if score < THRESHOLD_NO_FIT:
        return 'No Fit'
    elif score < THRESHOLD_POTENTIAL_FIT:
        return 'Potential Fit'
    else:
        return 'Good Fit'