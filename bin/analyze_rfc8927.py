#! /usr/bin/env python3
"""
For more information, visit https://jsontypedef.com/docs/python-codegen/
"""

import json

GLOBAL_KEYS = {}
GLOBAL_KEY_COUNT = {}
GLOBAL_KEY_TYPE = {}
GLOBAL_OUT_OF_ORDER = []
BLACK_LIST = ["description", "elements", "goType", "metadata", "properties", "ref", "optionalproperties", "type"]
EXCLUDE_LIST = []
SENZING_JSON_KEYS = []


def add_to_key_count(key_to_add):
    """Add a key to GLOBAL_KEY_COUNT."""
    if key_to_add not in BLACK_LIST:
        if key_to_add not in GLOBAL_KEY_COUNT:
            GLOBAL_KEY_COUNT[key_to_add] = 1
        else:
            GLOBAL_KEY_COUNT[key_to_add] += 1


def add_to_key_type(key_to_add, value_to_add):
    """Add a key to GLOBAL_KEY_TYPE."""
    if key_to_add not in BLACK_LIST:
        if isinstance(value_to_add, dict):
            if key_to_add not in GLOBAL_KEY_TYPE:
                GLOBAL_KEY_TYPE[key_to_add] = []
            if "type" in value_to_add:
                the_type = value_to_add.get("type")
                if the_type not in GLOBAL_KEY_TYPE[key_to_add]:
                    GLOBAL_KEY_TYPE[key_to_add] += [the_type]
            if "ref" in value_to_add:
                the_ref = value_to_add.get("ref")
                if the_ref not in GLOBAL_KEY_TYPE[key_to_add]:
                    GLOBAL_KEY_TYPE[key_to_add] += [the_ref]


def is_sorted(prefix, list_to_check):
    """Determine if list is sorted.  Return boolean"""
    global GLOBAL_OUT_OF_ORDER
    last_key = ""
    for key_to_check in list_to_check:
        if not key_to_check > last_key:
            GLOBAL_OUT_OF_ORDER += ["Key out of order: {0}.{1} > {2}".format(prefix, last_key, key_to_check)]
        last_key = key_to_check


def add_to_list(prefix, list_to_check):
    """Add a key to GLOBAL_KEYS."""
    key_list = [x for x in list_to_check.keys() if x not in BLACK_LIST]
    if len(key_list) > 0:
        key_list.sort()
        GLOBAL_KEYS[prefix] = key_list


def recurse(prefix, list_to_check):
    """Recurse though dictionary."""
    is_sorted(prefix, list_to_check)
    add_to_list(prefix, list_to_check)
    for key_to_check, value_to_check in list_to_check.items():
        add_to_key_count(key_to_check)
        add_to_key_type(key_to_check, value_to_check)
        if isinstance(value_to_check, dict):
            recurse("{0}.{1}".format(prefix, key_to_check), value_to_check)


def search_list(search_term):
    """Return a list to compare for identical lists."""
    search_results = []
    search_value = GLOBAL_KEYS.get(search_term)
    for key_to_check, value_to_check in GLOBAL_KEYS.items():
        if key_to_check not in EXCLUDE_LIST:
            if value_to_check == search_value:
                EXCLUDE_LIST.append(key_to_check)
                search_results.append(key_to_check)
    return search_results


# -----------------------------------------------------------------------------
# --- Main
# -----------------------------------------------------------------------------

# Read JSON from file.

INPUT_FILENAME = "./testdata/snapshot-RFC8927-00.json"
with open(INPUT_FILENAME, "r", encoding="utf-8") as input_file:
    DATA = json.load(input_file)

# Recurse through dictionary.

recurse("definitions", DATA.get("definitions"))

# Print "out of order" messages.

print("-"*80)
print("\nTEST 1: Verify that the JSON keys are in sorted order.\n")
if len(GLOBAL_OUT_OF_ORDER) > 0:
    for message in GLOBAL_OUT_OF_ORDER:
        print(message)
else:
    print("Everything is sorted properly.")

# Print missing JSON keys.

LISTS = {
    "definitions.Features": DATA.get("definitions", {}).get("Features", {}).get("properties", {}),
    "definitions.FeatureScores": DATA.get("definitions", {}).get("FeatureScores", {}).get("properties", {}),
    "definitions.JsonData": DATA.get("definitions", {}).get("JsonData", {}).get("properties", {}),
    "definitions.MatchInfoCandidateKeys": DATA.get("definitions", {}).get("MatchInfoCandidateKeys", {}).get("properties", {}),
    "definitions.MatchScores": DATA.get("definitions", {}).get("MatchScores", {}).get("properties", {}),
}

print("")
print("-"*80)
print("\nTEST 2: Detect lists not containing mandatory JSON keys.\n")
for key, value in LISTS.items():
    for senzing_json_key in SENZING_JSON_KEYS:
        if senzing_json_key not in value:
            print("Missing {0}.{1}".format(key, senzing_json_key))

print("")
print("-"*80)
print("\nTEST 3: Detect JSON keys not in mandatory list.\n")
for key, value in LISTS.items():
    for key2, value2 in value.items():
        if key2 not in SENZING_JSON_KEYS:
            print("Key not in master list: {0}.{1}".format(key, key2))

# Print result of test for similar lists.

print("")
print("-"*80)
print("\nTEST 4: Detect lists containing same properties.\n")

for key, value in GLOBAL_KEYS.items():
    EXCLUDE_LIST.append(key)
    results = search_list(key)
    if len(results) > 0:
        print("\n{0}:".format(key))
        for result in results:
            print("  - {0}".format(result))

# Print JSON key count results.

print("")
print("-"*80)
print("\nTEST 5: Count occurance of JSON keys")
print("\nCOUNT  KEY")
print("-----  -----------------------------")
SORTED_KEY_COUNTS = sorted(GLOBAL_KEY_COUNT.items(), key=lambda x: x[1], reverse=True)
for key, value in SORTED_KEY_COUNTS:
    if value > 1:
        print("{0:5d}  {1}".format(value, key))

# Print type/ref variances.

print("")
print("-"*80)
print("\nTEST 6: Check for JSON keys having different types\n")
SORTED_GLOBAL_KEY_TYPE = dict(sorted(GLOBAL_KEY_TYPE.items()))
for key, value in SORTED_GLOBAL_KEY_TYPE.items():
    if len(value) > 1:
        print("{0:30s}  {1}".format(key, sorted(value)))


# Epilog.

print("")
print("-"*80)
