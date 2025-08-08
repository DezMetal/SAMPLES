try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("The 'google-genai' library is not installed. Please run 'pip install google-genai'.")

import json
import os
from datetime import datetime
from typing import List, Dict, Union, Any
from dotenv import load_dotenv


class ContextManager:
    """Manages chat context for LLM interactions (basic truncation or AI summarization)."""

    def __init__(self, cfg: Dict[str, Any]):
        """
        Initializes with config.

        Args:
            cfg: Config dict.
        Raises:
            ValueError: If config is invalid.
        """
        self.cfg = self._val_cfg(cfg)
        self.verbose = False
        self._hist: Dict[str, List[Dict[str, Any]]] = {}
        self._arch: Dict[str, Dict[str, Any]] = {}
        self._len: Dict[str, int] = {}

        self._llm_client = None
        if self.cfg['mode'] == 'ai':
            llm_key = self.cfg.get('llm_key') or os.environ.get("GEMINI_API_KEY")
            if not llm_key:
                raise ValueError("GEMINI_API_KEY env var or 'llm_key' in config required for 'ai' mode.")
            try:
                self._llm_client = genai.Client(api_key=llm_key)
            except Exception as e:
                raise ValueError(f"Failed to initialize GenAI Client: {e}")

    @staticmethod
    def from_json_config(file_path: str):
        """Loads config from JSON and returns a ContextManager instance."""
        with open(file_path, 'r') as f:
            cfg = json.load(f)
        return ContextManager(cfg)

    def _val_cfg(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Validates config."""
        if 'mode' not in cfg or cfg['mode'] not in ["basic", "ai"]:
            raise ValueError("Config needs 'mode' ('basic'/'ai').")
        if 'max_active_msgs' not in cfg or not isinstance(cfg['max_active_msgs'], int) or cfg['max_active_msgs'] <= 0:
            raise ValueError("Config needs positive 'max_active_msgs' (int).")

        if cfg['mode'] == 'ai':
            if 'msg_count_sum_thresh' not in cfg or not isinstance(cfg['msg_count_sum_thresh'], int) or cfg['msg_count_sum_thresh'] <= 0:
                raise ValueError("AI mode needs positive 'msg_count_sum_thresh' (int).")
            if 'llm_mod' not in cfg or not isinstance(cfg['llm_mod'], str):
                raise ValueError("AI mode needs 'llm_mod' (str).")
            if 'keep_n' not in cfg:
                cfg['keep_n'] = 4
            elif not isinstance(cfg['keep_n'], int) or cfg['keep_n'] < 0:
                raise ValueError("'keep_n' must be non-negative (int).")
            if 'llm_sum_max_tok' not in cfg or not isinstance(cfg['llm_sum_max_tok'], int) or cfg['llm_sum_max_tok'] <= 0:
                raise ValueError("AI mode needs positive 'llm_sum_max_tok' (int).")
        return cfg

    def _est_tok_len(self, content: Union[str, List[Dict[str, Any]]]) -> int:
        """Estimates content token length (for AI mode LLM calls)."""
        if isinstance(content, str):
            return len(content.split())
        elif isinstance(content, list):
            total_len = 0
            for part in content:
                if part.get("text"):
                    total_len += self._est_tok_len(part["text"])
            return total_len
        return 0

    def set_initial_msgs(self, tid: str, msgs: List[Dict[str, Any]]):
        """
        Sets the initial messages for a thread.
        This should be called once per new thread.
        """
        self._hist[tid] = []
        self._arch[tid] = {"current": 0, "arch": []}
        self._len[tid] = 0
        for msg in msgs:
            self._hist[tid].append(msg)
            self._len[tid] += 1
        self._mng_ctx(tid)

    def add_msg(self, tid: str, role: str, content: Union[str, List[Dict[str, Any]]]):
        """Adds new message to context for a specific thread."""
        if tid not in self._hist:
            self._hist[tid] = []
            self._arch[tid] = {"current": 0, "arch": []}
            self._len[tid] = 0

        msg_parts = [{"text": content}] if isinstance(content, str) else content
        msg = {"role": role, "parts": msg_parts}
        self._hist[tid].append(msg)
        self._len[tid] += 1
        self._mng_ctx(tid)

    def _mng_ctx(self, tid: str):
        """Applies context management strategy for a specific thread."""
        if self.cfg['mode'] == 'basic':
            self._mng_basic(tid)
        elif self.cfg['mode'] == 'ai':
            self._mng_ai(tid)

    def _mng_basic(self, tid: str):
        """Truncates context by message count limit."""
        while self._len[tid] > self.cfg['max_active_msgs'] and len(self._hist[tid]) > 0:
            old_msg = self._hist[tid].pop(0)
            self._len[tid] -= 1

            timestamp = datetime.now().isoformat()
            self._arch[tid]["arch"].append({"ts": timestamp, "type": "trunc", "cont": old_msg})
            if self.verbose:
                print(f"Basic [{tid}]: Truncated. Current msg count: {self._len[tid]}") # Removed for module
        self._arch[tid]["current"] = self._len[tid]

    def _mng_ai(self, tid: str):
        """Summarizes older parts using LLM based on message count."""
        while len(self._hist[tid]) > self.cfg['msg_count_sum_thresh'] and len(self._hist[tid]) > self.cfg['keep_n']:
            msgs_to_sum = self._hist[tid][:-self.cfg['keep_n']]
            sum_in_txt = ""
            for msg in msgs_to_sum:
                role = msg['role']
                parts_txt = []
                for part in msg['parts']:
                    if part.get('text'):
                        parts_txt.append(part['text'])
                    else:
                        parts_txt.append(f"[{part.get('mimeType', 'NON-TEXT')}]")
                sum_in_txt += f"{role}: {' '.join(parts_txt)}\n"

            if not sum_in_txt.strip(): break

            if self.verbose:
                print(f"AI [{tid}]: Summarizing {len(msgs_to_sum)} msgs (approx {self._est_tok_len(sum_in_txt)} tokens)...") # Removed for module
            try:
                # Get the last summary from the archive if it exists
                last_summary = ""
                if self._arch[tid]["arch"]:
                    for entry in reversed(self._arch[tid]["arch"]):
                        if entry["type"] == "sum":
                            last_summary = entry["cont"]
                            break

                # Modify the summarization prompt to encourage progressive summarization
                summarization_prompt = (
                    f"You are summarizing a conversation. "
                    f"If there's a previous summary, update it with new information from the following messages. "
                    f"Otherwise, create a new summary. Focus on key events, decisions, and character interactions. "
                    f"Keep it concise and in the third person. "
                    f"Previous summary (if any): {last_summary}\n\n"
                    f"New messages to summarize:\n\n{sum_in_txt}"
                )

                sum_contents = [{"role": "user", "parts": [{"text": summarization_prompt}]}]

                gen_cfg = types.GenerateContentConfig(
                    max_output_tokens=self.cfg['llm_sum_max_tok']
                )

                response = self._llm_client.models.generate_content(
                    model=f"models/{self.cfg['llm_mod']}",
                    config=gen_cfg,
                    contents=sum_contents
                )
                sum_txt = response.text.strip()

                timestamp = datetime.now().isoformat()
                self._arch[tid]["arch"].append({"ts": timestamp, "type": "sum", "cont": sum_txt})

                # Replace summarized messages with a system message containing the new summary
                new_hist_head = [{"role": "system", "parts": [{"text": f"Prior summary: {sum_txt}"}]}]
                self._hist[tid] = new_hist_head + self._hist[tid][-self.cfg['keep_n']:]

                self._len[tid] = len(self._hist[tid])
                if self.verbose:
                    print(f"AI [{tid}]: Summarized. New msg count: {self._len[tid]}") # Removed for module

            except Exception as e:
                if self.verbose:
                    print(f"AI sum error [{tid}]: {e}. Skipping sum.") # Removed for module
                break
        self._arch[tid]["current"] = self._len[tid]

    def get_ctx(self, tid: str) -> List[Dict[str, Any]]:
        """Returns current active context for LLM for a specific thread."""
        return self._hist.get(tid, [])

    def get_arch(self, tid: str) -> Dict[str, Any]:
        """Returns archived history (summaries/truncated msgs) for a specific thread."""
        return self._arch.get(tid, {"current": 0, "arch": []})

    def get_len(self, tid: str) -> int:
        """Returns estimated current context message count for a specific thread."""
        return self._len.get(tid, 0)

    def save(self) -> Dict[str, Any]:
        """Saves current state of all threads."""
        return {"hist": self._hist, "arch": self._arch, "len": self._len}

    def load(self, state: Dict[str, Any]):
        """Loads saved state for all threads."""
        if not isinstance(state, dict): raise ValueError("State must be dict.")
        self._hist = state.get("hist", {})
        self._arch = state.get("arch", {})
        self._len = state.get("len", {})
        if self.verbose:
            print("State loaded for all threads.") # Removed for module
