def add_observable_pattern_(new_name, identifier_dict, context_dict):
    return add_observable_pattern(
        model,
        new_name,
        identifiers = identifier_dict,
        context = context_dict
    )

new_name = "{{ new_name }}"
identifier_keys = {{ identifier_keys }}
identifier_values = {{ identifier_values }}
context_keys = {{ context_keys }}
context_values = {{ context_values }}
identifier_dict = dict(zip(identifier_keys, identifier_values))
context_dict = dict(zip(context_keys, context_values))

add_observable_pattern_(new_name, identifier_dict, context_dict)