# How to Push to GitHub

## Option 1: Using Personal Access Token (Recommended)

1. **Create a token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: `ERP Merge App`
   - Select scope: `repo` ✅
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Push your code:**
   ```bash
   cd /Users/huytran/ERP_Merge
   git push -u origin main
   ```
   - When asked for username: `huytquocxx`
   - When asked for password: **paste your token** (not your GitHub password)

## Option 2: Using GitHub Desktop

1. Download: https://desktop.github.com/
2. Sign in with GitHub
3. File → Add Local Repository
4. Select: `/Users/huytran/ERP_Merge`
5. Click "Publish repository"

## After Pushing

Once your code is on GitHub, deploy on Streamlit Cloud:
1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `huytquocxx/erp-merge-app`
5. Main file: `erp_merge_app.py`
6. Click "Deploy"

Done! 🎉

