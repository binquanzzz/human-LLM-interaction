import json
import re
from typing import Any, Dict, List, Optional
from metagpt.actions import Action
from metagpt.llm import LLM
from metagpt.logs import logger
import utils_multi_wildbench as utils

try:
    from metagpt.llm import safe_update_costs
except Exception:
    def safe_update_costs(*args, **kwargs):
        return None


class SimpleWriteCode(Action):
    PROMPT_TEMPLATE: str = " "
    name: str = "SimpleWriteCode"

    def __init__(self, context=None):
        super().__init__()
        self._context = context
        self.set_llm(LLM(llm_config=utils.get_llm_config()))

    async def run(
        self,
        instruction: str,
        history: str = "",
        constraints: str = "",
        task_id: str = "",
        round_index: int = 0,
    ):
        if utils.TASK_COMPLETED:
            return None

        prompt = self.PROMPT_TEMPLATE.format(
            instruction=instruction,
            history=history or "None",
            constraints=constraints or "None",
        )
        utils.append_round_input(task_id, round_index, "coder", prompt)

        print(f"\n{'*' * 80}\nGENERATING CODE\n{'*' * 80}")
        if task_id:
            print(f"Task ID: {task_id}")
        if round_index:
            print(f"Round: {round_index}")
        print(f"Instruction: {instruction}")
        print(f"\nFULL PROMPT TO CODER:\n{prompt}")
        print(f"{'*' * 80}\n")

        try:
            response = await utils.api_retry_with_backoff(
                self.llm.aask,
                prompt,
                max_retries=3,
                base_delay=2
            )

            return response

        except Exception as e:
            logger.error(f"Failed to generate code using LLM: {e}")

            return f"Sorry, I couldn't generate code due to an error: {str(e)}"


class SelfReview(Action):
    PROMPT_TEMPLATE: str = " "
    name: str = "SelfReview"

    def __init__(self, context=None):
        super().__init__()
        self._context = context
        self.set_llm(LLM(llm_config=utils.get_llm_config()))

    async def run(
        self,
        instruction: str,
        history: str = "",
        invariants: str = "",
        task_id: str = "",
        round_index: int = 0,
    ) -> str:
        if utils.TASK_COMPLETED:
            return ""

        prompt = self.PROMPT_TEMPLATE.format(
            instruction=instruction,
            history=history or "None",
            invariants=invariants or "None",
        )
        utils.append_round_input(task_id, round_index, "self_review", prompt)

        try:
            response = await utils.api_retry_with_backoff(
                self.llm.aask,
                prompt,
                max_retries=3,
                base_delay=2,
            )
            return response or ""
        except Exception as e:
            logger.error(f"LLM self-review call failed: {e}")
            return ""


INTERACTION_SMELL_CATEGORIES: str = ("" )


class SmellDetector(Action):
    PROMPT_TEMPLATE: str = " "
    name: str = "SmellDetector"

    def __init__(self, context=None):
        super().__init__()
        self._context = context
        self.set_llm(LLM(llm_config=utils.get_llm_config()))

    async def run(
        self,
        instruction: str,
        history: str,
        invariants: Optional[List[str]] = None,
        self_review: str = "",
        task_id: str = "",
        round_index: int = 0,
    ) -> Dict[str, Any]:
        invariants_text = "None"
        if invariants:
            invariants_text = "\n".join([f"{idx + 1}. {item}" for idx, item in enumerate(invariants)])
        prompt = self.PROMPT_TEMPLATE.format(
            taxonomy=INTERACTION_SMELL_CATEGORIES,
            history=history or "None",
            instruction=instruction,
            invariants=invariants_text,
            self_review=self_review or "None",
        )
        utils.append_round_input(task_id, round_index, "smell_detector", prompt)

        try:
            response = await utils.api_retry_with_backoff(
                self.llm.aask,
                prompt,
                max_retries=3,
                base_delay=2,
            )
        except Exception as e:
            logger.error(f"Failed to call smellDetector: {e}")
            return {}

        if isinstance(response, str) and response.strip().startswith("```"):
            response = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", response.strip(), flags=re.DOTALL)

        try:
            json_pattern = r"\{[\s\S]*\}"
            json_match = re.search(json_pattern, response)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = json.loads(response)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse smellDetector JSON: {e}")
            return {}



