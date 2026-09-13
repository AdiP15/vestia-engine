# matching/grading.py
"""
Smart Grading: Penilaian jawaban esai pelamar secara semantik.

Cara kerja:
1. HRD menyediakan "jawaban ideal" untuk soal tertentu
2. Pelamar menjawab pertanyaan esai
3. Sistem encode keduanya pakai SBERT → cosine similarity
4. Hasilnya adalah nilai semantik (seberapa dekat makna jawabannya)

Ini berbeda dari pencocokan kata kunci biasa — SBERT paham makna,
jadi "I build web applications" dan "I develop websites" bisa
dapat nilai tinggi meskipun kata-katanya berbeda.
"""

from . import ml_model
from sklearn.metrics.pairwise import cosine_similarity


# Batas nilai huruf (sesuaikan dengan standar penilaian kampus kalian)
GRADE_THRESHOLDS = {
    'A':  85.0,  # 85–100: Jawaban sangat relevan & komprehensif
    'B':  70.0,  # 70–84 : Jawaban relevan dengan beberapa kekurangan
    'C':  55.0,  # 55–69 : Jawaban cukup relevan
    'D':  40.0,  # 40–54 : Jawaban kurang relevan
    'E':   0.0,  # 0–39  : Jawaban tidak relevan / kosong
}


def grade_essay(student_answer: str, ideal_answer: str) -> dict:
    """
    Nilai satu jawaban esai dibandingkan jawaban ideal.

    Args:
        student_answer : Jawaban esai dari pelamar
        ideal_answer   : Jawaban ideal yang ditulis HRD

    Returns:
        dict berisi:
            - score         : float, nilai 0.0–100.0
            - grade         : str, huruf mutu (A/B/C/D/E)
            - cosine_raw    : float, cosine similarity mentah
            - feedback      : str, pesan feedback otomatis
    """
    if not student_answer or not student_answer.strip():
        return {
            'score': 0.0,
            'grade': 'E',
            'cosine_raw': 0.0,
            'feedback': 'Jawaban kosong atau tidak diisi.',
        }

    if not ideal_answer or not ideal_answer.strip():
        # Kalau tidak ada jawaban ideal, tidak bisa dinilai
        return {
            'score': 0.0,
            'grade': 'N/A',
            'cosine_raw': 0.0,
            'feedback': 'Jawaban ideal belum tersedia untuk soal ini.',
        }

    # Encode dua jawaban sekaligus
    embeddings  = ml_model.encode([student_answer, ideal_answer])
    student_vec = embeddings[0].reshape(1, -1)
    ideal_vec   = embeddings[1].reshape(1, -1)

    cosine_raw  = float(cosine_similarity(student_vec, ideal_vec)[0][0])
    score       = max(0.0, min(100.0, cosine_raw * 100.0))
    grade       = _score_to_grade(score)
    feedback    = _generate_feedback(score, grade)

    return {
        'score':      round(score, 2),
        'grade':      grade,
        'cosine_raw': round(cosine_raw, 4),
        'feedback':   feedback,
    }


def grade_multiple_essays(answers_and_ideals: list[tuple[str, str]],
                           weights: list[float] | None = None) -> dict:
    """
    Nilai beberapa soal esai sekaligus dan hitung nilai akhir.

    Args:
        answers_and_ideals : list of (student_answer, ideal_answer)
        weights            : list bobot tiap soal (harus jumlahnya = 1.0).
                             Kalau None, semua soal diberi bobot sama.

    Returns:
        dict berisi:
            - results       : list hasil grade_essay per soal
            - final_score   : float, nilai akhir setelah pembobotan
            - final_grade   : str, huruf mutu akhir
    """
    if not answers_and_ideals:
        return {'results': [], 'final_score': 0.0, 'final_grade': 'E'}

    n = len(answers_and_ideals)

    # Kalau tidak ada bobot, distribusi rata
    if weights is None:
        weights = [1.0 / n] * n

    if len(weights) != n:
        raise ValueError("Jumlah weights harus sama dengan jumlah soal.")

    results = []
    total_score = 0.0

    for i, (student_ans, ideal_ans) in enumerate(answers_and_ideals):
        result = grade_essay(student_ans, ideal_ans)
        results.append(result)
        total_score += result['score'] * weights[i]

    final_score = round(total_score, 2)
    final_grade = _score_to_grade(final_score)

    return {
        'results':     results,
        'final_score': final_score,
        'final_grade': final_grade,
    }


# ── Helper internal ─────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    """Konversi skor numerik ke huruf mutu."""
    for grade, threshold in GRADE_THRESHOLDS.items():
        if score >= threshold:
            return grade
    return 'E'


def _generate_feedback(score: float, grade: str) -> str:
    """Generate pesan feedback otomatis berdasarkan skor."""
    if grade == 'A':
        return 'Jawaban sangat relevan dan komprehensif. Kecocokan semantik tinggi dengan jawaban ideal.'
    elif grade == 'B':
        return 'Jawaban relevan namun masih ada beberapa poin penting yang belum tercakup.'
    elif grade == 'C':
        return 'Jawaban cukup relevan. Perlu pengembangan lebih lanjut untuk mencakup aspek utama.'
    elif grade == 'D':
        return 'Jawaban kurang relevan dengan yang diharapkan. Banyak poin penting yang terlewat.'
    else:
        return 'Jawaban tidak relevan atau kosong.'