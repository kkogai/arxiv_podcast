# ===============================
# ビルドステージ
# ===============================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# メタデータの設定
LABEL maintainer="arxiv-podcast-system"
LABEL description="ArXiv論文ポッドキャスト生成システム"
LABEL version="0.1.0"

# ビルド時の環境変数を設定
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# セキュリティのため非rootユーザーを作成
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

# 依存関係を最初にインストール（レイヤーキャッシュの最適化）
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# ソースコードをコピー
COPY --chown=app:app . /app/

# プロジェクトをインストール
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# ===============================
# 実行ステージ
# ===============================
FROM python:3.11-slim-bookworm AS runtime

# セキュリティアップデートと必要な依存関係をインストール
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 非rootユーザーを作成
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# アプリケーションと仮想環境をコピー
COPY --from=builder --chown=app:app /app /app

# 作業ディレクトリとPATHを設定
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ="Asia/Tokyo"

# データディレクトリを作成（永続化用）
RUN mkdir -p /app/data && chown -R app:app /app/data

# 非rootユーザーに切り替え
USER app

# ヘルスチェックを追加
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# より良いシグナルハンドリングのためexec形式を使用
CMD ["python", "main.py", "--skip-audio"]

# エントリーポイントの使用例:
# 完全な処理（音声生成まで）を実行したい場合:
# docker run --rm -v $(pwd)/data:/app/data -e GEMINI_API_KEY=your_key your-image python main.py
#
# 台本生成のみ実行したい場合:
# docker run --rm -v $(pwd)/data:/app/data -e GEMINI_API_KEY=your_key your-image python main.py --skip-audio
#
# 音声生成のみ実行したい場合:
# docker run --rm -v $(pwd)/data:/app/data -e GEMINI_API_KEY=your_key your-image python output_podcast.py /app/data/yyyymmdd/
#
# MP3変換のみ実行したい場合:
# docker run --rm -v $(pwd)/data:/app/data your-image python convert_wav_to_mp3.py /app/data/yyyymmdd/