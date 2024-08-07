import pandas as pd
import translators as ts
from tqdm import tqdm
import os


class TextTranslator:
    """
    A class to translate text from Chinese to Vietnamese using the Baidu translator.
    """

    def __init__(self, professional_field="medicine", sleep_seconds=5, limit_of_length=500000):
        """
        Initialize the TextTranslator with specific translation settings.

        Parameters:
        professional_field (str): The field of expertise for translation (default is "medicine").
        sleep_seconds (int): Sleep time between translations to avoid rate limits (default is 5 seconds).
        limit_of_length (int): Maximum length of text to translate at once (default is 500000).
        """
        self.professional_field = professional_field
        self.sleep_seconds = sleep_seconds
        self.limit_of_length = limit_of_length

    def translate_text(self, text):
        """
        Translate text from Chinese to Vietnamese.

        Parameters:
        text (str or list): The text to be translated.

        Returns:
        str or list: The translated text.
        """
        try:
            if isinstance(text, list):
                # Translate each element recursively if the text is a list
                return [self.translate_text(item) for item in text]
            elif isinstance(text, str):
                # Translate from Chinese to English
                translated_text_en = ts.translate_text(
                    text, translator="baidu", professional_field=self.professional_field,
                    sleep_seconds=self.sleep_seconds, limit_of_length=self.limit_of_length
                )
                # Translate from English to Vietnamese
                translated_text_vi = ts.translate_text(
                    translated_text_en, translator="baidu", to_language="vie", professional_field=self.professional_field,
                    sleep_seconds=self.sleep_seconds, limit_of_length=self.limit_of_length
                )
                return translated_text_vi
            elif text == "" or pd.isnull(text):
                return None  # Return None if the text is empty or null
        except Exception as e:
            print(f"Error translating text: {text}")
            try:
                # Split text by "。"
                segments = text.split("。")
                # Translate each segment individually
                translated_segments = [self.translate_text(segment) for segment in segments]
                # Join translated segments with "."
                return ".".join(translated_segments)
            except Exception as e:
                text = "ERROR need to correct: " + text
                print(f"Error splitting and translating text: {text}")
                return text


class CSVTranslator:
    """
    A class to handle translation of CSV files.
    """

    def __init__(self, input_csv_file, output_csv_file, temp_output_csv_file, translator):
        """
        Initialize the CSVTranslator with file paths and a translator instance.

        Parameters:
        input_csv_file (str): Path to the input CSV file.
        output_csv_file (str): Path to the final output CSV file.
        temp_output_csv_file (str): Path to the temporary output CSV file.
        translator (TextTranslator): An instance of the TextTranslator class.
        """
        self.input_csv_file = input_csv_file
        self.output_csv_file = output_csv_file
        self.temp_output_csv_file = temp_output_csv_file
        self.translator = translator

    def translate_csv(self):
        """
        Translate all text in the CSV file and save the translated content to a new CSV file.
        """
        # Read the input CSV file into a pandas DataFrame
        df = pd.read_csv(self.input_csv_file, encoding="utf-8")

        # Translate all cells in the DataFrame
        translated_rows = []
        for i, row in tqdm(df.iterrows(), total=len(df), desc="Translating Rows", unit="row"):
            if i <= 720:
                continue
            try:
                translated_row = [self.translator.translate_text(cell) for cell in row]
                translated_rows.append(translated_row)
                if (i + 1) % 10 == 0:  # Save every 10 translated rows
                    temp_df = pd.DataFrame(translated_rows, columns=df.columns)
                    temp_df.to_csv(self.temp_output_csv_file, mode='a', index=False, encoding="utf-8")
                    translated_rows = []  # Reset for the next batch
            except Exception as e:
                print(f"Error translating row {i}")

        # Save the remaining translated rows
        if translated_rows:
            temp_df = pd.DataFrame(translated_rows, columns=df.columns)
            temp_df.to_csv(self.temp_output_csv_file, mode='a', index=False, header=False, encoding="utf-8")

        # Concatenate all saved translated parts into a single file
        all_translated_df = pd.concat(map(pd.read_csv, [self.temp_output_csv_file]))
        all_translated_df.to_csv(self.output_csv_file, index=False, encoding="utf-8")

        # Delete the temporary file
        os.remove(self.temp_output_csv_file)

        print("Translation completed. Output written to", self.output_csv_file)


def main():
    """
    Main function to execute the CSV translation.
    """
    input_csv_file = "../data/raw_data.csv"
    output_csv_file = "data_translated.csv"
    temp_output_csv_file = "data_temp.csv"

    translator = TextTranslator()
    csv_translator = CSVTranslator(input_csv_file, output_csv_file, temp_output_csv_file, translator)
    csv_translator.translate_csv()


if __name__ == "__main__":
    main()
