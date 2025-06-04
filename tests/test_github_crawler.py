# Add src directory from one directory above to the Python path
import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from github_crawler import GitHub_Crawler, ProxyRotator, GitHub_Search_Type

import pytest
from bs4 import BeautifulSoup
from typing import List
import json


def get_test_html_code(empty_html:bool = False) -> str:
    """
    A fixture to get the test HTML code for parsing search results.
    :param empty_html: if True, returns a response with empty search result.
    :return: the HTML code as a string.
    """
    if not empty_html:
        with open('props/test.html', encoding='utf-8') as file:
            html_code = file.read()
    else:
        with open('props/test_2.html', encoding='utf-8') as file:
            html_code = file.read()
    return html_code

def get_urls_list(empty_urls:bool = False) -> str:
    """
    A fixture to get a list of URLs for testing.
    :param empty_urls: if True, returns an empty list.
    :return: a JSON string of URLs.
    """
    if not empty_urls:
        with open('props/test_urls.json') as file:
            json_string = json.dumps(json.loads(file.read()))
    else:
        json_string = json.dumps([])
    return json_string

class Test_GitHub_Crawler(GitHub_Crawler):
    # @pytest.mark.skip(reason="For this test we actually need always to have a single working proxy, which we cannot afford for the test task, so this test will almost always fail.")
    def test_make_request(self, url = "https://google.com/", headers:dict = {}, proxy:str = "http://1.1.1.1:8080", timeout:int=None) -> str:
        """
        A test method to make a request to the specified URL with the given headers and proxy.
        
        :param url: the URL to make the request to.
        :param headers: the headers to include in the request.
        :param proxy: the proxy to use for the request.
        :param timeout: timeout for the request in seconds.
        :return: the response from the request.
        :raise: an exception if the request fails.
        """
        try:
            super().make_request(url, headers, proxy, timeout)
        except Exception as e:
            pytest.fail(f"Request failed: {e}")
    
    @pytest.mark.parametrize("expected_list", [get_urls_list(empty_urls=False), get_urls_list(empty_urls=True)])
    def test_parse_search_results(self, expected_list:list) -> List[dict]:
        """
        A method to test the parsing of the search results from the HTML response. Test if search results is empty or not.
        
        :param expected_list: the expected list of URLs as a JSON string.
        :return: a list of parsed search results.
        :raise: an assertion error if the parsed results do not match the expected list.
        """
        github_base_url = "https://github.com"
        
        if expected_list != "[]":
            html = get_test_html_code(empty_html=False)
        else:  
            html = get_test_html_code(empty_html=True)
        
        soup = BeautifulSoup(html, 'html.parser')
        all_search_divs = soup.find_all('div', class_ = "search-title")
        all_a = []
        for search_div in all_search_divs:
            all_a.extend(search_div.find_all('a', class_ = "prc-Link-Link-85e08"))
        url_list = [{"url": github_base_url + a['href']} for a in all_a if a and 'href' in a.attrs and a['href']] if all_a else []
        
        assert json.dumps(url_list) == expected_list, f"Expected {expected_list}, but got {url_list}"

    @pytest.mark.parametrize("keywords, type, proxies", [("dropbox box", GitHub_Search_Type.Repositories, ["1.1.1.1:8080"]), ("dropbox box wdfdqd dwq", GitHub_Search_Type.Wikis, None)])
    @pytest.mark.skip(reason="For this test we actually need always to have a single working proxy, which we cannot afford for the test task, so this test will almost always fail.")
    def test_search(self, keywords:str|List[str], type:GitHub_Search_Type, proxies:List[str], headers:dict = None, timeout:int = 30, retries:int = 5) -> List[dict]:
        """
        A method to test the search on GitHub for repositories, issues, or wikis based on keywords.
        
        :param keywords: a string separeted by spaces or list of strings to search for.
        :param type: the type of search to perform (repositories, issues, wikis).
        :param proxies: additional list of proxies to use for the request.
        :param headers: additional headers to include in the request.
        :param timeout: timeout for the request in seconds.
        :param retries: number of retries to make the request in case of failure.
        :raise: an error if requests were unsuccesfull.
        """
        if isinstance(keywords, str):
            keywords = keywords.split()
        
        keywords = [str(keyword).strip() for keyword in keywords]
        
        query = '+'.join(keywords)
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
    
def test_search_no_results(monkeypatch):
    """
    Test the search method of the GitHub_Crawler class when no results are found.
    
    :raise: an assertion error if the method returns results when it should not.
    """
    class DummyCrawler(GitHub_Crawler):
        def make_request(self, url, headers, proxy, timeout):
            return "<html></html>"  # no .search-title div

    crawler = DummyCrawler()
    results = crawler.search("somegibberishthatmatchesnothing", GitHub_Search_Type.Wikis, proxies=["http://1.1.1.1:8080"], retries=1)
    assert results == [], f"Expected no results, got: {results}"

def test_search_retries(monkeypatch):
    """
    Test the search method of the GitHub_Crawler class when retries are needed.
    
    :raise: an assertion error if the method does not retry the specified number of times.
    """
    class DummyCrawler(GitHub_Crawler):
        def make_request(self, url, headers, proxy, timeout):
            raise Exception("Always fails")

    crawler = DummyCrawler()
    results = crawler.search("dropbox", GitHub_Search_Type.Repositories, proxies=["http://1.1.1.1:8080"], retries=3)
    assert results == []

@pytest.mark.parametrize("proxies", [(["1.1.1.1:8080"]), (["http://1.1.1.1:8080"]), ([])])     
def test_proxy_rotator_get_proxy(proxies:List[str]):
    """
    Test the get_proxy method of the ProxyRotator class.
    
    :raise: an assertion error if the method returns None.
    """
    rotator = ProxyRotator()
    assert rotator.get_proxy() is not None, "ProxyRotator.get_proxy() returned None"
    
def test_proxy_rotator_queue_refill():
    proxies = ["http://1.1.1.1:8080", "http://2.2.2.2:8080"]
    rotator = ProxyRotator(proxies)
    
    # Empty the queue manually
    rotator.queue = []
    
    proxy = rotator.get_proxy()
    assert proxy in proxies, f"Expected proxy from list, got: {proxy}"

def test_get_proxy_list_failure():
    """
    Test the get_proxy_list method of the ProxyRotator class when it fails.
    
    :raise: an exception if the method raises an error.
    """
    class TestProxyRotator(ProxyRotator):
        def get_proxy_list(self, source):
            raise Exception("Mocked failure")

    with pytest.raises(Exception, match="Mocked failure"):
        TestProxyRotator(proxies=None)

@pytest.mark.parametrize("proxies", [(["1.1.1.1:8080"]), (["http://1.1.1.1:8080"]), ([])])
def test_proxy_rotator_initialization(proxies:List[str]):
    """
    Test the initialization of the ProxyRotator class which also test ProxyRotator.get_proxy_list() method when proxies is None.
    
    :raise: an assertion error if the initialization fails.
    """
    try:
        rotator = ProxyRotator()
        assert rotator is not None
    except Exception as e:
        pytest.fail(f"ProxyRotator initialization failed: {e}")

def test_github_crawler_initialization():
    """
    Test the initialization of the GitHub_Crawler class.
    
    :raise: an assertion error if the initialization fails.
    """
    try:
        crawler = GitHub_Crawler()
        assert crawler is not None
    except Exception as e:
        pytest.fail(f"GitHub_Crawler initialization failed: {e}")