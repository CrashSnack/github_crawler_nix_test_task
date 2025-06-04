import sys
import os
import argparse

# Add src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from github_crawler import GitHub_Crawler, GitHub_Search_Type

def main(keywords, search_type, proxies):
    print("Keywords:", keywords)
    print("Search Type:", search_type)
    print("Proxies:", proxies)
    
    # Initialize the GitHub crawler
    try:
        github_crawler = GitHub_Crawler()
    except Exception as e:
        print("Error initializing GitHub crawler:", e)

    # Perform the search
    try:
        urls = github_crawler.search(keywords=keywords, type=search_type, proxies=proxies)
    except Exception as e:
        print("Error during search:", e)
        
    print("Search URLs:", urls)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub crawler to search by keywords in desired GitHub section. Comes with proxy support.")
    parser.add_argument(
        "--keywords",
        type=str,
        required=True,
        help="Comma-separated list of keywords"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["Repositories", "Issues", "Wikis"],
        required=True,
        help="Type of search on GitHub"
    )
    parser.add_argument(
        "--proxies",
        type=str,
        required=False,
        help="Comma-separated list of proxies "
    )

    args = parser.parse_args()

    # Parse comma-separated inputs
    try:
        keywords = args.keywords.split(",")
        proxies = args.proxies.split(",")
    except Exception as e:
        print("Error parsing keywords or proxies:", e)
        exit(1)
        
    # Convert search type to GitHub_Search_Type enum
    search_type = GitHub_Search_Type[args.type]

    main(keywords, search_type, proxies)