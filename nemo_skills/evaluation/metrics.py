# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import json
import logging
import re
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path

from nemo_skills.inference.server.model import get_model
from nemo_skills.utils import unroll_files

LOG = logging.getLogger(__file__)


class BaseMetrics(abc.ABC):
    @abc.abstractmethod
    def fill_up_missing(self):
        pass

    @abc.abstractmethod
    def is_incomplete(self, elem):
        pass

    @abc.abstractmethod
    def update(self, predictions, aggregation_mode):
        pass

    @abc.abstractmethod
    def get_metrics(self):
        pass

    @abc.abstractmethod
    def reset(self):
        pass

    def setup(self, input_files):
        pass

    def max_metrics_to_print(self):
        """No limit by default."""
        return None


def is_correct_judgement(judgement):
    if 'Judgement:' not in judgement:
        return False  # improper judgement format, so have to judge as false
    verdict = judgement.split('Judgement:')[-1].strip()
    return verdict.lower() == 'yes'


class MathMetrics(BaseMetrics):
    def setup(self, input_files):
        # checking if judgements are ready and fusing them with predictions
        # might get permission errors when running locally, since original file
        # is generated inside docker. Is there any way around that?
        for jsonl_file in unroll_files(input_files):
            if Path(jsonl_file + '-batch-request-id').exists():
                with open(jsonl_file + '-batch-request-id', 'rt', encoding='utf-8') as fin:
                    request_id = json.load(fin)['request_id']

                llm = get_model(server_type='openai', model='gpt-4-1106-preview')
                metadata, outputs = llm.get_batch_results(request_id)

                if outputs is None:
                    raise RuntimeError(f"Judgements are not ready yet! Current status: {metadata}")

                with open(jsonl_file, 'rt', encoding='utf-8') as fin:
                    predictions = [json.loads(line) for line in fin]

                with open(jsonl_file, 'wt', encoding='utf-8') as fout:
                    for prediction, output in zip(predictions, outputs):
                        prediction['judgement'] = output['generation']
                        fout.write(json.dumps(prediction) + '\n')

                Path(jsonl_file + '-batch-request-id').unlink()

    def __init__(self):
        self.reset()

    def fill_up_missing(self):
        # TODO: not clear how to fill up missing, since we don't know whether llm or sympy was used
        return {'predicted_answer': None, 'is_correct': False}

    def is_incomplete(self, elem):
        incomplete = 'predicted_answer' not in elem
        if not incomplete:
            incomplete = 'is_correct' not in elem and 'judgement' not in elem
        return incomplete

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "majority", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1
        # TODO: rename is_correct since it's only for sympy now?
        if 'is_correct' in predictions[0]:
            self.has_sympy = True
        if 'judgement' in predictions[0]:
            self.has_judge = True

        current_correct_sympy = False
        current_correct_judge = False

        if aggregation_mode == "best":
            if self.has_sympy:
                current_correct_sympy = any([elem['is_correct'] for elem in predictions])
            if self.has_judge:
                current_correct_judge = any([is_correct_judgement(elem['judgement']) for elem in predictions])
            if all([elem['predicted_answer'] is None for elem in predictions]):
                self.no_answer += 1
        elif aggregation_mode == "majority":
            # TODO: currently majority does not take into account equivalent answers written in a different way
            # TODO: DRY
            if self.has_sympy:
                valid_answers_and_results = [
                    (elem['predicted_answer'], elem['is_correct'])
                    for elem in predictions
                    if elem['predicted_answer'] is not None
                ]
                if len(valid_answers_and_results) == 0:
                    self.no_answer += 1
                else:
                    majority_result = Counter(valid_answers_and_results).most_common(1)[0][0]
                    current_correct_sympy = majority_result[1]
            if self.has_judge:
                valid_answers_and_results = [
                    (elem['predicted_answer'], is_correct_judgement(elem['judgement']))
                    for elem in predictions
                    if elem['predicted_answer'] is not None
                ]

                if len(valid_answers_and_results) == 0:
                    self.no_answer += 1
                else:
                    majority_result = Counter(valid_answers_and_results).most_common(1)[0][0]
                    current_correct_judge = majority_result[1]
        elif aggregation_mode == "first":
            if self.has_sympy:
                current_correct_sympy += predictions[0]['is_correct']
            if self.has_judge:
                current_correct_judge += is_correct_judgement(predictions[0]['judgement'])
            self.no_answer += predictions[0]['predicted_answer'] is None
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

        if self.has_sympy:
            self.correct_sympy += current_correct_sympy
        if self.has_judge:
            self.correct_judge += current_correct_judge
        if self.has_sympy and self.has_judge:
            self.both_correct += current_correct_sympy and current_correct_judge
            self.any_correct += current_correct_sympy or current_correct_judge
            if current_correct_sympy != current_correct_judge:
                LOG.debug(
                    "Discrepancy between symbolic (%s) and LLM checkers (%s).\n"
                    "Question: %s\nPredicted answer: %s\nExpected answer: %s\nLLM reasoning: %s\n",
                    bool(current_correct_sympy),
                    bool(current_correct_judge),
                    predictions[0]['problem'],
                    predictions[0]['predicted_answer'],
                    predictions[0]['expected_answer'],
                    predictions[0]['judgement'],
                )

    def get_metrics(self):
        metrics = {"num_entries": self.total}
        if self.has_sympy:
            metrics["symbolic_correct"] = self.correct_sympy / self.total * 100.0
        if self.has_judge:
            metrics["judge_correct"] = self.correct_judge / self.total * 100.0
        if self.has_sympy and self.has_judge:
            metrics["both_correct"] = self.both_correct / self.total * 100.0
            metrics["any_correct"] = self.any_correct / self.total * 100.0
        metrics["no_answer"] = self.no_answer / self.total * 100.0
        return metrics

    def reset(self):
        self.correct_sympy = 0
        self.correct_judge = 0
        self.both_correct = 0
        self.any_correct = 0
        self.no_answer = 0
        self.total = 0
        self.has_sympy = False
        self.has_judge = False


