import pandas as pd; import io
output_buff = io.BytesIO()
{{ var_name|default("df") }}.to_csv(output_buff, index=True, header=True)
output_buff.seek(0)

for line in output_buff.getvalue().splitlines():
    print(line.decode())
