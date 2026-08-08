# reAlIty Dataset Diversity Gap Analysis

## Executive Summary

Your detector is built on a **strong foundation** but has **critical diversity gaps** that will prevent it from reaching 95-100% accuracy. The core problem isn't just quantity — it's that your training data is heavily concentrated from a single source (`Parveshiiii/AI-vs-Real`), missing modern AI generators, and lacking real-world human photo diversity. Additionally, **200 video files** sitting in your dataset are completely wasted because your training script ignores them.

---

## Current Dataset Composition

### Image Counts (On Disk)

| Split | AI Images | Human Images | Total |
|-------|-----------|--------------|-------|
| **Train** | ~1,813 | ~1,810 | ~3,623 |
| **Val** | ~354 | ~353 | ~707 |

### Video Counts (On Disk, Currently IGNORED by Training)

| Split | AI Videos | Human Videos | Total |
|-------|-----------|--------------|-------|
| **Train** | 75 | 75 | 150 |
| **Val** | 25 | 25 | 50 |

### Tracked Sources (From Manifests)

| Source | Count | Notes |
|--------|-------|-------|
| `Parveshiiii/AI-vs-Real` | ~1,585 | **~79% of all tracked data**. Single source risk. |
| Big Buck Bunny (Blender CG) | 249 | Labeled as "human" — good strategy but only one source |
| Derived hard cases | 120 | Annotations, timestamps, captions, collages, redactions |
| Independent val AI hard cases | 180 | Memes, story UI, markup, collages, reposts |
| Independent val human hard cases | 185 | Same variants as above |
| Validation human hard cases | 60 | Story UI, meme captions, collages, markup, reposts |
| **Unmanifested files** | ~3,541 | Likely manual downloads — source unknown |
| COCO 2017 (intended) | 0 in manifest | Script targets 6,500 but manifest is empty |
| FLUX Reason 6M (intended) | 0 in manifest | Script exists but never run |

---

## Critical Finding: The Single-Source Problem

**~79% of your tracked training data comes from one Hugging Face dataset.** This is your biggest bottleneck. Here's why:

- `Parveshiiii/AI-vs-Real` was likely built from a specific era of AI generators (probably Stable Diffusion 1.x/2.x, Midjourney v4/v5)
- It does NOT contain images from **Midjourney v6/v7**, **DALL-E 3**, **Stable Diffusion 3/3.5**, **FLUX.1**, **Ideogram**, **Recraft**, or **Grok** generations
- AI generators evolve rapidly. What looks "AI" in 2023 is different from 2025-2026
- If your model hasn't seen these modern styles, it will fail on them

---

## Critical Finding: Videos Are Completely Wasted

You have **200 video files** in your dataset folders. Your `finetune.py` uses `datasets.load_dataset("imagefolder", ...)` which **silently skips non-image files**. These videos are doing absolutely nothing for your model.

**Immediate fix needed:** Extract 5-10 representative frames from each video and add those frames to the image training folders. This alone could give you ~750-1,500 additional training images and ~250-500 validation images.

---

## What's Missing: AI-Generated Images (The Gaps)

To reach 95-100% accuracy, you need AI training images from **diverse generators and styles**:

### 1. Modern AI Image Generators (HIGH PRIORITY)

| Generator | Why It Matters | Target Count |
|-----------|---------------|--------------|
| **Midjourney v6 / v6.1 / v7** | Most photorealistic AI portraits on social media | 400+ train, 100+ val |
| **FLUX.1 [dev/pro/schnell]** | State-of-the-art open weights, extremely realistic | 400+ train, 100+ val |
| **DALL-E 3** | Microsoft's model, distinct style | 300+ train, 75+ val |
| **Stable Diffusion 3 / 3.5** | Common in open-source tools | 300+ train, 75+ val |
| **Ideogram 2.0 / 3.0** | Text-in-image specialist, unique look | 200+ train, 50+ val |
| **Recraft v3** | Vector + photorealistic hybrid | 150+ train, 40+ val |
| **Grok (xAI)** | Emerging, distinct aesthetic | 100+ train, 25+ val |
| **Imagen 3 (Google)** | Very clean, commercial look | 100+ train, 25+ val |

### 2. AI Image Types (By Content/Genre)

