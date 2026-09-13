# scripts/evaluate_model.py
"""
Evaluasi akurasi Modul 2 menggunakan dataset 0xnbk/resume-ats-score-v1-en.

Metrik yang dihitung:
- MAE (Mean Absolute Error): rata-rata selisih skor prediksi vs skor asli
- RMSE: akar dari rata-rata kuadrat selisih (lebih sensitif ke error besar)
- Accuracy label: seberapa sering prediksi label cocok dengan label asli

Jalankan: python scripts/evaluate_model.py
(Server Django TIDAK perlu jalan, tapi virtual env harus aktif)
"""

import os
import sys
from pathlib import Path

# 1. Paksa sistem membaca folder utama (tempat manage.py berada)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 2. Tentukan lokasi settings.py
# PERHATIAN: Jika folder yang berisi settings.py bernama BUKAN 'prismata', 
# ubah tulisan 'prismata.settings' di bawah ini sesuai nama folder tersebut.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prismata.settings')

import django
django.setup()

# --- Sisa impor dan kode di bawah ini biarkan sama ---
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from matching.services import compute_compatibility

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'prismata','dataset', 'validation.csv'
)
N_SAMPLES = 100  # Kurangi ini kalau RAM terbatas, atau naikkan untuk evaluasi lebih akurat


def evaluate():
    print("=" * 60)
    print("EVALUASI MODUL 2 — Skill Matching")
    print("=" * 60)

    if not os.path.exists(DATASET_PATH):
        print(f"❌ File dataset tidak ditemukan: {DATASET_PATH}")
        print("   Jalankan dulu: python scripts/explore_dataset.py")
        return

    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=['resume_text', 'job_description', 'ats_score'])
    df = df.head(N_SAMPLES)

    print(f"\nEvaluasi menggunakan {len(df)} sampel dari validation set ...")
    print("(Proses ini bisa makan 2–5 menit tergantung RAM)")

    true_scores  = []
    pred_scores  = []
    true_labels  = []
    pred_labels  = []

    for i, (_, row) in enumerate(df.iterrows()):
        result = compute_compatibility(
            resume_text    = str(row['resume_text']),
            job_description = str(row['job_description']),
        )
        pred_scores.append(result['score'])
        true_scores.append(float(row['ats_score']))
        pred_labels.append(result['label'])
        true_labels.append(str(row['original_label']))

        if (i + 1) % 10 == 0:
            print(f"  Selesai: {i+1}/{len(df)}")

    # Hitung metrik
    mae  = mean_absolute_error(true_scores, pred_scores)
    rmse = np.sqrt(mean_squared_error(true_scores, pred_scores))
    acc  = sum(p == t for p, t in zip(pred_labels, true_labels)) / len(true_labels) * 100

    print(f"\n{'=' * 60}")
    print(f"HASIL EVALUASI")
    print(f"{'=' * 60}")
    print(f"Jumlah sampel  : {len(df)}")
    print(f"MAE            : {mae:.2f}  (makin rendah makin baik, target < 15)")
    print(f"RMSE           : {rmse:.2f}  (makin rendah makin baik, target < 20)")
    print(f"Label Accuracy : {acc:.1f}% (target > 60%)")
    print(f"{'=' * 60}")

    # Per-label accuracy
    print(f"\nAkurasi per label:")
    for label in ['No Fit', 'Potential Fit', 'Good Fit']:
        indices  = [i for i, t in enumerate(true_labels) if t == label]
        correct  = sum(1 for i in indices if pred_labels[i] == true_labels[i])
        total    = len(indices)
        pct      = correct / total * 100 if total > 0 else 0
        print(f"  {label:<15}: {correct}/{total} benar ({pct:.1f}%)")

    print("\n✅ Evaluasi selesai.")
    print("   Masukkan angka MAE, RMSE, dan Accuracy ke laporan skripsi kamu.")


if __name__ == '__main__':
    evaluate()