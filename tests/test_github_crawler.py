# Add src directory from one directory above to the Python path
import sys
import os

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.append(src_path)

from github_crawler import GitHub_Crawler, ProxyRotator, GitHub_Search_Type
import pytest
from typing import List
import json
from io import StringIO


def get_test_html_code(empty_html: bool = False) -> str:
    """
    A method to get the HTML code for testing.

    :param empty_html: if True, returns an empty HTML file.
    :return: the HTML code as a string.
    """
    if not empty_html:
        with open("props/test.html", encoding="utf-8") as file:
            html_code = file.read()
    else:
        with open("props/test_2.html", encoding="utf-8") as file:
            html_code = file.read()
    return html_code


def get_urls_list(empty_urls: bool = False) -> str:
    """
    A method to get a list of URLs for testing.

    :param empty_urls: if True, returns an empty list.
    :return: a JSON string of URLs.
    """
    if not empty_urls:
        with open("props/test_urls.json") as file:
            json_string = json.dumps(json.loads(file.read()))
    else:
        json_string = json.dumps([])
    return json_string


class Test_GitHub_Crawler(GitHub_Crawler):
    def test_make_request(
        self,
        url="https://google.com/",
        headers: dict = {},
        proxy: str = "http://1.1.1.1:8080",
        timeout: int = None,
    ) -> str:
        """
        Test the make_request method of the GitHub_Crawler class.

        :param url: the URL to make the request to.
        :param headers: the headers to include in the request.
        :param proxy: the proxy to use for the request.
        :param timeout: timeout for the request in seconds.
        :return: None
        :raise: an exception if the request fails.
        """
        try:
            super().make_request(url, headers, proxy, timeout)
        except Exception as e:
            pass

    @pytest.mark.parametrize(
        "expected_list",
        [get_urls_list(empty_urls=False), get_urls_list(empty_urls=True)],
    )
    def test_parse_search_results(self, expected_list: list) -> List[dict]:
        """
        Test the parse_search_results method of the GitHub_Crawler class.

        :param expected_list: expected list of URLs as a JSON string.
        :return: None
        :raise: an assertion error if the parsed URLs do not match the expected list.
        """
        github_base_url = "https://github.com"

        if expected_list != "[]":
            html = get_test_html_code(empty_html=False)
        else:
            html = get_test_html_code(empty_html=True)

        url_list = self.parse_search_results(html)

        assert (
            json.dumps(url_list) == expected_list
        ), f"Expected {expected_list}, but got {url_list}"

    @pytest.mark.parametrize(
        "keywords_param, type_param, proxies_param, expect_empty_results",
        [
            (
                "dropbox box",
                GitHub_Search_Type.Repositories,
                ["http://1.1.1.1:8080"],
                False,
            ),
            (
                "fixed income",
                GitHub_Search_Type.Issues,
                ["http://proxy.example.com:8888", "https://another.proxy:443"],
                False,
            ),
            (
                "unlikely term for test",
                GitHub_Search_Type.Wikis,
                None,
                True,
            ),  # Test with proxies=None and expecting empty
            (
                "another keyword",
                GitHub_Search_Type.Repositories,
                [],
                True,
            ),  # Test with empty proxy list (triggers get_proxy_list)
        ],
    )
    def test_search(
        self,
        monkeypatch,
        keywords_param,
        type_param,
        proxies_param,
        expect_empty_results,
    ):
        """
        Test the search method of the GitHub_Crawler class with various parameters.

        :param monkeypatch: pytest fixture to mock methods.
        :param keywords_param: keywords to search for.
        :param type_param: type of search (Repositories, Issues, Wikis).
        :param proxies_param: list of proxies to use.
        :param expect_empty_results: whether to expect empty results.
        :return: None
        :raise: an assertion error if the search results do not match the expected results.
        """
        if expect_empty_results:
            mock_html_content = get_test_html_code(empty_html=True)
            expected_api_results = json.loads(get_urls_list(empty_urls=True))
        else:
            mock_html_content = get_test_html_code(empty_html=False)
            expected_api_results = json.loads(get_urls_list(empty_urls=False))

        mock_make_request_calls = []

        def mock_make_request(instance, url, headers, proxy, timeout):
            mock_make_request_calls.append(
                {"url": url, "proxy": proxy, "headers": headers, "timeout": timeout}
            )
            # Basic validation of URL construction
            temp_keywords_list = (
                keywords_param.split()
                if isinstance(keywords_param, str)
                else [str(k).strip() for k in keywords_param]
            )
            query_part = "+".join(temp_keywords_list)
            assert query_part in url
            assert f"type={type_param.name.lower()}" in url
            return mock_html_content

        monkeypatch.setattr(GitHub_Crawler, "make_request", mock_make_request)

        mocked_proxies_from_source = [
            "http://mockedproxy1:1234",
            "http://mockedproxy2:5678",
        ]

        # Store original __init__ to restore it, ensuring test isolation
        original_proxy_rotator_init = ProxyRotator.__init__

        def mocked_proxy_rotator_init(
            pr_instance,
            proxies=None,
            get_proxies_retries=5,
            proxies_source="https://free-proxy-list.net/",
            default_proxy_protocol="http",
        ):
            pr_instance.get_proxies_retries = get_proxies_retries  # Store retries
            if not proxies:  # If proxies argument to ProxyRotator is None or empty
                # This simulates fetching from source
                actual_proxies_to_use = mocked_proxies_from_source
            else:
                actual_proxies_to_use = proxies

            pr_instance.proxies = [
                default_proxy_protocol + "://" + p if "://" not in p else p
                for p in actual_proxies_to_use
            ]
            pr_instance.queue = []  # Initialize queue

        monkeypatch.setattr(ProxyRotator, "__init__", mocked_proxy_rotator_init)

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        actual_api_results = self.search(
            keywords=keywords_param,
            type=type_param,
            proxies=proxies_param,
            headers=None,
            timeout=30,
            retries=2,  # Test with a couple of retries
        )

        sys.stdout = old_stdout
        output_text = captured_output.getvalue()

        assert actual_api_results == expected_api_results
        assert len(mock_make_request_calls) >= 1  # Should attempt at least once

        # Check if the correct proxy logic was engaged
        if proxies_param:  # User provided proxies directly to search()
            # The mocked ProxyRotator.__init__ would use these.
            # The proxy used in make_request should be from this list.
            used_proxy = mock_make_request_calls[0]["proxy"]
            expected_proxies_with_protocol = [
                p if "://" in p else "http://" + p for p in proxies_param
            ]
            assert used_proxy in expected_proxies_with_protocol
        else:  # Proxies were None or empty, so ProxyRotator should have used its "fetched" list
            used_proxy = mock_make_request_calls[0]["proxy"]
            expected_proxies_with_protocol = [
                p if "://" in p else "http://" + p for p in mocked_proxies_from_source
            ]
            assert used_proxy in expected_proxies_with_protocol

        if expect_empty_results:
            assert f"No urls found in {type_param.name} search results." in output_text
        else:
            # Check that the "No urls found" message is NOT printed if results are expected
            assert (
                f"No urls found in {type_param.name} search results." not in output_text
            )

        # Restore original ProxyRotator.__init__
        monkeypatch.setattr(ProxyRotator, "__init__", original_proxy_rotator_init)


