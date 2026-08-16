# ---------------------------------------------------------------------------------------------------- #
# STAGE. 1  -  BUILDER
# ---------------------------------------------------------------------------------------------------- #
FROM python:3.13-slim as builder
# install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*
# copy requirements and install packages into user space
COPY server/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
# download spaCy model for Presidio PII detection
RUN python -m spacy download en_core_web_md
# ---------------------------------------------------------------------------------------------------- #
# STAGE. 2  -  RUN TIME STAGE
# ---------------------------------------------------------------------------------------------------- #
# run time stage, it references the above builder stage
FROM python:3.13-slim
RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
# copy installed package from builder stage -- copy only the final product (installed packages) not the build tools
# the build tools gcc are BIG and IRRELEVANT at runtime
# It copies only the installed Python packages from the builder stage into this final stage - we get all the dependancies without any of the build tools that were used to compile them
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
WORKDIR /api
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]