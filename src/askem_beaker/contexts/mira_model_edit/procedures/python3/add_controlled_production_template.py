# Define state variables
concepts_name_map = model.get_concepts_name_map()
initials = {}

if "{{ outcome_name }}" in concepts_name_map:
    outcome_concept = concepts_name_map.get("{{ outcome_name }}")
else:
    outcome_concept = Concept(name = "{{ outcome_name }}")
    initials["{{outcome_name }}"] = Initial(concept = outcome_concept, expression = sympy.Float({{outcome_initial_value }}))

if "{{controller_name}}" in concepts_name_map:
    controller_concept = concepts_name_map.get("{{controller_name}}")
else:
    controller_concept = Concept(name = "{{controller_name}}")
    initials["{{controller_name }}"] = Initial(concept = controller_concept, expression = sympy.Float({{controller_initial_value }}))


# Define parameters
parameters = {}
if "{{ parameter_name}}" in model.parameters: #note this is checks for paremeter's symbol
    parameters["{{ parameter_name}}"] = model.parameters.get("{{ parameter_name}}")
else: 
    parameters["{{ parameter_name}}"] = Parameter(name = "{{ parameter_name}}", value = {{ parameter_value }}, description = "{{ parameter_description}}")


# Add process as new template to the model
model = model.add_template(
    template = ControlledProduction(
        outcome = outcome_concept,
        controller = controller_concept,
        rate_law = safe_parse_expr("{{ template_expression }}", local_dict = _clash),
        name = "{{ template_name }}"
    ),
    parameter_mapping = parameters,
    initial_mapping = initials
)
