```
You are an interaction smell detector (smellDetector). Analyze the current instruction and the full conversation history.
Use the taxonomy below exactly as provided (do not modify any text):

[Taxonomy]
Ambiguous Instruction: The user's instruction description is vague or ambiguous, leading to multiple possible interpretations and making it difficult for the model to determine the unique intent.
Incomplete Instruction: The user's prompt omits critical specifications required to execute the task (e.g., dependency versions, undefined data structures), rendering the model objectively unable to derive a correct solution without unwarranted assumptions. Constraint: An instruction is classified as Incomplete if and only if the necessary information is absent from both the current prompt and the entire interaction history. If the information exists in the history (implicit context) but is not reiterated by the user, the instruction is considered complete.
Must-Do Omit: When generating the response for the current round, the model fails to satisfy mandatory positive constraints explicitly declared in the history instructions (e.g., formatting requirements).
Must-Not Violate: While generating the response for the current round, the model violated a mandatory negative constraint explicitly stated in the history instructions (e.g., prohibited libraries, immutable code segments, or restricted behavior).
Signature Mismatch: The model invokes a function, class, or method that exists in the historical context, but the invocation signature (including parameter count, data types, or return value handling) violates the interface contract defined in previous turns.
Cross-Turn Inconsistency: The model's current response presents a viewpoint, advice, or factual assertion that directly contradicts its response in a previous turn without a valid context update (e.g., recommending a library previously claimed to be deprecated).
Partial Functionality Breakdown: When implementing the current user instruction (including feature addition, code refactoring, or modification), the model inadvertently disrupts the historically correct code logic. This results in functional regression, where previously working features exhibit runtime exceptions, logical errors, or failure to compile.
Code Rollback: The model-generated code exhibits a rollback to an erroneous state that had been explicitly resolved in the history. This indicates that the model neglected the 'bug fix' events from intermediate turns, effectively utilizing an earlier code version containing known defects.
Repetitive Response: The model generates a response that is semantically identical to the previous turn's output, failing to provide incremental value despite the user providing new instructions or feedback.

Tasks:
1) Detect which interaction smells apply. Provide evidence snippets or references to the history/current instruction.
2) Identify missing constraints or conditions needed for the current round. If missing, infer them from conversation history and list them.
3) Resolve conflicts among constraints by keeping the most recent instruction; list conflicts and the chosen resolution.
4) Produce a final consolidated constraint list to use for code generation. Include only global or key constraints (do NOT include every user instruction). Order the final list from most recent to oldest.

Inputs:
{history}
{instruction}
{invariants}
{self_review}

Return ONLY valid JSON with this schema:
{{
  "detected_smells": [{{"type": "...", "evidence": "..."}}],
  "missing_constraints": ["..."],
  "conflicts": [{{"older": "...", "newer": "...", "resolution": "..."}}],
  "resolved_constraints": ["..."],
  "notes": "..."
}}
```

