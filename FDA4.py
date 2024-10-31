import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# FDA Drug Label API URL
url = "https://api.fda.gov/drug/label.json"

# Streamlit App Title
st.title("FDA Drug Approval Dashboard")

# Sidebar for search parameters
st.sidebar.header("Search Parameters")

# Date inputs for the search range
start_date = st.sidebar.date_input("Start Date", datetime(2024, 10, 1))
end_date = st.sidebar.date_input("End Date", datetime(2024, 10, 30))

# Input for manufacturer name with a note on wildcard usage
manufacturer_name = st.sidebar.text_input("Manufacturer Name (first 4 characters)")

# Optional secondary search for generic name
generic_name = st.sidebar.text_input("Generic Name (exact or first 4 characters)")

# Ensure that the start date is not after the end date
if start_date > end_date:
    st.error("Error: Start Date must be before End Date.")
else:
    # Convert dates to the required format (YYYYMMDD)
    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    # Base search parameter with date range
    search_query = f"effective_time:[{start_date_str} TO {end_date_str}]"

    # Add wildcard search for manufacturer if input is provided
    if manufacturer_name:
        manufacturer_search = manufacturer_name[:4] + "*"
        search_query += f" AND openfda.manufacturer_name:{manufacturer_search}"

    # Optional secondary search for generic name
    if generic_name:
        if len(generic_name) > 4:
            search_query += f" AND openfda.generic_name.exact:\"{generic_name}\""
        else:
            generic_search = generic_name[:4] + "*"
            search_query += f" AND openfda.generic_name:{generic_search}"

    # Parameters for the API request
    params = {
        "search": search_query,
        "limit": 500  # Limit to 500 results
    }

    # Fetch data button
    if st.sidebar.button("Fetch Drug Labels"):
        try:
            # Send request to FDA API
            response = requests.get(url, params=params)
            response.raise_for_status()  # Check for errors

            # Parse JSON response
            data = response.json()
            results = data.get('results', [])

            # If results are found, create a DataFrame
            if results:
                # Extract relevant fields for the DataFrame
                drug_data = []
                for drug in results:
                    drug_data.append({
                        "Brand Name": drug.get('openfda', {}).get('brand_name', ['N/A'])[0],
                        "Generic Name": drug.get('openfda', {}).get('generic_name', ['N/A'])[0],
                        "Manufacturer Name": drug.get('openfda', {}).get('manufacturer_name', ['N/A'])[0],
                        "Effective Time": drug.get('effective_time', 'N/A')
                    })

                # Create a DataFrame
                df = pd.DataFrame(drug_data)

                # Convert Effective Time to datetime and extract month-year for analysis
                df['Effective Time'] = pd.to_datetime(df['Effective Time'], errors='coerce', format='%Y%m%d')
                df['Approval Month'] = df['Effective Time'].dt.to_period('M')

                # Group by month and count approvals
                monthly_counts = df.groupby('Approval Month').size()

                # Display the DataFrame in the app
                st.dataframe(df)

                # Display monthly approval chart
                st.subheader("Monthly Drug Approvals")
                fig, ax = plt.subplots(figsize=(10, 6))
                monthly_counts.plot(kind='bar', ax=ax, color='skyblue')
                ax.set_xlabel("Approval Month")
                ax.set_ylabel("Number of Drugs Approved")
                ax.set_title("Number of Drugs Approved by Month")
                plt.xticks(rotation=45)
                st.pyplot(fig)

                # Downloadable CSV button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name="drug_labels.csv",
                    mime="text/csv"
                )
            else:
                st.info("No drug labels found for the selected parameters.")

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data from FDA API: {e}")
