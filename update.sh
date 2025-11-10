#!/bin/bash
# Quick update script for ERP Merge App
# Usage: ./update.sh "Your commit message"

echo "🚀 Updating ERP Merge App..."

# Check if commit message provided
if [ -z "$1" ]; then
    echo "❌ Please provide a commit message"
    echo "Usage: ./update.sh 'Your commit message'"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "erp_merge_app.py" ]; then
    echo "❌ Error: erp_merge_app.py not found!"
    echo "Please run this script from the ERP_Merge directory"
    exit 1
fi

# Show current status
echo ""
echo "📋 Current changes:"
git status --short

# Ask for confirmation
echo ""
read -p "Continue with commit and push? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Add all changes
echo ""
echo "📦 Adding changes..."
git add .

# Commit
echo "💾 Committing changes..."
git commit -m "$1"

# Push
echo "⬆️  Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Done! Streamlit Cloud will auto-deploy in 1-2 minutes"
echo "🌐 Check your app at: https://share.streamlit.io/"

