def replace_parameter_id(model: TemplateModel, old_id: str, new_id: str) -> TemplateModel:
    """Replace the ID of a parameter

    Given a pair of parameter names (old and new), replace the parameter names from old to new 
    in every instance (rate law, observable, initial expressions) in the given model.

    Parameters
    ----------
    model : JSON
        The model
    old_id :
        The ID of the parameter to replace
    new_id :
        The new ID to replace the old ID with

    Returns
    -------
    tm: TemplateModel
        The updated model
    """

    assert isinstance(model, TemplateModel)
    tm = model

    if old_id not in tm.parameters:
        raise ValueError(f"Parameter with ID {old_id} not found in model.")
    
    for template in tm.templates:
        if template.rate_law:
            template.substitute_parameter(old_id, sympy.Symbol(new_id))
            
    for observable in tm.observables.values():
        observable.expression = SympyExprStr(
            observable.expression.args[0].subs(sympy.Symbol(old_id),
                                               sympy.Symbol(new_id)))
        
    for key, param in copy.deepcopy(tm.parameters).items():
        if param.name == old_id:
            popped_param = tm.parameters.pop(param.name)
            popped_param.name = new_id
            tm.parameters[new_id] = popped_param

    for initial in tm.initials.values():
        if initial.expression:
            initial.substitute_parameter(old_id, sympy.Symbol(new_id))

    return tm

model = replace_parameter_id(model, '{{ old_name }}', '{{ new_name }}')
