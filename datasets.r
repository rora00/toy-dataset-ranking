library(jsonlite)

# Get the list of datasets that can be loaded using load()
datasets_in_base <- data(package = "datasets")$results[, 3]

# Write the list to a JSON file
write_json(datasets_in_base, "r_datasets_list.json")