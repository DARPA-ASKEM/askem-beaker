import copy

add_param_factor = {{ add_param_factor|default(True) }}
params_to_stratify= {{ params_to_stratify|default(None) }}

model_to_stratify = copy.deepcopy(model)
new_params = {}

if add_param_factor == True:
    new_params = {param: 'f' + param for param in params_to_stratify}
    for param, factor in new_params.items():
        # In case of parameter name clash
        while factor in model_to_stratify.parameters.keys():
            factor += '_0'
        new_params[param] = factor

        # Replace 'param' with 'param * factor' in all rate laws
        for template in model_to_stratify.templates:
            template.rate_law = SympyExprStr(
                template.rate_law.args[0].subs(
                    sympy.Symbol(param),
                    sympy.Symbol(param) * sympy.Symbol(factor)
                )
            )

        # Add the factor as a new model parameter
        model_to_stratify.add_parameter(
            parameter_id = factor,
            name = factor,
            description = f'Stratification factor of the parameter {param}.',
            value = 1.0
        )

    # Replace params with factored parameters
    params_to_stratify = list(new_params.values())



model = stratify(
    template_model=model_to_stratify,
    key= "{{ key }}",
    strata={{ strata }},
    structure= {{ structure|default(None) }},
    directed={{ directed|default(False) }},
    cartesian_control={{ cartesian_control|default(False) }},
    modify_names={{ modify_names|default(True) }},
    concepts_to_stratify={{ concepts_to_stratify|default(None) }}, #If none given, will stratify all concepts.
    concepts_to_preserve={{ concepts_to_preserve|default(None) }}, #If none given, will stratify all concepts.
    params_to_stratify=params_to_stratify,
    params_to_preserve= {{ params_to_preserve|default(None) }}, #If none given, will stratify all parameters.
    param_renaming_uses_strata_names = True
)

# Remove any leftover parameter
for __, factor in new_params.items():
    if factor in model.parameters.keys():
        __ = model.parameters.pop(factor)
