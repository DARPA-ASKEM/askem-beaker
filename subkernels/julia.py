import ast
import json
import logging
from typing import Any

from .base import BaseSubkernel

logger = logging.getLogger(__name__)


class JuliaSubkernel(BaseSubkernel):
    DISPLAY_NAME = "Julia"
    KERNEL_NAME = "julia-1.9"
    DATAFRAME_TYPE_NAME = "DataFrames"
    

    @classmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        return_raw = execution_result.get("return")
        if return_raw:
            return_str = ast.literal_eval(return_raw)
            try:
                return_obj = json.loads(return_str)
            except json.JSONDecodeError:
                raise
            return return_obj
