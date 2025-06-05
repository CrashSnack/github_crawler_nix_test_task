# 📘 GitHub Search Crawler

## 📝 Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage example](#usage)
4. [Testing](#testing)

## <a name="requirements"></a> ☑️ Requirements

All Python dependencies for the Scraper module are listed in [`requirements.txt`](requirements.txt).

## <a name="installation"></a> 🖥️ Installation

Clone or download the [`src`](src) folder into your project directory.
For tests installation you can also clone or download the [`tests`](tests) folder.
Also also clone or download [`run_crawler.py`](run_crawler.py) if you want a test example of how to use the module.

## <a name="usage"></a>▶️ Usage Example

A complete usage example of a crawler with [`run_crawler.py`](run_crawler.py) is provided below:

```shell
python run_crawler.py --keywords dropbox,box --type Wikis --proxies YOUR:PROXIE:1:1,YOUR:PROXIE:1:2
```

## <a name="testing"></a>⚙️ Testing and coverage check

All tests for this module use `pytest`. Tests are located at [`tests\test_github_crawler.py`](tests\test_github_crawler.py). To run them, go to the [`tests`](tests) folder and run next command:

```shell
pytest test_github_crawler.py -s
```

For the coverage check `coverage` library is being used with next two commands inside [`tests`](tests) folder:

```shell
coverage run -m pytest
coverage report -m
```