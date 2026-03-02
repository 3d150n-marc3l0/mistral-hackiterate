# Use the official uv image for a small footprint and efficient dependency management
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system dependencies (ffmpeg is required by pydub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY src ./src
COPY README.md .env ./

# Install the project
RUN uv sync --frozen --no-dev

# Expose the port Streamlit runs on
EXPOSE 8501

# Set the entrypoint to run the Streamlit app
ENTRYPOINT ["uv", "run", "streamlit", "run", "src/sentinel/app.py", "--server.address=0.0.0.0"]
