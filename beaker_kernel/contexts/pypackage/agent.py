import json
import logging
import re
import typing
from archytas.react import Undefined

from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef, is_tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
# from beaker_kernel.lib.context import BaseContext

logger = logging.getLogger(__name__)

@toolset()
class Toolset:
    """My toolset"""


    @tool()
    async def retrieve_documentation(
        self, target: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        This function retrieves documentation about a Python module.

        You should use this to discover what is available within a package and determine the proper syntax and functionality on how to use the code.
        Querying against the module or package should list all avialable submodules and functions that exist, so you can use this to discover available
        functions and the query the function to get usage information.

        Args:
            target (str): Python package, module or function for which documentation is requested
        """
        code = f'''
try:
    import {target}
except ImportError:
    pass
help({target})
'''
        logger.error(code)
        r = await agent.context.evaluate(code)
        logger.error(r)
        return str(r)

    retrieve_documentation.__doc__

class PyPackageAgent(BaseAgent):
    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [Toolset]
        libraries = {

        }
        super().__init__(context, tools, **kwargs)