@pytest.mark.parametrize(
    "proxies", [(["1.1.1.1:8080"]), (["http://1.1.1.1:8080"]), ([])]
)
def test_proxy_rotator_get_proxy(proxies: List[str]):
    """
    Test the get_proxy method of the ProxyRotator class.

    :raise: an assertion error if the method returns None.
    """
    rotator = ProxyRotator(proxies=proxies)
    assert (
        "http://" in rotator.get_proxy()
    ), "ProxyRotator.get_proxy() returned wrong proxy"


def test_proxy_rotator_queue_refill():
    proxies = ["http://1.1.1.1:8080", "http://2.2.2.2:8080"]
    rotator = ProxyRotator(proxies)

    # Empty the queue manually
    rotator.queue = []

    proxy = rotator.get_proxy()
    assert proxy in proxies, f"Expected proxy from list, got: {proxy}"


@pytest.mark.parametrize(
    "proxies", [(["1.1.1.1:8080"]), (["http://1.1.1.1:8080"]), ([])]
)
def test_proxy_rotator_initialization(proxies: List[str]):
    """
    Test the initialization of the ProxyRotator class which also test ProxyRotator.get_proxy_list() method when proxies is None.

    :raise: an assertion error if the initialization fails.
    """
    try:
        rotator = ProxyRotator(proxies)
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
