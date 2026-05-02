import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "hamzab/roberta-fake-news-classification"
LOCAL_DIR = "ml/models/distilbert-fakenews"


def download_model():
    if os.path.exists(os.path.join(LOCAL_DIR, "config.json")):
        return

    os.makedirs(LOCAL_DIR, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(LOCAL_DIR)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.save_pretrained(LOCAL_DIR)



if __name__ == "__main__":
    download_model()