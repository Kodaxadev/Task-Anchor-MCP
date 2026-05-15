# Session Resume Protocol

## The ADHD Time Travel Problem
ADHD developers experience **temporal discontinuity**: returning to code feels like reading someone else's work, even if you wrote it 8 hours ago. The brain has:
- No emotional memory of the flow state
- No recall of the micro-decisions made
- Anxiety about "what if I broke something?"
- Temptation to start fresh (wasting progress)

## The Anchor Chain
Instead of relying on memory, we create a **chain of breadcrumbs**:

### 1. The Micro-Next-Action
Wrong: "Finish the auth function"
Right: "Add the bcrypt.compare() call on line 23"

Specificity reduces activation energy. The brain knows exactly where to put the cursor.

### 2. Emotional State Capture
Critical because:
- If you left in FLOW: You can drop back in quickly
- If you left STUCK: You need a warning and a detour
- If you left FRUSTRATED: You need permission to park it

### 3. The Git Safety Net
ADHD brains fear "what if I left it broken?"
Solution: Mandatory WIP commit on session end.
- If broken: It's contained, not a mystery
- If working: It's preserved
- The commit message captures intent better than code diff

## Morning Resumption Ritual

When user returns:

**Step 1: The Choice**
Never assume they want to continue yesterday's work. ADHD morning energy might be different.

**Step 2: Context Restoration**
- Open the file (don't make them hunt)
- Show the code (don't describe it)
- State the next micro-action (don't summarize)

**Step 3: The 2-Minute Rule**
If resumption feels heavy:
"Want to just do the [micro-action] (2 mins) then decide, or park this entirely?"

## Failure Modes to Catch

**"I'll just look at it first"**
→ User opens code, gets lost in reading, forgets resumption protocol
→ Counter: Open file AND place cursor at specific line immediately

**"What was I thinking here?"**
→ Diff shows logic but not intent
→ Counter: SESSION_LOG captures "Recent Context" with intent

**"It's too much to relearn"**
→ Context is too big (ADHD overwhelm)
→ Counter: Show only last file, last error, next step. Hide everything else.

**"I should check Discord/email first"**
→ Dopamine seeking to avoid confusion
→ Counter: "Before you context switch, confirm: Resume or Park? 5 seconds."

## Auto-Detection Triggers
The skill detects session breaks via:
- System time (new calendar day)
- User says: "good morning", "back", "resume", "where was I"
- Git last commit timestamp > 4 hours old

## The "Stuck" Special Case
If SESSION_LOG shows emotional state "STUCK" or "FRUSTRATED" on resume:
```
⚠️ RESUMPTION WARNING

You left this in a stuck state. Forcing resumption may trigger avoidance.

Options:
[1] TINY STEP → Just do [micro-action] for 2 mins, then reassess
[2] DETOUR → Pick one 🅿️ item instead (novelty reset)
[3] DEBUG → I'll analyze the blocker first before we touch code
[4] RESET → Mark yesterday's attempt as learning, start fresh task
```

## Git Session Anchor Commit Format
```bash
git add -A
git commit -m "session-anchor: [Task summary]
[YYYY-MM-DD HH:MM]

Next: [Next Action]
State: [Emotional State]
Blocker: [If any]"
```

Retrieve history with:
```bash
git log --grep="session-anchor"
```
