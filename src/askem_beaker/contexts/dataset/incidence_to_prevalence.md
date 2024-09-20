## Task Overview

You are given one or more epidemiological datasets containing **incidence data** (new cases/events per time period). The user wants you to:

1. **Convert the incidence data to prevalence** (ongoing cases at each time point).
2. **Map the prevalence data to specific compartments** in a compartmental model, such as Susceptible (S), Infected (I), Recovered (R), Hospitalized (H), and Deceased (D).
3. **Handle different naming conventions** and **adjust time windows** as specified by the user.

---

## Steps

### 1. Data Loading and Interpretation

- Assume the user has provided one or more datasets as DataFrames, each containing columns for date, location, and an incidence measure (e.g., new cases, hospitalizations, deaths).
- The naming conventions of the datasets or columns might vary, so the task requires you to identify the meaning of each dataset from the provided description.

### 2. Key Definitions

- **Incidence** refers to the count of new events (e.g., new cases, hospitalizations, or deaths) at each time point.
- **Prevalence** refers to the total number of ongoing cases at each time point (e.g., currently infected or hospitalized individuals).
- **Compartmental Models** involve variables like:
  - **S** (Susceptible): Those who have not been infected.
  - **I** (Infected): Those currently infected (active cases).
  - **R** (Recovered): Those who have recovered from the infection.
  - **H** (Hospitalized): Those currently hospitalized.
  - **D** (Deceased): Those who have died (cumulative deaths).

### 3. Steps for Converting Incidence to Prevalence

#### 3.1. Identifying Data
- Identify which dataset corresponds to each compartment. The user might provide specific instructions like:
  - **Incident Cases**: Map to new infections.
  - **Incident Hospitalizations**: Map to new hospitalizations.
  - **Cumulative Deaths**: Map to the total number of deaths.

#### 3.2. Handling Dates and Locations
- Focus on the national data (e.g., `location_name = "United States"`). Ensure the dataset is sorted by date.

#### 3.3. User-Specified Windows
- Allow the user to specify recovery windows (e.g., 14 days for infections, 10 days for hospitalizations).
- Default values: 14 days for infections, 10 days for hospitalizations, 3 days for death-related hospitalization.

#### 3.4. Calculate Prevalence
- For incidence datasets (e.g., new infections or hospitalizations), use a rolling sum over the specified window to calculate prevalence. For example:
  - **Infected Prevalence (I)** = Sum of new infections over the last 14 days.
  - **Hospitalized Prevalence (H)** = Sum of new hospitalizations over the last 10 days.
  
- For cumulative datasets (e.g., deaths), directly use the cumulative sum as the prevalence:
  - **Deaths (D)** = Cumulative deaths.

#### 3.5. Calculate Recovered Individuals
- For recovered individuals, assume recovery occurs after a specified window (e.g., 14 days for infections). The formula is:
  - **Recovered (R)** = Cumulative sum of incident cases up to (current date - recovery window) - current deaths.

#### 3.6. Handle Variable Data Formats
- Assume the column names might differ (e.g., `"new_cases"`, `"incident_cases"`, or `"hospitalizations"`). Ask the user for clarification on naming conventions if needed.

---

### 4. Mapping to Compartmental Model

#### 4.1. Create a Shared DataFrame
- Combine the time series data into one DataFrame. Ensure that all variables (I, R, H, D) are aligned by their common date index.

#### 4.2. Calculate Susceptible Population (S)
- Define a total population (e.g., 150 million) if not provided by the user.
- Calculate the susceptible population as:
  - **S** = Total population - I - R - H - D.

#### 4.3. Adjust Recovered Population
- Ensure that recovered individuals exclude deaths:
  - Adjust R as: **R = R - D**.

---

### 5. Return the Final Data
- Return the final DataFrame with columns for S, I, R, H, D, and any additional user-specified compartments.
- Ensure the output is flexible and can handle various compartmental models or additional epidemiological categories.

---

## Examples and Pseudo Code

### Example 1: Incidence Cases to Prevalence

