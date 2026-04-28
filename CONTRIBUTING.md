# 🚀 Project Contribution Guide

Hello Team! To keep our code clean and our branches (`main`, `qa`, and `uat`) stable, please follow this workflow for all features and bug fixes.

---

## 🛠 1. Initial Setup
If you haven't cloned the repository yet:
```bash
git clone <YOUR_REPO_URL>
cd <REPO_NAME>

```

---

## 🌿 2. Branching Strategy

**Rule:** Never push directly to `main`, `qa`, or `uat`.

1. **Update your local environment:**
```bash
git checkout main
git pull origin main

```


2. **Create a new feature branch:**
```bash
# Use a descriptive name like 'login-page' or 'api-fix'
git checkout -b feature/your-feature-name

```



---

## 💾 3. Committing Your Work

As you work, save your changes locally:

```bash
# Check your changes
git status

# Stage all changes
git add .

# Commit with a clear message
git commit -m "feat: added login validation logic"

```

---

## 📤 4. Pushing and Pull Requests

Once your task is complete, send it to GitHub:

1. **Push your branch:**
```bash
git push origin feature/your-feature-name

```


2. **Open a Pull Request (PR):**
* Go to the GitHub repository in your browser.
* Click the **"Compare & pull request"** button.
* **Base Branch:** Select `qa` (for initial testing).
* **Compare Branch:** Select your `feature/your-feature-name`.
* Add a short description of what you did.


3. **Notify the Team Lead:** The Lead will review your code and merge it into the project.

---

## 💡 Quick Command Reference

| Action | Command |
| --- | --- |
| **Switch to a branch** | `git checkout <branch-name>` |
| **Get latest updates** | `git pull origin main` |
| **Save changes** | `git add .` + `git commit -m "msg"` |
| **Upload your branch** | `git push origin <branch-name>` |
| **Check current branch** | `git branch` |

---

**Note:** If you encounter merge conflicts, please reach out to the Team Lead before forcing any pushes!

```
