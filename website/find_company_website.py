import requests

def find_company_website(company_name):
    query = f"{company_name} official website"
    url = "https://api.duckduckgo.com/"

    try:
        response = requests.get(url, params={
            "q": query,
            "format": "json",
            "pretty": 1
        })

        data = response.json()
        if "Results" in data and len(data["Results"]) > 0:
            return data["Results"][0]["FirstURL"]
        elif "AbstractURL" in data and data["AbstractURL"]:
            return data["AbstractURL"]
        elif "Infobox" in data and "content_urls" in data["Infobox"] and len(data["Infobox"]["content_urls"]) > 0:
            return data["Infobox"]["content_urls"][0]["url"]

    except Exception as e:
        print(f"Error: {e}")

    return None

# Example usage:
company_name = "OpenAI"
website = find_company_website(company_name)
if website:
    print(f"Website for {company_name}: {website}")
else:
    print(f"Website for {company_name} not found.")
