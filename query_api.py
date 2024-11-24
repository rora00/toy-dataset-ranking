import requests
import urllib.parse
import json
import time
import os
import csv
from dotenv import load_dotenv


def query_sklearn_datasets(token: str):
    datasets = [
        "load_iris",
        "load_diabetes",
        "load_digits",
        "load_linnerud",
        "load_wine",
        "load_breast_cancer",
    ]

    # Open the CSV file in write mode, creating a new file or overwriting if it exists
    with open(
        "sklearn_datasets_counts.csv", mode="w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        # Write the header row to the CSV file
        writer.writerow(["dataset", "total_count"])

        for dataset in datasets:
            # Original query string
            query = f"sklearn.datasets {dataset} extension:py"

            # URL-encode the query string
            query_url = "https://api.github.com/search/code?q=" + urllib.parse.quote(
                query
            )

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
                continue  # Skip this dataset and move to the next one

            # Parse the JSON response
            data = response.json()

            # Extract and print the total count of results
            total_count = data.get("total_count", 0)
            print(f"{dataset}: {total_count}")

            # Write the result to the CSV file
            writer.writerow([dataset, total_count])


def query_r_datasets(token: str):
    # Read the JSON file
    with open("r_datasets_list.json", "r") as f:
        datasets_list = json.load(f)

    # Open the CSV file in write mode, creating a new file or overwriting if it exists
    with open("r_datasets_counts.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write the header row to the CSV file
        writer.writerow(["dataset", "total_count"])

        # Loop over each dataset in the list
        for dataset in datasets_list:
            # Skip any dataset that has whitespace or dot in the dataset name
            # TODO: Handle these datasets too
            if " " in dataset or "." in dataset:
                continue

            # Original query string
            query = f"data({dataset}) extension:r"

            # URL-encode the query string
            query_url = "https://api.github.com/search/code?q=" + urllib.parse.quote(
                query
            )

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

                        # Extract and print the total count of results
                        total_count = data.get("total_count", 0)
                        print(f"{dataset}: {total_count}")
                        success = True  # Mark success to exit retry loop

                        # Write the result to the CSV file
                        writer.writerow([dataset, total_count])

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
                    break  # Exit the loop if there's an error not related to 403

            # If we failed after all attempts, report the failure
            if not success:
                print(
                    f"Failed to retrieve data for {dataset} after {max_attempts} attempts."
                )


if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()

    # Sets token if exists and queries github
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
    else:
        print("GitHub token retrieved!")
        query_sklearn_datasets(token)
        query_r_datasets(token)
