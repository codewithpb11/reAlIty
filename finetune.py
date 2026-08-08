"""
finetune.py

Continues fine-tuning the Ateeqq/ai-vs-human-image-detector checkpoint on
YOUR OWN curated dataset of hard cases - specifically the failure modes we
found through manual testing (filtered/beautified selfies misclassified as
AI, edited photos, modern AI portrait generations).

HOW TO USE THIS IN GOOGLE COLAB:
1. Go to colab.research.google.com, start a new notebook.
2. Runtime -> Change runtime type -> select "T4 GPU" -> Save.
3. Build your dataset locally in this exact folder structure, zip it:

     dataset/
       train/
         ai/     <- AI-generated images (aim for a few hundred+)
         hum/    <- Real/human images - INCLUDE filtered selfies, edited
                    photos, the exact hard cases the base model gets wrong
       val/
         ai/     <- a smaller held-out set (~15-20% the size of train), used
         hum/       only to check progress, not trained on

4. In a Colab cell, upload and unzip your dataset:
     from google.colab import files
     files.upload()  # upload dataset.zip
     !unzip -q dataset.zip

5. Paste this whole file into a Colab cell (or split at the blank lines
   below into a few cells) and run it.
6. When it finishes, download the "reality-finetuned/final" folder (zip it
   first: !zip -r final.zip reality-finetuned/final) and save it somewhere
   safe on your computer.
"""

# --- Cell 1: install dependencies -------------------------------------------
# !pip install -q --upgrade transformers datasets accelerate evaluate pillow-avif-plugin pillow-heif
#
# NOTE: don't reinstall torch/torchvision in Colab. Colab already ships a
# GPU-linked build that matches its preinstalled CUDA drivers - forcing an
# upgrade is what causes the "cuda-toolkit ... requires 12.*, but you have
# ..." dependency-resolver warnings you saw. Those warnings are otherwise
# harmless, but skipping the reinstall avoids them and is a bit safer.
# After installing, sanity-check the GPU is still wired up correctly:
#   import torch; print(torch.__version__, torch.cuda.is_available())

# --- Cell 2: fine-tune -------------------------------------------------------
from datasets import load_dataset
from transformers import (
    AutoImageProcessor,
    EarlyStoppingCallback,
    SiglipForImageClassification,
    TrainingArguments,
    Trainer,
)
import numpy as np
import evaluate
from torchvision.transforms import Compose, RandomHorizontalFlip, ColorJitter, RandomApply

MODEL_ID = "Ateeqq/ai-vs-human-image-detector"  # continue from your working checkpoint
DATA_DIR = "/content/dataset"

processor = AutoImageProcessor.from_pretrained(MODEL_ID)
model = SiglipForImageClassification.from_pretrained(MODEL_ID)

# "imagefolder" auto-detects labels from your ai/ and hum/ subfolder names
dataset = load_dataset("imagefolder", data_dir=DATA_DIR)
print(f"Loaded {len(dataset['train'])} training images and {len(dataset['validation'])} validation images.")
print("Note: video files are not training examples here. Extract a few frames from each video first.")

# --- Sanity check: label order must match between the pretrained model and
# your dataset folders. "imagefolder" assigns ids by sorting folder names
# alphabetically (so "ai" -> 0, "hum" -> 1). If the base model's own
# id2label isn't ordered the same way, fine-tuning would silently learn
# AI and Human backwards - no error, just a confidently wrong model.
# This used to be a print-and-eyeball step; it's now an enforced check so a
# mismatch stops the run instead of quietly shipping a backwards model.
dataset_label_order = {index: name for index, name in enumerate(dataset["train"].features["label"].names)}
model_label_order = {int(index): name for index, name in model.config.id2label.items()}
print("Model id2label:      ", model_label_order)
print("Dataset label order: ", dataset_label_order)
assert model_label_order == dataset_label_order, (
    "Label order mismatch between the base model and your dataset folders!\n"
    f"  Model id2label:      {model_label_order}\n"
    f"  Dataset label order: {dataset_label_order}\n"
    "Fine-tuning on this would silently learn AI vs Human backwards - a confidently "
    "wrong model with no error. Rename your dataset/train and dataset/val subfolders "
    "(or re-check MODEL_ID) so the two orderings match exactly, then re-run."
)

# --- Data augmentation (train split only) -----------------------------------
# With only ~100-200 images per class, the model can memorize the training
# set rather than learn general "AI vs human" patterns. Light augmentation
# on train only (never on val, so val stays an honest read of how well the
# model generalizes) helps counter that.
train_augment = Compose([
    RandomHorizontalFlip(p=0.5),
    RandomApply([ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15)], p=0.5),
])


def transform_train(batch):
    images = [train_augment(img.convert("RGB")) for img in batch["image"]]
    inputs = processor(images=images, return_tensors="pt")
    inputs["labels"] = batch["label"]
    return inputs


def transform_eval(batch):
    images = [img.convert("RGB") for img in batch["image"]]
    inputs = processor(images=images, return_tensors="pt")
    inputs["labels"] = batch["label"]
    return inputs


dataset["train"] = dataset["train"].with_transform(transform_train)
dataset["validation"] = dataset["validation"].with_transform(transform_eval)

accuracy_metric = evaluate.load("accuracy")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return accuracy_metric.compute(predictions=preds, references=labels)


training_args = TrainingArguments(
    output_dir="reality-finetuned",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=6,
    learning_rate=5e-6,   # small - we're nudging an already-trained model, not starting fresh
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,   # keep only the 2 most recent checkpoints - avoids filling Colab's disk
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    logging_steps=10,
    report_to="none",     # skip W&B - without this, Trainer can prompt for an API key and hang
    remove_unused_columns=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
)

trainer.train()

# --- Cell 3: save the result -------------------------------------------------
trainer.save_model("reality-finetuned/final")
processor.save_pretrained("reality-finetuned/final")

print("Done. Zip 'reality-finetuned/final' and download it, then in detector.py")
print("change MODEL_ID from the Hugging Face hub name to the local folder path")
print("where you saved this - e.g. MODEL_ID = './reality-finetuned/final'")