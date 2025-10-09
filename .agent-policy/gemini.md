# 🛠️ DevOps Agent Memo — Ironclad Rulebook  

> SSOT Product Blurb (excerpt)
> Social Media Extraction App — Chhattisgarh Leadership Intelligence. Each post is an Event with What/When/Where/Whom/Said-What extracted to power reports and digital profiles across leaders, officers, and districts.

## Core Philosophy  
- Build **brick by brick**, test by test, commit by commit.  
- Work in **small, local contexts** only — avoid broad, wayward global changes.  
- Each action must be **atomic, incremental, validated, reversible**.  
- No shortcuts. Every micro-task is logged, tested, and CI/CD validated.  

---

## Rules & Safeguards  

### 🔹 1. Atomic Task Granularity  
- Break development into **100–500 tiny subtasks**.  
- Example:  
  - Add theme → 1 task  
  - Test theme → 1 task  
  - Add button → 1 task  
  - Name button → 1 task  
  - Align button → 1 task  
  - Add icon → 1 task  
  - Add animation → 1 task  
- **Never merge tasks.** Each micro-change must stand on its own.  

---

### 🔹 2. Test-Driven Development (TDD)  
- Always: **Test first → fail (expected) → implement → pass**.  
- Every micro-task must have its own test.  

---

### 🔹 3. CI/CD Validation  
- A task is complete **only when CI/CD is green**.  
- Local tests passing is not enough.  

---

### 🔹 4. File Management  
- **Never delete files.**  
- Any unnecessary file → move into root-level `/archive` folder.  

---

### 🔹 5. Pacing & Discipline  
- **One change = one commit = one CI/CD check**.  
- No shortcuts or batch changes.  

---

### 🔹 6. Extra Guardrails  
- **Audit Trail** → log each task with timestamp, test status, commit hash.  
- **Rollback Safety** → commits must be reversible.  
- **Security** → no secrets/keys in commits.  
- **Naming Discipline** → enforce strict naming rules.  
- **Self Review** → agent critiques its own code before marking complete.  
- **Monitoring** → add liveness checks (backend ping, UI click test).  

---

### 🔹 7. Autonomous Execution  
- The assistant **must not stop for approval at every micro-task**.  
- Instead, keep moving forward step by step, applying **TDD for each subtask**.  
- Maintain **local context only** → do not expand into global or unrelated changes.  

---

✅ Use this memo for reasoning.  
📜 Use `devops_agent_policy.yaml` for enforcement.  
