from metagpt.actions import UserRequirement
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

import utils_multi_wildbench as utils
from actions_multi_wildbench import ComprehensiveEvaluate, ExtractInvariants, SelfReview, SimpleWriteCode, SmellDetector


class WorkflowEnvironment(Environment):
    task_completed: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_completed = False

    def mark_task_completed(self):
        self.task_completed = True
        utils.TASK_COMPLETED = True
        logger.info("Task marked as completed")

    def reset(self):
        self.task_completed = False
        utils.reset_global_state()
        logger.info("Environment reset")
        return self


class SimpleCoder(Role):
    name: str = "Alice"
    profile: str = "SimpleCoder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteCode])
        self.user_id = kwargs.get("user_id", "default_user")
        self.original_instruction = kwargs.get("original_instruction", "")
        self.invariant_manager = kwargs.get("invariant_manager")
        self.evaluation_results = kwargs.get("evaluation_results")
        self.round_count = 0

    async def _act(self) -> Message:
        memories = self.get_memories()
        if not memories:
            return Message(content="Waiting for instructions.", role=self.profile)
        if utils.TASK_COMPLETED:
            logger.info("SimpleCoder: Task already completed, no action needed.")
            return None

        last_message = memories[-1]
        instruction = last_message.content

        print(f"\n{'*' * 80}\nCODER RECEIVED INSTRUCTION: {instruction}\n{'*' * 80}")

        if "successfully meets all" in instruction:
            logger.info("Task completed message received - no further action needed.")
            return None

        self.round_count += 1
        if self.evaluation_results:
            self.evaluation_results.mark_round_start(self.round_count)
        history_block = ""
        if self.evaluation_results:
            history_block = utils.format_conversation_history(self.evaluation_results.conversation_output)
        if not history_block:
            history_block = "None"
        invariants_block = ""
        invariants_list = []
        if self.invariant_manager:
            invariants_list = self.invariant_manager.items()
            invariants_block = self.invariant_manager.format_for_prompt()

        retrieval_mem = []
        memory_context = history_block
        if self.evaluation_results:
            self.evaluation_results.add_retrieval_mem(self.round_count, retrieval_mem)

        task_id = self.user_id or (self.evaluation_results.id if self.evaluation_results else "")

        self_review_text = ""
        smell_result = {}
        if not utils.TASK_COMPLETED:
            self_review_action = SelfReview()
            self_review_text = await self_review_action.run(
                instruction,
                history=history_block,
                invariants=invariants_block or "None",
                task_id=task_id,
                round_index=self.round_count,
            )

            smell_action = SmellDetector()
            smell_result = await smell_action.run(
                instruction=instruction,
                history=history_block,
                invariants=invariants_list,
                self_review=self_review_text,
                task_id=task_id,
                round_index=self.round_count,
            )

        resolved_constraints = []
        if isinstance(smell_result, dict):
            resolved_constraints = smell_result.get("resolved_constraints", []) or []
        if not isinstance(resolved_constraints, list):
            resolved_constraints = []
        if not resolved_constraints and isinstance(smell_result, dict):
            missing_constraints = smell_result.get("missing_constraints", []) or []
            if isinstance(missing_constraints, list) and missing_constraints:
                resolved_constraints = missing_constraints

        constraints_block = ""
        if resolved_constraints:
            constraints_lines = "\n".join([f"{idx + 1}. {item}" for idx, item in enumerate(resolved_constraints)])
            constraints_block = (
                "VALIDATED CONSTRAINTS (most recent wins):\n"
                f"{constraints_lines}\n"
                "END VALIDATED CONSTRAINTS"
            )
        elif invariants_block:
            constraints_block = invariants_block
        else:
            constraints_block = "None"

        write_code_action = SimpleWriteCode()
        if self.evaluation_results:
            self.evaluation_results.add_prompt_tokens(
                self.round_count,
                utils.safe_count_text_tokens(write_code_action.llm, instruction),
                utils.safe_count_text_tokens(write_code_action.llm, memory_context),
                utils.safe_count_text_tokens(write_code_action.llm, constraints_block),
            )
        code = await write_code_action.run(
            instruction,
            history=history_block,
            constraints=constraints_block,
            task_id=task_id,
            round_index=self.round_count,
        )
        if self.evaluation_results:
            self.evaluation_results.add_output_tokens(
                self.round_count,
                utils.safe_count_output_tokens(write_code_action.llm, code or ""),
            )

        result_msg = Message(
            content=code,
            role=self.profile,
            cause_by=SimpleWriteCode,
            send_to={"Evaluator"}
        )
        return result_msg


