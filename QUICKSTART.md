# reAlIty — Quick Start (Play Store Path)

## What You Have Now

| Component | Location | Status |
|-----------|----------|--------|
| Web backend (FastAPI) | `webapp/` | Works locally |
| Mobile app (Expo React Native) | `mobile-app/` | Ready to build |
| Deployment configs | `deploy/` | Ready |
| Model upload script | `deploy/setup-huggingface.ps1` | Ready |

---

## Step-by-Step to Play Store

### 1. Upload Model to Hugging Face (5 min)

```powershell
# In PowerShell, run from project root:
.\deploy\setup-huggingface.ps1
```

This uploads your 355MB model to Hugging Face Hub (free) so it doesn't need to be in git.

### 2. Update detector.py (1 min)

After the script runs, `detector.py` line 24 should read:
```python
MODEL_ID = "your-username/reality-detector-model"
```

If not, change it manually.

### 3. Push to GitHub (1 min)

```bash
git add .
git commit -m "Add mobile app and deployment configs"
git push
```

### 4. Deploy Backend to Hugging Face Spaces (2 min)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Name: `reality-detector`
4. SDK: **Docker**
5. Link to your GitHub repo
6. The Space will auto-build and deploy

Your API URL: `https://your-username-reality-detector.hf.space`

### 5. Update Mobile App API URL (1 min)

In `mobile-app/App.js`, change line 18:
```javascript
const API_URL = 'https://your-username-reality-detector.hf.space';
```

### 6. Install & Build APK (10 min)

```bash
cd mobile-app
npm install
npx expo install

# Create free Expo account at expo.dev, then:
npx eas-cli login
npx eas-cli build --platform android --profile preview
```

This gives you an `.apk` to test on your phone.

### 7. Add App Icons (10 min)

Create these images (black & white theme):
- `mobile-app/assets/icon.png` (1024×1024)
- `mobile-app/assets/adaptive-icon.png` (1024×1024)
- `mobile-app/assets/splash.png` (1242×2436)

Use [appicon.co](https://appicon.co) to generate all sizes from one image.

### 8. Set Up AdMob (15 min)

1. Go to [admob.google.com](https://admob.google.com)
2. Create account, add app "reAlIty", get App ID
3. In `mobile-app/app.json`, replace the placeholder App ID with your real one
4. In `mobile-app/app.json`, add your banner ad unit ID

### 9. Build Production AAB (10 min)

```bash
npx eas-cli build --platform android --profile production
```

This produces an `.aab` file for the Play Store.

### 10. Publish to Play Store (30 min + 1-3 days review)

1. Go to [play.google.com/console](https://play.google.com/console)
2. Pay $25 one-time fee
3. Create app listing:
   - Name: **reAlIty**
   - Short description: "Detect AI-generated images instantly"
   - Screenshots (take from your phone)
   - Feature graphic (1024×500)
4. Upload the `.aab` file from Step 9
5. Submit for review

---

## File Checklist

- [ ] `detector.py` — `MODEL_ID` points to HF Hub
- [ ] `mobile-app/App.js` — `API_URL` is your deployed backend
- [ ] `mobile-app/app.json` — Real AdMob App ID inserted
- [ ] `mobile-app/assets/icon.png` — App icon created
- [ ] `mobile-app/assets/splash.png` — Splash screen created

---

## Revenue Estimate

| Daily Users | Monthly Ad Revenue |
|------------|-------------------|
| 100 | $10–50 |
| 1,000 | $100–500 |
| 10,000 | $1,000–5,000 |

Add a $3.99 "Remove Ads" in-app purchase to double revenue.
