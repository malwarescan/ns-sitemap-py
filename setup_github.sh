#!/bin/bash

echo "🚀 Sitemap Priority System - GitHub Setup"
echo "=========================================="

# Check if git is configured
if ! git config --global user.name > /dev/null 2>&1; then
    echo "❌ Git not configured. Please set up git first:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

echo "✅ Git is configured"
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub username is required"
    exit 1
fi

# Repository name
REPO_NAME="sitemap-priority-system"
REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

echo ""
echo "📋 Repository Details:"
echo "   Username: $GITHUB_USERNAME"
echo "   Repository: $REPO_NAME"
echo "   URL: $REPO_URL"
echo ""

# Instructions for creating repository
echo "📝 Next Steps:"
echo "1. Go to https://github.com/new"
echo "2. Repository name: $REPO_NAME"
echo "3. Description: Data-driven sitemap generation system for SEO optimization"
echo "4. Make it Public or Private (your choice)"
echo "5. DO NOT initialize with README (we already have one)"
echo "6. DO NOT add .gitignore (we already have one)"
echo "7. Click 'Create repository'"
echo ""

read -p "Press Enter when you've created the repository..."

# Set up git remote
echo "🔗 Setting up git remote..."
git remote add origin $REPO_URL

# Push to GitHub
echo "📤 Pushing code to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Success! Your code is now on GitHub at:"
echo "   $REPO_URL"
echo ""
echo "🎉 Next step: Deploy to Vercel!"
echo "   Go to https://vercel.com/new and import your repository" 