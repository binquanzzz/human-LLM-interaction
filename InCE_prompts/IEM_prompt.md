```
You are given the full conversation history and the latest LLM response.
Extract a list of global invariants (persistent, cross-turn, or key constraints) that must not be changed in future iterations.
Do NOT treat every user instruction as an invariant. Only include global or most critical constraints.
If constraints conflict, keep the most recent instruction.
Each invariant should be specific and slightly detailed, but no more than 120 English words.
Return up to {max_items} items.

Conversation history：
{history}
Current instruction:
{instruction}
Latest LLM response:
{code}
Satisfied checklist items (reference only):
{satisfied_items}
Return ONLY a JSON array of strings, no extra text.
```

