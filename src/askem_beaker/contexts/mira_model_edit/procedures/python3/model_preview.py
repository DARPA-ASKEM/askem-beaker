from IPython.core.interactiveshell import InteractiveShell;
from IPython.core import display_functions;
from mira.modeling.amr.petrinet import template_model_to_petrinet_json
from mira.modeling.amr.stockflow import template_model_to_stockflow_json
from mira.modeling.amr.regnet import template_model_to_regnet_json

import IPython
formatter = IPython.get_ipython().display_formatter.formatters['text/plain']
formatter.max_seq_length = 0

# format_dict, md_dict = InteractiveShell.instance().display_formatter.format(GraphicalModel.for_jupyter(model))

if "{{ schema_name }}" == "regnet":
    model_json = template_model_to_regnet_json({{ var_name|default("model") }})
elif "{{ schema_name }}" == "stockflow":
    model_json = template_model_to_stockflow_json({{ var_name|default("model") }})
else:
    model_json = template_model_to_petrinet_json({{ var_name|default("model") }})

result = {
    "application/json": model_json
}
# for key, value in format_dict.items():
#     if "image" in key:
#         result[key] = value

result
