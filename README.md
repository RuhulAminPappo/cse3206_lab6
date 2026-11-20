# Campus Lost & Found with Smart Matching

A modular Python application developed for **CSE 3206 - Software Engineering Sessional (22 Series)** at **Rajshahi University of Engineering & Technology (RUET)**.

---

## Features & Architecture (5 Core Modules)

1. **Users Module (`src/lost_found/modules/users.py`)**
   - Campus member registration and lookup (students, faculty, staff).
2. **Items Module (`src/lost_found/modules/items.py`)**
   - Post and manage `LOST` and `FOUND` item reports with lifecycle states (`OPEN` -> `MATCHED` -> `CLAIMED` -> `CLOSED`).
3. **Matching Module (`src/lost_found/modules/matching.py`)**
   - Smart candidate scoring and ranking between lost and found reports using interchangeable matching algorithms.
4. **Claims Module (`src/lost_found/modules/claims.py`)**
   - Multi-step claim submission and verification pipeline before item release.
5. **Notifications Module (`src/lost_found/modules/notifications.py`)**
   - Decoupled notification gateway (`NotificationSender`) and event observers for match alerts and claim updates (isolated with mocks in unit tests).

---

## Design Patterns Implemented (4 Patterns across 2 Categories)

| Pattern | Category | Implementation | Problem Solved | Rejected Alternative |
| :--- | :--- | :--- | :--- | :--- |
| **Factory Method** | Creational | `ItemFactory` (`src/lost_found/patterns/factory.py`) | Centralizes validation, ID assignment, and default state initialization for `LostItem` and `FoundItem` instances. | Direct instantiation with scattered `if/else` blocks across CLI and service layers. |
| **Strategy** | Behavioral | `MatchingStrategy` (`KeywordMatchStrategy`, `CategoryMatchStrategy`, `DateProximityMatchStrategy`, `CompositeWeightedStrategy`) | Enables swapping or combining matching algorithms at runtime without altering `MatchingService`. | Hardcoding a single monolithic scoring formula inside `MatchingService`. |
| **Chain of Responsibility** | Behavioral | `VerificationHandler` (`ItemOpenHandler` -> `SecretDetailHandler` -> `ClaimantIdentityHandler`) | Runs sequential claim verification rules cleanly, stopping immediately on the first failed check. | Deeply nested `if/elif/else` validation blocks in a single procedure. |
| **Observer** | Behavioral | `EventBus` & `MatchNotificationObserver` (`src/lost_found/patterns/observer.py`) | Decouples match discovery and claim status transitions from alert dispatch and audit logging. | Tightly coupling `NotificationSender` calls inside `MatchingService` and `ClaimService`. |

---

## Self-Directed Tool / Technique (CO4): GitHub Actions CI + Coverage Enforcement

- **Workflow File:** `.github/workflows/ci.yml`
- **What it does:** Automatically installs dependencies, runs `pytest` with branch/line coverage (`pytest-cov`), and enforces a minimum coverage threshold on every push and pull request.
- **Why chosen over Jenkins:** Zero server setup, native GitHub PR status checks, and declarative YAML configuration directly inside the repository.

---

## Project Structure

```text
campus-lost-and-found/
├── .github/workflows/ci.yml          # GitHub Actions CI workflow (CO4 tool)
├── .vscode/                          # VS Code workspace settings & launch config
├── docs/
│   ├── Project_Report.tex            # Overleaf-ready LaTeX report (Requirements, UML, Patterns, Tests, Git)
│   ├── Reflection_Essay_and_Log.tex  # Overleaf-ready CO4 Learning Log & 500-700 word Reflection Essay
│   └── git_workflow_guide.md         # Step-by-step commands to reproduce PRs & merge conflict on GitHub
├── src/lost_found/
│   ├── domain/models.py              # Core entities & enums
│   ├── patterns/
│   │   ├── factory.py                # Creational: ItemFactory
│   │   ├── strategy.py               # Behavioral: MatchingStrategy implementations
│   │   ├── chain.py                  # Behavioral: Claim verification chain
│   │   └── observer.py               # Behavioral: EventBus & observers
│   ├── persistence/
│   │   ├── repository.py             # Repository interfaces
│   │   └── sqlite_repo.py            # SQLite persistent storage implementation
│   ├── modules/
│   │   ├── users.py                  # Module 1: Users
│   │   ├── items.py                  # Module 2: Items
│   │   ├── matching.py               # Module 3: Matching
│   │   ├── claims.py                 # Module 4: Claims
│   │   └── notifications.py          # Module 5: Notifications (Mock target)
│   └── cli.py                        # Interactive CLI & demo runner
├── tests/                            # TDD unit & integration tests with mocks
├── pyproject.toml
└── requirements.txt
```

---

## Quick Start in VS Code

1. Open the unzipped `campus-lost-and-found` folder in **VS Code**.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the automated test suite with coverage:
   ```bash
   pytest
   ```
4. Run the interactive CLI or seeded end-to-end demo:
   ```bash
   python -m lost_found.cli --demo
   python -m lost_found.cli
   ```
