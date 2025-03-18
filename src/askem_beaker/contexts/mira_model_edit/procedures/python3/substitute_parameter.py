# Substitute a parameter by a given value and remove it from the model
# Set value = 1 if the parameter is used multiplicatively 
# Set value = 0 if the parameter is used additively
model.substitute_parameter("{{ old_name }}", safe_parse_sympy("{{ new_name }}"), local_dict = _clash )