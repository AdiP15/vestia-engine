# matching/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class HasilMatching(models.Model):
    """
    Menyimpan hasil Skill Matching untuk satu pelamar pada satu lowongan.
    Satu pelamar bisa punya banyak hasil (kalau apply ke banyak lowongan).
    """

    LABEL_CHOICES = [
        ('No Fit',        'No Fit'),
        ('Potential Fit', 'Potential Fit'),
        ('Good Fit',      'Good Fit'),
    ]

    # Relasi ke user pelamar — ForeignKey agar satu user bisa punya banyak hasil
    pelamar          = models.ForeignKey(
                           User,
                           on_delete=models.CASCADE,
                           null=True, blank=True,
                           related_name='hasil_matching',
                           help_text='User pelamar (opsional untuk testing)'
                       )

    # Nama lowongan (teks, bukan ForeignKey ke Lowongan — lebih fleksibel untuk testing)
    nama_lowongan    = models.CharField(max_length=200, blank=True)

    # Input teks
    resume_text      = models.TextField(help_text='Teks resume/skill yang dinilai')
    job_desc_text    = models.TextField(help_text='Deskripsi + kualifikasi lowongan')

    # Hasil compatibility
    compatibility_score = models.FloatField(
                              help_text='Skor kecocokan 0.0–100.0'
                          )
    label            = models.CharField(
                           max_length=15,
                           choices=LABEL_CHOICES,
                           help_text='Kategori: No Fit / Potential Fit / Good Fit'
                       )
    cosine_raw       = models.FloatField(
                           default=0.0,
                           help_text='Nilai cosine similarity mentah (0.0–1.0)'
                       )

    # Skill Gap Analysis
    matched_skills   = models.TextField(
                           blank=True,
                           help_text='Skill yang cocok (pisah koma)'
                       )
    missing_skills   = models.TextField(
                           blank=True,
                           help_text='Skill yang kurang (pisah koma)'
                       )
    skill_match_pct  = models.FloatField(
                           default=0.0,
                           help_text='Persentase skill yang cocok (0–100)'
                       )

    dibuat_pada      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat_pada']
        verbose_name = 'Hasil Matching'
        verbose_name_plural = 'Hasil Matching'

    def __str__(self):
        return f"[{self.label}] {self.nama_lowongan} — {self.compatibility_score:.1f}%"

    @property
    def matched_skills_list(self):
        """Kembalikan matched_skills sebagai Python list."""
        return [s.strip() for s in self.matched_skills.split(',') if s.strip()]

    @property
    def missing_skills_list(self):
        """Kembalikan missing_skills sebagai Python list."""
        return [s.strip() for s in self.missing_skills.split(',') if s.strip()]


class HasilSmartGrading(models.Model):
    """
    Menyimpan hasil Smart Grading untuk satu sesi penilaian esai.
    """

    GRADE_CHOICES = [
        ('A', 'A — Sangat Baik (85–100)'),
        ('B', 'B — Baik (70–84)'),
        ('C', 'C — Cukup (55–69)'),
        ('D', 'D — Kurang (40–54)'),
        ('E', 'E — Sangat Kurang (< 40)'),
    ]

    pelamar          = models.ForeignKey(
                           User,
                           on_delete=models.CASCADE,
                           null=True, blank=True,
                           related_name='hasil_grading',
                       )
    nama_soal        = models.CharField(
                           max_length=500,
                           help_text='Pertanyaan atau judul soal esai'
                       )
    jawaban_pelamar  = models.TextField(help_text='Jawaban esai pelamar')
    jawaban_ideal    = models.TextField(help_text='Jawaban ideal dari HRD')

    score            = models.FloatField(help_text='Nilai 0.0–100.0')
    grade            = models.CharField(max_length=5, choices=GRADE_CHOICES)
    cosine_raw       = models.FloatField(default=0.0)
    feedback         = models.TextField(blank=True)

    dibuat_pada      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat_pada']
        verbose_name = 'Hasil Smart Grading'
        verbose_name_plural = 'Hasil Smart Grading'

    def __str__(self):
        return f"[{self.grade}] {self.nama_soal[:60]} — {self.score:.1f}"

