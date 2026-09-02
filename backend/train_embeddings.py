import time
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODEL_DIR = Path(__file__).parent / "model"
MODEL_NAME = "all-MiniLM-L6-v2"


def build():
    df: pd.DataFrame = pd.read_pickle(MODEL_DIR / "df.pkl")

    def build_sentence(row):
        parts = [str(row["overview"])]
        if row["genres"]:
            parts.append(f"Genres: {row['genres']}.")
        if row["tagline"]:
            parts.append(str(row["tagline"]))
        return " ".join(p for p in parts if p and p != "nan")

    sentences = df.apply(build_sentence, axis=1).tolist()

    print(f"Loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Encoding {len(sentences)} movies (this takes a few minutes on CPU) ...")
    t0 = time.time()
    embeddings = model.encode(
        sentences,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(f"Done in {time.time() - t0:.1f}s. Shape: {embeddings.shape}")

    np.save(MODEL_DIR / "embeddings.npy", embeddings.astype(np.float32))
    print(f"Saved to {MODEL_DIR / 'embeddings.npy'}")


if __name__ == "__main__":
    build()