| Genre | Why It Matters | Target Count |
|-------|---------------|--------------|
| **Photorealistic portraits** | Most common AI image type | 600+ total |
| **Landscapes & nature** | AI excels at these | 300+ total |
| **Architecture & interiors** | Distinct AI patterns | 200+ total |
| **Product photography** | E-commerce AI images | 150+ total |
| **Food photography** | Very realistic AI generations | 150+ total |
| **Fashion & clothing** | Common on social media | 150+ total |
| **Animals & wildlife** | AI often struggles with anatomy | 200+ total |
| **Concept art / sci-fi** | Distinct from photorealistic | 200+ total |
| **NSFW-adjacent portraits** | AI has telltale artifacts | 100+ total |
| **Text-heavy images** | Typography errors are AI signatures | 150+ total |
| **Group photos (3+ people)** | AI struggles with consistency | 150+ total |
| **Hands & fingers close-ups** | Classic AI failure mode | 100+ total |
| **Reflections & mirrors** | AI often gets these wrong | 100+ total |

### 3. AI Image Manipulations

| Type | Why It Matters | Target Count |
|------|---------------|--------------|
| **AI-upscaled real photos** | Real photo processed by AI | 100+ total |
| **AI-restored old photos** | Real photo + AI enhancement | 100+ total |
| **AI-generated faces swapped into real photos** | Deepfake-style | 100+ total |
| **AI background replacement** | Real subject, AI background | 100+ total |
| **AI inpainting** | Partial AI, partial real | 100+ total |

---

## What's Missing: Human/Real Images (The Gaps)

Your human dataset needs to cover the **full spectrum of real photography** that users will actually upload:

### 1. Camera Types & Quality

| Type | Why It Matters | Target Count |
|------|---------------|--------------|
| **Smartphone photos (iPhone, Samsung, Pixel)** | Most common user uploads | 500+ total |
| **DSLR/mirrorless (Canon, Sony, Nikon)** | Professional look, sharp details | 300+ total |
| **Point-and-shoot / compact cameras** | Distinct processing | 100+ total |
| **Action cameras (GoPro)** | Wide angle, distinct look | 100+ total |
| **Drone photography** | Aerial, unique perspective | 100+ total |
| **360° / panoramic photos** | Distorted but real | 50+ total |
| **Film scans** | Grain, color characteristics | 100+ total |
| **Polaroid / instant film** | Distinct borders and colors | 50+ total |

### 2. Image Processing Variants (CRITICAL FOR ACCURACY)

| Type | Why It Matters | Target Count |
|------|---------------|--------------|
| **Heavy Instagram/Snapchat filters** | Often misclassified as AI | 300+ total |
| **Beauty filters / face smoothing** | Very common false positive | 200+ total |
| **HDR photography** | Can look "too perfect" | 100+ total |
| **Long exposure** | Surreal but real | 100+ total |
| **Night photography / low light** | Noise patterns differ from AI | 200+ total |
| **Motion blur** | Real artifact AI rarely mimics | 100+ total |
| **Lens flare / bokeh** | Real optical effects | 100+ total |
| **Underexposed / overexposed** | Real photos have these | 100+ total |
| **Heavy JPEG compression** | Compression artifacts look like AI | 150+ total |
| **Multiple resaves / reposts** | Degraded real photos | 100+ total |
| **Screenshots of real photos** | Pixelation, UI elements | 150+ total |

### 3. Content Types

| Type | Why It Matters | Target Count |
|------|---------------|--------------|
| **Selfies (front camera)** | Distinct distortion, skin texture | 300+ total |
| **Group photos (candid)** | Natural imperfections | 200+ total |
| **Street photography** | Candid, unposed | 200+ total |
| **Event photography (weddings, concerts)** | Flash, motion, chaos | 150+ total |
| **Sports photography** | Action, fast shutter | 150+ total |
| **Wildlife photography** | Telephoto, natural settings | 150+ total |
| **Macro photography** | Extreme detail, shallow DOF | 100+ total |
| **Documentary / photojournalism** | Gritty, real-world | 150+ total |
| **Stock photography** | Often confused with AI | 200+ total |
| **Real estate photography** | Wide angle, processed | 100+ total |
| **Medical imaging (X-rays, MRIs)** | Real but unusual | 50+ total |
| **Satellite imagery** | Real but patterned | 50+ total |
| **Microscopy** | Scientific real images | 50+ total |

### 4. Graphic Overlays (Already Started — Expand This)

