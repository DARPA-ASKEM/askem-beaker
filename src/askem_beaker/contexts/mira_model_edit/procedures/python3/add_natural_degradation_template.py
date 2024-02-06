subject_concept = Concept(name = "{{ subject_name }}")
parameter_unit = Unit(expression = sympy.Symbol("{{ parameter_units}}"))

parameters = {
    "{{ parameter_name }}": Parameter(name = "{{ parameter_name }}", value = {{ parameter_value }}, units = parameter_unit, description = "{{ parameter_description }}")
}

initials = { 
    "{{subject_name }}": Initial(concept = subject_concept, expression = sympy.Float({{subject_initial_value }}))
}

model = model.add_template(
    template = NaturalDegradation(
        subject = subject_concept,
        rate_law = sympy.parsing.sympy_parser.parse_expr("{{ template_expression }}"),
        name = "{{ template_name }}"
    ),
    parameter_mapping = parameters,
    initial_mapping = initials
)
