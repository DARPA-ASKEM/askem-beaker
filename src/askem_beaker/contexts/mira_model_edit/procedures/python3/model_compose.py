def model_compose(models):
    """Merge the models into a single model

    Parameters
    ----------
    models : dict
        The models to merge

    """

#TODO: Do groundings happen on hmi side?

    merged_model = compose(models)
    return merged_model