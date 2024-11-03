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

import hydra
import time

from nemo_skills.utils import setup_logging

import sys
sys.path.append("/ameister/StreamPR/NeMo-speech-data-processor")
from sdp.run_processors import SDPRunner


@hydra.main(version_base=None, config_path="data_preparation_utils/", config_name="prepare_sft_data.yaml")
def main(cfg):
    sdp = SDPRunner(cfg)
    sdp.run()


if __name__ == "__main__":
    start = time.time()
    setup_logging()
    main()
    end = time.time()
    print(f"Execution finished in {end - start} seconds.")
