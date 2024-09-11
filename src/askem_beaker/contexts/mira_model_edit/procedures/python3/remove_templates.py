from typing import List
def remove_templates(tm: TemplateModel, template_names: List[str]) -> TemplateModel:

    # Create new template model,
    # skipping over templates with given names
    tm_new = copy.deepcopy(tm)
    tm_new.templates = []
    for t in tm.templates:
        if t.name in template_names:
            continue
        tm_new.templates.append(t)
    
    # Remove parameters only used in removed templates
    # tm_new.eliminate_unused_parameters()

    # Ditto for initials
    tm_new.initials = {i: c for i, c in tm_new.initials.items() if i in tm_new.get_concepts_name_map()}

    return tm_new

model = remove_templates(model, {{ template_names }})