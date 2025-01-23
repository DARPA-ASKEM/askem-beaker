import json
import logging
import re

import requests
from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage
from typing import Collection, Iterable, Optional, Tuple

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

    Instead of manipulating the model directly, the agent will always return code that will be run externally in a jupyter notebook
    except in the case of inspect_template_model where the agent will return the model.

    The template model will be the variable called `model`. If you are asked to perform multiple edits to a model at once you should consider
    which tools to use and in which order to use them.

    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        super().__init__(context, tools, **kwargs)

    @tool()
    async def inspect_template_model(self, agent: AgentRef):
        """
        This tool is used to inspect the template model to learn about its transitions, parameters, rates, states, observables, etc.
        """
        code = agent.context.get_code("inspect_template_model", {"model_name": "model"})
        response = await agent.context.evaluate(code)
        return response["return"]
    
    @tool()
    async def replace_template_name(self, old_name: str, new_name: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a template that is part of a model.

        Args:
            old_name (str): The old/existing name of the template as it exists in the model before changing.
            new_name (str): The name that the template should be changed to.
        """
        code = agent.context.get_code("replace_template_name", {"old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def remove_templates(self, template_names: list[str], agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to remove existing template(s) that are part of a model.

        Args:
            template_names (list[str]): This is a list of template names that are to be removed.
        """
        code = agent.context.get_code("remove_templates", template_names)
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def replace_state_name(self, template_name: str, old_name: str, new_name: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a state name within a template that is part of a model.

        Args:
            template_name (str): the template within the model where these changes will be made
            old_name (str): The old/existing name of the state as it exists in the model before changing.
            new_name (str): The name that the state should be changed to.
        """
        code = agent.context.get_code("replace_state_name", {"template_name": template_name, "old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_observable(self, new_id: str, new_name: str, new_expression: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add an observable.

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            new_id (str): The new ID provided for the observable. If this is not provided the value for new_name should be used
            new_name (str): The new name provided for the observable. If this is not provided for the new_id should be used.
            new_expression (str): The math expression that represents the observable as a function.
        """
        code = agent.context.get_code("add_observable", {"new_id": new_id, "new_name": new_name, "new_expression": new_expression})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
    
    @tool()
    async def add_observable_pattern(self, new_name: str, 
                                     identifier_keys: list[str], 
                                     identifier_values: list[str],
                                     context_keys: list[str],
                                     context_values: list[str],
                                     agent: AgentRef, 
                                     loop: LoopControllerRef):
        """
        This tool is used when a user wants to add an observable via a complex pattern. You should inspect the model BEFORE using this tool
        so that you can properly map the users request to the correct identifiers and contexts in the model. Typically the identifier key
        will be something like "ido" and the identifier value will be something like "0000514". Context keys will be the name of the strata context (e.g. "Age")
        and the values will be the value for that strata context (e.g. "youth"). 

        When the user specifies a high level state (such as Infected) this would be specified via the identifiers; when the user specifies 
        a strata (such as "youth") that is specified via the context.

        Args:
            new_name (str): The new name provided for the observable. If this is not provided something intuitive should be set.
            identifier_keys (list[str]): The keys for the identifiers that will be used in the observable.
            identifier_values (list[str]): The values for the identifiers that will be used in the observable.
            context_keys (list[str]): The keys for the context that will be used in the observable.
            context_values (list[str]): The values for the context that will be used in the observable.
        """
        identifier_dict = dict(zip(identifier_keys, identifier_values))
        context_dict = dict(zip(context_keys, context_values))
        code = agent.context.get_code("add_observable_pattern", 
                                      {"new_name": new_name,
                                       "identifier_keys": identifier_keys,
                                       "identifier_values": identifier_values,
                                       "context_keys": context_keys,
                                       "context_values": context_values,
                                       "identifier_dict": identifier_dict,
                                       "context_dict": context_dict}
                                      )
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )    

    @tool()
    async def remove_observable(self, remove_id: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to remove an observable.

        Args:
            remove_id (str): The existing observable id to be removed.
        """
        code = agent.context.get_code("remove_observable", {"remove_id": remove_id })
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural conversion to the model.
        A natural conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is receiving population from the transition.
        The transition rate may only depend on the subject state.

        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v"
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression.

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number associated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled conversion to the model.
        A controlled conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is receiving population from the transition.
        This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v. v depends on I"
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression and I is the controller_name.

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number associated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural production transition to the model.
        A natural-production transition is a template that contains only one concept or state:
          - there is only an outcome
          - there are no subject or controller(s)
          - the outcome is the state variable representing a population that grows at some constant rate
        
        An example of a natural-production transition is the natural birth of a population of humans susceptible to an infectious disease:
          - the user request could be "add a natural birth process for the state 'Susceptible_humans' at a rate of 'b'"
          - outcome_name = "Susceptible_humans"
          - parameter_name = "b"
          - parameter_description = "Natural birth rate of susceptible humans"
          - template_expression = "b"
          - template_name = "Natural Birth of Susceptible Humans"

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `0` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled production to the model.
        A controlled production is a template that contains two concepts or state variables: 
          - the outcome represents a population that grows due to this transition
          - the controller represents a second population upon which the growth rate depends

        One example of a controlled-production transition is the shedding of viral particles from a population of infected people into wastewater:
          - The user request could be "add a new transition named 'viral shedding' to the state 'ViralLoad' with rate law 'alpha * Infected'"
          - "ViralLoad" is the outcome_name, "Infected" is the controller_name, "viral shedding" is the template_name, "Infected" is the controller_name, "alpha" is the parameter_name, and "alpha * Infected" is the template_expression.

        Another example of a controlled-production transition is to model the cumulative sum of a population over time:
          - The user request could be "create a cumulative sum of the state variable 'Infected' and name it 'InfectedCumSum"
          - outcome_name = "InfectedCumSum"
          - controller_name = "Infected"
          - template_name = "CumSum of Infected"
          - there is no parameter
          - template_expression = "Infected"

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            outcome_name (str): the name of the concept that is the outcome of the new transition.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If unknown or unspecified, the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If unknown or unspecified, the default value of `` should be used
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural degradation transition to the model.
        A natural-degradation transition is a template that contains only one concept or state:
          - there is only an subject
          - there are no outcome or controller(s)
          - the subject is the state variable representing a population that decays or dies at some rate proportional to the population itself
          - the parameter is the degradation or decay rate
        
        An example of a natural-degradation transition is the natural death of a population of living organisms:
          - the user request could be "add a natural death process for the state 'Recovered_humans' at a rate of 'c'"
          - subject_name = "Recovered_humans"
          - parameter_name = "c"
          - parameter_description = "Natural death rate of recovered humans"
          - template_expression = "c * Recovered_humans"
          - template_name = "Natural Death of Recovered Humans"

        Other examples of natural degradation are radioactive decay of atomic nuclei and any other processes that can be modelled as an exponential decay.

        If the user provides a "lifetime" instead of a decay rate, then the parameter of the natural-degradation transition is this "lifetime" and the template_expression is "(1 / lifetime) * subject_name".        
        If the user provides a "half-life", then the parameter is this "halflife" and the template_expression is "0.301 / halflife * subject_name".

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
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
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled degradation to the model.
        A controlled degradation transition is similar to the natural degradation transition:
          - it only has a subject
          - it has no outcome
          - it does have a controller unlike a natural degradation

        An example of a controlled degradation transition is predation or the decrease of a prey population caused by a predator population
          - the user request could be "add a death process to the 'Rabbit' caused by 'Wolf' at a rate of 'beta' = 0.01"
          - template_name = "Death of Rabbits caused by Wolf"
          - template_expression = "beta * Rabbit * Wolf"
          - subject_name = "Rabbit"
          - controller_name = "Wolf"
          - parameter_name = "beta"
          - parameter_value = "0.01"

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression
        
        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
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

    @tool()
    async def replace_ratelaw(self,
        template_name: str,
        new_rate_law: str,
        agent: AgentRef, loop: LoopControllerRef
    ):
        """
        This tool is used when a user wants to replace a rate law.
        
        An example of this would be "change the rate law of the 'infection' template to 'S * I * beta / N'"
          - template_name = "infection"
          - new_rate_law = "S * I * beta / N"

        Always make sure that new_rate_law is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression
        
        Args:
            template_name (str): This is the name of the template that has the rate law.
            new_rate_law (str): This is the mathematical expression used to determine the rate law.
        """
        code = agent.context.get_code("replace_ratelaw", {
            "template_name": template_name,
            "new_rate_law": new_rate_law
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
    async def stratify(self,
        agent: AgentRef, loop: LoopControllerRef,
        key: str,
        strata: Collection[str],
        structure: Optional[Iterable[Tuple[str, str]]] = None,
        directed: bool = False,
        cartesian_control: bool = False,
        modify_names: bool = True,
        concepts_to_stratify: Optional[Collection[str]] = None,
        concepts_to_preserve: Optional[Collection[str]] = None,
        params_to_stratify: Optional[Collection[str]] = None,
        params_to_preserve: Optional[Collection[str]] = None
    ):
        """
        This tool is used when a user wants to stratify a model.
        This will multiple the model utilizing several strata.

        An example of this would be "Stratify by location Toronto, Ottawa and Montreal. There are no interactions between members unless they are in the same location."
        Here we can see that the key is location.
        We can also see that the strata groups are Toronto, Ottawa and Montreal so we will write this as ["Toronto", "Ottawa", "Montreal"].
        The last sentence here informs us that cartesian_control is True, directed is False, and structure can be left as []

        Args:
            key (str):
                The (singular) name which describe the stratification. Some examples include, ``"City"``, ``"Age"``, ``"Vacination_Status"``, and ``"Location"``
                If a key cannot be explicitly grabbed from try your best to categorize the strata
            strata (Collection):
                These will be the individual groups used to stratify by. This should be converted to a list of strings for e.g., ``["boston", "nyc"]``
                or ``["geonames:4930956", "geonames:5128581"]``.
            structure (Optional):
                This describes how different strata within the same state are able to interact.
                An iterable of pairs corresponding to a directed network structure
                where each of the pairs has two strata. If none given, will assume a complete
                network structure. If no structure is necessary, pass an empty list.
                For example [["Young", "Old"]] would mean that the population in Young can interact with the population in Old provided they are within the same state.
                [["Toronto", "New York"], ["New York", "Toronto"]] would mean that the population in Toronto and New York can interact with each other provided they are in the same state.
                By default this should be an empty list.
            directed (bool):
                If the structure tuples are combinations this should be True. If they are permutations this should be false.
                If this value cannot be found it should default to False
            cartesian_control (bool):
                True if the strata from different state variables can interact.
                For example Susceptible young people can interact with infected old poeple.
                false if they cannot interact.
                For example the infected people in Toronto do not interact with the susceptible people in Boston

                This will split all control relationships based on the stratification.

                This should be true for an SIR epidemiology model, the susceptibility to
                infected transition is controlled by infected. If the model is stratified by
                vaccinated and unvaccinated, then the transition from vaccinated
                susceptible population to vaccinated infected populations should be
                controlled by both infected vaccinated and infected unvaccinated
                populations.

                This should be false for stratification of an SIR epidemiology model based
                on cities, since the infected population in one city won't (directly,
                through the perspective of the model) affect the infection of susceptible
                population in another city.

                If this cannot be found it should default to False
            modify_names (bool):
                If true, will modify the names of the concepts to include the strata
                (e.g., ``"S"`` becomes ``"S_boston"``). If false, will keep the original
                names.
                If this cannot be found it should default to True
            concepts_to_stratify (Optional): 
                This is a list of the state variables in the model that is required to be stratified.
                For example, given a model with state variables ("S", "E", "I", "R") and a request to only stratify the "S" state variable, the value of this argument should be ["S"].
                If the request does not specify any state variable to stratify in particular, then the value of this argument should default to None.
            concepts_to_preserve (Optional): 
                This is a list of the state variables in the model that must not be stratified.
                For example, given a model with state variables ("S", "E", "I", "R") and a request like "preserve" or "do not stratify" the "S" state variable, the value of this argument should be ["S"].
                If the request does not specify any state variable to not be stratified or preserved in particular, then the value of this argument should default to None.
            params_to_stratify (Optional):
                This is a list of the parameters in the model that is required to be stratified.
                For example, given a model with parameters ("beta", "gamma") and a request to only stratify the "beta" parameter, the value of this argument should be ["beta"].
                If the request does not specify any parameter to stratify in particular, then the value of this argument should default to None.
            params_to_preserve (Optional):
                This is a list of the parameters in the model that must not be stratified.
                For example, given a model with parameters ("beta", "gamma") and a request like "preserve" or "do not stratify" the "beta" parameter, the value of this argument should be ["beta"].
                If the request does not specify any parameter to not be stratified or preserved in particular, then the value of this argument should default to None.
        """

        code = agent.context.get_code("stratify", {
            "key": key,
            "strata": strata,
            "structure": structure,
            "directed": directed,
            "cartesian_control": cartesian_control,
            "modify_names": modify_names,
            "concepts_to_stratify": concepts_to_stratify,
            "concepts_to_preserve": concepts_to_preserve,
            "params_to_stratify": params_to_stratify,
            "params_to_preserve": params_to_preserve
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
    async def add_parameter(self,
        agent: AgentRef, loop: LoopControllerRef,
        parameter_id: str,
        name: str,
        description: str,
        value: float,
        distribution: str,
        units_mathml: str
    ):
        """
        This tool is used when a user wants to add a parameter to a model.

        Args:
            parameter_id (str): The ID of the new parameter to add
            name (str): The optional display name of the new parameter. If not known or not specified this should be set to the parameter_id.
            description (str): The optional description of the new parameter. If not known or not specified this should be set to ``.
            value (float): The optional value of the new parameter. If not known or not specified this should be set to None.
            distribution (str): The optional distribution of the new parameter. If not known or not specified this should be set to None.
            units_mathml (str): The optional units of the new parameter as a MathML XML string. If not known or not specified this should be set to None.
        """

        code = agent.context.get_code("add_parameter", {
            "parameter_id": parameter_id,
            "name": name,
            "description": description,
            "value": value,
            "distribution": distribution,
            "units_mathml": units_mathml
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
    async def change_rate_law_and_add_parameter(self,
        agent: AgentRef, loop: LoopControllerRef,
        template_name: str,
        new_rate_law: str,
        parameter_id: str,
        name: str,
        description: str,
        value: float,
        distribution: str,
        units_mathml: str
    ):
        """
        This tool is used when a user wants to replace a ratelaw and add a parameter to a model.

        If the parameter is specified as a distribution, the distribution arg should be a dictionary
        object that looks like

        {
            "type": <distribution_type>
            "parameters": {
                <user_specified_criteria>
            }
        }

        If the distribution is uniform, then <distribution_type> should be "StandardUniform1"

        Try to match the distribution to one of the templates below if possible, otherwise use your best judgement

        1. uniform distribution, this is specified with a low value nad a high value
        {
          "type": "StandardUniform1",
          "parameters": {
            "minimum": <low value>,
            "maximum": <high value>
          }
        }

        2. a normal/gaussian distribution with a mean and standard deviation
        {
          "type": "Normal1",
          "parameters": {
            "mean": <mean value>,
            "stdev": <standard deviation>
          }
        }


        Args:
            template_name (str): This is the name of the template that has the rate law.
            new_rate_law (str): This is the mathematical expression used to determine the rate law.
            parameter_id (str): The ID of the new parameter to add
            name (str): The optional display name of the new parameter. If not known or not specified this should be set to the parameter_id.
            description (str): The optional description of the new parameter. If not known or not specified this should be set to ``.
            value (float): The optional value of the new parameter. If not known or not specified this should be set to None.
            distribution (str): The optional distribution of the new parameter. If not known or not specified this should be set to None.
            units_mathml (str): The optional units of the new parameter as a MathML XML string. If not known or not specified this should be set to None.
        """

        code = agent.context.get_code("add_parameter", {
            "parameter_id": parameter_id,
            "name": name,
            "description": description,
            "value": value,
            "distribution": distribution,
            "units_mathml": units_mathml
        })

        code2 = agent.context.get_code("replace_ratelaw", {
            "template_name": template_name,
            "new_rate_law": new_rate_law
        })

        loop.set_state(loop.STOP_SUCCESS)

        # Order matters here, the parameter need to exist in order to have an expression with said parameter
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip() + "\n\n\n\n\n" + code2.strip(),
            }
        )

    @tool()
    async def add_group_controlled_degradation_template(self,
        subject_name: str,
        subject_initial_value: float,
        controller_names: list[str],
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a grouped controlled degradation to the model.
        A grouped controlled degradation transition is similar to the natural degradation transition:
          - it only has a subject
          - it has no outcome
          - it does have a list of controllers

        An example of a grouped controlled degradation transition is predation or the decrease of a prey population caused by a predator population
          - the user request could be "add a death process to the 'Rabbit' caused by 'Wolf', and 'Owl' 
          - template_name = "Death of Rabbits caused by Wolf"
          - template_expression = "beta * Rabbit * Wolf"
          - subject_name = "Rabbit"
          - controller_names = ["Wolf", "Owl"]
          - parameter_name = "beta"
          - parameter_value = "0.01"

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression
        
        Args:
            subject_name (str): the state names that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_names (list[str]): The names of the controller states. These are the states that will impact the transition's rate.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_group_controlled_degradation_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "controller_names": controller_names,
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
    async def add_group_controlled_conversion_template(self,
        subject_name: str,
        subject_initial_value: float,
        outcome_name: str,
        outcome_initial_value: float,
        controller_names: list[str],
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a grouped controlled conversion to the model.
        A grouped controlled conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is receiving population from the transition.
        This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v. v depends on I and S"
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression and ["I","S"] are the controller_names.

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number associated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_names (list[str]): The names of the controller states. These are the states that will impact the transition's rate.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_group_controlled_conversion_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_names": controller_names,
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
    async def add_group_controlled_production_template(self,
        outcome_name: str,
        outcome_initial_value: float,
        controller_names: list[str],
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a group controlled production to the model.
        A group controlled production is a template that contains two concepts or state variables: 
          - the outcome represents a population that grows due to this transition
          - the controller represents a group of populations upon which the growth rate depends

        An example of a group controlled production transition is to model the cumulative sum of a population over time:
          - The user request could be "create a cumulative sum of the state variables 'Infected' and 'Recovered'. Name it 'cumulativeSum"
          - outcome_name = "cumulativeSum"
          - controller_names = ["Infected", "Recovered"]
          - template_name = "cumulativeSum"
          - there is no parameter
          - template_expression = "Infected + Recovered"

        Always make sure that template_expression is the string representation of a mathematical expression that can be parsed by SymPy.
        If the user provides a math expression containing the operator "^", replace it with "**".
        If the user provides an equation, pick the right hand side expression.

        Args:
            outcome_name (str): the name of the concept that is the outcome of the new transition.
            outcome_initial_value (float): The number associated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_names (list[str]): The names of the controller states. These are the states that will impact the transition's rate.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units associated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If unknown or unspecified, the default value of `1` should be used.
            parameter_description (str): The description associated with the parameter. If unknown or unspecified, the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_group_controlled_production_template", {
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_names": controller_names,
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
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generate code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and interacting with a Mira
        Template Model.

        Input is a full grammatically correct question about or request for an action to be performed on the model or related to the model.

        Args:
            query (str): A fully grammatically correct question about the current model.

        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        prompt = """
You are a programmer writing code to help with Mira Template Model editing and manipulation in a Jupyter Notebook.

Please write code that satisfies the user's request.

You have access to a model `model` that is a Mira Template Model. You can use the `inspect_template_model` tool to better understand it
and its structure.

If you are asked to edit the model, you should try to use other tools for it. You can use the `replace_template_name`, `remove_template`, 
`replace_state_name`, `add_observable`, `remove_observable`, `add_natural_conversion_template`, `add_controlled_conversion_template`, 
`add_natural_production_template`, `add_controlled_production_template`, `add_natural_degradation_template`, `add_controlled_degradation_template`, 
`replace_ratelaw`, `stratify`, `add_parameter`, `change_rate_law_and_add_parameter` tools to help with this.

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
                "language": agent.context.lang,
                "content": code.strip(),
            }
        )
        return result
