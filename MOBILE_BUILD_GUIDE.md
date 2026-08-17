# reAlIty Mobile — Build & Publish Guide

Complete guide to deploy the backend, build the Android app, and publish to the Play Store.

---

## Phase 1: Deploy the Backend

Your 355MB model is too large for GitHub. You have two options:

### Option A: Hugging Face Spaces (Recommended — Free)

1. **Create a Hugging Face account** at [huggingface.co](https://huggingface.co/join)

2. **Install the Hugging Face CLI:**
   ```bash
   pip install huggingface-hub
   huggingface-cli login
   ```

3. **Upload your model to Hugging Face Hub:**
   ```bash
   # Create a model repo (replace 'your-username' with your HF username)
   huggingface-cli repo create reality-detector-model --type model

   # Clone it and copy your model files
   git clone https://huggingface.co/your-username/reality-detector-model
   cd reality-detector-model
   cp -r ../reality-finetuned/final/* .
   git lfs track "*.safetensors"
   git add .
   git commit -m "Upload model"
   git push
   ```

4. **Update detector.py** to use the HF model ID:
   ```python
   MODEL_ID = "your-username/reality-detector-model"  # instead of local path
   ```

5. **Create a Hugging Face Space:**
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Name it `reality-detector`
   - Select "Docker" as the SDK
   - Push your code to the Space's git repo

6. **Your API will be live at:**
   ```
   https://your-username-reality-detector.hf.space
   ```

### Option B: Render (Paid for this model size)

Render's free tier doesn't have enough disk/RAM for a 355MB PyTorch model. You'd need the **Starter plan ($7/month)**.

1. Push your code to GitHub
2. Connect the repo on [render.com](https://render.com)
3. Use `deploy/Dockerfile` as the build context
4. Upgrade to Starter plan (2GB RAM minimum needed)

---

## Phase 2: Configure the Mobile App

### 1. Install dependencies

```bash
cd mobile-app
npm install
# or
npx expo install
```

### 2. Update the API URL

Open `mobile-app/App.js` and change this line:

```javascript
const API_URL = 'https://your-username-reality-detector.hf.space';
```

Replace with your actual deployed backend URL.

### 3. Add app icons

Create these images and place them in `mobile-app/assets/`:

| File | Size | Purpose |
|------|------|---------|
| `icon.png` | 1024x1024 | App icon |
| `adaptive-icon.png` | 1024x1024 | Android adaptive icon (foreground) |
| `splash.png` | 1242x2436 | Splash screen |

Use the same black & white theme. The background color is set to `#0d0d0d` in `app.json`.

**Free icon generators:**
- [appicon.co](https://appicon.co/) — generates all sizes from one image
- [Canva](https://canva.com) — design the icon

---

## Phase 3: Set Up AdMob (Monetization)

### 1. Create AdMob Account

- Go to [admob.google.com](https://admob.google.com)
- Sign in with your Google account
- Complete the account setup (requires tax info for payouts)

### 2. Register Your App

- In AdMob, click **Apps → Add App**
- Choose "Android"
- Enter your app name: **reAlIty**
- Package name: `com.yourcompany.reality` (must match `app.json`)

### 3. Create Ad Units

- Go to **Ad Units → Add Ad Unit**
- Choose **Banner** (best for this app — sits at bottom)
- Name it: "reality-banner-ad"
- Copy the **Ad Unit ID** (looks like `ca-app-pub-1234567890123456/1234567890`)

### 4. Update app.json with your real IDs

```json
"plugins": [
  [
    "react-native-google-mobile-ads",
    {
      "androidAppId": "ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX",
      "iosAppId": "ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX"
    }
  ]
]
```

> **Important:** Use your real App ID from AdMob, not the placeholder.

---

## Phase 4: Build the APK (Android App)

### 1. Install EAS CLI

```bash
npm install -g eas-cli
```

### 2. Log in to Expo

```bash
eas login
# Enter your Expo account credentials (create free account at expo.dev)
```

### 3. Configure the project

```bash
cd mobile-app
eas init
# Follow prompts to link to your Expo project
```

### 4. Build the APK (for testing)

```bash
eas build --platform android --profile preview
```

This creates an `.apk` file you can install directly on any Android phone.

### 5. Build the AAB (for Play Store)

```bash
eas build --platform android --profile production
```

This creates an `.aab` (Android App Bundle) — the format Google Play requires.

> EAS builds in the cloud (free tier: 30 build credits/month). An Android build uses ~5 credits.

---

## Phase 5: Publish to Play Store

### 1. Create Google Play Developer Account

- Go to [play.google.com/console](https://play.google.com/console)
- Pay the **$25 one-time fee**
- Complete account verification (ID, tax info)

### 2. Create App Listing

- Click **Create app**
- App name: **reAlIty**
- Default language: English
- App or game: App
- Free or paid: Free (monetize via ads)

### 3. Fill Store Listing

Required assets:
- **Short description** (80 chars max): "Detect AI-generated images instantly"
- **Full description**: Explain what the app does
- **App icon**: 512x512 PNG
- **Feature graphic**: 1024x500 PNG
- **Screenshots**: Upload 2-8 phone screenshots (use the app on your phone, screenshot the results)
- **Content rating**: Fill the questionnaire (your app is suitable for everyone)

### 4. Upload AAB

- Go to **Production → Create new release**
- Upload your `.aab` file from the EAS build
- Review and roll out

### 5. Wait for Review

Google Play review takes **1-3 days** for new apps.

---

## Phase 6: Monetization Strategy

### AdMob Revenue Estimates

| Daily Active Users | Estimated Monthly Revenue |
|-------------------|--------------------------|
| 100 | $10-50 |
| 1,000 | $100-500 |
| 10,000 | $1,000-5,000 |

**Tips to maximize revenue:**
- Add an interstitial ad (full-screen) after every 3-5 analyses
- Offer a "Pro" in-app purchase to remove ads ($2.99-4.99)
- Use rewarded video ads: "Watch an ad to analyze unlimited images today"

---

## Summary Checklist

- [ ] Upload model to Hugging Face Hub
- [ ] Update `MODEL_ID` in `detector.py`
- [ ] Deploy backend to Hugging Face Spaces
- [ ] Update `API_URL` in `mobile-app/App.js`
- [ ] Create app icons (1024x1024)
- [ ] Set up AdMob account & get App ID
- [ ] Update `app.json` with real AdMob IDs
- [ ] Build APK with `eas build --profile preview`
- [ ] Test APK on your phone
- [ ] Build AAB with `eas build --profile production`
- [ ] Pay $25 Google Play Developer fee
- [ ] Create Play Store listing
- [ ] Upload AAB and publish

---

## Troubleshooting

**"Build failed on EAS"**
- Make sure `app.json` has valid package name format: `com.yourcompany.reality`
- Ensure icon files exist in `assets/` folder

**"App can't connect to API"**
- Check that `API_URL` in `App.js` uses `https://` (not `http://`)
- Verify your Hugging Face Space is "Running" (not "Building" or "Sleeping")

**"AdMob ads not showing"**
- New AdMob accounts take 24-48 hours to activate
- Use test ad IDs during development:
  - Banner: `ca-app-pub-3940256099942544/6300978111`
  - App ID: `ca-app-pub-3940256099942544~3347511713`