class ComprehensiveEvaluate(Action):
    PROMPT_TEMPLATE: str = " "
    name: str = "ComprehensiveEvaluate"

    def __init__(self, context=None):
        super().__init__()
        self._context = context
        self.set_llm(LLM(llm_config=utils.get_llm_config()))

    async def run(
        self,
        original_instruction: str,
        code: str,
        checklist: List[str],
        round_count: int = 1,
        task_id: str = "",
    ):
        if utils.TASK_COMPLETED:
            return None

        self.round_count = round_count

        checklist_str = "\n".join([f"{i+1}. {item}" for i, item in enumerate(checklist)])
        prompt = self.PROMPT_TEMPLATE.format(
            original_instruction=original_instruction,
            code=code,
            checklist=checklist_str
        )
        utils.append_round_input(task_id, round_count, "evaluator", prompt)
        input_eval_tokens = utils.safe_count_text_tokens(self.llm, prompt)
        output_eval_tokens = 0

        try:
            async def safe_aask_with_usage():
                try:
                    response, usage = await self.llm.aask_to_usage(prompt)
                    safe_update_costs(self.llm, usage)
                    return response
                except AttributeError:
                    response = await self.llm.aask(prompt)
                    return response

            response = await utils.api_retry_with_backoff(
                safe_aask_with_usage,
                max_retries=3,
                base_delay=2
            )
            output_eval_tokens = utils.safe_count_output_tokens(self.llm, response)


            if isinstance(response, str) and response.strip().startswith("```"):
                response = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", response.strip(), flags=re.DOTALL)


            try:
                json_pattern = r"\{[\s\S]*\}"
                json_match = re.search(json_pattern, response)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    result = json.loads(response)

                if not isinstance(result.get("invariants"), list):
                    result["invariants"] = []
                result["input_eval_tokens"] = input_eval_tokens
                result["output_eval_tokens"] = output_eval_tokens

                satisfied_count = len(result.get('satisfied_items', []))
                total_items = len(checklist)

                print(f"\n{'*' * 80}\nCOMPREHENSIVE EVALUATION RESULTS (Round {self.round_count}):\n{'*' * 80}")

                if total_items > 0:
                    percentage = (satisfied_count/total_items)*100
                    print(f"Satisfied items: {satisfied_count}/{total_items} ({percentage:.1f}%)")
                else:
                    print(f"Satisfied items: {satisfied_count}/{total_items} (N/A - no checklist items)")


                if 'unsatisfied_items' in result and result['unsatisfied_items']:
                    print("\nUnsatisfied items:")
                    for item_num in result['unsatisfied_items']:
                        item_idx = item_num - 1
                        if 0 <= item_idx < len(checklist):
                            item_text = checklist[item_idx]
                            explanation = result.get('evaluation', {}).get(str(item_num), {}).get('explanation', 'No explanation')
                            print(f"  {item_num}. {item_text} - {explanation}")

                print(f"\nSCORE: {result.get('score', 'N/A')}/10")
                print(f"Justification: {result.get('justification', 'No justification provided')}")


                print(f"\nNEXT INSTRUCTION: {result.get('next_instruction', 'No instruction generated')}")
                print(f"{'*' * 80}")

                return result

            except json.JSONDecodeError as e:
                print(f"Error parsing evaluation result: {str(e)}")
                print(f"Original response: {response}")


                score_match = re.search(r'"score"\\s*:\\s*([0-9]+(?:\\.[0-9]+)?)', str(response))
                parsed_score = score_match.group(1) if score_match else response


                return {
                    "satisfied_items": [],
                    "unsatisfied_items": list(range(1, len(checklist) + 1)),
                    "evaluation": {},
                    "score": parsed_score,
                    "justification": "Failed to parse response format; kept raw/regex-extracted score",
                    "next_instruction": "Please improve your solution based on the feedback.",
                    "invariants": [],
                    "error": str(e),
                    "raw_response": response,
                    "input_eval_tokens": input_eval_tokens,
                    "output_eval_tokens": output_eval_tokens,
                }
        except Exception as e:
            logger.error(f": {e}")

            return {
                "satisfied_items": [],
                "unsatisfied_items": list(range(1, len(checklist) + 1)),
                "evaluation": {},
                "score": f"error: {e}",
                "justification": f"Failed due to API error: {str(e)}",
                "next_instruction": "Please improve your solution based on the feedback.",
                "invariants": [],
                "input_eval_tokens": input_eval_tokens,
                "output_eval_tokens": output_eval_tokens,
            }


class ExtractInvariants(Action):
    PROMPT_TEMPLATE: str = " "
    name: str = "ExtractInvariants"

    def __init__(self, context=None):
        super().__init__()
        self._context = context
        self.set_llm(LLM(llm_config=utils.get_llm_config()))

    async def run(
        self,
        history: str,
        instruction: str,
        code: str,
        satisfied_items: List[str],
        max_items: int = 10,
        task_id: str = "",
        round_index: int = 0,
    ) -> List[str]:
        checklist_str = "\n".join([f"- {item}" for item in satisfied_items]) or "None"
        prompt = self.PROMPT_TEMPLATE.format(
            history=history or "None",
            instruction=instruction,
            code=code,
            satisfied_items=checklist_str,
            max_items=max_items,
        )
        utils.append_round_input(task_id, round_index, "extract_invariants", prompt)

        try:
            response = await utils.api_retry_with_backoff(
                self.llm.aask,
                prompt,
                max_retries=3,
                base_delay=2
            )
        except Exception as e:
            logger.error(f"Failed to extract invariants using LLM: {e}")
            return []

        if isinstance(response, str) and response.strip().startswith("```"):
            response = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", response.strip(), flags=re.DOTALL)

        try:
            result = json.loads(response)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse invariants JSON: {e}")

        return []
