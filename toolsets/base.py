from __future__ import annotations
import codecs
import copy
import datetime
import json
import logging
import os
import re
import requests
import tempfile
from typing import Optional, Callable, List, Tuple, TYPE_CHECKING

from jupyter_kernel_proxy import JupyterMessage
from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

if TYPE_CHECKING:
    from llmkernel.kernel import PythonLLMKernel

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


class BaseToolset:
    """ """

    # Typing
    code: dict[str, str]
    intercepts: dict[str, tuple[Callable, str]]
    kernel: PythonLLMKernel

    # TODO: Find a better way to organize and store these items. Maybe store as files and load into codeset dict at init?
    CODE = {
        "python": {},
    }

    def __init__(self, kernel=None, language="python", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kernel = kernel
        # TODO: add checks and protections around loading codeset
        self.codeset = self.CODE[language]

    async def post_execute(self, message: JupyterMessage) -> None:
        ...

    async def context(self) -> str:
        ...


#     @tool()
#     async def generate_python_code(
#         self, query: str, agent: AgentRef, loop: LoopControllerRef
#     ) -> str:
#         """
#         Generated Python code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Pandas Dataframe.

#         Input is a full grammatically correct question about or request for an action to be performed on the loaded dataframe.

#         Assume that the dataframe is already loaded and has the variable name `df`.

#         Args:
#             query (str): A fully grammatically correct queistion about the current dataset.

#         Returns:
#             str: A LLM prompt that should be passed evaluated.
#         """
#         # set up the agent
#         # str: Valid and correct python code that fulfills the user's request.
#         df_info = await self.describe_dataset()
#         prompt = f"""
# You are a programmer writing code to help with scientific data analysis and manipulation in Python.

# Please write code that satisfies the user's request below.

# You have access to a variable name `df` that is a Pandas Dataframe with the following structure:
# {df_info}

# If you are asked to modify or update the dataframe, modify the dataframe in place, keeping the updated variable to still be named `df`.

# You also have access to the libraries pandas, numpy, scipy, matplotlib.

# Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
# You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
# No addtional text is needed in the response, just the code block.
# """

#         llm_response = agent.oneshot(prompt=prompt, query=query)
#         loop.set_state(loop.STOP_SUCCESS)
#         preamble, code, coda = re.split("```\w*", llm_response)
#         result = json.dumps(
#             {
#                 "action": "code_cell",
#                 "language": "python",
#                 "content": code.strip(),
#             }
#         )
#         return result
