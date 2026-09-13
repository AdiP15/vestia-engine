# scripts/explore_dataset.py
"""
Skrip untuk download, eksplorasi, dan simpan dataset ke folder dataset/
Jalankan SEKALI saja: python scripts/explore_dataset.py
"""

import os
import sys
import pandas as pd
from datasets import load_dataset

# ── Setup path agar bisa import dari root project ──────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_and_save():
    """Download dataset dari Hugging Face dan simpan ke CSV lokal."""
    print("=" * 60)
    print("Mengunduh dataset 0xnbk/resume-ats-score-v1-en ...")
    print("(Ukuran ~54MB, tunggu sebentar)")
    print("=" * 60)

    # Load dari Hugging Face — otomatis di-cache di ~/.cache/huggingface/
    dataset = load_dataset("0xnbk/resume-ats-score-v1-en")

    # Konversi ke pandas DataFrame
    train_df = pd.DataFrame(dataset['train'])
    val_df   = pd.DataFrame(dataset['validation'])

    # Pisahkan kolom 'text' menjadi 'resume_text' dan 'job_description'
    # Format di dataset: "resume_teks [SEP] job_description_teks"
    def split_text(text):
        parts = text.split(' SEP ', 1)  # split hanya pada [SEP] pertama
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return text.strip(), ''  # fallback kalau tidak ada SEP

    print("\nMemisahkan kolom resume dan job description ...")
    train_df[['resume_text', 'job_description']] = pd.DataFrame(
        train_df['text'].apply(split_text).tolist(), index=train_df.index
    )
    val_df[['resume_text', 'job_description']] = pd.DataFrame(
        val_df['text'].apply(split_text).tolist(), index=val_df.index
    )

    # Hapus kolom 'text' asli (sudah dipecah)
    train_df = train_df.drop(columns=['text'])
    val_df   = val_df.drop(columns=['text'])

    # Simpan ke CSV
    train_path = os.path.join(OUTPUT_DIR, 'train.csv')
    val_path   = os.path.join(OUTPUT_DIR, 'validation.csv')

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)

    print(f"\n✅ Dataset berhasil disimpan:")
    print(f"   Train      : {train_path} ({len(train_df)} baris)")
    print(f"   Validation : {val_path} ({len(val_df)} baris)")

    return train_df, val_df


def explore(df, split_name="train"):
    """Tampilkan statistik dasar dataset."""
    print(f"\n{'=' * 60}")
    print(f"EKSPLORASI DATASET — split: {split_name}")
    print(f"{'=' * 60}")

    print(f"\nJumlah baris  : {len(df)}")
    print(f"Kolom         : {list(df.columns)}")

    print(f"\n── Statistik ATS Score ──────────────────────────────────")
    print(df['ats_score'].describe().round(2).to_string())

    print(f"\n── Distribusi Label ─────────────────────────────────────")
    label_counts = df['original_label'].value_counts()
    for label, count in label_counts.items():
        pct = count / len(df) * 100
        print(f"  {label:<15} : {count:>4} baris ({pct:.1f}%)")

    print(f"\n── Contoh Data ──────────────────────────────────────────")
    for label in ['Good Fit', 'Potential Fit', 'No Fit']:
        row = df[df['original_label'] == label].iloc[0]
        print(f"\n[{label}] ATS Score: {row['ats_score']}")
        print(f"Resume     : {row['resume_text'][:200]}...")
        print(f"Job Desc   : {row['job_description'][:200]}...")


if __name__ == '__main__':
    train_df, val_df = download_and_save()
    explore(train_df, "train")
    explore(val_df, "validation")
    print("\n✅ Selesai! Jalankan server Django untuk mulai pakai Modul 2.")