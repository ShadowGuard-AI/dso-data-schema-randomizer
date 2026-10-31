#!/usr/bin/env python
import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
import csv
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataSchemaRandomizer:
    """
    Generates random, but structurally valid, schema for various data formats.
    """

    def __init__(self, data_format, input_file=None, output_file=None, locale='en_US'):
        """
        Initializes the DataSchemaRandomizer.

        Args:
            data_format (str): The format of the data (e.g., json, xml, csv).
            input_file (str, optional): Path to the input file. Defaults to None.
            output_file (str, optional): Path to the output file. Defaults to None.
            locale (str, optional): Faker locale. Defaults to 'en_US'.
        """
        self.data_format = data_format.lower()
        self.input_file = input_file
        self.output_file = output_file
        self.fake = Faker(locale)

        if self.data_format not in ['json', 'xml', 'csv']:
            raise ValueError(f"Unsupported data format: {self.data_format}")

    def randomize_json_value(self, value):
        """Randomizes individual values based on their type."""
        # bool is tested before int on purpose: bool is a subclass of
        # int in Python, so the old order sent every true and false
        # through the integer branch and the boolean branch never ran.
        if isinstance(value, bool):
            return self.fake.boolean()  # Replace with random boolean
        elif isinstance(value, str):
            return self.fake.word()  # Replace with random word
        elif isinstance(value, int):
            return self.fake.random_int()  # Replace with random integer
        elif isinstance(value, float):
            return self.fake.pyfloat()  # Replace with random float
        elif isinstance(value, list):
            return [self.randomize_json_value(item) for item in value] # Randomize each item in the list
        elif isinstance(value, dict):
            return self.randomize_json_schema(value)  # Recursively randomize nested dictionaries
        else:
            return None # Handle unknown data types

    def randomize_json_schema(self, input_data):
        """
        Randomizes a JSON schema.

        Args:
            input_data (dict): The input JSON data as a dictionary.

        Returns:
            dict: The randomized JSON data.
        """

        if not isinstance(input_data, dict):
            logging.error("Input data must be a dictionary for JSON format.")
            raise TypeError("Input data must be a dictionary for JSON format.")

        randomized_data = {}
        for key, value in input_data.items():
            # Faker words come from a small vocabulary and can repeat. A
            # repeated randomized key would silently merge two entries and
            # shrink the object, so collisions are redrawn.
            new_key = self.fake.word()
            while new_key in randomized_data:
                new_key = self.fake.word()
            randomized_data[new_key] = self.randomize_json_value(value) # Randomize Key and Value

        return randomized_data

    def randomize_xml_schema(self, input_xml):
        """
        Randomizes an XML schema.

        Args:
            input_xml (str): The input XML data as a string.

        Returns:
            str: The randomized XML data as a string.
        """
        try:
            root = ET.fromstring(input_xml)
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            raise

        # One replacement per distinct original tag, reused at every
        # occurrence. A fresh tag per element split sibling elements that
        # shared a tag into unrelated names and broke the structure a
        # downstream parser relies on. Collisions with a tag already
        # assigned to a different original are redrawn, as in JSON keys.
        tag_map = {}

        def replacement_tag(tag):
            if tag not in tag_map:
                new_tag = self.fake.word()
                while new_tag in tag_map.values():
                    new_tag = self.fake.word()
                tag_map[tag] = new_tag
            return tag_map[tag]

        def randomize_element(element):
            """Randomizes element tags, text, and attribute values."""
            element.tag = replacement_tag(element.tag) # Randomize element tag
            if element.text:
                element.text = self.fake.word() # Randomize element text
            # Attribute values are data too: an id attribute kept its real
            # value while everything around it was randomized.
            for attr in element.attrib:
                element.attrib[attr] = self.fake.word()
            for child in element:
                randomize_element(child)

        randomize_element(root)
        return ET.tostring(root, encoding='utf8').decode('utf8')


    def randomize_csv_schema(self, input_csv):
        """
        Randomizes a CSV schema.

        Args:
            input_csv (str): The input CSV data as a string.

        Returns:
            str: The randomized CSV data as a string.
        """
        reader = csv.reader(input_csv.splitlines())
        rows = list(reader)

        if not rows or not any(cell.strip() for row in rows for cell in row):
            logging.error("CSV file is empty: nothing to randomize.")
            raise ValueError("CSV file is empty: nothing to randomize.")

        header = rows[0] #get header

        #Randomize Header. Faker words can repeat, and a repeated header
        #name would merge two columns for a reader keyed by name, so a
        #colliding name is redrawn, as the JSON path does for keys.
        randomized_header = []
        for _ in header:
            new_name = self.fake.word()
            while new_name in randomized_header:
                new_name = self.fake.word()
            randomized_header.append(new_name)

        randomized_rows = [randomized_header]

        for row in rows[1:]:
             randomized_row = [self.fake.word() for _ in row]
             randomized_rows.append(randomized_row)

        output = ""
        for row in randomized_rows:
             output += ",".join(row) + "\n"
        return output

    def process_data(self):
        """
        Processes the data based on the specified format.

        Raises:
            ValueError: If the input file is not provided.
            FileNotFoundError: If the input file does not exist.
            Exception: If an error occurs during data processing.
        """

        if not self.input_file:
            logging.error("Input file is required.")
            raise ValueError("Input file is required.")

        # Refuse in place output: an output path that resolves to the
        # input file (same spelling, ./ alias, or symlink) would destroy
        # the original before anyone can compare the two.
        if self.output_file and os.path.realpath(self.output_file) == os.path.realpath(self.input_file):
            logging.error("Output file resolves to the input file; refusing to overwrite it in place.")
            raise ValueError("Output file resolves to the input file; refusing to overwrite it in place.")

        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = f.read()
        except FileNotFoundError:
            logging.error(f"File not found: {self.input_file}")
            raise FileNotFoundError(f"File not found: {self.input_file}")
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            raise

        try:
            if self.data_format == 'json':
                input_data = json.loads(data)
                # An empty object or list holds nothing to randomize, so
                # it fails instead of writing itself back under a success
                # line.
                if isinstance(input_data, (dict, list)) and not input_data:
                    logging.error("JSON input is empty: nothing to randomize.")
                    raise ValueError("JSON input is empty: nothing to randomize.")
                # A top level list of records is valid JSON input, not an
                # error: randomize each item and keep the list shape.
                if isinstance(input_data, dict):
                    randomized_data = self.randomize_json_schema(input_data)
                elif isinstance(input_data, list):
                    randomized_data = [self.randomize_json_value(item) for item in input_data]
                else:
                    randomized_data = self.randomize_json_value(input_data)
                output_data = json.dumps(randomized_data, indent=4)
            elif self.data_format == 'xml':
                output_data = self.randomize_xml_schema(data)
            elif self.data_format == 'csv':
                output_data = self.randomize_csv_schema(data)
            else:
                raise ValueError(f"Unsupported data format: {self.data_format}")

            if self.output_file:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                logging.info(f"Randomized data written to {self.output_file}")
            else:
                print(output_data)
                logging.info("Randomized data printed to console.")

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            raise
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            raise


