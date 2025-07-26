import streamlit as st
import os
import pandas as pd
import time

# --- Configuration ---
DATA_PATH = "output/mock-data.parquet"

# --- Streamlit UI ---
st.title("Credit Scoring - Synthetic Data Generator")

st.write(
    "Use this tool to generate synthetic credit scoring data. "
    "Specify the number of records you want to create and click 'Start Generation'."
)

# The mock file has 1000 rows, so we limit the input to that.
num_rows = st.number_input(
    "Number of Rows to Generate",
    min_value=1,
    max_value=1000,
    value=100,
    step=10,
)

start_button = st.button("Start Data Generation")

if start_button:
    with st.spinner("Generating data... Please wait."):
        if os.path.exists(DATA_PATH):
            try:
                # Add a short delay to simulate processing
                time.sleep(2)

                # Read the full dataset
                df = pd.read_parquet(DATA_PATH)

                # Sample the dataframe to match the user's input
                display_df = df.sample(n=num_rows).reset_index(drop=True)

                # Display the result
                st.dataframe(display_df)
                st.success(
                    f"Successfully generated {num_rows} rows of synthetic data."
                )

            except Exception as e:
                st.error(f"An error occurred while generating data.")
                st.error(f"Error: {e}")
        else:
            st.error("The required data file could not be found.")
            st.info("Please ensure the application is set up correctly.")
