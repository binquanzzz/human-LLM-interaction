from typing import List

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message

import utils_multi_wildbench as utils
from invariants_multi_wildbench import InvariantManager
from roles_multi_wildbench import SimpleCoder, SimpleEvaluator, WorkflowEnvironment, WorkflowTeam



async def run_workflow(
    idea: str,
    checklist: List[str] = None,
    investment: float = 3.0,
    n_round: int = 3,
    evaluation_results: utils.EvaluationResults = None,
    round_input_file: str = None
):


    if checklist is None:
        checklist = []

    utils.reset_global_state()
    if round_input_file is not None:
        utils.set_round_input_file(round_input_file, reset=False)


    env = WorkflowEnvironment()
    env.reset()


    if not evaluation_results:
        evaluation_results = utils.EvaluationResults(id=idea[:10])

    invariant_manager = InvariantManager()


    coder = SimpleCoder(
        user_id=evaluation_results.id,
        original_instruction=idea,
        invariant_manager=invariant_manager,
        evaluation_results=evaluation_results,
    )
    evaluator = SimpleEvaluator(
        user_id=evaluation_results.id,
        original_instruction=idea,
        checklist=checklist,
        max_rounds=n_round,
        invariant_manager=invariant_manager,
        evaluation_results=evaluation_results,
    )


    roles_list = [coder, evaluator]


    team = WorkflowTeam(env=env, roles=roles_list)
    team.invest(investment)


    print(f"\n{'#' * 80}\nSTARTING TASK: {idea}\n{'#' * 80}")

    if checklist:
        print(f"\nCHECKLIST:")
        for i, item in enumerate(checklist):
            print(f"{i+1}. {item}")


    initial_message = Message(
        content=idea,
        role="User",
        cause_by=UserRequirement,
        send_to={"Alice"}
    )


    team.env.publish_message(initial_message)

    await team.run(n_round=n_round)

    print(evaluation_results.summary())

    print("\n" + "#" * 80)
    print("EXECUTION COMPLETE")
    print("#" * 80)

    return evaluation_results
