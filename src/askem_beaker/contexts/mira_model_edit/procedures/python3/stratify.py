import copy

model = stratify(
    template_model=model,
    key= "{{ key }}",
    strata={{ strata }},
    structure= {{ structure|default(None) }},
    directed={{ directed|default(False) }},
    cartesian_control={{ cartesian_control|default(False) }},
    modify_names={{ modify_names|default(True) }},
    concepts_to_stratify={{ concepts_to_stratify|default(None) }}, #If none given, will stratify all concepts.
    concepts_to_preserve={{ concepts_to_preserve|default(None) }}, #If none given, will stratify all concepts.
    params_to_stratify= {{ params_to_stratify|default(None) }}, #If none given, will stratify all parameters.
    params_to_preserve= {{ params_to_preserve|default(None) }}, #If none given, will stratify all parameters.
    param_renaming_uses_strata_names = True
)

add_param_factor = {{ add_param_factor | True }}

# FIXME: need to juggle inclusive vs exclusive
params_to_stratify= {{ params_to_stratify|default(None) }}

model_ = copy.deepcopy(model)

if add_param_factor:
    new_params = {param: 'f_' + param for param in params_to_stratify}
    for param, factor in new_params.items():

        # In case of parameter name clash
        while factor in model_.parameters.keys():
            factor += '_0'
        new_params[param] = factor

        # Replace 'param' with 'param * factor' in all rate laws
        for template in model_.templates:
            template.rate_law = SympyExprStr(
                template.rate_law.args[0].subs(
                    sympy.Symbol(param),
                    sympy.Symbol(param) * sympy.Symbol(factor)
                )
            )

        # Add the factor as a new model parameter
        model_.add_parameter(
            parameter_id = factor,
            name = factor,
            description = f'Stratification factor of the parameter {param}.',
            value = 1.0
        )

model = model_
