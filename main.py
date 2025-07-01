#!/usr/bin/env python
import argparse
import json
import logging
import random
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

        def randomize_value(value):
            """Randomizes individual values based on their type."""
            if isinstance(value, str):
                return self.fake.word()  # Replace with random word
            elif isinstance(value, int):
                return self.fake.random_int()  # Replace with random integer
            elif isinstance(value, float):
                return self.fake.pyfloat()  # Replace with random float
            elif isinstance(value, bool):
                return self.fake.boolean()  # Replace with random boolean
            elif isinstance(value, list):
                return [randomize_value(item) for item in value] # Randomize each item in the list
            elif isinstance(value, dict):
                return self.randomize_json_schema(value)  # Recursively randomize nested dictionaries
            else:
                return None # Handle unknown data types
        
        randomized_data = {}
        for key, value in input_data.items():
            randomized_data[self.fake.word()] = randomize_value(value) # Randomize Key and Value
            
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

        def randomize_element(element):
            """Randomizes element tags and text."""
            element.tag = self.fake.word() # Randomize element tag
            if element.text:
                element.text = self.fake.word() # Randomize element text
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

        if not rows:
            logging.warning("CSV file is empty.")
            return ""

        header = rows[0] #get header

        #Randomize Header
        randomized_header = [self.fake.word() for _ in header]

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
                randomized_data = self.randomize_json_schema(input_data)
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
    except FileNotFoundError as e:
        logging.error(f"File Not Found Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

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