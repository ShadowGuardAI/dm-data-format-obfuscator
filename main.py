import argparse
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom
import logging
import random
from faker import Faker
import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Faker
fake = Faker()

class DataFormatObfuscator:
    """
    Transforms data into a visually similar but structurally different format to prevent direct interpretation.
    Supports JSON to XML and date format changes.
    """

    def __init__(self, input_file, output_file, transformation_type):
        """
        Initializes the DataFormatObfuscator.

        Args:
            input_file (str): Path to the input file.
            output_file (str): Path to the output file.
            transformation_type (str): Type of transformation to apply (e.g., 'json_to_xml', 'date_obfuscation').
        """
        self.input_file = input_file
        self.output_file = output_file
        self.transformation_type = transformation_type

    def load_data(self):
        """
        Loads data from the input file based on the expected format.

        Returns:
            The loaded data.  The type varies based on file content.

        Raises:
            FileNotFoundError: If the input file does not exist.
            ValueError: If the file type is not supported.
        """
        try:
            with open(self.input_file, 'r') as f:
                if self.input_file.lower().endswith('.json'):
                    return json.load(f)
                elif self.input_file.lower().endswith('.xml'):
                    # Parse XML directly.  The obfuscation logic can handle it.
                    return ET.parse(f)
                else:
                    raise ValueError("Unsupported file type. Only JSON and XML are supported.")
        except FileNotFoundError:
            logging.error(f"Input file not found: {self.input_file}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON in file: {self.input_file}")
            raise
        except ET.ParseError:
            logging.error(f"Failed to parse XML in file: {self.input_file}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading data: {e}")
            raise


    def transform_json_to_xml(self, data):
        """
        Transforms JSON data to XML format with obfuscated field names.

        Args:
            data (dict): JSON data to transform.

        Returns:
            str: XML representation of the data.
        """
        try:
            root = ET.Element("root")  # Root element for XML
            self._json_to_xml_recursive(data, root)
            return self._prettify_xml(root)
        except Exception as e:
            logging.error(f"Error during JSON to XML transformation: {e}")
            raise

    def _json_to_xml_recursive(self, data, parent):
        """
        Recursively converts JSON data to XML elements, obfuscating field names.

        Args:
            data (dict or list or str): JSON data to convert.
            parent (xml.etree.ElementTree.Element): Parent XML element.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                obfuscated_key = fake.word()  # Generate a random word for the new key
                element = ET.SubElement(parent, obfuscated_key)
                self._json_to_xml_recursive(value, element)
        elif isinstance(data, list):
            for item in data:
                element = ET.SubElement(parent, fake.word())  # use a random word for list items
                self._json_to_xml_recursive(item, element)
        else:
            parent.text = str(data)

    def _prettify_xml(self, elem):
        """
        Return a pretty-printed XML string for the Element.
        """
        try:
            rough_string = ET.tostring(elem, 'utf-8')
            reparsed = xml.dom.minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            logging.error(f"Error prettifying XML: {e}")
            return ET.tostring(elem, 'utf-8').decode('utf-8')

    def transform_date_format(self, data):
        """
        Obfuscates date formats within the data.  This is applied recursively.

        Args:
            data (any): The data structure to obfuscate (dict, list, string, etc.)

        Returns:
            any: The obfuscated data.
        """
        try:
            if isinstance(data, dict):
                return {k: self.transform_date_format(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self.transform_date_format(item) for item in data]
            elif isinstance(data, str):
                # Attempt to parse as date and reformat
                try:
                    date_obj = datetime.datetime.strptime(data, '%Y-%m-%d') # Common format - adjust as needed.
                    new_format = random.choice(['%m/%d/%Y', '%d.%m.%Y', '%Y/%m/%d', '%d-%b-%Y'])
                    return date_obj.strftime(new_format)
                except ValueError:
                    # Not a recognizable date, return the original string
                    return data
            else:
                return data # Return non-string data unchanged
        except Exception as e:
            logging.error(f"Error during date format transformation: {e}")
            raise

    def process_data(self):
        """
        Processes the data based on the specified transformation type.
        """
        try:
            data = self.load_data()

            if self.transformation_type == 'json_to_xml':
                transformed_data = self.transform_json_to_xml(data)
            elif self.transformation_type == 'date_obfuscation':
                transformed_data = self.transform_date_format(data)
            else:
                raise ValueError(f"Unsupported transformation type: {self.transformation_type}")

            self.save_data(transformed_data)

        except Exception as e:
            logging.error(f"Data processing failed: {e}")
            raise

    def save_data(self, data):
        """
        Saves the transformed data to the output file.

        Args:
            data (str or any): The transformed data to save.
        """
        try:
            with open(self.output_file, 'w') as f:
                if self.transformation_type == 'json_to_xml':
                    f.write(data)
                elif self.transformation_type == 'date_obfuscation':
                    # For date obfuscation, try to dump back to JSON if the original was JSON.  Otherwise, just write the string.
                    if self.input_file.lower().endswith('.json'):
                        json.dump(data, f, indent=4)
                    else:
                        f.write(str(data))  # Handle cases where the input wasn't JSON.
                else:
                    f.write(str(data))
            logging.info(f"Data saved to {self.output_file}")
        except Exception as e:
            logging.error(f"Failed to save data to file: {self.output_file}. Error: {e}")
            raise


def setup_argparse():
    """
    Sets up the argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(description="Transforms data into a visually similar but structurally different format.")
    parser.add_argument("-i", "--input", dest="input_file", required=True, help="Path to the input file.")
    parser.add_argument("-o", "--output", dest="output_file", required=True, help="Path to the output file.")
    parser.add_argument("-t", "--type", dest="transformation_type", required=True, choices=['json_to_xml', 'date_obfuscation'], help="Type of transformation to apply (json_to_xml, date_obfuscation).")
    return parser

def main():
    """
    Main function to parse arguments and execute the data transformation.
    """
    try:
        parser = setup_argparse()
        args = parser.parse_args()

        # Input validation: check if input file exists.
        if not os.path.exists(args.input_file):
            raise FileNotFoundError(f"The input file '{args.input_file}' does not exist.")

        obfuscator = DataFormatObfuscator(args.input_file, args.output_file, args.transformation_type)
        obfuscator.process_data()

        logging.info("Data obfuscation completed successfully.")

    except FileNotFoundError as e:
        logging.error(e)
    except ValueError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()