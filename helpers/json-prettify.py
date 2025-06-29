import json, sys

# Path to your JSON file
file_path = sys.argv[1]

# Read and prettify the JSON file
with open(file_path, "r") as file:
    data = json.load(file)

# Write the prettified JSON back to the file
with open(file_path, "w") as file:
    json.dump(data, file, indent=4)

print("JSON file has been prettified!")