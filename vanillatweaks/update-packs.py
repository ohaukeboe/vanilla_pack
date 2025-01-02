import urllib.parse
import urllib.request
import json
import sys
import shutil
import os

def fetch_valid_packs():
    try:
        url = "https://vanillatweaks.net/assets/resources/json/1.21/dpcategories.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://vanillatweaks.net/',
        }

        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())

        valid_packs = {}
        for category in data['categories']:
            category_id = category['category'].lower().replace('/', '-').replace(' ', '-')
            for pack in category['packs']:
                valid_packs[pack['name']] = category_id
        return valid_packs
    except urllib.error.URLError as e:
        print(f"Error fetching valid packs: {e}")
        sys.exit(1)

def read_packs_from_file(filename, valid_packs):
    try:
        with open(filename, 'r') as file:
            requested_packs = [line.strip().lower() for line in file if line.strip()]

        categorized_packs = {}
        invalid_packs = []

        for pack in requested_packs:
            if pack in valid_packs:
                category = valid_packs[pack]
                if category not in categorized_packs:
                    categorized_packs[category] = []
                # Don't modify the pack name here
                categorized_packs[category].append(pack)
            else:
                invalid_packs.append(pack)

        if invalid_packs:
            print("Warning: The following packs are invalid:")
            for pack in invalid_packs:
                print(f"- {pack}")

        return categorized_packs
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

def get_download_link(categorized_packs, version="1.21"):
    url = "https://vanillatweaks.net/assets/server/zipdatapacks.php"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://vanillatweaks.net/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Format packs with spaces replaced by plus signs
    formatted_packs = {}
    for category, packs in categorized_packs.items():
        formatted_packs[category] = [pack.replace(' ', '+') for pack in packs]

    # Create JSON string with no extra spaces
    pack_json = json.dumps(formatted_packs, separators=(',', ':'))

    # URL encode the JSON string, but preserve the plus signs
    encoded_json = urllib.parse.quote(pack_json).replace('%2B', '+')

    # Create the final request data
    data = f"packs={encoded_json}&version={version}"

    try:
        req = urllib.request.Request(url, data=data.encode('utf-8'), headers=headers)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())

        if data.get("status") == "success" and data.get("link"):
            return f"https://vanillatweaks.net{data['link']}"
        else:
            print(f"Error: Server response: {data}")
            sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error getting download link: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response from server: {e}")
        sys.exit(1)

def download_packs(url, output_filename="datapacks.zip"):
    try:
        print("Downloading packs...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/zip',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://vanillatweaks.net/',
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response, open(output_filename, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Successfully downloaded to {output_filename}")
    except urllib.error.URLError as e:
        print(f"Error downloading packs: {e}")
        sys.exit(1)

def install_packs():
    install_packs = input("Do you want to install the downloaded packs? (y/n): ").lower()

    if install_packs == 'y':
        try:
            print("Unzipping packs...")
            shutil.unpack_archive("datapacks.zip", "datapacks", 'zip')
            os.remove("datapacks.zip")
            os.system("packwiz refresh")
            print("Successfully installed packs.")
        except Exception as e:
            print(f"Error installing packs: {e}")
            sys.exit(1)

def main():
    file = "vanillatweaks/datapacks.txt"

    valid_packs = fetch_valid_packs()
    categorized_packs = read_packs_from_file(file, valid_packs)

    if not categorized_packs:
        print("No valid packs found to download.")
        sys.exit(1)

    download_url = get_download_link(categorized_packs)
    download_packs(download_url)

    install_packs()

if __name__ == "__main__":
    main()