class CodeMetrics(BaseMetrics):
    def __init__(self):
        self.reset()

    def fill_up_missing(self):
        return {'is_correct': False, 'is_correct-plus': False}

    def is_incomplete(self, elem):
        return 'is_correct' not in elem or 'is_correct-plus' not in elem

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1
        if aggregation_mode == "best":
            self.total_correct += any([elem['is_correct'] for elem in predictions])
            self.total_correct_plus += any([elem['is_correct-plus'] for elem in predictions])
        elif aggregation_mode == "first":
            self.total_correct += predictions[0]['is_correct']
            self.total_correct_plus += predictions[0]['is_correct-plus']
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        return {
            "num_entries": self.total,
            "passing_base_tests": self.total_correct / self.total * 100.0,
            "passing_plus_tests": self.total_correct_plus / self.total * 100.0,
        }

    def reset(self):
        self.total_correct = 0
        self.total_correct_plus = 0
        self.total = 0


class IFMetrics(BaseMetrics):
    # loosely adapted from
    # https://github.com/google-research/google-research/blob/master/instruction_following_eval/evaluation_main.py

    required_keys = ['follow_instruction_list', 'instruction_id_list']

    def __init__(self):
        self.reset()

    def fill_up_missing(self):
        return {
            'loose_eval': {key: [] for key in self.required_keys},
            'strict_eval': {key: [] for key in self.required_keys},
        }

    def is_incomplete(self, elem):
        incomplete = 'loose_eval' not in elem or 'strict_eval' not in elem
        if incomplete:
            return True

        if any([key not in elem['loose_eval'] for key in self.required_keys]):
            return True

        if any([key not in elem['strict_eval'] for key in self.required_keys]):
            return True

        return False

    def _update_single_stat(self, stats_dict, elems):
        """Will update using the pass@k strategy (just pass a single-element list to get greedy)."""
        # has to be the same across all elements as they are solutions for the same question
        instruction_id_list = elems[0]['instruction_id_list']
        # computing "pass@k" score
        follow_instruction_list = elems[0]['follow_instruction_list']
        for elem in elems:
            follow_instruction_list = [
                follow_instruction_list[i] or elem['follow_instruction_list'][i]
                for i in range(len(follow_instruction_list))
            ]

        stats_dict['prompt']['total'] += 1
        if all(follow_instruction_list):
            stats_dict['prompt']['correct'] += 1

        stats_dict['instruction']['total'] += len(instruction_id_list)
        stats_dict['instruction']['correct'] += sum(follow_instruction_list)

        for instruction_id, followed_or_not in zip(instruction_id_list, follow_instruction_list):
            instruction_id = instruction_id.split(":")[0]
            stats_dict['tier0']['total'][instruction_id] += 1
            if followed_or_not:
                stats_dict['tier0']['correct'][instruction_id] += 1

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        if aggregation_mode == "best":
            self._update_single_stat(self.strict_stats, [pred['strict_eval'] for pred in predictions])
            self._update_single_stat(self.loose_stats, [pred['loose_eval'] for pred in predictions])
        elif aggregation_mode == "first":
            self._update_single_stat(self.strict_stats, [predictions[0]['strict_eval']])
            self._update_single_stat(self.loose_stats, [predictions[0]['loose_eval']])
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        prompt_total = self.strict_stats['prompt']['total']
        inst_total = self.strict_stats['instruction']['total']
        prompt_strict = self.strict_stats['prompt']['correct'] / prompt_total * 100.0
        inst_strict = self.strict_stats['instruction']['correct'] / inst_total * 100.0
        prompt_loose = self.loose_stats['prompt']['correct'] / prompt_total * 100.0
        inst_loose = self.loose_stats['instruction']['correct'] / inst_total * 100.0
        return {
            "num_prompts": prompt_total,
            "num_instructions": inst_total,
            "average_score": (prompt_strict + inst_strict + prompt_loose + inst_loose) / 4,
            "prompt_strict_accuracy": prompt_strict,
            "instruction_strict_accuracy": inst_strict,
            "prompt_loose_accuracy": prompt_loose,
            "instruction_loose_accuracy": inst_loose,
        }

    def reset(self):
        # the original code also has a deeper breakdown into tier1 scores,
        # but that's probably too much for us to track at this stage
        self.strict_stats = {
            "prompt": {"total": 0, "correct": 0},
            "instruction": {"total": 0, "correct": 0},
            "tier0": {"total": defaultdict(int), "correct": defaultdict(int)},
        }
        self.loose_stats = {
            "prompt": {"total": 0, "correct": 0},
            "instruction": {"total": 0, "correct": 0},
            "tier0": {"total": defaultdict(int), "correct": defaultdict(int)},
        }


