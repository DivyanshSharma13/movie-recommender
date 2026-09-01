FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-fetch NLTK data at build time so the container doesn't need
# internet access for this at runtime.
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

COPY . .

# model/ (the .pkl artifacts) must exist before building the image --
# run `python train_model.py` locally first, or add a build step that
# does it (see README "Deploying the backend").

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