```python
# User provides incidence data
inc_cases = user_input_inc_cases  # e.g., "incident_cases" column
window = user_specified_window or 14  # Recovery time, default is 14 days

# Convert incident cases to prevalence
prevalence_I = inc_cases.rolling(window).sum().dropna()

# Adjust for recovered individuals
prevalence_R = inc_cases.cumsum().shift(window) - cumulative_deaths
```

### Example 2: Hospitalizations to Prevalence
```python
# User provides hospitalization data
inc_hospitalizations = user_input_hosp_data  # e.g., "new_hospitalizations" column
window = user_specified_window or 10  # Hospitalization recovery time, default is 10 days

# Convert incident hospitalizations to prevalence
prevalence_H = inc_hospitalizations.rolling(window).sum().dropna()
```

### Example 3: Combining Data into Compartmental Model
```python
# Initialize total population
total_population = 150e6  # User-specified or default

# Create DataFrame with compartments
compartments_df = pd.DataFrame({
    "I": prevalence_I,
    "R": prevalence_R - prevalence_D,  # Adjust for deaths
    "H": prevalence_H,
    "D": cumulative_deaths,
})

# Calculate Susceptible population
compartments_df["S"] = total_population - compartments_df["I"] - compartments_df["R"] - compartments_df["H"] - compartments_df["D"]
```

### Example 4: Different Column Headers, Date Formats, and Groupings

#### Dataset Example:
This dataset might come from a public health organization with different column names and some additional grouping variables, such as age group and gender.

| country      | region     | date_reported | new_infections | new_hospitalizations | total_deaths | age_group | gender |
|--------------|------------|---------------|----------------|----------------------|--------------|-----------|--------|
| United States | Northeast  | 2022-01-01    | 500            | 20                   | 15           | 18-30     | M      |
| United States | Northeast  | 2022-01-01    | 600            | 25                   | 10           | 18-30     | F      |
| United States | Northeast  | 2022-01-02    | 450            | 15                   | 12           | 18-30     | M      |
| United States | Southeast  | 2022-01-01    | 300            | 10                   | 5            | 30-50     | F      |

#### Key Differences:
1. **Date Column**: This dataset uses `date_reported` rather than `date`.
2. **Incidence Columns**: `new_infections`, `new_hospitalizations`, and `total_deaths` are named differently.
3. **Grouping Variables**: The dataset includes additional groupings by `age_group`, `gender`, and `region`, which might or might not be relevant depending on the user’s goals.

#### Approach:
To work with this dataset, we:
1. **Align the column names** by either renaming them or referencing them directly based on the schema.
2. **Aggregate data** if needed by summing over categories like `age_group` and `gender` to get national or regional totals.
3. **Convert incidence to prevalence** using user-specified time windows.

##### Pseudo Code Example:
```python
# Set date as index and ensure datetime format
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

# Now process the columns to convert to prevalence
# Infected Prevalence (I)
prevalence_I = df.groupby("region")["incident_cases"].rolling(window).sum().dropna().reset_index()

# Hospitalized Prevalence (H)
prevalence_H = df.groupby("region")["incident_hospitalizations"].rolling(window).sum().dropna().reset_index()

# Deaths (D)
prevalence_D = df.groupby("region")["cumulative_deaths"].apply(lambda x: x).reset_index()

# Recovered (R)
prevalence_R = df.groupby("region")["incident_cases"].cumsum().shift(window).reset_index()
prevalence_R['prevalence_R'] = prevalence_R['incident_cases'] - prevalence_D['cumulative_deaths']

# Combine into a final DataFrame
final_df = prevalence_I.merge(prevalence_R, on=["region", "date"]).merge(prevalence_H, on=["region", "date"]).merge(prevalence_D, on=["region", "date"])
final_df = final_df.rename(columns={
    'sum_x': 'I',
    'sum_y': 'R',
    'sum': 'H',
    'cumulative_deaths': 'D'
})
```

### Example 5: Weekly Aggregated Data with Cumulative Incidence

#### Dataset Example:
Some organizations (e.g., WHO or CDC) might release **weekly aggregated** data with cumulative cases and hospitalizations, which requires different handling.

