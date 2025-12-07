# 🚀 Panduan Deploy ke Railway

## File yang Dibutuhkan

```
financial_tracker_bot/
├── bot.py           ← Kode utama
├── requirements.txt ← Dependencies
├── Procfile         ← Instruksi run untuk Railway
├── runtime.txt      ← Versi Python
└── .gitignore       ← File yang diabaikan Git
```

## Step-by-Step Deploy

### Step 1: Buat Akun Railway
1. Buka https://railway.app
2. Klik "Login" → Login pakai GitHub (recommended)

### Step 2: Upload ke GitHub
Bot ini perlu di-upload ke GitHub dulu.

**Kalau belum punya repo:**
1. Buka https://github.com/new
2. Buat repo baru, nama bebas (misal: `expense-tracker-bot`)
3. **Jangan** centang "Add README" (biar kosong)
4. Klik "Create repository"

**Upload file via GitHub web:**
1. Di repo kosong, klik "uploading an existing file"
2. Drag & drop semua file:
   - bot.py
   - requirements.txt
   - Procfile
   - runtime.txt
   - .gitignore
3. Klik "Commit changes"

**Atau via terminal:**
```bash
cd financial_tracker_bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/expense-tracker-bot.git
git push -u origin main
```

### Step 3: Deploy di Railway
1. Buka https://railway.app/dashboard
2. Klik **"New Project"**
3. Pilih **"Deploy from GitHub repo"**
4. Pilih repo `expense-tracker-bot`
5. Tunggu Railway detect dan mulai build

### Step 4: Set Environment Variable (PENTING!)
1. Di dashboard Railway, klik service yang baru dibuat
2. Pergi ke tab **"Variables"**
3. Klik **"+ New Variable"**
4. Tambahkan:
   ```
   Name:  TELEGRAM_BOT_TOKEN
   Value: 8578037119:AAHSq4yc6rFPEQZ3sPWHXY7NBwG6PMxNiSk
   ```
5. Klik "Add"

### Step 5: Setup Volume (Untuk Database Persistent)
⚠️ **INI PENTING!** Tanpa volume, database akan hilang setiap deploy.

1. Di dashboard project, klik **"+ New"** → **"Volume"**
2. Isi:
   - Name: `data`
   - Mount Path: `/data`
3. Klik "Add"
4. Tambah variable lagi:
   ```
   Name:  DATA_DIR
   Value: /data
   ```

### Step 6: Pastikan Worker Jalan
1. Pergi ke tab **"Settings"**
2. Scroll ke **"Deploy"**
3. Pastikan **Start Command** kosong atau isi: `python bot.py`

### Step 7: Cek Logs
1. Pergi ke tab **"Deployments"**
2. Klik deployment terbaru
3. Lihat logs, harusnya muncul:
   ```
   🚀 Bot is running...
   ```

### Step 8: Test Bot!
1. Buka Telegram
2. Cari bot lo (nama yang lo buat di @BotFather)
3. Klik Start atau ketik /start
4. Coba chat: `bakso 15000`

---

## Troubleshooting

### Bot ga jalan / Error
- Cek logs di Railway
- Pastikan TELEGRAM_BOT_TOKEN sudah di-set
- Pastikan token benar (copy dari @BotFather)

### Database hilang setelah redeploy
- Pastikan Volume sudah di-setup
- Pastikan DATA_DIR=/data sudah di-set

### "Worker failed to start"
- Cek Procfile ada dan isinya: `worker: python bot.py`
- Cek requirements.txt ada

### Bot lambat respond
- Normal di free tier, ada cold start ~10-30 detik kalau idle lama

---

## Biaya

- **30 hari pertama**: Gratis ($5 credit)
- **Setelahnya**: ~$1/bulan untuk bot kecil seperti ini
- **Estimasi usage**: 0.5GB RAM × ~720 jam = ~$3-5/bulan
  (Tapi free credit $5 biasanya cukup)

---

## Update Bot

Kalau mau update kode:
1. Edit file di GitHub
2. Commit & push
3. Railway otomatis redeploy

Atau via Railway dashboard:
1. Connect GitHub
2. Enable auto-deploy

---

Happy tracking! 💰