Your hard-case generation is **exactly the right idea**. Expand significantly:

| Overlay Type | Current Count | Target Count |
|--------------|--------------|--------------|
| **Meme captions / text overlays** | ~71 | 300+ |
| **Story UI (Instagram/Snapchat stories)** | ~71 | 200+ |
| **Redaction boxes / blur** | ~91 | 200+ |
| **Markup / arrows / circles** | ~71 | 200+ |
| **Collages / multi-image grids** | ~91 | 200+ |
| **Timestamps / watermarks** | ~20 | 150+ |
| **Repost indicators** | ~70 | 150+ |
| **Screenshot UI (batteries, notches, toolbars)** | ~0 | 200+ |
| **News article embeds** | ~0 | 100+ |
| **Social media UI (likes, comments, shares)** | ~0 | 150+ |

---

## What's Missing: Video Content

Your app supports video detection but your training ignores videos. For video accuracy:

### For Training (Extract Frames)

| Video Type | Why It Matters | Target Videos | Frames per Video |
|------------|---------------|--------------|-----------------|
| **AI-generated video (Sora, Runway, Kling, Pika, Luma)** | Core detection target | 100+ | 5-10 frames |
| **Deepfake face-swap videos** | High-stakes detection | 50+ | 5-10 frames |
| **AI-enhanced real video** | Real footage with AI upscaling | 50+ | 5-10 frames |
| **Real smartphone video** | Most common upload | 100+ | 5-10 frames |
| **Professional video (cinema, TV)** | High quality real | 50+ | 5-10 frames |
| **Screen recordings** | Distinct real artifact | 50+ | 5-10 frames |
| **CCTV / security footage** | Low quality real | 50+ | 5-10 frames |
| **Video game recordings** | CG but not AI — tricky edge case | 50+ | 5-10 frames |
| **Animation / anime** | Hand-drawn or CG, not AI | 50+ | 5-10 frames |

### Note on Video
Your current approach (frame-by-frame classification + median) is fine for short clips. But if you want true video-level accuracy, consider adding temporal consistency checks in post-processing. For now, extracting frames and training on them is the right move.

---

## Recommended Target Dataset (Revised)

Based on this analysis, here are my revised targets:

### Images

| Split | AI Target | Human Target | Total |
|-------|-----------|--------------|-------|
| **Train** | 3,000 | 3,000 | 6,000 |
| **Val** | 700 | 700 | 1,400 |

### Videos (Extracted as Frames)

| Split | AI Videos | Human Videos | Extracted Frames |
|-------|-----------|--------------|-----------------|
| **Train** | 100 | 100 | ~1,000-2,000 frames |
| **Val** | 50 | 50 | ~500-1,000 frames |

### Total Training Images After Extraction: ~7,000-8,000 per class

---

## Sourcing Strategy: Where to Get These Images

### AI Images (Legally and Safely)

1. **Generate them yourself** (Recommended for control)
   - Use free tiers of Midjourney, DALL-E, Ideogram, FLUX
   - Generate specific categories with varied prompts
   - Document the generator version in your manifest

2. **Hugging Face Datasets**
   - `LucasFang/FLUX-Reason-6M` — Your script already targets this, but it never ran
   - `zzliux/StableDiffusion3.5-T2I` — SD 3.5 generations
   - `Sonnentier/diffusiondb-small` — Diverse Stable Diffusion outputs
   - `poloclub/diffusiondb` — Large curated AI image dataset
   - `dalle-mini/dalle-mini` — Older DALL-E generations

3. **Reddit / Social Media (with caution)**
   - r/midjourney, r/StableDiffusion, r/dalle — check subreddit rules
   - Only use images explicitly shared as AI-generated
   - Avoid copyrighted characters or identifiable people

4. **AI Image Galleries**
   - Lexica.art (has download features)
   - Civitai (Stable Diffusion model hub, has generated images)
   - Midjourney showcase (can screenshot)

### Human/Real Images (Legally and Safely)

1. **COCO 2017** — Your script targets 6,500 but manifest is empty
   - Fix and run `collect_coco_human_images.py`
   - 330k+ real photographs with captions

2. **Flickr30k / MSCOCO Captions**
   - Real photos with diverse content

3. **Unsplash** (free, CC0)
   - High-quality real photography
   - API available for bulk download

4. **Pexels / Pixabay** (free)
   - Stock-style real photos

