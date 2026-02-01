import asyncio
import random
import sys
import time
import traceback
import fire
from metagpt.logs import logger
import utils_multi_wildbench as utils
from workflow_multi_wildbench import run_workflow


async def main(
    idea: str = "write a function that calculates the product of a list",
    investment: float = 3.0,
    n_round: int = 3,
    jsonl_file: str = None,
    output_file: str = "output.jsonl",
    start_index: int = 0,
    save_interval: int = 5,
    retry_delay_base: int = 20,
    real_time_save: bool = True,
    round_input_file: str = "round_input.txt",
    use_timeout: bool = False,
    timeout_seconds: int = 1800,
    return_results: bool = False
):
    try:
        await utils.init_http_session()
        utils.reset_global_state()
        utils.set_round_input_file(round_input_file, reset=real_time_save)

        all_results = []
        start_time = time.time()

        if real_time_save:
            with open(output_file, 'w', encoding='utf-8') as f:
                pass
            logger.info(f"Output file has been cleared. {output_file}，Prepare for real-time incremental saving")

        if jsonl_file:
            try:
                data_list = utils.read_jsonl(jsonl_file)
                logger.info(f"Loaded {len(data_list)} tasks from {jsonl_file}")


                if start_index > 0:
                    if start_index >= len(data_list):
                        logger.error(f"Start index {start_index} exceeds data length {len(data_list)}")
                        return [] if return_results else None
                    data_list = data_list[start_index:]
                    logger.info(f"Starting from index {start_index}, {len(data_list)} items remaining")

                for i, task_data in enumerate(data_list):
                    current_index = i + start_index
                    task_start_time = time.time()

                    progress_percent = (i / len(data_list)) * 100
                    logger.info(f"Processing Progress: {progress_percent:.1f}% ({i}/{len(data_list)})")

                    retry_count = 0
                    max_retries = 3

                    while retry_count <= max_retries:
                        try:
                            task_id = task_data.get("task_id", f"task_{current_index}")
                            conversation_input = task_data.get("conversation_input", [])

                            if conversation_input and isinstance(conversation_input, list) and len(conversation_input) > 0 and isinstance(conversation_input[0], dict) and "content" in conversation_input[0]:
                                instruction = conversation_input[0]["content"]
                                print(f"Task {task_id}: Using content from first conversation_input element")
                                logger.info(f"Task {task_id}: Using content from first conversation_input element")
                            else:
                                logger.warning(f"Task {task_id}: First element in conversation_input has no 'content' field or is not in expected format. Using default instruction.")
                                instruction = idea

                            checklist = task_data.get("checklist", [])

                            print(f"\nProcessing task {current_index+1}/{len(data_list) + start_index}: {task_id}")
                            print(f"Instruction: {instruction}")
                            print(f"Checklist items: {len(checklist)}")


                            evaluation_results = utils.EvaluationResults(id=task_id)

                            logger.info(f"Running task {current_index+1}/{len(data_list) + start_index}: {task_id}")
                            try:

                                if use_timeout:
                                    logger.info(f"Running task with {timeout_seconds} second timeout")

                                    await asyncio.wait_for(
                                        run_workflow(instruction, checklist, investment, n_round, evaluation_results, round_input_file=round_input_file),
                                        timeout=timeout_seconds
                                    )


                                else:
                                    logger.info("Running task without timeout (will wait until completion)")
                                    await run_workflow(instruction, checklist, investment, n_round, evaluation_results, round_input_file=round_input_file)
                            except asyncio.TimeoutError:
                                logger.error(f"Task {task_id} timed out after {timeout_seconds} seconds (will retry if quota remains)")
                                raise

                            result_dict = evaluation_results.to_dict()
                            all_results.append(result_dict)

                            if real_time_save:
                                utils.append_result_to_jsonl(result_dict, output_file)
                                print(f"The results of task {task_id} have been saved to {output_file} in real time.")


                            if (i + 1) % save_interval == 0:
                                utils.save_intermediate_results(all_results, output_file)
                                logger.info(f"Intermediate results ({i+1} in total) have been saved to the backup file.")

                            task_duration = time.time() - task_start_time
                            elapsed_total = time.time() - start_time
                            tasks_completed = i + 1
                            tasks_remaining = len(data_list) - (i + 1)


                            if tasks_completed > 0:
                                avg_time_per_task = elapsed_total / tasks_completed
                                estimated_remaining_time = avg_time_per_task * tasks_remaining

                                logger.info(f"Task {task_id} completed in {task_duration:.2f} seconds")
                                logger.info(f"Progress: {tasks_completed}/{len(data_list)} tasks completed")
                                logger.info(f"Estimated time remaining: {estimated_remaining_time/60:.2f} minutes")

                                print(f"\nTiming info:")
                                print(f"- Task duration: {task_duration:.2f} seconds")
                                print(f"- Average time per task: {avg_time_per_task:.2f} seconds")
                                print(f"- Estimated time remaining: {estimated_remaining_time/60:.2f} minutes")

                            await asyncio.sleep(1)

                            break

                        except asyncio.TimeoutError:
                            retry_count += 1
                            logger.error(f"Task {task_id} timed out after {timeout_seconds} seconds (attempt {retry_count}/{max_retries + 1})")

                            if retry_count <= max_retries:
                                delay = retry_delay_base * (2 ** (retry_count - 1))
                                logger.info(f"Retry the timeout task in {delay} seconds (attempting) {retry_count}/{max_retries})")
                                await asyncio.sleep(delay)
                                continue

                            logger.error(f"The timeout has reached the maximum retry count. Task skipped. {task_id}")


                            if evaluation_results.rounds > 0:
                                result_dict = evaluation_results.to_dict()
                                all_results.append(result_dict)
                                if real_time_save:
                                    utils.append_result_to_jsonl(result_dict, output_file)
                                    print(f"Partial results for the timed-out task {task_id} have been saved in real time.")
                            if len(all_results) > 0:
                                utils.save_intermediate_results(all_results, output_file)
                            break

                        except Exception as e:
                            retry_count += 1
                            logger.error(f"Processing tasks {current_index} ({task_id}) fail: {e}")

                            if retry_count <= max_retries:
                                delay = retry_delay_base * (2 ** (retry_count - 1))
                                logger.info(f"The task will be retried in {delay} seconds (attempt {retry_count}/{max_retries}).")
                                await asyncio.sleep(delay)

                            else:
                                logger.error(f"Maximum number of retries reached, skipping task {task_id}.")


                            if hasattr(evaluation_results, 'rounds') and evaluation_results.rounds > 0:
                                result_dict = evaluation_results.to_dict()
                                all_results.append(result_dict)

                                if real_time_save:
                                    utils.append_result_to_jsonl(result_dict, output_file)
                                    print(f"Partial results for failed task {task_id} have been saved in real time.")

                            if len(all_results) > 0:
                                utils.save_intermediate_results(all_results, output_file)
                            traceback.print_exc()


                    task_interval = 2 + random.random() * 2
                    logger.info(f"Waiting {task_interval:.2f} seconds before processing the next task.")
                    await asyncio.sleep(task_interval)

            except Exception as e:
                logger.error(f"Critical error in main processing loop: {e}")
                print(f"CRITICAL ERROR: {e}")
                traceback.print_exc()


                if len(all_results) > 0:
                    utils.save_intermediate_results(all_results, output_file)
                    logger.info(f"Saved results after critical error")
        else:
            logger.info(f"Running single task with idea: {idea}")
            evaluation_results = utils.EvaluationResults(id="default_task")
            await run_workflow(idea, [], investment, n_round, evaluation_results, round_input_file=round_input_file)
            result_dict = evaluation_results.to_dict()
            all_results.append(result_dict)
            if real_time_save:
                utils.append_result_to_jsonl(result_dict, output_file)
                print(f"The results of a single task have been saved in real time {output_file}")

        if not real_time_save:
            utils.save_results_to_jsonl(all_results, output_file)
            logger.info(f"Results saved to {output_file}")
        else:
            logger.info(f"All results have been saved in real time {output_file}")


        total_time = time.time() - start_time
        logger.info(f"Total execution time: {total_time/60:.2f} minutes")
        print(f"Total execution time: {total_time/60:.2f} minutes")


        return all_results if return_results else None


    finally:
        await utils.cleanup_resources()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        fire.Fire(main)
    except Exception as e:
        print(f"Main program execution error: {e}")
        logger.error(f"Main program execution error: {e}")
        traceback.print_exc()
