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

> **Note**: after setup, the model configuration is accessible via the variable name `model_config`.

This context's LLM agent allows the user to ask various questions of the configuration values and to edit the values. It is aware of the schema constraints and oeprates within them.

This context has **1 custom message types**:

1. `save_model_config_request`: this does not require arguments; it simply executes a `PUT` on the model configuration to update it in place based on the operations performed in the context.

> Note if you doing this in the dev UI you just type in the custom message name as `save_model_config` (drop the _request)