5. **Your own photos**
   - Smartphone selfies, filtered photos, screenshots
   - The exact kind of content your users will upload

6. **Open Images Dataset (Google)**
   - 9M+ images with annotations
   - Very diverse

---

## Immediate Action Plan (Priority Order)

### Phase 1: Fix the Low-Hanging Fruit (Do This First)

1. **Extract frames from all 200 videos** and add to train/val image folders
   - This gives you ~1,500-2,000 "free" training images instantly
   - Use `extract_dataset_frames.py` or write a quick script

2. **Run your existing `collect_coco_human_images.py`**
   - It targets 6,500 real photos
   - Make sure the manifest is being written
   - These are all real, diverse photographs

3. **Run your existing `collect_realistic_flux_ai.py`**
   - Targets 619 train + 90 val FLUX images
   - Balanced across 11 genres and 3 styles
   - This is exactly the kind of modern AI data you need

### Phase 2: Expand Hard Cases (Do This Second)

4. **Massively expand overlay/graphics hard cases**
   - Current: ~505 total hard cases
   - Target: 2,000+ hard cases
   - Create variants for BOTH AI and human base images
   - Include more screenshot UI, social media elements

5. **Add more Blender CG / 3D render "human" images**
   - Big Buck Bunny is great but limited
   - Add frames from other CC-licensed animations
   - Sintel, Tears of Steel, Cosmos Laundromat (all Blender Foundation)
   - This teaches the model that "CG/render ≠ AI"

### Phase 3: Modern AI Generators (Do This Third)

6. **Collect from modern generators**
   - Generate your own with Midjourney, DALL-E 3, FLUX, Ideogram
   - Or find datasets on Hugging Face with recent generators
   - Focus on photorealistic styles (not anime/cartoon)

7. **Add real photos with heavy processing**
   - Filtered selfies, HDR, night mode, portrait mode
   - Heavily compressed JPEGs
   - Screenshots of real photos

### Phase 4: Video (Do This Fourth)

8. **Collect AI video and real video**
   - Sora, Runway Gen-3, Kling, Pika, Luma Dream Machine
   - Extract frames and add to training
   - Also collect deepfake videos for critical edge cases

---

## Training Recommendations for 95-100% Accuracy

Once you have the expanded dataset:

1. **Increase training epochs**: With 6,000+ per class, you can train longer without overfitting
   - Current: 6 epochs
   - Suggested: 8-12 epochs with early stopping (patience=3)

2. **Stronger augmentation**:
   ```python
   train_augment = Compose([
       RandomHorizontalFlip(p=0.5),
       RandomApply([ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05)], p=0.5),
       RandomApply([GaussianBlur(kernel_size=3, sigma=(0.1, 2.0))], p=0.2),
   ])
   ```

3. **Consider ensemble at inference**:
   - Run the image through multiple crops/flips
   - Average predictions for more robust scoring
   - This is how production detectors work

4. **Add a confidence threshold**:
   - If AI% and Human% are both close to 50%, flag as "Uncertain"
   - Better to say "I don't know" than be confidently wrong

5. **Periodic retraining**:
   - AI generators evolve every 3-6 months
   - Plan to retrain quarterly with new data
   - Keep a "challenge set" of images your model gets wrong

---

## Bottom Line

| Current State | What's Holding You Back |
|--------------|------------------------|
| ~79% from single source | Won't generalize to new AI styles |
| 200 videos ignored | Wasted training potential |
| No modern generators (FLUX, MJ v6, DALL-E 3) | Will fail on current social media AI |
| Limited real-world photo diversity | Will false-positive on filtered selfies, HDR, night shots |
| ~505 hard cases | Not enough to learn robust overlay detection |
| No CG/render diversity | May confuse 3D renders with AI |

**To reach 95-100% accuracy, you don't just need more images — you need the RIGHT images from diverse sources, generators, cameras, and processing styles.**

---

## Quick Wins (Do These Today)

1. ✅ Extract frames from your 200 videos
2. ✅ Run `collect_coco_human_images.py` (fix manifest writing if broken)
3. ✅ Run `collect_realistic_flux_ai.py` 
4. ✅ Generate 200 AI images yourself with free Midjourney/DALL-E trials
5. ✅ Take 100 filtered selfies and 100 unfiltered real photos with your phone

These five actions alone could add 2,000+ diverse training images.
