# matching/admin.py
from django.contrib import admin
from .models import HasilMatching, HasilSmartGrading


@admin.register(HasilMatching)
class HasilMatchingAdmin(admin.ModelAdmin):
    list_display  = ['nama_lowongan', 'compatibility_score', 'label',
                     'skill_match_pct', 'dibuat_pada']
    list_filter   = ['label']
    search_fields = ['nama_lowongan', 'resume_text']
    readonly_fields = ['compatibility_score', 'label', 'cosine_raw',
                       'matched_skills', 'missing_skills', 'skill_match_pct']


@admin.register(HasilSmartGrading)
class HasilSmartGradingAdmin(admin.ModelAdmin):
    list_display  = ['nama_soal', 'score', 'grade', 'dibuat_pada']
    list_filter   = ['grade']
    search_fields = ['nama_soal', 'jawaban_pelamar']
    readonly_fields = ['score', 'grade', 'cosine_raw', 'feedback']

# Tambahkan di bawah HasilSmartGradingAdmin di matching/admin.py

import json
from .models import SoalSJT, HasilSJT


class PilihanInlineAdmin(admin.TabularInline):
    """Tidak dipakai sebagai inline — pilihan disimpan sebagai JSON."""
    pass


@admin.register(SoalSJT)
class SoalSJTAdmin(admin.ModelAdmin):
    list_display  = ['kompetensi', 'skenario_preview', 'aktif', 'dibuat_pada']
    list_filter   = ['kompetensi', 'aktif']
    search_fields = ['skenario']
    readonly_fields = ['dibuat_pada']

    def skenario_preview(self, obj):
        return obj.skenario[:80] + '...' if len(obj.skenario) > 80 else obj.skenario
    skenario_preview.short_description = 'Skenario'

    # Petunjuk pengisian pilihan_json di admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['pilihan_json'].help_text = (
            'Format JSON wajib diisi seperti ini:<br>'
            '<code>[{"huruf":"A","teks":"Teks pilihan A","bobot":0.2},'
            '{"huruf":"B","teks":"Teks pilihan B","bobot":0.9},'
            '{"huruf":"C","teks":"Teks pilihan C","bobot":0.6},'
            '{"huruf":"D","teks":"Teks pilihan D","bobot":0.3}]</code><br>'
            'Bobot: 0.0 = pilihan terburuk, 1.0 = pilihan terbaik. '
            'Biasanya hanya satu pilihan yang bobotnya > 0.8.'
        )
        return form


@admin.register(HasilSJT)
class HasilSJTAdmin(admin.ModelAdmin):
    list_display  = ['nama_sesi', 'pelamar', 'skor_total', 'grade_total', 'dibuat_pada']
    list_filter   = ['grade_total', 'nama_sesi']
    readonly_fields = ['skor_total', 'grade_total', 'profil_json',
                       'rekomendasi', 'detail_json', 'dibuat_pada']