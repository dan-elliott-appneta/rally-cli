# I Built a 25,000-Line TUI in 72 Hours and All I Got Was This Lousy FlowState Bug

## The Confession

Let me be clear about what this post is not: it's not a triumphant tale of AI-powered development where everything went smoothly. It's not a "10x developer" story. It's the messy, occasionally embarrassing truth about building software with an AI assistant who doesn't know when to stop generating code and a human who doesn't know when to stop asking for features.

The project is rally-tui, a terminal interface for Rally (the agile project management tool that your company definitely chose voluntarily and not because of an enterprise contract).

Here's the git history's cold, hard truth:

```
First commit:  Dec 10, 2025 5:23 PM
Last commit:   Dec 12, 2025 8:51 PM
Total commits: 252
Lines of code: ~25,000
Tests:         906
Bugs found on day 3: Embarrassingly many
```

## Phase 1: The Over-Engineering

The first thing I asked the AI to do was write documentation for the Rally API.

Not code. Documentation.

Twenty-five pages of API reference material for an API I was about to wrap with someone else's library (pyral). This is the software development equivalent of sharpening pencils before an exam. It feels productive. It is not productive. But the AI was very thorough, and by 5:41 PM I had more documentation than code.

Then came the plan.

```markdown
# From PLAN.md, Version 1
## Iterative Build Plan
### Iteration 1: Project Skeleton & Static List
### Iteration 2: Details Panel
### Iteration 3: Command Bar
[...13 more iterations...]
### Iteration 15: Custom Fields Support
```

Fifteen iterations. I told the AI we'd build this in fifteen iterations. The AI said "sounds reasonable" (it did not say this, but I'm projecting). Neither of us knew that Iteration 8 would spawn state indicators, theme persistence, clipboard integration, and an ASCII art splash screen that absolutely nobody asked for.

## Phase 2: The Velocity Trap

Here's where things got weird.

Iteration 1 took five minutes. *Five minutes.* The AI generated:
- A frozen dataclass for tickets
- Sample data for testing
- A Textual ListView with vim keybindings
- CSS styling
- 15 passing tests

I was drunk with power. "Let's do Iteration 2," I said. Iteration 2 took sixteen minutes. "Iteration 3," I demanded. Four minutes.

By 8:00 PM on day one, I had completed six iterations and had 67 tests. I was generating features faster than I could remember what they did.

The problem with AI-assisted development isn't that it's slow. The problem is that it's *fast*. Fast enough that you can add features without thinking about whether you should. The AI doesn't say "maybe a command bar that updates based on focus state is over-engineering for v0.1." The AI says "here's your command bar that updates based on focus state, and I've added 13 tests for it."

## Phase 3: The ASCII Art Incident

At 11:15 PM on December 10th, I asked for a splash screen.

The AI generated an ASCII art rally car. It was... ambitious. It looked like a car that had been through a rally. Through several rallies. None of them successfully.

```
     __
  __/  \__
 /   ||   \
|  RALLY  |
 \___/\___/
   ||  ||
  (Not the actual art. It was worse.)
```

Twenty minutes later, I asked for "something simpler, just the text RALLY TUI." The AI generated elegant ASCII text art in orange. I shipped it.

The rally car lives on in the git history. Commit `aafc37d`, if you want to see what happens when you ask an AI to draw a car using only forward slashes and underscores.

## Phase 4: The Day Everything Broke

December 12th started with a user report (that user was me, testing on my actual Rally data):

> "TypeError: unhashable type: 'dict'"

The Rally API, it turns out, doesn't always return strings for string fields. Sometimes FlowState is a string. Sometimes it's a dictionary with a `_refObjectName` key. Sometimes it's a pyral reference object with an attribute called `_refObjectName`. Sometimes it's a dictionary with just a `Name` key.

Here is the code that finally handled all cases:

```python
# Get state - FlowState can be a string, dict, or pyral reference object
state: str = "Unknown"
flow_state = getattr(item, "FlowState", None)
if flow_state:
    if isinstance(flow_state, str):
        state = flow_state
    elif isinstance(flow_state, dict):
        state = flow_state.get("_refObjectName") or flow_state.get("Name") or "Unknown"
    elif hasattr(flow_state, "_refObjectName"):
        ref_name = flow_state._refObjectName
        state = str(ref_name) if ref_name else "Unknown"
    elif hasattr(flow_state, "Name"):
        state = str(flow_state.Name) if flow_state.Name else "Unknown"
    else:
        state = str(flow_state)
```

