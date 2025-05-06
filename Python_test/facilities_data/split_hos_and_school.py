import pandas as pd

# Read the CSV file; update the filename as needed.
df = pd.read_csv('nz_school_and_hospital_loglat.csv')

# Separate data by facility type
schools_df = df[df['facility_type'] == 'School']
hospitals_df = df[df['facility_type'] == 'Hospital']

# Write each subset to a new CSV file, preserving all columns (including location)
schools_df.to_csv('schools_data.csv', index=False)
hospitals_df.to_csv('hospitals_data.csv', index=False)

print("Files 'schools.csv' and 'hospitals.csv' have been created.")