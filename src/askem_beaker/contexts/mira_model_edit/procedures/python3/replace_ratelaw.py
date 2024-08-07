import sympy
def replace_rate_law_sympy(model, template_name, new_rate_law):
    """Replace the rate law of transition. The new rate law passed in will be a sympy.Expr object

    Parameters
    ----------
    template_name :
        The ID of the transition whose rate law is to be replaced, this is
        typically the name of the transition
    new_rate_law :
        The new rate law to replace the existing rate law with

    Returns
    -------
    :
        The updated model as an AMR JSON
    """
    assert isinstance(model, TemplateModel)
    tm = model
    local_dict = { key:sympy.Symbol(key) for key, _value in tm.parameters.items() }
    for k, v in mmt.get_concepts_name_map().items():
        local_dict[k] = sympy.Symbol(k)

    for template in tm.templates:
        if template.name == template_name:
            template.set_rate_law(new_rate_law, local_dict=local_dict)
    return tm

model = replace_rate_law_sympy(model, "{{ template_name }}", "{{ new_rate_law }}")
