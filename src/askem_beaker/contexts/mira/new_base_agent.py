# -*- coding: utf-8 -*-
import json
import logging
import re
import typing

from archytas.react import ReActAgent, Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool
from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool
from beaker_kernel.lib.agent import BeakerAgent
from beaker_kernel.lib.utils import togglable_tool

if typing.TYPE_CHECKING:
    from beaker_kernel.lib.context import BaseContext

logger = logging.getLogger(__name__)


class NewBaseAgent(BeakerAgent):

    context: "BaseContext"

    def __init__(
        self,
        context: "BaseContext" = None,
        tools: list = None,
        **kwargs,
    ):
        context.beaker_kernel.debug(
            "init-agent",
            {
                "debug": context.beaker_kernel.debug_enabled,
                "verbose": context.beaker_kernel.verbose,
            },
        )
        super().__init__(
            context=context,
            tools=tools,
            verbose=context.beaker_kernel.verbose,
            max_errors=5,
            spinner=None,
            rich_print=False,
            allow_ask_user=False,
            thought_handler=context.beaker_kernel.handle_thoughts,
            **kwargs,
        )

    def get_info(self):
        """ """
        info = {
            "name": self.__class__.__name__,
            "tools": {tool_name: tool_func.__doc__.strip() for tool_name, tool_func in self.tools.items()},
            "agent_prompt": self.__class__.__doc__.strip(),
        }
        return info

    def debug(self, event_type: str, content: typing.Any = None) -> None:
        self.context.beaker_kernel.debug(event_type=f"agent_{event_type}", content=content)
        logger.error(f"Archytas debug: {event_type} -- {content}")
        return super().debug(event_type=event_type, content=content)

    def display_observation(self, observation):
        content = {"observation": observation}
        parent_header = {}
        self.context.send_response(
            stream="iopub",
            msg_or_type="llm_observation",
            content=content,
            parent_header=parent_header,
        )
        return super().display_observation(observation)

    @togglable_tool("ENABLE_USER_PROMPT")
    async def ask_user(
        self,
        query: str,
        agent: AgentRef,
        loop: LoopControllerRef,
        react_context: ReactContextRef,
    ) -> str:
        """
        Sends a query to the user and returns their response

        Args:
            query (str): A fully grammatically correct question for the user.

        Returns:
            str: The user's response to the query.
        """
        return await self.context.beaker_kernel.prompt_user(query, parent_message=react_context.get("message", None))
