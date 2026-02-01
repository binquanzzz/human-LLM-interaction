import asyncio
import gc
import json
import os
import random
import time
import traceback
from typing import Dict, List, Any

import aiohttp
import httpx

from metagpt.config2 import config as metagpt_config
from metagpt.logs import logger
from metagpt.utils.token_counter import count_output_tokens
from pydantic import BaseModel, Field, PrivateAttr


def get_llm_config():
    return metagpt_config.llm


global_session = None
TASK_COMPLETED = False
ROUND_INPUT_FILE = "round_input.txt"


def safe_count_text_tokens(llm, text: str) -> int:
    if not text:
        return 0
    try:
        return llm.count_tokens([{"role": "user", "content": text}])
    except Exception:
        return int(len(text) * 0.5)


def safe_count_output_tokens(llm, text: str) -> int:
    if not text:
        return 0
    model = getattr(llm, "model", None) or getattr(getattr(llm, "config", None), "model", None) or "gpt-4o"
    try:
        return count_output_tokens(text, model)
    except Exception:
        return int(len(text) * 0.5)


def set_round_input_file(path: str, reset: bool = False) -> None:
    global ROUND_INPUT_FILE
    if path is None:
        ROUND_INPUT_FILE = ""
        return
    if path:
        ROUND_INPUT_FILE = path
    if reset and ROUND_INPUT_FILE:
        output_dir = os.path.dirname(ROUND_INPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(ROUND_INPUT_FILE, "w", encoding="utf-8") as f:
            pass


def append_round_input(task_id: str, round_index: int, stage: str, content: str) -> None:
    if not ROUND_INPUT_FILE:
        return
    try:
        output_dir = os.path.dirname(ROUND_INPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        header = f"=== {timestamp} | task_id: {task_id} | round: {round_index} | stage: {stage} ===\n"
        with open(ROUND_INPUT_FILE, "a", encoding="utf-8") as f:
            f.write(header)
            f.write(content or "")
            if not (content or "").endswith("\n"):
                f.write("\n")
            f.write("=== END ===\n\n")
    except Exception as e:
        logger.error(f"Failed to append round input: {e}")


def format_conversation_history(conversation_output: List[Dict[str, Any]]) -> str:
    if not conversation_output:
        return ""

    grouped: Dict[int, Dict[str, str]] = {}
    for entry in conversation_output:
        round_index = entry.get("round")
        if round_index is None:
            continue
        role = entry.get("role")
        content = str(entry.get("content", ""))
        if round_index not in grouped:
            grouped[round_index] = {"user": "", "assistant": ""}
        if role in ("user", "assistant"):
            grouped[round_index][role] = content

    def _indent_block(text: str, prefix: str = "  ") -> str:
        if text == "":
            return ""
        return "\n".join(f"{prefix}{line}" for line in text.splitlines())

    blocks: List[str] = []
    for round_index in sorted(grouped.keys()):
        user_text = grouped[round_index].get("user", "")
        assistant_text = grouped[round_index].get("assistant", "")
        user_block = _indent_block(user_text)
        assistant_block = _indent_block(assistant_text)
        blocks.append(
            "\n".join(
                [
                    f"round {round_index}:",
                    "user:",
                    user_block,
                    "assistant:",
                    assistant_block,
                ]
            ).rstrip()
        )
    return "\n\n".join(blocks)


async def api_retry_with_backoff(func, *args, max_retries=5, base_delay=1, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            retries += 1
            is_rate_limit = any(term in str(e).lower() for term in ["rate limit", "too many", "throttl", "capacity", "429"])

            if retries >= max_retries:
                logger.error(f"Maximum number of retries reached ({max_retries})，The last mistake: {e}")
                raise

            delay = base_delay * (2 ** (retries - 1)) * (0.5 + random.random())

            if is_rate_limit:
                delay = delay * 2
                logger.warning(f"API rate limit detected. Retrying after... {delay:.2f} seconds ({retries}/{max_retries})")
            else:
                logger.warning(f"API call failed: {e}. Retrying in {delay:.2f} seconds ({retries}/{max_retries})")
            await asyncio.sleep(delay)


def reset_global_state():
    global TASK_COMPLETED
    TASK_COMPLETED = False
    logger.info("Global state reset")


def save_results_to_jsonl(results, output_file="output.jsonl"):
    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        print(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results to {output_file}: {e}")
        print(f"Error: Failed to save results to {output_file}: {e}")
    return results


def save_intermediate_results(results, output_file="output_intermediate.jsonl"):
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        intermediate_file = f"{os.path.splitext(output_file)[0]}_intermediate_{timestamp}.jsonl"

        with open(intermediate_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        logger.info(f"Intermediate results saved to {intermediate_file}")
    except Exception as e:
        logger.error(f"Failed to save intermediate results: {e}")
    return results


def append_result_to_jsonl(result, output_file="output.jsonl"):
    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        logger.info(f"Save individual results in real time to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save additional results: {e}")
        print(f"Error: Failed to append and save results: {e}")
        return False



class EvaluationResults(BaseModel):
    id: str
    score: List[float] = Field(default_factory=list)
    turn: int = 0
    rounds: int = 0
    conversation_output: List[Dict[str, str]] = Field(default_factory=list)
    save_mem: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_mem: List[Dict[str, Any]] = Field(default_factory=list)
    invar_mem: List[Dict[str, Any]] = Field(default_factory=list)
    instruct_tokens: List[int] = Field(default_factory=list)
    mem_tokens: List[int] = Field(default_factory=list)
    inva_tokens: List[int] = Field(default_factory=list)
    output_tokens: List[int] = Field(default_factory=list)
    input_eval_tokens: List[int] = Field(default_factory=list)
    output_eval_tokens: List[int] = Field(default_factory=list)
    round_time: List[float] = Field(default_factory=list)

    _round_start_times: Dict[int, float] = PrivateAttr(default_factory=dict)

    def add_score(self, score):
        self.score.append(score)
        self.rounds = len(self.score)
        print(f"Added score {score} for round {self.rounds}")

    def add_conversation_turn(self, user_content, assistant_content):
        self.conversation_output.append({"content": user_content, "role": "user", "round": self.rounds + 1})
        self.conversation_output.append({"content": assistant_content, "role": "assistant", "round": self.rounds + 1})
        self.turn += 1

    def add_save_mem(self, round_index, mem_list):
        self._upsert_round_mem(self.save_mem, round_index, mem_list)

    def add_retrieval_mem(self, round_index, mem_list):
        self._upsert_round_mem(self.retrieval_mem, round_index, mem_list)

    def add_invar_mem(self, round_index, mem_list):
        self._upsert_round_mem(self.invar_mem, round_index, mem_list)

    def add_prompt_tokens(self, round_index, instruct_tokens, mem_tokens, inva_tokens):
        self._ensure_round_length(self.instruct_tokens, round_index)
        self._ensure_round_length(self.mem_tokens, round_index)
        self._ensure_round_length(self.inva_tokens, round_index)
        self.instruct_tokens[round_index - 1] = int(instruct_tokens or 0)
        self.mem_tokens[round_index - 1] = int(mem_tokens or 0)
        self.inva_tokens[round_index - 1] = int(inva_tokens or 0)

    def add_output_tokens(self, round_index, output_tokens):
        self._ensure_round_length(self.output_tokens, round_index)
        self.output_tokens[round_index - 1] = int(output_tokens or 0)

    def add_eval_tokens(self, round_index, input_tokens, output_tokens):
        self._ensure_round_length(self.input_eval_tokens, round_index)
        self._ensure_round_length(self.output_eval_tokens, round_index)
        self.input_eval_tokens[round_index - 1] = int(input_tokens or 0)
        self.output_eval_tokens[round_index - 1] = int(output_tokens or 0)

    def mark_round_start(self, round_index):
        if round_index is None:
            return
        self._round_start_times[round_index] = time.time()

    def mark_round_end(self, round_index):
        if round_index is None:
            return
        start_time = self._round_start_times.pop(round_index, None)
        if start_time is None:
            return
        duration = time.time() - start_time
        self._ensure_round_length(self.round_time, round_index)
        self.round_time[round_index - 1] = duration

    @staticmethod
    def _upsert_round_mem(container, round_index, mem_list):
        if round_index is None:
            return
        mem_list = list(mem_list) if mem_list else []
        for entry in container:
            if entry.get("round") == round_index:
                entry["mem"] = mem_list
                return
        container.append({"round": round_index, "mem": mem_list})

    @staticmethod
    def _ensure_round_length(container, round_index):
        if round_index is None:
            return
        while len(container) < round_index:
            container.append(0)

    def to_dict(self):
        total_tokens = (
            sum(self.instruct_tokens)
            + sum(self.inva_tokens)
            + sum(self.mem_tokens)
            + sum(self.output_tokens)
            + sum(self.input_eval_tokens)
            + sum(self.output_eval_tokens)
        )
        total_time = sum(self.round_time)
        return {
            "id": self.id,
            "score": self.score,
            "turn": self.turn,
            "rounds": self.rounds,
            "conversation_output": self.conversation_output,
            "save_mem": self.save_mem,
            "retrieval_mem": self.retrieval_mem,
            "invar_mem": self.invar_mem,
            "tokens": {
                "insturct_tokens": self.instruct_tokens,
                "inva_tokens": self.inva_tokens,
                "mem_tokens": self.mem_tokens,
                "output_tokens": self.output_tokens,
                "input_eval_tokens": self.input_eval_tokens,
                "output_eval_tokens": self.output_eval_tokens,
                "total_tokens": [total_tokens],
            },
            "time": {
                "round_time": self.round_time,
                "total_time": [total_time],
            },

        }


    def summary(self):

        if not self.score:
            return "No evaluation data available."

        result = "\n" + "=" * 80 + "\n"
        result += f"EVALUATION SUMMARY FOR TASK: {self.id}\n"
        result += "=" * 80 + "\n"

        for round_num, score in enumerate(self.score, 1):
            result += f"Round {round_num}: Score {score}/10\n"

        numeric_scores = [s for s in self.score if isinstance(s, (int, float))]

        if self.rounds > 0 and numeric_scores:
            avg_score = sum(numeric_scores) / len(numeric_scores)
            result += "-" * 80 + "\n"
            result += f"Average Score: {avg_score:.1f}/10\n"
        result += "=" * 80 + "\n"

        return result


def read_jsonl(file_path):
    data_list = []
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            print(f"Error: File {file_path} not found")

            current_dir = os.getcwd()

            alternative_path = os.path.join(current_dir, file_path)
            if os.path.exists(alternative_path):
                logger.info(f"Found alternative file path: {alternative_path}")
                file_path = alternative_path
            else:
                logger.error(f"Couldn't find {file_path} in {current_dir}")
                return []

        print(f"Reading file: {file_path}")

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            line_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    task_data = {}
                    if "task_id" in data:
                        task_data["task_id"] = data["task_id"]
                    elif "id" in data:
                        task_data["task_id"] = data["id"]
                    else:
                        task_data["task_id"] = f"task_{line_count}"

                    if "conversation_input" in data:
                        task_data["conversation_input"] = data["conversation_input"]
                    else:
                        task_data["conversation_input"] = []

                    if "checklist" in data:
                        task_data["checklist"] = data["checklist"]
                    else:
                        task_data["checklist"] = []

                    print(f"Line {line_count}: {task_data['task_id']} - {len(task_data['conversation_input'])} inputs, {len(task_data['checklist'])} checklist items")
                    data_list.append(task_data)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON at line {line_count}: {line}. Error: {e}")
                    print(f"Error: Failed to parse JSON at line {line_count}: {line[:50]}... Error: {e}")

        logger.info(f"Successfully read {len(data_list)} data items from {file_path}")
        if data_list:
            logger.info(f"First data item: {data_list[0]}")
            print(f"First data item task ID: {data_list[0]['task_id']}")
        else:
            logger.warning(f"Data list from {file_path} is empty")
            print(f"Warning: Data list from {file_path} is empty")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        print(f"Error reading {file_path}: {e}")
        traceback.print_exc()

    return data_list


async def init_http_session():
    global global_session
    if global_session is None:

        conn = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
        global_session = aiohttp.ClientSession(connector=conn)
        logger.info("Initialize the global HTTP session.")
    return global_session


async def cleanup_resources():
    global global_session
    if global_session:
        await global_session.close()
        global_session = None
    gc.collect()
    logger.info("Resource cleanup completed.")
