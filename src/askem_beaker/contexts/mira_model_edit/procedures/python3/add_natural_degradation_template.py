# Define state variables
concepts_name_map = model.get_concepts_name_map()
initials = {}
if "{{ subject_name }}" in concepts_name_map:
    subject_concept = concepts_name_map.get("{{ subject_name }}")
else:
    subject_concept = Concept(name = "{{ subject_name }}")
    initials["{{subject_name }}"] = Initial(concept = outcome_concept, expression = sympy.Float({{subject_initial_value }}))

# Define parameters
parameters = {}
if "{{ parameter_name}}" in model.parameters: #note this is checks for paremeter's symbol
    parameters["{{ parameter_name}}"] = model.parameters.get("{{ parameter_name}}")
else: 
    parameters["{{ parameter_name}}"] = Parameter(name = "{{ parameter_name}}", value = {{ parameter_value }}, description = "{{ parameter_description}}")

# Add process as new template to the model
model = model.add_template(
    template = NaturalDegradation(
        subject = subject_concept,
        rate_law = safe_parse_expr("{{ template_expression }}", local_dict = _clash),
        name = "{{ template_name }}"
    ),
    parameter_mapping = parameters,
    initial_mapping = initials
)
