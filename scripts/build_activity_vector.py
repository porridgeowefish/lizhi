from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_INPUT = Path("text/activity/club.txt")
DEFAULT_OUTPUT_DIR = Path(".run/embeddings")


def split_text(text: str, *, max_chars: int = 240) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    pieces = [
        piece.strip()
        for piece in re.split(r"(?<=[。！？!?；;])\s*|\n+", normalized)
        if piece.strip()
    ]
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
            continue
        if len(current) + len(piece) + 1 <= max_chars:
            current = f"{current} {piece}"
        else:
            chunks.append(current)
            current = piece
    if current:
        chunks.append(current)

    long_safe_chunks: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            long_safe_chunks.append(chunk)
            continue
        for start in range(0, len(chunk), max_chars):
            part = chunk[start : start + max_chars].strip()
            if part:
                long_safe_chunks.append(part)
    return long_safe_chunks


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.clip(norm, 1e-12, None)


def encode_texts(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    return model.encode(
        texts,
        batch_size=8,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-chars", type=int, default=240)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")
    chunks = split_text(text, max_chars=args.max_chars)
    if not chunks:
        raise SystemExit(f"No text found in {args.input}")

    model = SentenceTransformer(args.model, device="cpu")
    embeddings = encode_texts(model, chunks)
    centroid = l2_normalize(embeddings.mean(axis=0))

    probes = [
        "深圳大学创业者联盟春季纳新，欢迎同学加入社团并参加活动。",
        "学院发布期末考试安排和准考证打印通知。",
        "学校举办户外徒步和社团招新活动，报名加入咨询群。",
        "企业校园招聘宣讲会开放投递。",
    ]
    probe_embeddings = encode_texts(model, probes)
    probe_scores = (probe_embeddings @ centroid).tolist()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    vector_path = args.output_dir / f"{stem}_centroid.npy"
    chunks_path = args.output_dir / f"{stem}_chunks.json"
    meta_path = args.output_dir / f"{stem}_meta.json"

    np.save(vector_path, centroid)
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "input": str(args.input),
        "model": args.model,
        "chunk_count": len(chunks),
        "embedding_dim": int(centroid.shape[0]),
        "vector_path": str(vector_path),
        "chunks_path": str(chunks_path),
        "probe_scores": [
            {"text": text, "score": round(float(score), 4)}
            for text, score in zip(probes, probe_scores, strict=True)
        ],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
