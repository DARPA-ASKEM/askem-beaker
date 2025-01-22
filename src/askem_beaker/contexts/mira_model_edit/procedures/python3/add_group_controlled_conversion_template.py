# Define state variables
concepts_name_map = model.get_concepts_name_map()
initials = {}
controller_concept_list = []

if "{{ subject_name }}" in concepts_name_map:
    subject_concept = concepts_name_map.get("{{ subject_name }}")
else:
    subject_concept = Concept(name = "{{ subject_name }}")
    initials["{{subject_name }}"] = Initial(concept = subject_concept, expression = sympy.Float({{subject_initial_value }}))

if "{{ outcome_name }}" in concepts_name_map:
    outcome_concept = concepts_name_map.get("{{ outcome_name }}")
else:
    outcome_concept = Concept(name = "{{ outcome_name }}")
    initials["{{outcome_name }}"] = Initial(concept = outcome_concept, expression = sympy.Float({{outcome_initial_value }}))

for controller_name in "{{ controller_names }}":
    if controller_name in concepts_name_map:
        controller_concept_list.append(concepts_name_map.get(controller_name))
    else:
        controller_concept = Concept(name = controller_name)
        controller_concept_list.append(controller_concept)
        initials[controller_name] = Initial(concept = controller_concept, expression = sympy.Float(1))

# Define parameters
parameters = {}
if "{{ parameter_name}}" in model.parameters: #note this is checks for paremeter's symbol
    parameters["{{ parameter_name}}"] = model.parameters.get("{{ parameter_name}}")
else: 
    parameters["{{ parameter_name}}"] = Parameter(name = "{{ parameter_name}}", value = {{ parameter_value }}, description = "{{ parameter_description}}")


# Add process as new template to the model
model = model.add_template(
    template = GroupedControlledConversion(
        subject = subject_concept,
        outcome = outcome_concept,
        controllers = controller_concept_list,
        rate_law = safe_parse_expr("{{ template_expression }}", local_dict = _clash),
        name = "{{ template_name }}"
    ),
    parameter_mapping = parameters,
    initial_mapping = initials
)
