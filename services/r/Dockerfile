# Build from the repository root:  docker build -f services/r/Dockerfile -t aie-service-r .
FROM rocker/r-ver:4.4.1
RUN install2.r --error plumber httr2 jsonlite
WORKDIR /app
COPY aie_r/ aie_r/
COPY prompts/ prompts/
COPY data/ data/
COPY services/ services/
ENV OLLAMA_URL=http://host.docker.internal:11434 AIE_ROOT=/app
EXPOSE 8001
CMD ["Rscript", "-e", "plumber::pr_run(plumber::pr('services/r/plumber.R'), host = '0.0.0.0', port = 8001)"]
