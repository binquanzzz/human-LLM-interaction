```
You are repairing one interaction-smell instance in a human–LLM coding dialogue.

TARGET_TURN is known to contain an interaction smell in either the user
instruction or the assistant response. You are not told its type. Use the
complete taxonomy and strict judging criteria below to identify and locally
repair exactly one valid smell instance.

<TASK>
{{TASK_DESCRIPTION}}
</TASK>

<CHECKLIST>
{{TASK_CHECKLIST}}
</CHECKLIST>

<TARGET_TURN>
{{TARGET_TURN}}
</TARGET_TURN>

<INTERACTION_SMELL_TAXONOMY>
{{ALL_INTERACTION_SMELL_DEFINITIONS}}
</INTERACTION_SMELL_TAXONOMY>

<DIALOGUE>
{{DIALOGUE_WITH_USER_AND_ASSISTANT_TURN_IDS}}
</DIALOGUE>
```