def setup_argparse():
    """
    Sets up the argument parser.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(description="Generates random schema for data formats (JSON, XML, CSV).")
    parser.add_argument("data_format", choices=['json', 'xml', 'csv'], help="The format of the data.")
    parser.add_argument("input_file", help="Path to the input file.")
    parser.add_argument("-o", "--output_file", help="Path to the output file (optional). If not provided, output will be printed to the console.", required=False)
    parser.add_argument("-l", "--locale", help="Faker locale (e.g., en_US, fr_FR). Defaults to en_US.", default="en_US", required=False)

    return parser


def main():
    """
    Main function to execute the data schema randomizer.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    try:
        randomizer = DataSchemaRandomizer(args.data_format, args.input_file, args.output_file, args.locale)
        randomizer.process_data()
    except ValueError as e:
        logging.error(f"Value Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logging.error(f"File Not Found Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Usage Examples:

1. Randomize a JSON file and print to console:
   python dso_data_schema_randomizer.py json input.json

2. Randomize a JSON file and save to an output file:
   python dso_data_schema_randomizer.py json input.json -o output.json

3. Randomize an XML file and save to an output file:
   python dso_data_schema_randomizer.py xml input.xml -o output.xml

4. Randomize a CSV file and save to an output file:
   python dso_data_schema_randomizer.py csv input.csv -o output.csv

5. Randomize a JSON file with french locale
   python dso_data_schema_randomizer.py json input.json -l fr_FR -o output.json

"""