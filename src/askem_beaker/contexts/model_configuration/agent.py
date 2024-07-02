import json
import logging
import re

import requests
from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


class ConfigEditAgent(BaseAgent):
    """
    LLM agent used for working editing model configuration in Python 3.
    This will be used to update model configurations. The name of the model configuration variable is `model_config`.

    Any time the user asks to make edits to the model configuration, the agent will generate the code to be executed in a Jupyter Notebook cell which updates
    a JSON object in accordance with the above schema. The user will be able to update the model configuration's parameters, initial conditions, and other attributes.
    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        super().__init__(context, tools, **kwargs)

#     @tool()
#     async def describe_configuration(
#         self, query: str, agent: AgentRef, loop: LoopControllerRef
#     ) -> None:
#         """
#         This tool is used to answer questions about the model configuration. It fetches the model configuration for analysis.

#         Input is a full grammatically correct question about or request for an action to be performed on the loaded model configuration.

#         Args:
#             query (str): A fully grammatically correct question about the current model configuration.

#         """
# #         prompt = f"""
# # You are a scientific assistant helping answer questions about a model configuration.

# # Model configurations are defined by a specific model configuration JSON schema and are JSON objects themselves.

# # The current configuration is:
# # {agent.context.model_config}

# # Please analyze the configuration and answer the user's question.
# # """       
#         code = agent.context.get_code("load_config")
#         model_config = await agent.context.evaluate(code)
#         return model_config

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated  code to be run in an interactive Jupyter notebook for the purpose of modifying a model configuration.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model configuration.

        Args:
            query (str): A fully grammatically correct question about the current model configuration.

        """
        prompt = f"""
You are a programmer writing code to help with writing model configuration updates and edits in Python.

Model configurations are defined by a specific model configuration JSON schema and are JSON objects themselves. Therefore, code to update them
can be considered updates to the dictionary/JSON of the model configuration.

You should always operate on the assumption that the model configuration exists, is schema compliant and is stored in a variable named `model_config`.

It will comply with the schema:
{await agent.context.get_schema()}

The current configuration is:
{agent.context.model_config}

Please write code that satisfies the user's request below.

Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
No addtional text is needed in the response, just the code block.
"""

        llm_response = await agent.oneshot(prompt=prompt, query=query)
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", llm_response)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": self.context.subkernel.KERNEL_NAME,
                "content": code.strip(),
            }
        )
        return result