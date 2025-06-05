import random
import requests

from bs4 import BeautifulSoup
from enum import Enum
from typing import List
from abc import abstractmethod


class GitHub_Search_Type(Enum):
    """
    An enumeration for the different types of GitHub search.

    Repositories: Search for repositories.
    Issues: Search for issues.
    Wikis: Search for wikis.
    """

    Repositories = 1
    Issues = 2
    Wikis = 3


class ProxyRotator:
    """
    A class to manage a list of proxies and provide a method to get a random proxy.
    It can also fetch a list of proxies from a specified source.

    :param proxies: a list of proxies to use. If None, it will fetch from the source.
    :param get_proxies_retries: number of retries to get the proxies list.
    :param proxies_source: the URL of the proxy list source.
    :param default_proxy_protocol: the default protocol to use for the proxies.
    """

    def __init__(
        self,
        proxies: List[str] = None,
        get_proxies_retries: int = 5,
        proxies_source: str = "https://free-proxy-list.net/",
        default_proxy_protocol: str = "http",
    ):
        self.get_proxies_retries = get_proxies_retries
        if not proxies:
            proxies = self.get_proxy_list(proxies_source)
        self.proxies = proxies[:]

        # Add protocol to proxies if not present
        self.proxies = [
            default_proxy_protocol + "://" + proxy if not "://" in proxy else proxy
            for proxy in self.proxies
        ]
        self.queue = []

    @abstractmethod
    def get_proxy_list(self, source: str) -> List[str]:
        """
        A method to get a list of proxies.

        :param source: the URL of the proxy list source.
        :return: a list of proxies.
        """
        print(f"Getting proxies list from {source}...")
        retries = self.get_proxies_retries
        proxy_list = []
        for i in range(retries):
            if i > 0:
                print(f"Retrying to get proxies list... ({i}/{retries})")
            try:
                proxy_response = requests.get(source)
                if proxy_response.status_code == 200:
                    soup = BeautifulSoup(proxy_response.text, "html.parser")
                    proxy_table = soup.find(
                        "table", {"class": "table table-striped table-bordered"}
                    )

                    # Get first td element in each tr
                    for row in proxy_table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        proxy_list.append(
                            {
                                "ip": cols[0].text.strip(),
                                "port_http": cols[1].text.strip(),
                            }
                        )
                    break
                else:
                    print(
                        f"Failed to get proxies list from {source}. Status code: {proxy_response.status_code}"
                    )
                    continue
            except Exception as err:
                raise Exception("Couldn't get proxies list.", err)

        ip_list = []
        for proxy in proxy_list:
            ip = proxy["ip"]
            port = proxy["port_http"]
            ip_list.append(f"{ip}:{port}")

        return ip_list

    def get_proxy(self):
        """
        A method to get a random proxy from the list.
        If the queue is empty, it will refill it with the proxies list.
        :return: a random proxy from the list.
        """
        if not self.queue:
            self.queue = self.proxies[:]
            random.shuffle(self.queue)  # Shuffle for randomness each round
        return self.queue.pop()


class GitHub_Crawler:
    """
    A class to crawl GitHub for repositories, issues, or wikis based on keywords.

    Example:
        ```python
        crawler = GitHub_Crawler()
        results = crawler.search(
            "example keyword",
            GitHub_Search_Type.Repositories,
            proxies=["http://proxy1:port", "http://proxy2:port"]
        )
        ```
    """

    def make_request(
        self, url: str, headers: dict = {}, proxy: str = None, timeout: int = None
    ) -> str:
        """
        A method to make a request to the specified URL with the given headers and proxy.

        :param url: the URL to make the request to.
        :param headers: the headers to include in the request.
        :param proxy: the proxy to use for the request.
        :param timeout: timeout for the request in seconds.
        :return: the response from the request.
        :raise: an exception if the request fails.
        """
        try:
            response = (
                requests.get(
                    url,
                    headers=headers,
                    proxies={"http": proxy, "https": proxy},
                    timeout=timeout,
                )
                if proxy
                else requests.get(url, headers=headers, timeout=timeout)
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            raise e

    def parse_search_results(self, html: str) -> List[dict]:
        """
        A method to parse the search results from the HTML response.

        :param html: the HTML response from the search request.
        :return: a list of parsed search results.
        """
        github_base_url = "https://github.com"

        soup = BeautifulSoup(html, "html.parser")
        all_search_divs = soup.find_all("div", class_="search-title")
        all_a = []
        for search_div in all_search_divs:
            all_a.extend(search_div.find_all("a", class_="prc-Link-Link-85e08"))
        url_list = (
            [
                {"url": github_base_url + a["href"]}
                for a in all_a
                if a and "href" in a.attrs and a["href"]
            ]
            if all_a
            else []
        )
        return url_list

    def search(
        self,
        keywords: str | List[str],
        type: GitHub_Search_Type,
        proxies: List[str] = None,
        headers: dict = None,
        timeout: int = 30,
        retries: int = 5,
    ) -> List[dict]:
        """
        A method to search GitHub for repositories, issues, or wikis based on keywords.

        :param keywords: a string separeted by spaces or list of strings to search for.
        :param type: the type of search to perform (repositories, issues, wikis).
        :param proxies: additional list of proxies to use for the request.
        :param headers: additional headers to include in the request.
        :param timeout: timeout for the request in seconds.
        :param retries: number of retries to make the request in case of failure.
        :return: a list of search results.
        """
        if isinstance(keywords, str):
            keywords = keywords.split()

        keywords = [str(keyword).strip() for keyword in keywords]

        query = "+".join(keywords)
        url = f"https://github.com/search?q={query}&type={type.name.lower()}"

        proxy_rotator = ProxyRotator(proxies) if proxies else ProxyRotator()

        results = []
        for _ in range(retries):
            proxy = proxy_rotator.get_proxy()
            print(f"Using proxy: {proxy}")
            try:
                print("GET:", url)
                html_response = self.make_request(url, headers, proxy, timeout)
                results = self.parse_search_results(html_response)
                break
            except Exception as e:
                print(f"Error fetching data: {e}")

        print(f"No urls found in {type.name} search results.") if not results else None
        return results
