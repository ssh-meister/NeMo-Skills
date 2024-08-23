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

import logging

import torch
from torchmetrics import Metric

from nemo_skills.code_execution.math_grader import extract_answer
from nemo_skills.code_execution.sandbox import get_sandbox

LOG = logging.getLogger(__name__)


class CodeGenerationAccuracy(Metric):
    """How many of the generated programs are correct."""

    def __init__(self, dist_sync_on_step=False, *args, **sandbox_cfg):
        super().__init__(dist_sync_on_step=dist_sync_on_step)
        self.add_state("correct", default=torch.tensor(0.0, device='cuda'), dist_reduce_fx="sum")
        self.add_state("total", default=torch.tensor(0, device='cuda'), dist_reduce_fx="sum")
        self.sandbox = get_sandbox(**sandbox_cfg)

    def compute(self):
        return self.correct.float() / self.total

    def update(self, pred: str, target):
        try:
            answer = extract_answer(pred)
            correct = self.sandbox.is_output_correct(answer, target)
        except Exception as e:  # TODO: proper logging
            print("Some error occured during code verification!")
            print(e)
            correct = False
        self.correct += correct
        self.total += 1
