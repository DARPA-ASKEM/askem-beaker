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


class MiraModelEditAgent(BaseAgent):
    """
    LLM agent used for working with the Mira Modeling framework ("mira_model" package) in Python 3.
    This will be used to find pre-written functions which will be used to edit a model.

    A mira model is made up of multiple templates that are merged together like ...

    An example mira model will look like this when encoded in json:
    ```
    {
      "id": "foo",
      "bar": "foobar",
      ...
    }

    Instead of manipulating the model directly, the agent will always return code that will be run externally in a jupyter notebook.

    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        super().__init__(context, tools, **kwargs)

    @tool()
    async def replace_template_name(self, old_name: str, new_name: str, model: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a template that is part of a model.

        Args:
            model (str): The variable name identifier of the model. If not known or specified, the default value of `model` should be used.
            old_name (str): The old/existing name of the template as it exists in the model before changing.
            new_name (str): The name that the template should be changed to.
        """
        code = agent.context.get_code("replace_template_name", {"model": model, "old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def replace_state_name(self, template_name: str, old_name: str, new_name: str, model: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a state name within a template that is part of a model.

        Args:
            model (str): The variable name identifier of the model. If not known or specified, the default value of `model` should be used.
            template_name (str): the template within the model where these changes will be made
            old_name (str): The old/existing name of the state as it exists in the model before changing.
            new_name (str): The name that the state should be changed to.
        """
        code = agent.context.get_code("replace_state_name", {"model": model, "template_name": template_name, "old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
  
    @tool()
    async def add_natural_conversion_template(self,
        subject_name: str, 
        subject_initial_value: float,
        outcome_name: str, 
        outcome_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural conversion to the model. 
        A natural conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is recieving population from the transition.
        The transition rate may only depend on the subject state.
        
        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v" 
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression.

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number assosiated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter. 
            parameter_units (str): The units assosiated with the parameter. 
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """
        
        code = agent.context.get_code("add_natural_conversion_template", {
            "subject_name": subject_name, 
            "subject_initial_value": subject_initial_value,
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_conversion_template(self,
        subject_name: str, 
        subject_initial_value: float,
        outcome_name: str, 
        outcome_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled conversion to the model. 
        A controlled conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is recieving population from the transition.
        This transition rate depends on a controller state. This controller state can be an existing or new state in the model.
        
        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v. v depends on I"
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression and I is the controller_name. 

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number assosiated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_conversion_template", {
            "subject_name": subject_name, 
            "subject_initial_value": subject_initial_value,
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_natural_production_template(self,
        outcome_name: str, 
        outcome_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural production to the model. 
        A natural production is a template that contains one state which is recieving population by one transition. The transition will not depend on any state.

        An example of this would be "Add a new transition from the transition rec to S with a rate of f."
        Where S is the outcome state, rec is the template_name, and f is the template_expression

        Args:
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_natural_production_template", {
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_production_template(self,
        outcome_name: str, 
        outcome_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled production to the model. 
        A controlled production is a template that contains one state which is recieving population by one transition. This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from the transition rec to S with a rate of f. f depends on R. "
        Where S is the outcome state, rec is the template_name, f is the template_expression and the controller is R.

        Args:
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_production_template", {
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_natural_degradation_template(self,
        subject_name: str, 
        subject_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural degradation to the model. 
        A natural degradation is a template that contains one state in which the population is leaving through one transition. The transition may only depend on the subject state.

        An example of this would be "Add a new transition from state S to transition rec with a rate of v."
        Where S is the subject state, rec is the template_name, and v is the template_expression.

        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_natural_degradation_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_degradation_template(self,
        subject_name: str, 
        subject_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: str,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled degradation to the model. 
        A controlled degradation is a template that contains one state in which the population is leaving through one transition. This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from S to rec with a rate of v. v depends on R."
        Where S is the subject state, rec is the template_name, v is the template_expression and R is the controller state.

        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (str): the value of the parameter provided by the user.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_degradation_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
