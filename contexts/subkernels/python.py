import ast
from typing import Any

from .base import BaseSubkernel



class PythonSubkernel(BaseSubkernel):
    DISPLAY_NAME = "Python 3"
    KERNEL_NAME = "python3"
    DATAFRAME_TYPE_NAME = "pandas"
    

    @classmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        return_str = execution_result.get("return")
        if return_str:
            return_obj = ast.literal_eval(return_str)
            return return_obj

        
