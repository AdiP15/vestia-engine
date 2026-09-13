# matching/views.py
"""
Views untuk Modul 2: Skill Matching & Smart Grading.

Endpoint:
  GET/POST /matching/         → form + hasil skill matching
  GET/POST /matching/grading/ → form + hasil smart grading
  GET      /matching/history/ → riwayat hasil (untuk HRD)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from .services import run_full_matching
from .grading   import grade_essay
from .models    import HasilMatching, HasilSmartGrading


def skill_matching_view(request):
    """
    Form Skill Matching dan tampilkan hasilnya.
    GET  → tampilkan form kosong
    POST → proses input, tampilkan hasil
    """
    result = None

    if request.method == 'POST':
        resume_text          = request.POST.get('resume_text', '').strip()
        job_description      = request.POST.get('job_description', '').strip()
        required_skills_csv  = request.POST.get('required_skills', '').strip()
        nama_lowongan        = request.POST.get('nama_lowongan', 'Lowongan Tidak Diketahui').strip()

        if not resume_text or not job_description:
            messages.error(request, 'Resume dan deskripsi lowongan wajib diisi.')
        else:
            # Panggil logika utama dari services.py
            result = run_full_matching(
                resume_text         = resume_text,
                job_description     = job_description,
                required_skills_csv = required_skills_csv,
            )

            # Simpan ke database
            HasilMatching.objects.create(
                pelamar             = request.user if request.user.is_authenticated else None,
                nama_lowongan       = nama_lowongan,
                resume_text         = resume_text,
                job_desc_text       = job_description,
                compatibility_score = result['score'],
                label               = result['label'],
                cosine_raw          = result['cosine_raw'],
                matched_skills      = ', '.join(result['matched_skills']),
                missing_skills      = ', '.join(result['missing_skills']),
                skill_match_pct     = result['skill_match_pct'],
            )

            messages.success(request, f"Matching selesai! Skor: {result['score']:.1f}% ({result['label']})")

    context = {
        'result':     result,
        'page_title': 'Skill Matching',
    }
    return render(request, 'matching/match_form.html', context)


def smart_grading_view(request):
    """
    Form Smart Grading esai dan tampilkan hasilnya.
    GET  → tampilkan form kosong
    POST → proses input, tampilkan hasil
    """
    result = None

    if request.method == 'POST':
        nama_soal       = request.POST.get('nama_soal', '').strip()
        jawaban_pelamar = request.POST.get('jawaban_pelamar', '').strip()
        jawaban_ideal   = request.POST.get('jawaban_ideal', '').strip()

        if not jawaban_pelamar or not jawaban_ideal:
            messages.error(request, 'Jawaban pelamar dan jawaban ideal wajib diisi.')
        else:
            result = grade_essay(jawaban_pelamar, jawaban_ideal)

            # Simpan ke database
            HasilSmartGrading.objects.create(
                pelamar         = request.user if request.user.is_authenticated else None,
                nama_soal       = nama_soal or 'Soal Tidak Diberi Judul',
                jawaban_pelamar = jawaban_pelamar,
                jawaban_ideal   = jawaban_ideal,
                score           = result['score'],
                grade           = result['grade'],
                cosine_raw      = result['cosine_raw'],
                feedback        = result['feedback'],
            )

            messages.success(request, f"Penilaian selesai! Nilai: {result['score']:.1f} ({result['grade']})")

    context = {
        'result':     result,
        'page_title': 'Smart Grading',
    }
    return render(request, 'matching/grading_form.html', context)


def history_view(request):
    """Riwayat semua hasil matching dan grading (untuk HRD/Admin)."""
    matching_list = HasilMatching.objects.all().order_by('-dibuat_pada')[:50]
    grading_list  = HasilSmartGrading.objects.all().order_by('-dibuat_pada')[:50]

    context = {
        'matching_list': matching_list,
        'grading_list':  grading_list,
        'page_title':    'Riwayat Hasil',
    }
    return render(request, 'matching/history.html', context)

# Tambahkan di bagian bawah matching/views.py

import json
from .sjt     import grade_sesi_sjt
from .models  import SoalSJT, HasilSJT


def sjt_kerjakan_view(request):
    """
    Halaman pelamar mengerjakan tes SJT.
    GET  → tampilkan semua soal SJT aktif
    POST → proses jawaban, simpan hasil, redirect ke halaman hasil
    """
    soal_list = SoalSJT.objects.filter(aktif=True).order_by('kompetensi')

    if not soal_list.exists():
        messages.warning(
            request,
            'Belum ada soal SJT yang aktif. Minta HRD untuk menambahkan soal '
            'lewat halaman Admin Django.'
        )
        return render(request, 'matching/sjt_kerjakan.html', {'soal_list': []})

    if request.method == 'POST':
        nama_sesi = request.POST.get('nama_sesi', 'Psikotes SJT').strip()

        # Kumpulkan jawaban dari form: {'soal_id': 'huruf_pilihan'}
        jawaban = {}
        for soal in soal_list:
            pilihan = request.POST.get(f'soal_{soal.id}', '')
            if pilihan:
                jawaban[str(soal.id)] = pilihan

        if len(jawaban) < soal_list.count():
            messages.error(request, 'Semua soal wajib dijawab sebelum submit.')
            return render(request, 'matching/sjt_kerjakan.html', {
                'soal_list': soal_list,
                'jawaban_sebelumnya': jawaban,
            })

        # Siapkan bank soal dalam format yang dibutuhkan sjt.py
        bank_soal = []
        for soal in soal_list:
            bank_soal.append({
                'id':         str(soal.id),
                'skenario':   soal.skenario,
                'kompetensi': soal.kompetensi,
                'pilihan':    soal.pilihan,
            })

        # Hitung skor
        hasil = grade_sesi_sjt(jawaban, bank_soal)

        # Simpan ke database
        obj = HasilSJT.objects.create(
            pelamar      = request.user if request.user.is_authenticated else None,
            nama_sesi    = nama_sesi,
            jawaban_json = json.dumps(jawaban),
            skor_total   = hasil['skor_total'],
            grade_total  = hasil['grade_total'],
            profil_json  = json.dumps(hasil['profil_kompetensi']),
            rekomendasi  = hasil['rekomendasi'],
            detail_json  = json.dumps(hasil['hasil_per_soal']),
        )

        return redirect('matching:sjt_hasil', pk=obj.pk)

    return render(request, 'matching/sjt_kerjakan.html', {'soal_list': soal_list})


def sjt_hasil_view(request, pk):
    """Tampilkan laporan hasil SJT untuk satu sesi (by primary key)."""
    from django.shortcuts import get_object_or_404
    obj = get_object_or_404(HasilSJT, pk=pk)

    context = {
        'obj':       obj,
        'profil':    obj.profil_kompetensi,
        'detail':    obj.detail_per_soal,
        'page_title': f'Hasil SJT — {obj.nama_sesi}',
    }
    return render(request, 'matching/sjt_hasil.html', context)


def sjt_soal_form_view(request):
    """
    Form untuk HRD menambah soal SJT baru tanpa masuk ke halaman Admin.
    GET  → tampilkan form kosong
    POST → simpan soal baru ke database
    """
    if request.method == 'POST':
        skenario   = request.POST.get('skenario', '').strip()
        kompetensi = request.POST.get('kompetensi', '').strip()

        # Ambil teks dan bobot tiap pilihan
        pilihan = []
        valid   = True
        for huruf in ['A', 'B', 'C', 'D']:
            teks  = request.POST.get(f'teks_{huruf}', '').strip()
            bobot = request.POST.get(f'bobot_{huruf}', '').strip()

            if not teks:
                messages.error(request, f'Teks pilihan {huruf} wajib diisi.')
                valid = False
                break
            try:
                bobot_float = float(bobot)
                if not (0.0 <= bobot_float <= 1.0):
                    raise ValueError
            except ValueError:
                messages.error(request, f'Bobot pilihan {huruf} harus angka 0.0–1.0.')
                valid = False
                break

            pilihan.append({'huruf': huruf, 'teks': teks, 'bobot': bobot_float})

        if valid and skenario and kompetensi:
            soal = SoalSJT(
                skenario   = skenario,
                kompetensi = kompetensi,
                dibuat_oleh = request.user if request.user.is_authenticated else None,
            )
            soal.set_pilihan(pilihan)
            soal.save()
            messages.success(request, f'Soal SJT [{kompetensi}] berhasil disimpan!')
            return redirect('matching:sjt_soal_form')
        elif not skenario:
            messages.error(request, 'Skenario soal wajib diisi.')

    from .sjt import KOMPETENSI_LIST
    context = {
        'kompetensi_list': KOMPETENSI_LIST,
        'page_title':      'Tambah Soal SJT',
    }
    return render(request, 'matching/sjt_soal_form.html', context)