class SimpleEvaluator(Role):
    name: str = "Evaluator"
    profile: str = "SimpleEvaluator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ComprehensiveEvaluate])
        self.code = None
        self.original_instruction = kwargs.get("original_instruction", "")
        self.checklist = kwargs.get("checklist", [])
        self.round_count = 0
        self.max_rounds = kwargs.get("max_rounds", 3)
        self.evaluation_results = kwargs.get("evaluation_results", None)
        self.current_instruction = self.original_instruction
        self.user_id = kwargs.get("user_id") or (self.evaluation_results.id if self.evaluation_results else "default_user")
        self.invariant_manager = kwargs.get("invariant_manager")

    async def _act(self) -> Message:
        memories = self.get_memories()
        if not memories:
            return Message(content="Waiting for code to evaluate.", role=self.profile)

        if utils.TASK_COMPLETED:
            logger.info("SimpleEvaluator: Task already completed, no action needed.")
            return None

        last_message = memories[-1]
        self.code = last_message.content

        self.round_count += 1
        logger.info(f"SimpleEvaluator: Processing round {self.round_count}/{self.max_rounds}")

        print(f"\n{'*' * 80}\nEVALUATOR CHECKING CODE (Round {self.round_count}/{self.max_rounds})\n{'*' * 80}")


        comprehensive_action = ComprehensiveEvaluate()
        task_id = self.user_id or (self.evaluation_results.id if self.evaluation_results else "")
        evaluation_results = await comprehensive_action.run(
            self.current_instruction,
            self.code,
            self.checklist,
            self.round_count,
            task_id=task_id,
        )
        input_eval_tokens = (evaluation_results or {}).get("input_eval_tokens", 0)
        output_eval_tokens = (evaluation_results or {}).get("output_eval_tokens", 0)


        raw_score = evaluation_results.get('score', None) if evaluation_results else None
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = None


        if self.evaluation_results:
            self.evaluation_results.add_conversation_turn(self.current_instruction, self.code)
            self.evaluation_results.add_score(score if score is not None else raw_score)
            self.evaluation_results.add_eval_tokens(self.round_count, input_eval_tokens, output_eval_tokens)

            print(f"\n{'*' * 80}\nROUND {self.round_count} SCORING:\n{'*' * 80}")
            print(f"Score: {score if score is not None else raw_score}/10")
            print(f"{'*' * 80}")

        if self.evaluation_results is not None:
            self.evaluation_results.add_save_mem(self.round_count, [])

        if self.invariant_manager and evaluation_results:
            satisfied_items = evaluation_results.get("satisfied_items", [])
            satisfied_texts = []
            for item_num in satisfied_items:
                item_idx = item_num - 1
                if 0 <= item_idx < len(self.checklist):
                    satisfied_texts.append(self.checklist[item_idx])

            history_block = ""
            if self.evaluation_results:
                history_block = utils.format_conversation_history(self.evaluation_results.conversation_output)
            if not history_block:
                history_block = "None"

            extract_action = ExtractInvariants()
            max_items = min(getattr(self.invariant_manager, "max_items", 35) or 35, 10)
            invariants = await extract_action.run(
                history=history_block,
                instruction=self.current_instruction,
                code=self.code or "",
                satisfied_items=satisfied_texts,
                max_items=max_items,
                task_id=task_id,
                round_index=self.round_count,
            )

            if not invariants:
                invariants = evaluation_results.get("invariants", []) or []

            self.invariant_manager.update_for_round(invariants, target_count=None)
            if self.evaluation_results is not None:
                self.evaluation_results.add_invar_mem(
                    self.round_count,
                    self.invariant_manager.items(),
                )
        if self.evaluation_results:
            self.evaluation_results.mark_round_end(self.round_count)

        all_satisfied = not evaluation_results.get('unsatisfied_items', []) if evaluation_results else False


        if score is not None and score >= 9.0:
            print(f"\n{'#' * 80}\nHIGH SCORE ACHIEVED ({score}/10) - STOPPING EXECUTION\n{'#' * 80}")

            utils.TASK_COMPLETED = True
            logger.info("SimpleEvaluator: High score reached, stopping execution")

            if isinstance(self.rc.env, WorkflowEnvironment):
                self.rc.env.mark_task_completed()
                logger.info("SimpleEvaluator: Marked environment task as completed due to high score")

            return Message(
                content=f"Code achieved a high score of {score}/10. Stopping iterations early.",
                role=self.profile,
                cause_by=ComprehensiveEvaluate,
                send_to={"Evaluator"}
            )


        elif all_satisfied:
            print(f"\n{'#' * 80}\nALL CHECKLIST ITEMS SATISFIED!\n{'#' * 80}")

            utils.TASK_COMPLETED = True
            logger.info("SimpleEvaluator: Setting TASK_COMPLETED to True")

            if isinstance(self.rc.env, WorkflowEnvironment):
                self.rc.env.mark_task_completed()
                logger.info("SimpleEvaluator: Marked environment task as completed")


            return Message(
                content=f"Code successfully meets all {len(self.checklist)} checklist requirements with a score of {score}/10!",
                role=self.profile,
                cause_by=ComprehensiveEvaluate,
                send_to={"Evaluator"}
            )


        elif self.round_count >= self.max_rounds:
            print(f"\n{'#' * 80}\nMAX ROUNDS ({self.max_rounds}) REACHED - STOPPING EXECUTION\n{'#' * 80}")


            utils.TASK_COMPLETED = True
            logger.info(f"SimpleEvaluator: Max rounds ({self.max_rounds}) reached, stopping execution")

            if isinstance(self.rc.env, WorkflowEnvironment):
                self.rc.env.mark_task_completed()
                logger.info("SimpleEvaluator: Marked environment task as completed")

            return Message(
                content=f"Max rounds ({self.max_rounds}) reached. Code satisfies {len(evaluation_results.get('satisfied_items', []))} out of {len(self.checklist)} checklist items with a score of {score}/10.",
                role=self.profile,
                cause_by=ComprehensiveEvaluate,
                send_to={"Evaluator"}
            )


        new_instruction = evaluation_results.get('next_instruction', "Please improve your solution based on the feedback.")


        self.current_instruction = new_instruction


        return Message(
            content=new_instruction,
            role=self.profile,
            cause_by=UserRequirement,
            send_to={"Alice"}
        )


