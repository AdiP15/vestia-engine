# matching/ml_model.py
"""
Singleton loader untuk model Sentence-BERT (SBERT).

Model di-load SEKALI saat server Django pertama kali startup,
lalu disimpan di variabel modul (_model) supaya tidak reload
setiap ada request baru. Ini penting karena load model SBERT
bisa makan waktu 10-30 detik.

Model yang dipakai: paraphrase-multilingual-MiniLM-L12-v2
  - Ringan: ukuran ~450MB
  - Mendukung multibahasa termasuk Indonesia
  - Cocok untuk semester ini tanpa perlu GPU
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Variabel internal — None sampai load() dipanggil pertama kali
_model: SentenceTransformer | None = None

# Nama model yang akan di-download otomatis dari Hugging Face
# Bisa diganti dengan model lain kalau ingin eksperimen
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load() -> SentenceTransformer:
    """
    Kembalikan instance model SBERT. Load dari disk/internet
    hanya jika belum pernah di-load sebelumnya (singleton pattern).

    Returns:
        SentenceTransformer: model yang siap dipakai untuk encode()
    """
    global _model

    if _model is None:
        logger.info(f"[ML Model] Loading SBERT model: {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("[ML Model] Model berhasil di-load dan siap dipakai.")

    return _model


def encode(texts: list[str]) -> list:
    """
    Shortcut untuk encode daftar teks jadi vektor embeddings.

    Args:
        texts: list string yang akan di-encode

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    model = load()
    return model.encode(texts, convert_to_numpy=True)