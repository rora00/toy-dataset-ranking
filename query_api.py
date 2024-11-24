import requests
import urllib.parse
import json
import time
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import matplotlib.pyplot as plt


def plot_dataset_usage(sklearn_df: pd.DataFrame, r_df: pd.DataFrame, n_top: int = 10) -> None:
    """Creates a comparative visualization of most used datasets from both sklearn and R using only matplotlib

    Args:
        sklearn_df (pd.DataFrame): DataFrame containing sklearn dataset usage counts
        r_df (pd.DataFrame): DataFrame containing R dataset usage counts
        n_top (int, optional): Number of top datasets to show for each. Defaults to 10.
    """
    # Sort datasets by count and get top N
    sklearn_top = sklearn_df.nlargest(n_top, 'total_count')
    r_top = r_df.nlargest(n_top, 'total_count')
    
    # Create figure and axes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Colors for bars
    colors = plt.cm.viridis(np.linspace(0, 0.8, n_top))
    
    # Plot sklearn datasets
    bars1 = ax1.barh(range(len(sklearn_top)), sklearn_top['total_count'], color=colors)
    ax1.set_yticks(range(len(sklearn_top)))
    ax1.set_yticklabels(sklearn_top['dataset'])
    ax1.set_title('Most Used Scikit-learn Datasets', pad=15)
    ax1.set_xlabel('Number of Repositories')
    ax1.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    # Add value labels on the bars
    for bar in bars1:
        width = bar.get_width()
        ax1.text(width, bar.get_y() + bar.get_height()/2, 
                f'{int(width):,}',
                ha='left', va='center', fontsize=8)
    
    # Plot R datasets
    bars2 = ax2.barh(range(len(r_top)), r_top['total_count'], color=colors)
    ax2.set_yticks(range(len(r_top)))
    ax2.set_yticklabels(r_top['dataset'])
    ax2.set_title('Most Used R Datasets', pad=15)
    ax2.set_xlabel('Number of Repositories')
    ax2.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    # Add value labels on the bars
    for bar in bars2:
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2, 
                f'{int(width):,}',
                ha='left', va='center', fontsize=8)
    
    # Customize the appearance
    plt.style.use('default')  # Clean style
    for ax in [ax1, ax2]:
        # Add spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # Customize ticks
        ax.tick_params(axis='both', which='major', labelsize=9)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('plot.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()


def query_sklearn_datasets(token: str) -> pd.DataFrame:
    """Counts unique repositories where sklearn datasets are imported using Github search API

    Args:
        token (str): Github personal access token

    Returns:
        pd.DataFrame: DataFrame containing dataset names and their usage counts
    """
    datasets = [
        "load_iris",
        "load_diabetes",
        "load_digits",
        "load_linnerud",
        "load_wine",
        "load_breast_cancer",
    ]

    # Initialize lists to store results
    dataset_names = []
    counts = []

    for dataset in datasets:
        # Original query string
        query = f"sklearn.datasets {dataset} extension:py"

        # URL-encode the query string
        query_url = "https://api.github.com/search/code?q=" + urllib.parse.quote(query)

        # Send the GET request to GitHub API
        response = requests.get(
            query_url,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        # Check if the request was successful
        if not response.ok:
            print(f"Request failed for {dataset}: {response.status_code}")
            continue

        # Parse the JSON response
        data = response.json()

        # Extract the total count of results
        total_count = data.get("total_count", 0)
        print(f"{dataset}: {total_count}")

        # Append results to lists
        dataset_names.append(dataset)
        counts.append(total_count)

    # Create DataFrame from results
    df = pd.DataFrame({"dataset": dataset_names, "total_count": counts})

    # Write DataFrame to CSV
    df.to_csv("sklearn_datasets_counts.csv", index=False)

    return df


def query_r_datasets(token: str) -> pd.DataFrame:
    """Counts unique repositories where base R datasets are loaded using Github search API

    Args:
        token (str): Github personal access token

    Returns:
        pd.DataFrame: DataFrame containing dataset names and their usage counts
    """
    # Read the JSON file
    with open("r_datasets_list.json", "r") as f:
        datasets_list = json.load(f)

    # Initialize lists to store results
    dataset_names = []
    counts = []

    # Loop over each dataset in the list
    for dataset in datasets_list:
        # Skip any dataset that has whitespace or dot in the dataset name
        if " " in dataset or "." in dataset:
            continue

        # Original query string
        query = f"data({dataset}) extension:r"

        # URL-encode the query string
        query_url = "https://api.github.com/search/code?q=" + urllib.parse.quote(query)

        # Number of retry attempts
        max_attempts = 10
        attempt = 0
        success = False

        while attempt < max_attempts and not success:
            try:
                # Send the GET request to GitHub API
                response = requests.get(
                    query_url,
                    headers={
                        "Authorization": "Bearer " + token,
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )

                # If the response is successful (status code 200), process it
                if response.ok:
                    # Parse the JSON response
                    data = response.json()

                    # Extract the total count of results
                    total_count = data.get("total_count", 0)
                    print(f"{dataset}: {total_count}")
                    success = True  # Mark success to exit retry loop

                    # Append results to lists
                    dataset_names.append(dataset)
                    counts.append(total_count)

                # Handle 403 response by retrying after 60 seconds
                elif response.status_code == 403:
                    attempt += 1
                    wait_time = 60  # Fixed 60-second wait time before retrying
                    print(
                        f"Rate limit exceeded for {dataset}. Waiting {wait_time} seconds before retrying..."
                    )
                    time.sleep(wait_time)  # Wait before retrying

                else:
                    # For other HTTP errors, raise an exception
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                # Handle general exceptions (e.g., network errors, timeout, etc.)
                print(f"Error querying {dataset}: {e}")
                break

        # If we failed after all attempts, report the failure
        if not success:
            print(
                f"Failed to retrieve data for {dataset} after {max_attempts} attempts."
            )

    # Create DataFrame from results
    df = pd.DataFrame({"dataset": dataset_names, "total_count": counts})

    # Write DataFrame to CSV
    df.to_csv("r_datasets_counts.csv", index=False)

    return df


if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()

    # Sets token if exists and queries github
    token = os.getenv("GITHUB_TOKEN")

    if token:
        print("GitHub token retrieved!")
        sklearn_df = query_sklearn_datasets(token)
        r_df = query_r_datasets(token)

        print("\nCreating visualization...")
        plot_dataset_usage(sklearn_df, r_df)
        print("Visualization saved as plot.png")

        print("\nScikit-learn datasets summary:")
        print(sklearn_df.describe())

        print("\nR datasets summary:")
        print(r_df.describe())
    else:
        print("Error: GITHUB_TOKEN environment variable is not set.")
