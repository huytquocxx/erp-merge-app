# 🔧 Development & Update Workflow

## How to Make Changes and Update Your Deployed App

### Step 1: Make Changes Locally

1. **Edit your files:**
   ```bash
   cd /Users/huytran/ERP_Merge
   # Edit erp_merge_app.py or any other files
   ```

2. **Test locally before deploying:**
   ```bash
   streamlit run erp_merge_app.py
   ```
   - This runs on `http://localhost:8501`
   - Test all your changes thoroughly
   - Fix any bugs before pushing

### Step 2: Commit Your Changes

```bash
cd /Users/huytran/ERP_Merge

# See what changed
git status

# Add all changes
git add .

# Commit with a descriptive message
git commit -m "Fix: Updated merge logic for better handling of empty values"
# or
git commit -m "Feature: Added new validation step"
# or
git commit -m "Debug: Fixed Google Sheets URL conversion"
```

### Step 3: Push to GitHub

```bash
git push origin main
```

**Note:** You'll need to authenticate again. You can either:
- Use your token again (or create a new one)
- Set up SSH keys for easier authentication (see below)

### Step 4: Streamlit Cloud Auto-Deploys! 🎉

**Streamlit Cloud automatically redeploys when you push to GitHub!**

- No need to manually redeploy
- Usually takes 1-2 minutes
- You'll see the update in your Streamlit Cloud dashboard

### Step 5: Verify Deployment

1. Go to: https://share.streamlit.io/
2. Check your app status
3. Click on your app to see the live version
4. Test the changes

---

## 🔐 Easier Authentication (Optional but Recommended)

### Option A: Use GitHub Credential Helper (Saves Token)

```bash
# Configure Git to remember your credentials
git config --global credential.helper osxkeychain

# Now when you push, it will save your token
git push origin main
# Enter username: huytquocxx
# Enter password: [your token]
# It will save it for future pushes!
```

### Option B: Set Up SSH Keys (Most Secure)

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Press Enter for no passphrase (or set one)
   ```

2. **Add SSH key to GitHub:**
   ```bash
   # Copy your public key
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   
   Then:
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste your key
   - Click "Add SSH key"

3. **Update remote URL to use SSH:**
   ```bash
   cd /Users/huytran/ERP_Merge
   git remote set-url origin git@github.com:huytquocxx/erp-merge-app.git
   ```

4. **Now you can push without tokens:**
   ```bash
   git push origin main
   ```

---

## 🐛 Debugging Tips

### Local Debugging

1. **Run with debug mode:**
   ```bash
   streamlit run erp_merge_app.py --logger.level=debug
   ```

2. **Check logs:**
   - Look at terminal output for errors
   - Check browser console (F12) for frontend errors

3. **Add print statements:**
   ```python
   # In your code
   st.write("Debug: Variable value =", variable)
   # or
   print("Debug: Processing row", row_index)
   ```

4. **Use Streamlit's built-in debugging:**
   ```python
   import streamlit as st
   
   # Show debug info
   with st.expander("🔍 Debug Info"):
       st.write("Current state:", st.session_state)
       st.write("Data shape:", df.shape)
   ```

### Production Debugging

1. **Check Streamlit Cloud logs:**
   - Go to: https://share.streamlit.io/
   - Click on your app
   - Click "Manage app" → "Logs"
   - See real-time error messages

2. **Add error handling:**
   ```python
   try:
       # Your code
   except Exception as e:
       st.error(f"Error: {str(e)}")
       st.exception(e)  # Shows full traceback
   ```

---

## 📋 Typical Development Cycle

```bash
# 1. Make changes to code
# 2. Test locally
streamlit run erp_merge_app.py

# 3. If it works, commit
git add .
git commit -m "Description of changes"

# 4. Push to GitHub
git push origin main

# 5. Wait 1-2 minutes for auto-deployment
# 6. Test on live app
```

---

## 💡 Best Practices

1. **Always test locally first** - Don't push broken code
2. **Write descriptive commit messages** - Helps track changes
3. **Push frequently** - Small commits are better than big ones
4. **Check Streamlit Cloud logs** if something breaks
5. **Use version control** - Git helps you revert if needed

---

## 🔄 Reverting Changes (If Something Breaks)

```bash
# See commit history
git log

# Revert to previous commit
git revert HEAD
git push origin main

# Or go back to specific commit
git reset --hard <commit-hash>
git push origin main --force  # ⚠️ Use carefully!
```

---

## 📚 Quick Reference

| Task | Command |
|------|---------|
| Test locally | `streamlit run erp_merge_app.py` |
| Check changes | `git status` |
| Commit changes | `git add . && git commit -m "message"` |
| Push to GitHub | `git push origin main` |
| View logs | Streamlit Cloud dashboard → Manage app → Logs |

