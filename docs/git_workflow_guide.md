# Git & GitHub Workflow Evidence Guide (CSE 3206)

To satisfy **Section 4 (Configuration Management)** of the assignment rubric, execute the following commands after creating a new empty GitHub repository:

```bash
git init -b main
git add .
git commit -m "chore: initialize project structure, CI workflow, and core domain models"
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

### 1. Feature Branch + Accepted Pull Request
```bash
git checkout -b feat/matching-strategies
git commit --allow-empty -m "feat(matching): refine composite weighted strategy scoring"
git push -u origin feat/matching-strategies
```
Open a Pull Request on GitHub (`feat/matching-strategies` -> `main`), add a review comment approving the strategy separation, and **Merge** it.

### 2. Feature Branch + Revised/Rejected Pull Request
```bash
git checkout main
git pull
git checkout -b feat/direct-notification-coupling
git commit --allow-empty -m "feat(notify): initial direct call prototype"
git push -u origin feat/direct-notification-coupling
```
Open a PR on GitHub, leave a review comment noting why direct coupling violates SRP/extensibility, and **Close (Reject)** the PR in favor of the Observer implementation.

### 3. Intentional Merge Conflict & Resolution Note
1. Create two branches from `main`: `feat/threshold-strict` and `feat/threshold-relaxed`.
2. In both branches, edit `min_threshold=0.45` in `src/lost_found/cli.py` to two different values (`0.60` vs `0.35`), commit, and push.
3. Merge `feat/threshold-strict` into `main` first.
4. When merging `feat/threshold-relaxed` into `main`, Git reports a conflict in `src/lost_found/cli.py`.
5. Resolve the conflict by keeping `min_threshold=0.45` (balanced precision/recall), run `pytest`, and commit:
   ```bash
   git add src/lost_found/cli.py
   git commit -m "fix(merge): resolve min_threshold conflict in cli.py"
   ```
6. Take screenshots of the PR history, review comments, merge conflict diff, and GitHub Actions CI green checks for `docs/Project_Report.tex`.
