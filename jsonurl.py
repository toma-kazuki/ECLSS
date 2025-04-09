import requests
import json
import time

# File path to the JSON file
#json_file_path = 'jsonfile/sim_data.json'
json_file_path = 'formatted_sim_data.json'

# URL to post to
# url = 'https://daphne-at-lab.selva-research.com/api/at/receiveHeraFeed'
url = 'http://localhost:8000/api/at/receiveHeraFeed'

def post_json_continuously():
    try:
        while True:
            # Read the JSON file
            with open(json_file_path, 'r') as file:
                json_data = json.load(file)  # Load JSON data from the file

            # Make the POST request
            response = requests.post(url, json=json_data)

            # Print the response status and data
            if response.status_code == 200:
                print("Success:", response.json())
            else:
                print("Failed:", response.status_code)

            # Wait for 1 second before the next request
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("An error occurred:", e)

# Start posting JSON data continuously
if __name__ == '__main__':
    post_json_continuously()