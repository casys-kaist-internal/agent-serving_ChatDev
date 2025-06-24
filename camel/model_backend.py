# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from abc import ABC, abstractmethod
from typing import Any, Dict

import openai
import tiktoken
import yaml

from camel.typing import ModelType
from camel.utils import get_model_token_limit, num_tokens_from_messages
from chatdev.statistics import prompt_cost
from chatdev.utils import log_visualize

try:
    from openai.types.chat import ChatCompletion

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version

import os

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if 'BASE_URL' in os.environ:
    BASE_URL = os.environ['BASE_URL']
else:
    BASE_URL = None


class ModelBackend(ABC):
    r"""Base class for different model backends.
    May be OpenAI API, a local LLM, a stub for unit tests, etc."""

    @abstractmethod
    def run(self, *args, **kwargs):
        r"""Runs the query to the backend model.

        Raises:
            RuntimeError: if the return value from OpenAI API
            is not a dict that is expected.

        Returns:
            Dict[str, Any]: All backends must return a dict in OpenAI format.
        """
        pass


class OpenAIModel(ModelBackend):
    r"""OpenAI API in a unified ModelBackend interface."""

    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict

        model_config_path = os.getenv('VLLM_MODEL_CONFIG_PATH')
        assert model_config_path is not None, "VLLM_MODEL_CONFIG_PATH environment variable is not set"

        model_config = yaml.safe_load(open(model_config_path, 'r'))
        # overwrite model_config['sampling_params'] with model_config_dict
        if sampling_params := model_config.get('sampling_params'):
            self.model_config_dict.update(sampling_params)

    def run(self, *args, **kwargs):
        string = "\n".join([message["content"] for message in kwargs["messages"]])
        # encoding = tiktoken.encoding_for_model(self.model_type.value)
        # num_prompt_tokens = len(encoding.encode(string))
        num_prompt_tokens = num_tokens_from_messages(kwargs["messages"], self.model_type)
        gap_between_send_receive = 15 * len(kwargs["messages"])
        num_prompt_tokens += gap_between_send_receive

        # num_max_token_map = {
        #     "gpt-3.5-turbo": 4096,
        #     "gpt-3.5-turbo-16k": 16384,
        #     "gpt-3.5-turbo-0613": 4096,
        #     "gpt-3.5-turbo-16k-0613": 16384,
        #     "gpt-4": 8192,
        #     "gpt-4-0613": 8192,
        #     "gpt-4-32k": 32768,
        #     "gpt-4-turbo": 100000,
        #     "gpt-4o": 4096, #100000
        #     "gpt-4o-mini": 16384, #100000
        #     "gemma3:27b-it-qat": 131072,
        # }
        num_max_token = get_model_token_limit(self.model_type)
        num_max_completion_tokens = num_max_token - num_prompt_tokens - 1000  # reserve 1000 tokens for safety
        self.model_config_dict['max_completion_tokens'] = num_max_completion_tokens

        log_visualize(
            "**[OpenAI_Usage_Info Send]**\nmodel: {}\napi_key: {}\nbase_url: {}\n".format(
            self.model_type.value, OPENAI_API_KEY, BASE_URL)
        )
        assert openai_new_api, "Old OpenAI API version is not supported. Please update to the new version."

        # Experimental, add base_url
        if BASE_URL:
            client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=BASE_URL,
            )
        else:
            client = openai.OpenAI(
                api_key=OPENAI_API_KEY
            )

        response = client.chat.completions.create(*args, **kwargs, model=self.model_type.value,
                                                    **self.model_config_dict)

        cost = prompt_cost(
            self.model_type.value,
            num_prompt_tokens=response.usage.prompt_tokens,
            num_completion_tokens=response.usage.completion_tokens
        )

        log_visualize(
            "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                response.usage.prompt_tokens, response.usage.completion_tokens,
                response.usage.total_tokens, cost))
        if not isinstance(response, ChatCompletion):
            raise RuntimeError("Unexpected return from OpenAI API")
        return response


class StubModel(ModelBackend):
    r"""A dummy model used for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        ARBITRARY_STRING = "Lorem Ipsum"

        return dict(
            id="stub_model_id",
            usage=dict(),
            choices=[
                dict(finish_reason="stop",
                     message=dict(content=ARBITRARY_STRING, role="assistant"))
            ],
        )


class ModelFactory:
    r"""Factory of backend models.

    Raises:
        ValueError: in case the provided model type is unknown.
    """

    @staticmethod
    def create(model_type: ModelType, model_config_dict: Dict) -> ModelBackend:
        default_model_type = ModelType.GPT_3_5_TURBO

        if model_type in {
            ModelType.GPT_3_5_TURBO,
            ModelType.GPT_3_5_TURBO_NEW,
            ModelType.GPT_4,
            ModelType.GPT_4_32k,
            ModelType.GPT_4_TURBO,
            ModelType.GPT_4_TURBO_V,
            ModelType.GPT_4O,
            ModelType.GPT_4O_MINI,
            ModelType.OLLAMA_MODEL,
            ModelType.VLLM_MODEL,
            None
        }:
            model_class = OpenAIModel
        elif model_type == ModelType.STUB:
            model_class = StubModel
        else:
            raise ValueError("Unknown model")

        if model_type is None:
            model_type = default_model_type

        # log_visualize("Model Type: {}".format(model_type))
        inst = model_class(model_type, model_config_dict)
        return inst
