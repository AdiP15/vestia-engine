# scripts/seed_soal_sjt.py
"""
Script untuk mengisi bank soal SJT dengan contoh soal.
Jalankan SEKALI: python scripts/seed_soal_sjt.py
(Server Django tidak perlu jalan, tapi venv harus aktif)
"""

import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prismata.settings')
import django
django.setup()

from matching.models import SoalSJT

CONTOH_SOAL = [
    {
        'skenario': (
            'Kamu sedang mengerjakan laporan penting dengan deadline besok pagi. '
            'Tiba-tiba rekan kerja datang meminta bantuan urgent untuk masalah teknis '
            'yang tidak bisa dia selesaikan sendiri dan akan menghambat pekerjaan timnya. '
            'Apa yang kamu lakukan?'
        ),
        'kompetensi': 'Teamwork',
        'pilihan': [
            {'huruf': 'A', 'teks': 'Menolak karena deadline laporan kamu lebih penting.', 'bobot': 0.1},
            {'huruf': 'B', 'teks': 'Membantu sebentar untuk memahami masalahnya, lalu bersama mencari solusi cepat agar keduanya bisa selesai.', 'bobot': 0.9},
            {'huruf': 'C', 'teks': 'Menyuruh rekan itu mencari bantuan ke orang lain agar tidak mengganggu pekerjaanmu.', 'bobot': 0.2},
            {'huruf': 'D', 'teks': 'Meninggalkan laporan dan fokus membantu rekan sampai selesai meskipun deadline terlewat.', 'bobot': 0.4},
        ]
    },
    {
        'skenario': (
            'Dalam rapat tim, kamu menyadari bahwa keputusan yang akan diambil atasan '
            'berpotensi menimbulkan masalah teknis serius di kemudian hari. '
            'Namun atasan tampak sangat yakin dan tim lain sudah menyetujuinya. '
            'Apa yang kamu lakukan?'
        ),
        'kompetensi': 'Communication',
        'pilihan': [
            {'huruf': 'A', 'teks': 'Diam saja karena tidak ingin terlihat mempermasalahkan keputusan atasan di depan umum.', 'bobot': 0.1},
            {'huruf': 'B', 'teks': 'Menyampaikan kekhawatiranmu dengan sopan, disertai data dan analisis teknis yang mendukung, serta menawarkan alternatif solusi.', 'bobot': 0.9},
            {'huruf': 'C', 'teks': 'Keluar dari rapat dan mengirim email keberatan kepada manajemen di atas atasan.', 'bobot': 0.2},
            {'huruf': 'D', 'teks': 'Meminta rekan yang lebih senior untuk menyampaikan kekhawatiranmu agar tidak terlihat konfrontatif.', 'bobot': 0.5},
        ]
    },
    {
        'skenario': (
            'Kamu diberi tanggung jawab memimpin proyek baru dengan anggota tim yang '
            'memiliki latar belakang dan pengalaman sangat berbeda. Salah satu anggota '
            'yang paling berpengalaman sering tidak setuju dengan arahanmu di depan tim. '
            'Apa yang kamu lakukan?'
        ),
        'kompetensi': 'Leadership',
        'pilihan': [
            {'huruf': 'A', 'teks': 'Menegurnya keras di depan tim agar tidak terjadi lagi.', 'bobot': 0.1},
            {'huruf': 'B', 'teks': 'Mengabaikannya dan tetap melanjutkan arahanmu tanpa merespons ketidaksetujuannya.', 'bobot': 0.2},
            {'huruf': 'C', 'teks': 'Berbicara dengannya secara pribadi, mendengarkan perspektifnya, dan mencari cara agar pengalamannya bisa memperkuat proyek.', 'bobot': 0.9},
            {'huruf': 'D', 'teks': 'Melaporkan sikapnya ke manajer agar mendapat teguran resmi.', 'bobot': 0.1},
        ]
    },
    {
        'skenario': (
            'Di pertengahan proyek, kamu menyadari bahwa estimasi waktu yang sudah '
            'kamu janjikan ke klien tidak akan tercapai karena ada kendala teknis '
            'yang tidak terprediksi sebelumnya. Klien sangat mengandalkan jadwal ini. '
            'Apa yang kamu lakukan?'
        ),
        'kompetensi': 'Integrity',
        'pilihan': [
            {'huruf': 'A', 'teks': 'Tidak memberitahu klien dan berharap tim bisa mengejar keterlambatan.', 'bobot': 0.1},
            {'huruf': 'B', 'teks': 'Segera memberitahu klien tentang situasinya, menjelaskan penyebab keterlambatan, dan menawarkan solusi atau jadwal revisi yang realistis.', 'bobot': 0.9},
            {'huruf': 'C', 'teks': 'Menyalahkan kendala teknis ke pihak vendor agar klien tidak menyalahkan timmu.', 'bobot': 0.1},
            {'huruf': 'D', 'teks': 'Meminta perpanjangan waktu tanpa penjelasan detail kepada klien.', 'bobot': 0.4},
        ]
    },
    {
        'skenario': (
            'Perusahaan baru saja mengadopsi tools dan workflow baru yang sangat '
            'berbeda dari yang biasa kamu gunakan. Kamu merasa lebih nyaman dengan '
            'cara lama dan belum terbiasa dengan sistem baru ini, sementara deadline '
            'project sudah mendekat. Apa yang kamu lakukan?'
        ),
        'kompetensi': 'Adaptability',
        'pilihan': [
            {'huruf': 'A', 'teks': 'Tetap menggunakan cara lama karena lebih cepat dan efisien untukmu saat ini.', 'bobot': 0.2},
            {'huruf': 'B', 'teks': 'Belajar tools baru secara aktif di luar jam kerja, meminta bantuan rekan yang sudah familiar, dan mulai menerapkannya meskipun masih dalam proses adaptasi.', 'bobot': 0.9},
            {'huruf': 'C', 'teks': 'Meminta atasan untuk menunda adopsi tools baru sampai setelah project selesai.', 'bobot': 0.3},
            {'huruf': 'D', 'teks': 'Menyelesaikan project ini dengan cara lama, baru belajar tools baru di project berikutnya.', 'bobot': 0.4},
        ]
    },
]


def seed():
    print("=" * 55)
    print("Mengisi bank soal SJT dengan contoh soal ...")
    print("=" * 55)

    created = 0
    for data in CONTOH_SOAL:
        # Cek apakah soal dengan skenario serupa sudah ada
        if SoalSJT.objects.filter(skenario=data['skenario']).exists():
            print(f"  SKIP (sudah ada): [{data['kompetensi']}] {data['skenario'][:50]}...")
            continue

        soal = SoalSJT(
            skenario   = data['skenario'],
            kompetensi = data['kompetensi'],
            aktif      = True,
        )
        soal.set_pilihan(data['pilihan'])
        soal.save()
        created += 1
        print(f"  ✅ Dibuat: [{data['kompetensi']}] {data['skenario'][:50]}...")

    print(f"\n✅ Selesai! {created} soal baru ditambahkan.")
    print(f"   Total soal aktif: {SoalSJT.objects.filter(aktif=True).count()} soal")
    print(f"\n   Buka http://127.0.0.1:8000/matching/sjt/ untuk mencoba.")


if __name__ == '__main__':
    seed()