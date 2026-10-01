```
You are repairing a human–LLM coding interaction.

The dialogue below contains the interaction smell "{{TARGET_SMELL}}".

Definition:
{{TARGET_SMELL_DEFINITION}}

The message marked TARGET is the known occurrence. Earlier turns are context
only.

Requirements:
1. Repair only the target smell "{{TARGET_SMELL}}".
2. Revise only the target message:
   - For Ambiguous Instruction or Incomplete Instruction, revise the user
     instruction and return it with role "user".
   - For every other smell type, revise the assistant response and return it
     with role "assistant".
3. Preserve all correct content and all checklist items already satisfied.
4. Do not reduce task quality or introduce new interaction smells.
5. Do not intentionally repair other smell types unless necessary to
   preserve correctness.
6. Do not discuss or explain the repair.
7. Return only the required JSON object.

Task checklist:
{{TASK_CHECKLIST}}

Dialogue:
{{DIALOGUE}}
```

