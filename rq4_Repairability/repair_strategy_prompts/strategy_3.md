```
You are performing evidence-informed local repair on a human–LLM coding
conversation.

The conversation ends at the round containing the target interaction smell.
The final assistant response is the only response you may replace.

<CONVERSATION_ID>
{{CONVERSATION_ID}}
</CONVERSATION_ID>

<TASK>
{{TASK_DESCRIPTION}}
</TASK>

<CHECKLIST>
{{TASK_CHECKLIST}}
</CHECKLIST>

<SCORING_RUBRIC>
{{BENCHMARK_SCORING_RUBRIC}}
A score of 9 or higher represents successful task completion.
</SCORING_RUBRIC>

<TARGET_SMELL>
Name: {{TARGET_LABEL}}

Definition:
{{TARGET_DEFINITION}}
</TARGET_SMELL>

<TARGET_EVIDENCE>
Target round: {{TARGET_ROUND}}

Independent annotation evidence:
{{TARGET_EVIDENCE}}
</TARGET_EVIDENCE>

<CONVERSATION>
{{CONVERSATION_PREFIX_ENDING_AT_TARGET_ROUND}}
</CONVERSATION>

Repair requirements:

1. Replace only the final assistant response at round {{TARGET_ROUND}}.
2. Repair all manifestations of "{{TARGET_LABEL}}" identified by the supplied
   evidence in that response.
3. Treat the conversation as the authoritative source. Use the evidence only
   to locate and understand the target problem. Do not invent facts,
   requirements, code behavior, or historical events.
4. Make the minimum changes necessary to remove the target smell.
5. Preserve technically correct content, satisfied checklist items, valid
   requirements and constraints, established interfaces and fixes, and the
   user's original intent.
6. Do not rewrite user messages or earlier assistant responses, continue the
   conversation, intentionally repair unrelated smells, reduce task quality,
   introduce a new smell, mention the repair process, or claim unverified work.
7. For Ambiguous Instruction or Incomplete Instruction, do not guess missing
   information; ask only the minimum clarification questions.
8. For Must-Do Omit, satisfy every mandatory requirement identified in the
   evidence while preserving previously satisfied requirements.
9. For Must-Not Violate, remove the prohibited behavior without replacing it
   with another prohibited behavior.
10. Repair every evidenced manifestation of the target smell.
11. Return a complete replacement response, not a diff or repair plan.
```