class WorkflowTeam(Team):
    def __init__(self, env=None, roles=None, **kwargs):
        super().__init__(env=env, roles=roles, **kwargs)
        self._roles = roles or []

    @staticmethod
    def _print_invariants(evaluator_role):
        if not evaluator_role or not getattr(evaluator_role, "invariant_manager", None):
            return

        invariants = evaluator_role.invariant_manager.items()
        round_index = evaluator_role.round_count
        print(
            f"\n{'*' * 80}\nGLOBAL INVARIANTS (Round {round_index}):\n{'*' * 80}",
            flush=True,
        )
        if invariants:
            for idx, item in enumerate(invariants, 1):
                print(f"{idx}. {item}", flush=True)
        else:
            print("None", flush=True)
        print(f"{'*' * 80}", flush=True)

    async def run(self, n_round=3):
        logger.info(f"Starting workflow with max {n_round} rounds")

        evaluator_role = None
        for role in self._roles:
            if isinstance(role, SimpleEvaluator):
                evaluator_role = role
                break
        if not evaluator_role:
            logger.error("No SimpleEvaluator role found in team")
            return

        evaluator_role.max_rounds = n_round
        utils.TASK_COMPLETED = False
        logger.info(f"Starting initial workflow processing")
        await super().run(n_round=1)
        self._print_invariants(evaluator_role)

        while not utils.TASK_COMPLETED and evaluator_role.round_count < n_round:
            logger.info(f"Continuing workflow processing for round {evaluator_role.round_count + 1}")

            await super().run(n_round=1)
            self._print_invariants(evaluator_role)

            if utils.TASK_COMPLETED:
                logger.info(f"Task completed in round {evaluator_role.round_count}")
                break


        if evaluator_role.round_count >= n_round and not utils.TASK_COMPLETED:
            logger.info(f"Max rounds reached ({n_round}) without completing task")
            utils.TASK_COMPLETED = True


        if hasattr(evaluator_role, "evaluation_results"):
            return evaluator_role.evaluation_results

        return None