# Tambahkan di bawah class HasilSmartGrading di matching/models.py

import json as _json


class SoalSJT(models.Model):
    """
    Bank soal SJT yang dibuat oleh HRD.
    Satu soal punya satu skenario dan 4 pilihan jawaban dengan bobot.
    """

    KOMPETENSI_CHOICES = [(k, k) for k in [
        'Teamwork', 'Problem Solving', 'Communication', 'Leadership',
        'Adaptability', 'Time Management', 'Integrity', 'Customer Focus',
    ]]

    skenario    = models.TextField(help_text='Deskripsi situasi yang dihadapi pelamar')
    kompetensi  = models.CharField(
                      max_length=50,
                      choices=KOMPETENSI_CHOICES,
                      default='Teamwork',
                      help_text='Kompetensi yang diukur oleh soal ini'
                  )
    # Pilihan A–D disimpan sebagai JSON:
    # [{"huruf":"A","teks":"...","bobot":0.2}, {"huruf":"B",...}, ...]
    pilihan_json = models.TextField(
                       help_text='Pilihan A-D dalam format JSON (isi lewat admin)'
                   )
    aktif        = models.BooleanField(default=True)
    dibuat_pada  = models.DateTimeField(auto_now_add=True)
    dibuat_oleh  = models.ForeignKey(
                       'auth.User',
                       on_delete=models.SET_NULL,
                       null=True, blank=True,
                       related_name='soal_sjt_dibuat',
                   )

    class Meta:
        verbose_name = 'Soal SJT'
        verbose_name_plural = 'Bank Soal SJT'
        ordering = ['kompetensi', 'dibuat_pada']

    def __str__(self):
        return f'[{self.kompetensi}] {self.skenario[:80]}...'

    @property
    def pilihan(self) -> list:
        """Kembalikan pilihan sebagai Python list of dict."""
        try:
            return _json.loads(self.pilihan_json)
        except Exception:
            return []

    def set_pilihan(self, pilihan_list: list):
        """Simpan list pilihan ke pilihan_json."""
        self.pilihan_json = _json.dumps(pilihan_list, ensure_ascii=False)


class HasilSJT(models.Model):
    """
    Menyimpan hasil satu sesi tes SJT oleh satu pelamar.
    """

    GRADE_CHOICES = [
        ('A', 'A — Sangat Baik (85–100)'),
        ('B', 'B — Baik (70–84)'),
        ('C', 'C — Cukup (55–69)'),
        ('D', 'D — Kurang (40–54)'),
        ('E', 'E — Sangat Kurang (< 40)'),
    ]

    pelamar         = models.ForeignKey(
                          'auth.User',
                          on_delete=models.CASCADE,
                          null=True, blank=True,
                          related_name='hasil_sjt',
                      )
    nama_sesi       = models.CharField(
                          max_length=200,
                          default='Psikotes SJT',
                          help_text='Nama sesi tes, misal: Psikotes SJT Batch 1'
                      )
    # Jawaban pelamar disimpan sebagai JSON: {"soal_id": "huruf_pilihan", ...}
    jawaban_json    = models.TextField(help_text='Jawaban pelamar dalam JSON')

    # Hasil akhir
    skor_total      = models.FloatField()
    grade_total     = models.CharField(max_length=5, choices=GRADE_CHOICES)

    # Profil kompetensi JSON: {"Teamwork": 82.5, "Leadership": 70.0, ...}
    profil_json     = models.TextField(blank=True, default='{}')
    rekomendasi     = models.TextField(blank=True)

    # Detail per soal JSON (list hasil tiap soal)
    detail_json     = models.TextField(blank=True, default='[]')

    dibuat_pada     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat_pada']
        verbose_name = 'Hasil SJT'
        verbose_name_plural = 'Hasil SJT'

    def __str__(self):
        return f'[{self.grade_total}] {self.nama_sesi} — {self.skor_total:.1f}'

    @property
    def profil_kompetensi(self) -> dict:
        try:
            return _json.loads(self.profil_json)
        except Exception:
            return {}

    @property
    def detail_per_soal(self) -> list:
        try:
            return _json.loads(self.detail_json)
        except Exception:
            return []