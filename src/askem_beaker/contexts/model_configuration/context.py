import copy
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import ConfigEditAgent
from askem_beaker.utils import get_auth

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)

class ConfigEditContext(BaseContext):

    agent_cls = ConfigEditAgent

    model_config_id: Optional[str]
    model_config_json: Optional[str]
    model_config_dict: Optional[dict[str, Any]]
    var_name: Optional[str] = "model_config"

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.reset()
        logger.error("initializing...")
        super().__init__(beaker_kernel, self.agent_cls, config)

    def reset(self):
        pass
        
    async def setup(self, context_info, parent_header):
        logger.error(f"performing setup...")
        self.config["context_info"] = context_info
        item_id = self.config["context_info"]["id"]
        item_type = self.config["context_info"].get("type", "model_config")
        self.dataset_id = self.config["context_info"].get("dataset_id", None)
        logger.error(f"Processing {item_type} {item_id}")
        self.auth = get_auth()
        await self.set_model_config(
            item_id, item_type, parent_header=parent_header
        )
        if self.dataset_id:
            await self.load_dataset(parent_header=parent_header)        

    async def auto_context(self):
        context = f"""You are an scientific modeler whose goal is to help the user understand and update a model configuration.

Model configurations are defined by a specific model configuration JSON schema. 
The schema defines the structure of the model configuration, including the parameters, initial conditions, and other attributes of the model.

The schema is:
{await self.get_schema()}

The actual instance of the model configuration is:
{await self.get_config()}

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.

If you need to generate code, you should write it in the '{self.subkernel.DISPLAY_NAME}' language for execution
in a Jupyter notebook using the '{self.subkernel.KERNEL_NAME}' kernel.
"""
        if self.dataset_id:
            context += f"""\n Additionally, a DataFrame is loaded called `dataset`. 
            This DataFrame contains the data that can be used to parameterize the model configuration. If the user mentions updating the model
            configuration based on a dataset, use the `dataset` DataFrame.

            It has the following structure:
            {await self.describe_dataset()}\n

            When running or generating code to update the model configuration, make sure to do so based on your knowledge of `dataset`s structure
            and schema. You should never "assume" a dataset in the code that you generate or run, instead you should always use the `dataset` DataFrame.
            You'll need to access various values from it based on your knowledge of the model configuration schema and your understanding of the dataset.

            A common convention is that strata are delinated with `_n` where `n` is a number in increasing order. For example, if there are multiple `age` strata
            you might expect that `_1` indicates the first (or youngest) strata, `_2` the second, and so on. 

            You'll also find that for stratified models, the parameter `referenceId` often indicates the strata to which the parameter applies. For example you may see a
            `referenceId` of `beta_old_young` which would correspond with the interaction in the `dataset` between these two strata (if the interaction represents the `beta` parameter).
            So if there are three strata, `old`, `middle`, and `young`, you might expect to see `beta_old_middle`, `beta_old_young`, and `beta_middle_young` as 
            the referenceIds for the interactions between these strata. In the dataset you might see groups delineated with `_1`, `_2`, `_3` to indicate the strata. 
            The value at `S_3` and `I_2` would correspond with `beta_old_middle` in this case since it reflects the transition from from old susceptible population 
            and middle infected population.
            """
        return context

    async def get_schema(self) -> str:
        """
        Get the model configuration schema.

        This should be used to understand the structure of the model configuration JSON object.


        Returns:
            str: a JSON representation of the model configuration schema
        """
        schema = (
            await self.evaluate(self.get_code("get_schema", {"HMI_SERVER_URL": os.environ["HMI_SERVER_URL"]}))
        )["return"]
        return json.dumps(schema, indent=2)


    async def get_config(self) -> str:
        """
        Get the current instance of the model configuration.

        This should be used to understand the model configuration.


        Returns:
            str: a JSON representation of the model configuration schema
        """
        schema = (
            await self.evaluate(self.get_code("get_config"))
        )["return"]
        return json.dumps(schema, indent=2)


    async def describe_dataset(self) -> str:
        """
        Describe structure of provided dataset to assist in model configuration.

        Returns:
            str: a description of the dataset structure
        """
        schema = (
            await self.evaluate(self.get_code("describe_dataset", {"dataset_name": "dataset"}))
        )["return"]
        return schema


    async def set_model_config(self, item_id, agent=None, parent_header={}):
        self.config_id = item_id
        meta_url = f"{os.environ['HMI_SERVER_URL']}/model-configurations/{self.config_id}"
        logger.error(f"Meta url: {meta_url}")
        self.model_config = requests.get(meta_url, auth=self.auth.requests_auth()).json()
        logger.error(f"Succeeded in fetching configured model, proceeding.") 
        await self.load_config()

    async def load_config(self):
        command = "\n".join(
            [
                self.get_code("load_config", {
                    "var_name": self.var_name,
                    "model_config_json": self.model_config,
                }),
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)   

    async def load_dataset(self, parent_header={}):
        meta_url = f"{os.environ['HMI_SERVER_URL']}/datasets/{self.dataset_id}"
        dataset = requests.get(meta_url, auth=self.auth.requests_auth())
        if dataset.status_code == 404:
            raise Exception(f"Dataset '{self.dataset_id}' not found.") 
        filename = dataset.json().get("fileNames", [])[0]      
        meta_url = f"{os.environ['HMI_SERVER_URL']}/datasets/{self.dataset_id}"
        url = f"{meta_url}/download-url?filename={filename}"
        data_url_req = requests.get(
            url=url,
            auth=self.auth.requests_auth(),
        )
        data_url = data_url_req.json().get("url", None)
        command = "\n".join(
            [
                self.get_code("load_dataset", {
                    "var_name": "dataset",
                    "data_url": data_url,
                }),
            ]
        )
        await self.execute(command)      

    async def post_execute(self, message):
        content = (await self.evaluate(self.get_code("get_config")))["return"]
        self.beaker_kernel.send_response(
            "iopub", "model_configuration_preview", content, parent_header=message.parent_header
        )

    @intercept()
    async def save_model_config_request(self, message):
        '''
        Updates the model configuration in place.
        '''
        content = message.content

        unloader = f"{self.var_name}"
            
        updated_config: dict = (
            await self.evaluate(unloader)
        )["return"]

        create_req = requests.put(
            f"{os.environ['HMI_SERVER_URL']}/model-configurations/{self.config_id}", json=updated_config,
                auth =(os.environ['AUTH_USERNAME'], os.environ['AUTH_PASSWORD'])
        )

        if create_req.status_code == 200:
            logger.error(f"Successfuly updated model config {self.config_id}")
        response_id = create_req.json()["id"]

        content = {"model_configuration_id": response_id}
        self.beaker_kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
