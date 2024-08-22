---
layout: default
title: mira_config_edit
parent: Contexts
nav_order: 1
has_toc: true
---

# model_configuration

This context is used for editing model configurations in Terarium's new JSON style. On setup it expects a model configuration `id` to be provided; unlike other contexts the key is always `id` and the value is the model configuration `id`. For example:

```
{
  "id": "27ec5daa-d137-43d2-bc3b-8109ba91a7b1"
}
```

You can also provide a `dataset_id` if you wish to parameterize a model configuration based on a dataset. For example:

```
{"id": "161bee2c-f5eb-4811-a407-0d789ebccbf5",
 "dataset_id": "e3eecbf9-bc90-4591-9d90-0b9ab20472ad"}
```

> **Note**: after setup, the model configuration is accessible via the variable name `model_config`. If a dataset is provided it's loaded as a Pandas DataFrame `dataset`.

This context's LLM agent allows the user to ask various questions of the configuration values and to edit the values. It is aware of the schema constraints and oeprates within them.

This context has **1 custom message types**:

1. `save_model_config_request`: this does not require arguments; it simply executes a `PUT` on the model configuration to update it in place based on the operations performed in the context.

> Note if you doing this in the dev UI you just type in the custom message name as `save_model_config` (drop the _request)