class ArenaMetrics(BaseMetrics):
    def __init__(self):
        self.reset()

    def setup(self, input_files):
        # checking if judgements are ready and fusing them with predictions
        # might get permission errors when running locally, since original file
        # is generated inside docker. Is there any way around that?
        for jsonl_file in unroll_files(input_files):
            if Path(jsonl_file + '-batch-request-id').exists():
                with open(jsonl_file + '-batch-request-id', 'rt', encoding='utf-8') as fin:
                    request_id = json.load(fin)['request_id']

                llm = get_model(server_type='openai', model='gpt-4-1106-preview')
                metadata, outputs = llm.get_batch_results(request_id)

                if outputs is None:
                    raise RuntimeError(f"Judgements are not ready yet! Current status: {metadata}")

                with open(jsonl_file, 'rt', encoding='utf-8') as fin:
                    predictions = [json.loads(line) for line in fin]

                with open(jsonl_file, 'wt', encoding='utf-8') as fout:
                    for idx, output in enumerate(outputs):
                        if idx % 2 == 0:
                            prediction = predictions[idx // 2]
                            prediction['judgement-gen-base'] = output['generation']
                        else:
                            prediction['judgement-base-gen'] = output['generation']
                            fout.write(json.dumps(prediction) + '\n')

                Path(jsonl_file + '-batch-request-id').unlink()

    def _get_judge_score(self, judgment):
        # adapted from https://github.com/lm-sys/arena-hard-auto/blob/main/gen_judgment.py
        pattern = re.compile('\[\[([AB<>=]+)\]\]')
        matches = pattern.findall(judgment)
        matches = [m for m in matches if m != ""]
        if len(set(matches)) == 0:
            return None
        elif len(set(matches)) == 1:
            return matches[0].strip("\n")
        else:
            return None

    def fill_up_missing(self):
        return {'judgement-gen-base': '', 'judgement-base-gen': '', 'generation': ''}

    def is_incomplete(self, elem):
        return 'judgement-gen-base' not in elem or 'judgement-base-gen' not in elem or 'generation' not in elem

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1
        self.scores.append([])
        if aggregation_mode == "best":
            judge_scores = [self._get_judge_score(elem['judgement-gen-base']) for elem in predictions]
            # adding the best score out of all the generations
            possible_scores = ['A>>B', 'A>B', 'A=B', 'B>A', 'B>>A']
            for possible_score in possible_scores:
                # picking the best available score
                if any([score == possible_score for score in judge_scores]):
                    self.scores[-1].append(possible_score)
                    best_id = judge_scores.index(possible_score)
                    self.lengths += len(predictions[best_id]['generation'])
                    break
            else:
                self.scores[-1].append(None)  # in case judge didn't generate a valid score

            judge_scores = [self._get_judge_score(elem['judgement-base-gen']) for elem in predictions]
            # second score is grading swapped answers, so we iterate from the end
            for possible_score in possible_scores[::-1]:
                # picking the best available score
                if any([score == possible_score for score in judge_scores]):
                    self.scores[-1].append(possible_score)
                    best_id = judge_scores.index(possible_score)
                    self.lengths += len(predictions[best_id]['generation'])
                    break
            else:
                self.scores[-1].append(None)  # in case judge didn't generate a valid score
        elif aggregation_mode == "first":
            self.lengths += len(predictions[0]['generation'])
            self.scores[-1] = [
                self._get_judge_score(predictions[0]['judgement-gen-base']),
                self._get_judge_score(predictions[0]['judgement-base-gen']),
            ]
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        from nemo_skills.evaluation.arena_utils import get_aggregate_score

        metrics = {'num_entries': self.total}
        metrics.update(get_aggregate_score(self.scores))
        metrics['avg_response_length'] = self.lengths / self.total
        return metrics

    def reset(self):
        self.scores = []  # list of lists
        self.lengths = 0
        self.total = 0


class MtBenchMetrics(BaseMetrics):
    def __init__(self):
        self.reset()

    def setup(self, input_files):
        # checking if judgements are ready and fusing them with predictions
        # might get permission errors when running locally, since original file
        # is generated inside docker. Is there any way around that?
        for jsonl_file in unroll_files(input_files):
            if Path(jsonl_file + '-batch-request-id').exists():
                with open(jsonl_file + '-batch-request-id', 'rt', encoding='utf-8') as fin:
                    request_id = json.load(fin)['request_id']

                llm = get_model(server_type='openai', model='gpt-4-0125-preview')
                metadata, outputs = llm.get_batch_results(request_id)

                if outputs is None:
                    raise RuntimeError(f"Judgements are not ready yet! Current status: {metadata}")

                with open(jsonl_file, 'rt', encoding='utf-8') as fin:
                    predictions = [json.loads(line) for line in fin]

                with open(jsonl_file, 'wt', encoding='utf-8') as fout:
                    for idx, output in enumerate(outputs):
                        if idx % 2 == 0:
                            prediction = predictions[idx // 2]
                            prediction['judgement-turn1'] = output['generation']
                        else:
                            prediction['judgement-turn2'] = output['generation']
                            fout.write(json.dumps(prediction) + '\n')

                Path(jsonl_file + '-batch-request-id').unlink()

    def fill_up_missing(self):
        return {'judgement-turn1': '', 'judgement-turn2': ''}

    def is_incomplete(self, elem):
        return 'judgement-turn1' not in elem or 'judgement-turn2' not in elem

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1
        if aggregation_mode == "best":
            # TODO: might all have missing judgement?
            rating1 = max(
                int(re.search(r'Rating: \[\[(\d+)\]\]', elem['judgement-turn1']).group(1))
                for elem in predictions
                if re.search(r'Rating: \[\[(\d+)\]\]', elem['judgement-turn1'])
            )
            rating2 = max(
                int(re.search(r'Rating: \[\[(\d+)\]\]', elem['judgement-turn2']).group(1))
                for elem in predictions
                if re.search(r'Rating: \[\[(\d+)\]\]', elem['judgement-turn2'])
            )
            category = predictions[0]['category']
            self.scores[category].append((rating1, rating2))
        elif aggregation_mode == "first":
            rating1_match = re.search(r'Rating: \[\[(\d+)\]\]', predictions[0]['judgement-turn1'])
            rating1 = int(rating1_match.group(1)) if rating1_match else None
            rating2_match = re.search(r'Rating: \[\[(\d+)\]\]', predictions[0]['judgement-turn2'])
            rating2 = int(rating2_match.group(1)) if rating2_match else None
            category = predictions[0]['category']
            self.scores[category].append((rating1, rating2))
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        metrics = {'num_entries': self.total}

        # Calculate average scores across all categories for each turn
        all_ratings1 = [r1 for scores in self.scores.values() for r1, _ in scores if r1 is not None]
        all_ratings2 = [r2 for scores in self.scores.values() for _, r2 in scores if r2 is not None]

        all_ratings = all_ratings1 + all_ratings2
        if all_ratings:
            metrics['average'] = sum(all_ratings) / len(all_ratings)

        if all_ratings1:
            metrics['average_turn1'] = sum(all_ratings1) / len(all_ratings1)
        if all_ratings2:
            metrics['average_turn2'] = sum(all_ratings2) / len(all_ratings2)

        none_count_turn1 = 0
        none_count_turn2 = 0
        for category, scores in self.scores.items():
            if not scores:
                continue
            ratings1 = [r1 for r1, _ in scores if r1 is not None]
            ratings2 = [r2 for _, r2 in scores if r2 is not None]
            none_count_turn1 += sum(1 for r1, _ in scores if r1 is None)
            none_count_turn2 += sum(1 for _, r2 in scores if r2 is None)
            metrics[f'{category}_turn1'] = sum(ratings1) / len(ratings1)
            metrics[f'{category}_turn2'] = sum(ratings2) / len(ratings2)
        metrics["missing_rating_turn1"] = none_count_turn1
        metrics["missing_rating_turn2"] = none_count_turn2
        print("Please see metrics.json for MT-bench per-category breakdown")
        return metrics

    def reset(self):
        self.scores = defaultdict(list)
        self.total = 0

    def max_metrics_to_print(self):
        """We are only printing the averages, but all other metrics can still be found in metrics.json"""
        return 4


class Lean4Metrics(BaseMetrics):
    def setup(self, input_files):
        pass

    def __init__(self):
        self.reset()

    def fill_up_missing(self):
        return {'predicted_answer': None, 'proof_status': "failed"}

    def is_incomplete(self, elem):
        incomplete = 'predicted_answer' not in elem
        if not incomplete:
            incomplete = 'proof_status' not in elem
        return incomplete

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1

        if aggregation_mode == "best":
            self.correct_proof += any([elem['proof_status'] == "completed" for elem in predictions])
            if all([elem['proof_status'] == "timeout" for elem in predictions]):
                self.timeout_error += 1
        elif aggregation_mode == "first":
            self.correct_proof += predictions[0]['proof_status'] == "completed"
            self.timeout_error += predictions[0]['proof_status'] == "timeout"
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        metrics = {"num_entries": self.total}
        metrics["lean4_correct"] = self.correct_proof / self.total * 100.0
        metrics["timeout_error"] = self.timeout_error / self.total * 100.0
        return metrics

    def reset(self):
        self.correct_proof = 0
        self.timeout_error = 0
        self.total = 0


class AnswerJudgementMetrics(BaseMetrics):
    def __init__(self):
        self.reset()

    def fill_up_missing(self):
        return {'judgement': "Judgement: No", 'expected_judgement': "Judgement: No"}

    def is_incomplete(self, elem):
        return 'judgement' not in elem or 'expected_judgement' not in elem

    def update(self, predictions, aggregation_mode):
        """Updating the evaluation results with the current element.

        Args:
            predictions (list[dict]): aggregated predictions across all generations.
                The content of the file is benchmark specific.
            aggregation_mode (str): "best", "majority", "first", etc. Might vary by benchmark.
        """
        # this shouldn't do any heavy calculation, but just read the metric from existing json entry
        # all the heavy lifting should be done in the evaluation script
        self.total += 1
        if aggregation_mode == "best":
            is_correct = any(
                [
                    is_correct_judgement(elem['judgement']) == is_correct_judgement(elem['expected_judgement'])
                    for elem in predictions
                ]
            )
            self.total_correct += is_correct
            if not is_correct:
                if is_correct_judgement(predictions[0]['judgement']):
                    self.fp_count += 1
                else:
                    self.fn_count += 1
        elif aggregation_mode == "majority":
            answers = [is_correct_judgement(elem['judgement']) for elem in predictions]
            majority_judgement = Counter(answers).most_common(1)[0]
            is_correct = majority_judgement == is_correct_judgement(predictions[0]['expected_judgement'])
            self.total_correct += is_correct
            if not is_correct:
                if majority_judgement:
                    self.fp_count += 1
                else:
                    self.fn_count += 1
        elif aggregation_mode == "first":
            is_correct = is_correct_judgement(predictions[0]['judgement']) == is_correct_judgement(
                predictions[0]['expected_judgement']
            )
            self.total_correct += is_correct
            if not is_correct:
                if is_correct_judgement(predictions[0]['judgement']):
                    self.fp_count += 1
                else:
                    self.fn_count += 1
        else:
            raise ValueError(f"Unsupported mode {aggregation_mode}")

    def get_metrics(self):
        return {
            "num_entries": self.total,
            "correct_judgements": self.total_correct / self.total * 100.0,
            "false_positives": self.fp_count / self.total * 100.0,
            "false_negatives": self.fn_count / self.total * 100.0,
        }

    def reset(self):
        self.total_correct = 0
        self.fp_count = 0
        self.fn_count = 0
        self.total = 0


def read_predictions(predictions, evaluator, allow_incomplete=False):
    data = []
    for prediction in predictions:
        if not prediction:  # could have missing predictions
            if not allow_incomplete:
                raise RuntimeError("Some data is missing!")
            data.append(evaluator.fill_up_missing())
            continue
        prediction_dict = json.loads(prediction)
        if not prediction_dict:
            if not allow_incomplete:
                raise RuntimeError("Some data is missing!")
            data.append(evaluator.fill_up_missing())
            continue
        if evaluator.is_incomplete(prediction_dict):
            if not allow_incomplete:
                raise RuntimeError("Some data is missing!")
            data.append(evaluator.fill_up_missing())
            continue
        data.append(prediction_dict)

    return data


def compute_metrics(
    input_files,
    metrics_calculator,
    allow_incomplete=False,
    max_samples=-1,
    aggregation_mode='first',
):
    metrics_calculator.reset()
    metrics_calculator.setup(input_files)

    file_handles = [open(file, "rt", encoding="utf-8") for file in unroll_files(input_files)]
    for idx, predictions in enumerate(zip_longest(*file_handles)):
        if idx == max_samples:
            break
        data = read_predictions(predictions, metrics_calculator, allow_incomplete)
        metrics_calculator.update(data, aggregation_mode)

    for file_handle in file_handles:
        file_handle.close()

    return metrics_calculator.get_metrics()
