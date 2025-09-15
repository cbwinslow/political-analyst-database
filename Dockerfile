FROM python:3.11-slim

# Set up a non-root user
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Expose port and set entrypoint
EXPOSE 8001
CMD ["uvicorn", "crawler_service:app", "--host", "0.0.0.0", "--port", "8001"]