| location     | week_start  | cumulative_cases | cumulative_hospitalizations | cumulative_deaths |
|--------------|-------------|------------------|-----------------------------|-------------------|
| United States | 2022-01-03  | 50000            | 500                         | 1000              |
| United States | 2022-01-10  | 55000            | 530                         | 1050              |
| United States | 2022-01-17  | 60000            | 560                         | 1100              |

#### Key Differences:
1. **Weekly Data**: Data is reported by week (`week_start`), not daily.
2. **Cumulative Incidence**: Cases and hospitalizations are reported as cumulative totals, which means we need to calculate the **difference** between weeks to get the **weekly incidence**.
3. **Prevalence** needs to be calculated using custom time windows over these weekly intervals.

#### Approach:
We will:
1. **Compute weekly incidence** from the cumulative totals.
2. **Convert weekly incidence to prevalence** using rolling sums with adjusted windows to reflect weekly reporting.

##### Pseudo Code Example:
```python
# First calculate the weekly incidence
df["weekly_cases"] = df["cumulative_cases"].diff().fillna(0)
df["weekly_hospitalizations"] = df["cumulative_hospitalizations"].diff().fillna(0)
df["weekly_deaths"] = df["cumulative_deaths"].diff().fillna(0)

# Now convert to prevalence based on weekly data:
window_weeks = user_specified_window or 2  # 14 days is roughly 2 weeks

# Infected Prevalence (I)
prevalence_I = df["weekly_cases"].rolling(window_weeks).sum().dropna()

# Hospitalized Prevalence (H)
prevalence_H = df["weekly_hospitalizations"].rolling(window_weeks).sum().dropna()

# Deaths (D)
prevalence_D = df["cumulative_deaths"]

# Recovered (R)
prevalence_R = df["cumulative_cases"].shift(window_weeks) - prevalence_D

# Combine into final DataFrame
final_df = pd.DataFrame({
    "I": prevalence_I,
    "R": prevalence_R,
    "H": prevalence_H,
    "D": prevalence_D,
    "time": df["week_start"]
}).dropna().set_index("time")
```

### Example 6: Global Data with Multiple Countries and Granularity

#### Dataset Example:
In global datasets, organizations like the WHO might report data for multiple countries with varying levels of granularity (e.g., daily vs. weekly).

| Country      | Date        | Confirmed_Cases | New_Hospitalizations | Deaths  |
|--------------|-------------|-----------------|----------------------|---------|
| United States | 2022-01-01  | 500             | 20                   | 15      |
| United Kingdom| 2022-01-01  | 600             | 25                   | 10      |
| Germany      | 2022-01-01  | 450             | 15                   | 12      |
| United States | 2022-01-02  | 520             | 18                   | 17      |

#### Key Differences:
1. **Multiple Countries**: Data is reported for several countries, requiring handling of the `Country` field.
2. **Granularity**: Data might be reported daily or weekly, depending on the country.
3. **Different naming conventions**: Confirmed cases, new hospitalizations, and deaths are labeled differently.

#### Approach:
- **Filter by country** as necessary.
- **Handle varying granularity** by grouping data appropriately for the specified task (daily or weekly prevalence).
- **Map the column headers** to a consistent format.

##### Pseudo Code Example:
```python
# Filter data by specific country if necessary
df = user_dataset[user_dataset["Country"] == "United States"]

# Rename columns for consistency
df = df.rename(columns={
    "Confirmed_Cases": "incident_cases",
    "New_Hospitalizations": "incident_hospitalizations",
    "Deaths": "cumulative_deaths"
})

# Convert to prevalence:
window_days = user_specified_window or 14  # Assuming 14 days for recovery

# Infected Prevalence (I)
prevalence_I = df["incident_cases"].rolling(window_days).sum().dropna()

# Hospitalized Prevalence (H)
prevalence_H = df["incident_hospitalizations"].rolling(window_days).sum().dropna()

# Deaths (D)
prevalence_D = df["cumulative_deaths"]

# Recovered (R)
prevalence_R = df["incident_cases"].cumsum().shift(window_days) - prevalence_D

# Combine into a final DataFrame
final_df = pd.DataFrame({
    "I": prevalence_I,
    "R": prevalence_R,
    "H": prevalence_H,
    "D": prevalence_D,
    "time": df["Date"]
}).dropna().set_index("time")
```