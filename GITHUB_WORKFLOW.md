# GitHub Workflow Guide - Step by Step

This guide provides step-by-step instructions to fork the repository, push your changes, and create a Pull Request.

## 📋 Prerequisites

- GitHub account
- Git installed on your machine (already done ✅)
- Project location: `/Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService`

---

## 🍴 Step 1: Fork the Original Repository

### Via GitHub Website:

1. **Open your browser** and go to:
   ```
   https://github.com/KevinEstebanQ/FinanceTrackerService
   ```

2. **Click the "Fork" button** in the top right corner
   - It looks like: 🍴 Fork

3. **Select your account** as the destination
   - GitHub will create a copy at: `https://github.com/YOUR_USERNAME/FinanceTrackerService`

4. **Wait for the fork** to complete (usually takes a few seconds)

✅ **You now have your own copy of the repository!**

---

## 🔗 Step 2: Add Your Fork as a Remote

Open Terminal and run:

```bash
cd /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService

# Add your fork as a remote (replace YOUR_USERNAME with your GitHub username)
git remote add myfork https://github.com/YOUR_USERNAME/FinanceTrackerService.git

# Verify remotes
git remote -v
```

**Expected output:**
```
myfork  https://github.com/YOUR_USERNAME/FinanceTrackerService.git (fetch)
myfork  https://github.com/YOUR_USERNAME/FinanceTrackerService.git (push)
origin  https://github.com/KevinEstebanQ/FinanceTrackerService.git (fetch)
origin  https://github.com/KevinEstebanQ/FinanceTrackerService.git (push)
```

---

## 🚀 Step 3: Push Your Feature Branch

```bash
cd /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService

# Verify you're on the feature branch
git branch

# Push to your fork
git push myfork feature/complete-roadmap-implementation
```

**Expected output:**
```
Counting objects: XX, done.
Writing objects: 100% (XX/XX), XX KiB | XX MiB/s, done.
Total XX (delta XX), reused XX (delta XX)
To https://github.com/YOUR_USERNAME/FinanceTrackerService.git
 * [new branch]      feature/complete-roadmap-implementation -> feature/complete-roadmap-implementation
```

✅ **Your feature branch is now on GitHub!**

---

## 📝 Step 4: Create Pull Request

### Via GitHub Website:

1. **Go to your fork** on GitHub:
   ```
   https://github.com/YOUR_USERNAME/FinanceTrackerService
   ```

2. **You'll see a yellow banner** saying:
   ```
   feature/complete-roadmap-implementation had recent pushes
   [Compare & pull request] button
   ```
   Click the **"Compare & pull request"** button

   **OR**

   - Click the **"Pull requests"** tab
   - Click the green **"New pull request"** button
   - Click **"compare across forks"**
   - Set:
     - Base repository: `KevinEstebanQ/FinanceTrackerService`
     - Base branch: `main`
     - Head repository: `YOUR_USERNAME/FinanceTrackerService`
     - Compare branch: `feature/complete-roadmap-implementation`

3. **Fill in the PR details:**

   **Title:**
   ```
   feat: Complete roadmap implementation with CRUD, Docker, tests, CI/CD, and RBAC
   ```

   **Description:**
   Copy the entire content from `PR_TEMPLATE.md` file:
   ```bash
   # In terminal, get the content:
   cat /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService/PR_TEMPLATE.md
   ```
   Then paste it into the description box on GitHub

4. **Review the changes:**
   - Scroll down to see the "Files changed" tab
   - You should see 22 files changed with ~1,400 additions

5. **Create the Pull Request:**
   - Click the green **"Create pull request"** button

✅ **Pull Request created!**

---

## 📊 Step 5: What Happens Next

After creating the PR:

1. **GitHub Actions will automatically run:**
   - Test job (runs all 23 tests)
   - Lint job (checks code formatting)
   - Docker job (builds and tests container)

2. **You'll see status checks** on the PR:
   - ✅ Test / ✅ Lint / ✅ Docker = All passing
   - ❌ Any failures = Check the logs and fix

3. **Wait for review:**
   - The repository owner (KevinEstebanQ) will review your PR
   - They may request changes or approve it
   - You can make additional commits if needed

---

## 🔧 Making Changes After PR

If you need to make changes after creating the PR:

```bash
cd /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService

# Make your changes to files
# Then commit and push:

git add .
git commit -m "fix: Address review comments"
git push myfork feature/complete-roadmap-implementation
```

The PR will automatically update with your new commits!

---

## 📱 Alternative: Using GitHub CLI (Optional)

If you have GitHub CLI installed (`gh`):

```bash
cd /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService

# Login to GitHub (if not already)
gh auth login

# Create fork
gh repo fork KevinEstebanQ/FinanceTrackerService --clone=false

# Push branch
git push origin feature/complete-roadmap-implementation

# Create PR with template
gh pr create --base main \
  --title "feat: Complete roadmap implementation with CRUD, Docker, tests, CI/CD, and RBAC" \
  --body-file PR_TEMPLATE.md
```

---

## ✅ Verification Checklist

Before creating the PR, verify:

- [ ] Fork created on GitHub
- [ ] Remote added locally (`git remote -v` shows myfork)
- [ ] Branch pushed successfully
- [ ] PR created with proper title and description
- [ ] Files changed: ~22 files
- [ ] Additions: ~1,400 lines
- [ ] CI checks are running or passed

---

## 🆘 Troubleshooting

### Issue: "Permission denied (publickey)"

**Solution:** Set up SSH key or use HTTPS with token

```bash
# Use HTTPS instead
git remote set-url myfork https://github.com/YOUR_USERNAME/FinanceTrackerService.git
```

### Issue: "Updates were rejected"

**Solution:** Your local branch might be behind

```bash
git pull origin main
git push myfork feature/complete-roadmap-implementation --force
```

### Issue: "Fatal: not a git repository"

**Solution:** Make sure you're in the right directory

```bash
cd /Users/ritesh/Downloads/submission_folder/fork/FinanceTrackerService
```

---

## 📚 Useful Commands

```bash
# Check current branch
git branch

# View commit log
git log --oneline -5

# Check remote repositories
git remote -v

# View changes
git status

# View what will be pushed
git log origin/main..feature/complete-roadmap-implementation --oneline
```

---

## 🎓 Summary

**3 Simple Steps:**

1. **Fork** on GitHub website → Click 🍴 Fork button
2. **Push** your branch → `git push myfork feature/complete-roadmap-implementation`
3. **Create PR** on GitHub → Use PR_TEMPLATE.md as description

That's it! Your contribution is now ready for review! 🎉

---

**Need Help?**
- GitHub Docs: https://docs.github.com/en/pull-requests
- Git Documentation: https://git-scm.com/doc
