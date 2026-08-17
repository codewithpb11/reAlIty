# Gumroad Upload Guide — reAlIty

Follow these steps in order. Everything you need is in the `gumroad/` folder.

---

## Step 0 — Build the release zip

Open PowerShell in the project folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File gumroad\package.ps1
```

This creates **`gumroad/reAlIty-v1.0.zip`** (~355 MB). That's the file you upload.

**Test it yourself before publishing:**
1. Copy the zip somewhere else (e.g. Desktop)
2. Unzip it
3. Follow `QUICKSTART.txt` inside
4. Confirm `python main.py` launches and detects an image

---

## Step 1 — Create a Gumroad account

1. Go to [https://gumroad.com](https://gumroad.com)
2. Sign up (email or Google)
3. Complete profile: add a display name and profile picture
4. Connect a payout method: **Settings → Payments** (PayPal or bank)

---

## Step 2 — Create the product

1. Click **Start selling** (or the **+** button) → **New product**
2. Choose **Digital product**

---

## Step 3 — Product details tab

### Name
```
reAlIty — AI or Not? Desktop Detector
```

### URL
```
reality-ai-detector
```
(Gumroad shows the full link: `yourname.gumroad.com/l/reality-ai-detector`)

### Price
- Set to **$15** (or your chosen price)
- Currency: **USD**
- Leave "Pay what you want" **off** for now

### Description
Open `gumroad/LISTING.txt` and copy everything under **FULL DESCRIPTION** into the description box.

Gumroad supports basic Markdown (`**bold**`, bullet lists).

---

## Step 4 — Content tab (upload the file)

1. Click **Content** in the left sidebar
2. Click **Add content** → **File**
3. Upload **`gumroad/reAlIty-v1.0.zip`**
4. Wait for upload to finish (~355 MB, may take several minutes)

Optional: add a second file — one of the screenshots from `docs/` — as a "preview" so buyers see what the app looks like before downloading.

---

## Step 5 — Cover image

Gumroad cover size: **1280 × 720 px** (16:9) recommended.

**Option A — Use the included cover:**
Upload `gumroad/cover.png` (generated for this release).

**Option B — Use your screenshot:**
1. Open `docs/screenshot-ai.png` in any image editor
2. Crop/resize to 1280×720
3. Optionally add text: "reAlIty" + "AI or Not? Find out." + "Runs 100% offline"

Upload under **Cover** on the product page.

---

## Step 6 — Settings tab

| Setting | Value |
|---------|-------|
| **Customizable receipt** | On — paste the email message from `LISTING.txt` |
| **Max purchase count** | Off (unlimited) |
| **Sales tax** | Let Gumroad handle it (recommended) |
| **Discover** | On — helps people find you in Gumroad search |
| **Tags** | Add tags from `LISTING.txt` |

### Refund policy
In the description or a separate note, add:
> 7-day refund if the app doesn't run on your system. Email me via your Gumroad receipt.

---

## Step 7 — Thumbnail & gallery (optional but recommended)

Add 2–3 images to the product gallery:
1. `docs/screenshot-ai.png` — AI detection result
2. `docs/screenshot-human.png` — human detection result
3. (Optional) a simple graphic showing supported formats

These appear on your product page and improve conversion.

---

## Step 8 — Preview / Publish

1. Click **Preview** to see the live product page
2. Read through description, price, and cover
3. Click **Publish**

Your link will be:
```
https://YOUR_USERNAME.gumroad.com/l/reality-ai-detector
```

---

## Step 9 — Test purchase (important)

1. Gumroad lets you buy your own product at a discount
2. Go to product → **Share** → use "Test mode" or buy with a 100% off coupon
3. Confirm:
   - Email arrives with download link
   - Zip downloads and unzips correctly
   - QUICKSTART.txt is inside
   - Model files are present in `reality-finetuned/final/`

Create a test coupon: **Product → Offer codes → New offer code → 100% off**

---

## Step 10 — Share it

Once tested, share your link:

- **Twitter/X:** "Built a desktop app that detects AI vs real images/videos — runs fully offline. [link]"
- **Reddit:** r/SideProject, r/InternetIsBeautiful (check sub rules first)
- **Product Hunt:** Submit as a tool (good for launch day)
- **Hacker News:** Show HN post with honest limitations disclaimer

---

## Checklist before going live

- [ ] Zip built with `package.ps1`
- [ ] Tested install on a clean machine (or fresh folder)
- [ ] Cover image uploaded (1280×720)
- [ ] Description pasted from `LISTING.txt`
- [ ] Price set ($15 recommended)
- [ ] Download file uploaded (`reAlIty-v1.0.zip`)
- [ ] Custom receipt email set
- [ ] Test purchase completed with 100% off coupon
- [ ] Payout method connected in Gumroad settings

---

## Updating later (v1.1, etc.)

1. Edit `gumroad/package.ps1` → change `$Version` and output filename
2. Re-run the script
3. In Gumroad: **Content → Replace file** with the new zip
4. Email existing buyers: Gumroad → **Audience** → email purchasers about the update

---

## File reference

| File | Purpose |
|------|---------|
| `gumroad/reAlIty-v1.0.zip` | Upload this to Gumroad |
| `gumroad/LISTING.txt` | Copy-paste product description |
| `gumroad/QUICKSTART.txt` | Included inside the zip for buyers |
| `gumroad/CREDITS.txt` | Included inside the zip |
| `gumroad/cover.png` | Product cover image |
| `docs/screenshot-*.png` | Gallery images |

---

## Common buyer support questions

**"pip install is slow"**
→ Normal. PyTorch is ~2 GB. Tell them to wait 10–15 min.

**"python not found"**
→ They didn't check "Add Python to PATH". Reinstall Python.

**"Model not found"**
→ They didn't unzip the full folder, or moved files around. `reality-finetuned/final/` must sit next to `main.py`.

**"Can I get a refund?"**
→ Honor 7-day policy if it genuinely won't run. Ask for OS + error message first — most issues are fixable in one reply.