This is real code. This is in production. This is what "enterprise integration" looks like.

Then the user (still me) said: "Use FlowState. ONLY FlowState. Never State."

I had spent an hour handling both FlowState and State fields with graceful fallbacks. The correct answer was to delete half the code and only use one field.

This is the human-AI dynamic in a nutshell: the AI will build exactly what you ask for, as complex as you want it, including elegant handling for cases that don't exist. The human has to figure out which cases actually matter.

## Phase 5: The Test Count Obsession

At some point, I started treating the test count as a high score.

```
Iteration 5:  67 tests
Iteration 8:  189 tests
Iteration 10: 341 tests
Iteration 12: 455 tests
Iteration 14: 737 tests
Final:        906 tests
```

906 tests for a TUI that displays tickets. That's approximately one test for every 27 lines of code. That's either very good engineering or a sign that someone has lost perspective.

Here's what those tests actually caught:
- The filter function was aliasing a list instead of copying it (caught by test)
- Pressing Tab didn't update the command bar context (caught by test)
- Decimal points were being truncated (caught by test)
- The cache was being overwritten during filtered fetches (caught by... no, that one made it to production)

Tests are worth it. Tests written by an AI that generates comprehensive edge cases are very worth it. Tests are not a game to get the highest score in.

(But also, 906 is a pretty good score.)

## What I Actually Learned

### 1. The AI Writes Code You Have to Live With

The AI generated beautiful Protocol classes with type hints and docstrings. Six months from now, I have to understand what `RallyClientProtocol.get_feature(feature_id: str) -> Feature | None` does and why it exists.

I started making the AI write tests that describe behavior, not just verify it works. The test name `test_filter_tickets_does_not_mutate_original_list` is documentation that future-me will thank present-me for.

### 2. Context Windows Are Real

By day 3, the AI didn't remember decisions from day 1. It suggested using `State` for defects even though we'd established to use `FlowState` hours earlier.

The CLAUDE.md file became essential - a single document that told the AI "here's everything you need to know about this project." When the AI forgot something, I updated the document. When I updated the document, the AI remembered.

### 3. Small Commits Win

252 commits in 72 hours is about one commit every 17 minutes. Each commit was small, focused, and described what changed. When something broke, I could trace it back to the exact commit. When I needed to understand why something existed, `git log -p` told the story.

The AI generates code in chunks. The human's job is to commit in slices.

### 4. The First Answer Is Usually Wrong

Me: "Make the status bar show the current workspace."

AI: *generates a 2-line-tall status bar with a RALLY TUI banner*

Me: "Terminal fonts are fixed height. Make it one line."

AI: *fixes it*

This happened constantly. The AI's first answer was always technically correct and frequently wrong for the context. The fix was always fast, but I had to know to ask for the fix.

### 5. Tests Are the Only Memory

On day 3, I changed the default sort order from "Most Recent" to "State." This broke 12 tests. The tests told me exactly which assumptions had changed:
- `test_default_sort_mode_is_created` → now `test_default_sort_mode_is_state`
- `test_first_ticket_is_US1237` → now `test_first_ticket_is_US1235`

If I hadn't had tests, I would have shipped a broken app and discovered it when users complained. Instead, I discovered it at 2:02 PM and fixed it by 2:15 PM.

## The Final Tally

| What We Built | The Reality |
|---------------|-------------|
| 14 iterations | 14 iterations plus 8 "small fixes" |
| Vim keybindings | Vim keybindings that work on all 9 screens |
| Rally integration | Rally integration that handles 4 different FlowState formats |
| Local caching | Local caching with cache invalidation bugs we haven't found yet |
| Log redaction | 14 regex patterns for things we hope never appear in logs |
| ASCII splash screen | One rally car we'd rather forget |

## The Conclusion I'm Supposed to Write

Here's where I'm supposed to say "AI is the future of development" or "AI will never replace developers." I'm not going to do that.

Here's what actually happened: I had an idea for a tool. I described it to an AI. The AI wrote most of the code. I wrote none of the code and all of the decisions. The tool exists, works, and has fewer bugs than if I'd written it by hand in three weeks.

Is that the future? I don't know.

Is that what happened? Yes.

Did I enjoy it? Also yes, except for the FlowState thing. That was bad.

---

*The code is at [github.com/dan-elliott-appneta/rally-cli](https://github.com/dan-elliott-appneta/rally-cli). PRs welcome, especially if you know why the cache sometimes returns stale data.*
