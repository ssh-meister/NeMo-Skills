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


import nemo.collections.nlp.data.language_modeling.megatron.gpt_sft_chat_dataset as gpt_sft_chat_dataset
import torch.multiprocessing as mp

# adding custom metric
from code_generation_accuracy import CodeGenerationAccuracy
from hydra.utils import instantiate
from nemo.collections.common.metrics.metric_string_to_torchmetric import MetricStringToTorchMetric
from nemo.collections.nlp.models.language_modeling.megatron_gpt_sft_model import MegatronGPTSFTModel
from nemo.collections.nlp.parts.megatron_trainer_builder import MegatronLMPPTrainerBuilder
from nemo.core.config import hydra_runner
from nemo.utils import logging
from nemo.utils.exp_manager import exp_manager
from omegaconf.omegaconf import OmegaConf

from nemo_skills.inference.inference_strategy import CodeExecutionStrategy

MetricStringToTorchMetric["code_generation_accuracy"] = CodeGenerationAccuracy


"""Script to start SFT training"""

OmegaConf.register_new_resolver("multiply", lambda x, y: x * y, replace=True)
OmegaConf.register_new_resolver("int_div", lambda x, y: x // y, replace=True)

mp.set_start_method("spawn", force=True)


@hydra_runner(config_path=".", config_name="sft_config")
def main(cfg) -> None:
    logging.info("\n\n************** Experiment configuration ***********")
    logging.info(f'\n{OmegaConf.to_yaml(cfg)}')

    trainer = MegatronLMPPTrainerBuilder(cfg).create_trainer()
    exp_manager(trainer, cfg.exp_manager)

    model_cfg = MegatronGPTSFTModel.merge_cfg_with(cfg.model.restore_from_path, cfg)
    model = MegatronGPTSFTModel.restore_from(cfg.model.restore_from_path, model_cfg, trainer=trainer)

    if cfg.model.data.validation_ds.metric.name == 'code_generation_accuracy':
        model.val_metric[0].init_sandbox(**cfg.model.data.validation_ds.metric.sandbox_cfg)
    if 'inference' in cfg.model:
        config = OmegaConf.to_container(cfg.model.inference, resolve=True)
        # registering code execution inference strategy
        config['strategy'] = CodeExecutionStrategy(
            sandbox_cfg=cfg.model.data.validation_ds.metric.sandbox_cfg, model=model
        )  # instantiate(cfg.model.inference.strategy)
        model.set_inference_config(config)

    trainer.fit(model)


if __name__ == "__main__":
    main()
