import pandas as pd

def describe_dataframe_structure(df):
    # Basic information about the DataFrame
    description = f"The DataFrame has {df.shape[0]} rows and {df.shape[1]} columns.\n"
    
    # Extract column names and types
    description += "Column names and types:\n"
    for column in df.columns:
        description += f"- {column}: {df[column].dtype}\n"
    
    # Check if the DataFrame has a matrix-like structure
    if not df.index.is_integer():
        description += "The DataFrame appears to have a matrix-like structure with row headers.\n"
        description += "Row headers:\n"
        for idx_name in df.index.names:
            description += f"- {idx_name or 'Unnamed index'}: {df.index.get_level_values(idx_name).dtype}\n"
        
    # Append the head of the DataFrame
    description += "\nThe first few rows of the DataFrame (head):\n"
    description += df.head().to_string(index=True)
    
    return description

describe_dataframe_structure({{ dataset_name }})