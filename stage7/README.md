# 📊 Twitch Viewer Analytics Dashboard

Personal Twitch viewing behavior dashboard — 8 years of data, 12 interactive charts, built with Streamlit + Plotly.

---

## File structure

```
twitch_dashboard/
├── app.py                        ← main Streamlit app
├── charts.py                     ← all 12 chart functions
├── requirements.txt
├── .streamlit/
│   └── config.toml               ← dark theme config
├── README.md
└── data/
    ├── df_engineered.csv         ← required
    ├── df_daily.csv              ← required
    └── df_video_play_clean.csv   ← optional (V8 + V9)
```

---

## 🖥️ Run locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Put your data files in the `data/` folder
```bash
mkdir data
# Copy your CSV files:
#   df_engineered.csv
#   df_daily.csv
#   df_video_play_clean.csv  (optional)
```

### 3. Run the app
```bash
streamlit run app.py
```

Opens automatically at **http://localhost:8501**

---

## 🌐 Deploy to Streamlit Cloud (share with anyone)

Streamlit Cloud gives you a **free permanent public URL** like `yourname-twitch.streamlit.app`.

### Step 1 — Push to GitHub

```bash
# In your project folder:
git init
git add app.py charts.py requirements.txt .streamlit/config.toml README.md
git commit -m "Twitch analytics dashboard"
```

Create a new repo on [github.com](https://github.com) then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/twitch-analytics.git
git push -u origin main
```

> ⚠️ **Do NOT add the `data/` folder** if you want to keep your viewing history private.

### Step 2 — Handle data files (two options)

**Option A — Include data in the repo (simplest)**
```bash
git add data/
git commit -m "Add data files"
git push
```
Fine for personal Twitch data — it's not sensitive.

**Option B — Keep data private using Streamlit Secrets**
Store your data in a private location and load it via environment variables.
For most personal projects, Option A is fine.

### Step 3 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo, branch `main`, and file `app.py`
5. Click **Deploy**

Your app will be live at `https://YOUR_USERNAME-twitch-analytics-app-XXXX.streamlit.app`

Share the URL with anyone — they can view it on any device, no setup needed.

---

## 📊 Charts included

| # | Chart | Tab |
|---|---|---|
| V1  | Viewer Lifecycle Bubble         | Overview   |
| V2  | Rolling Engagement Timeline     | Overview   |
| V3  | Channel Loyalty Heatmap         | Loyalty    |
| V4  | Channel Portfolio Sunburst      | Loyalty    |
| V5  | LoL Esports Calendar            | Content    |
| V6  | Game Genre Treemap              | Content    |
| V7  | Platform Divergence             | Platform   |
| V8  | Hour × Day Heatmap              | Platform   |
| V9  | Stream Discovery Funnel         | Discovery  |
| V10 | Binge Calendar Heatmap          | Binge      |
| V11 | Year-over-Year Change           | Overview   |
| V12 | Monthly Engagement Heatmap      | Content    |

---

## Built with
- [Streamlit](https://streamlit.io)
- [Plotly](https://plotly.com/python)
- [Pandas](https://pandas.pydata.org)
