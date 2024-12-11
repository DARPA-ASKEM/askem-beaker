import pandas as pd

{% for var_name, data_url in  .items() -%}
{{ var_name }} = pd.read_csv('{{ data_url }}',)
{% endfor %}
