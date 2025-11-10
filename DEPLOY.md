# 🚀 Quick Deployment Guide - Streamlit Cloud (FREE)

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `erp-merge-app` (or any name you like)
3. Make it **Public** (required for free Streamlit Cloud)
4. **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

## Step 2: Push Your Code to GitHub

After creating the repo, GitHub will show you commands. Use these:

```bash
cd /Users/huytran/ERP_Merge
git remote add origin https://github.com/YOUR_USERNAME/erp-merge-app.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

## Step 3: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click **"Sign in"** (use your GitHub account)
3. Click **"New app"**
4. Fill in:
   - **Repository:** Select `YOUR_USERNAME/erp-merge-app`
   - **Branch:** `main`
   - **Main file path:** `erp_merge_app.py`
5. Click **"Deploy"**

⏳ Wait 1-2 minutes for deployment...

## Step 4: Your App is Live! 🎉

Your app will be available at:
`https://YOUR-APP-NAME.streamlit.app`

---

## Need Help?

If you get stuck, just let me know and I can help you with any step!

