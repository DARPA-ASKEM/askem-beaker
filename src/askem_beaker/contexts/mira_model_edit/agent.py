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
    async def model_compose(self, models: list[str], agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used to compose merge multiple models together.

        Args:
            models (list[str]): The models as a list.
        """
        logger.error(f"COMPOSING MODEL: {models}")
        code = agent.context.get_code("model_compose", {"models": models})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

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

        Args:
            new_id (str): The new ID provided for the observable. If this is not provided the value for new_name should be used
            new_name (str): The new name provided for the observable. If this is not provided for the new_id should be used.
            new_expression (str): The expression that the observable represents.
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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
        parameter_value: float,
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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
        parameter_value: float,
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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
        parameter_value: float,
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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
        parameter_value: float,
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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
        parameter_value: float,
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
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
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

    @tool()
    async def replace_ratelaw(self,
        template_name: str,
        new_rate_law: str,
        agent: AgentRef, loop: LoopControllerRef
    ):
        """
        This tool is used when a user wants to replace a ratelaw.

        An example of this would be "change rate law of inf to S * I * z"
        Where inf is the template_name and "S * I * z" is the new_rate_law

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