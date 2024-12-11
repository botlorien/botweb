import os
import time
import json
import html
import shutil
import logging
import getpass
import platform
import requests
import subprocess

from requests import Response
from bs4 import BeautifulSoup
from typing import Optional, List
from abc import ABC, abstractmethod
from urllib.parse import urlencode, unquote
from bs4.element import Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .exceptions import (
    EmptyCookies,
    TokenNotFound,
    PrefixEnvNotSet
)
from .decorators import retry


class BotWeb(ABC):
    _profile_path: str | None
    _path_to_downloads: str | None
    _browser: str | None
    _ignore_profile: bool | None
    _headless: bool | None
    _extensions: list | None
    _driver: WebDriver | None
    _cookies: list | None
    _session: requests.Session | None

    def __init__(
            self,
            prefix_env: Optional[str] = None,
            credentials_keys: Optional[List[str]] = None
            ):
        self._profile_path = None
        self._path_to_downloads = None
        self._browser = None
        self._ignore_profile = True
        self._headless = False
        self._extensions = None
        self._driver = None
        self._cookies = None
        self._session = None

        self.session = requests.Session()
        self.prefix_env = prefix_env
        self.credentials_keys = credentials_keys
        if self.credentials_keys:
            self.credentials = dict.fromkeys(self.credentials_keys)
            self._load_credentials()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.quit()
        return False

    def quit(self):
        self.driver.quit()

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, new):
        if isinstance(new, requests.Session):
            self._session = new
        else:
            raise TypeError(
                f"Invalid type for session: {type(new)}"
                f"Expected: {requests.Session}"
            )

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    def cookies(self, new):
        if isinstance(new, list):
            self._cookies = new
        else:
            raise TypeError(
                f"Invalid type for cookies: {type(new)}"
                f"Expected: {list}"
            )

    @property
    def driver(self):
        return self._driver

    @driver.setter
    def driver(self, new):
        if isinstance(new, WebDriver):
            self._driver = new
        else:
            raise TypeError(
                f"Invalid type for driver: {type(new)}"
                f"Expected: {WebDriver}"
            )

    @property
    def credentials_keys(self):
        return self._credentials_keys

    @credentials_keys.setter
    def credentials_keys(self, new):
        if new and not self.prefix_env:
            raise PrefixEnvNotSet(
                "prefix_env doesn't could be None of falsy"
                "when credentials_keys is provided!"
            )
        if isinstance(new, list):
            self._credentials_keys = [str(s).upper() for s in new]
        else:
            raise TypeError(
                f"Invalid type for credentials_keys: {type(new)}"
                f"Expected: {list}"
            )

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, new):
        if not isinstance(new, dict):
            raise TypeError(
                (
                    "The type for credentials parameter needs to be dict type."
                    f" Got {type(new)}"
                )
            )
        else:
            self._credentials = new

    @property
    def browser(self):
        return self._browser

    @browser.setter
    def browser(self, new):
        if isinstance(new, str):
            self._browser = new.lower()
        else:
            raise TypeError(
                f"Invalid type for browser: {type(new)}. "
                f"Expected {str}"
            )

    @property
    def profile_path(self):
        return self._profile_path

    @profile_path.setter
    def profile_path(self, new):
        if new:
            if isinstance(new, str):
                new = os.path.abspath(new)
                os.makedirs(new, exist_ok=True)
                self._profile_path = new
            else:
                raise TypeError(
                    f"Invalid type for profile_path: {type(new)}. "
                    f"Expected {str}"
                )

    @property
    def ignore_profile(self):
        return self._ignore_profile

    @ignore_profile.setter
    def ignore_profile(self, new):
        if isinstance(new, bool):
            self._ignore_profile = new
        else:
            raise TypeError(
                f"Invalid type for ignore_profile: {type(new)}. " 
                f"Expected {bool}"
            )

    @property
    def path_to_downloads(self):
        return self._path_to_downloads

    @path_to_downloads.setter
    def path_to_downloads(self, new):
        if isinstance(new, str) and len(new.strip()) > 0:
            new = os.path.abspath(new)
            os.makedirs(new, exist_ok=True)
            self._path_to_downloads = new
        else:
            raise ValueError(
                f"Invalid value for path_to_downloads: {new}. "
                f"Expected {str} of length > 0"
            )

    @property
    def headless(self):
        return self._headless

    @headless.setter
    def headless(self, new):
        if isinstance(new, bool):
            self._headless = new
        else:
            raise TypeError(
                f"Invalid type for headless: {type(new)}. " f"Expected {bool}"
            )

    @property
    def action_chains(self):
        return self._action_chains

    @action_chains.setter
    def action_chains(self, new):
        if isinstance(new, ActionChains):
            self._action_chains = new
        else:
            raise TypeError(
                f"Invalid type for action_chains: {type(new)}. "
                f"Expected {ActionChains}"
            )

    @property
    def extensions(self):
        return self._extensions

    @extensions.setter
    def extensions(self, new):
        if isinstance(new, list) and all(os.path.exists(f) for f in new):
            self._extensions = new
        elif not new:
            self._extensions = None
        else:
            raise ValueError(
                f"Invalid value for extensions: {new}. "
                f"Expected {list[os.PathLike]} the extension files "
                "needs to exists in path"
            )

    def _load_credentials(self):
        self.credentials = {
            key: os.getenv(f"{self.prefix_env}_{key}")
            for key in self.credentials
        }
        if params := [key for key in self.credentials
                      if not self.credentials[key]]:
            self.ask_credentials_cli(params)

    def ask_credentials_cli(self, list_params: list) -> None:
        for param in list_params:
            if param.lower() in ("senha", "password"):
                value = getpass.getpass(
                    f"Informe a Senha para" f" ({self.prefix_env}): "
                )
            else:
                value = input(f"Informe o(a) {param} " 
                              f"para ({self.prefix_env}): ")
            self.set_persistent_env_var(f"{self.prefix_env}_{param}".upper(),
                                        value)
            self.credentials[param] = value

    def set_persistent_env_var(self, var_name: str, var_value: str) -> None:
        system = platform.system()

        if system == "Windows":
            subprocess.run(["setx", var_name, var_value], check=True)
        elif system == "Linux":
            home = os.path.expanduser("~")
            bashrc_path = os.path.abspath(os.path.join(home, ".bashrc"))
            with open(bashrc_path, "a") as bashrc:
                bashrc.write(f'\nexport {var_name}="{var_value}"\n')
            logging.info(
                f"Variable added to {bashrc_path}. "
                "Please re-login or source the file."
            )
        else:
            raise NotImplementedError(
                f"Setting environment variables persistently"
                f" is not implemented for {system}"
            )

    @abstractmethod
    def login(self):
        """Abstract method for implement login system logic"""
        pass

    @staticmethod
    def move_file(
            from_path_file: os.PathLike,
            to_path_file: os.PathLike
            ) -> None:
        shutil.copy2(from_path_file, to_path_file)

    def wait_download(
            self,
            timeout: int = 3600,
            use_to_ext: tuple = (".xls", ".csv", ".sswweb", ".json", ".pdf")
            ) -> None:

        # loop over path download until file be found
        contador_while = 0
        while contador_while < timeout:

            # getting the files extentions
            ext_files_list = (
                str(file_name).split(".")[-1].lower()
                for file_name in os.listdir(self.path_to_downloads)
            )
            if any(True for ext in ext_files_list if ext in use_to_ext):
                break
            contador_while += 1
            time.sleep(1)

    def init_browser(
            self,
            profile_path: str | None = "profile_browser",
            ignore_profile: bool = True,
            path_to_downloads: str = "downloads",
            headless: bool = True,
            browser: str = "edge",
            extensions: list[os.PathLike] | None = None,
            **kwargs,
            ) -> None:

        self.profile_path = profile_path
        self.ignore_profile = ignore_profile
        self.path_to_downloads = path_to_downloads
        self.headless = headless
        self.browser = browser
        self.extensions = extensions

        if self.browser == "chrome":
            self._chrome_driver(**kwargs)
        elif self.browser == "edge":
            self._edge_driver(**kwargs)
        elif self.browser in ["firefox", "mozilla"]:
            self._firefox_driver(**kwargs)
        else:
            raise NotImplementedError(
                f"The browser name: {browser} "
                "provided was not implemented yet!"
            )

        self.action_chains = ActionChains(self.driver)

    def _chrome_driver(self, **kwargs) -> None:
        logging.info("...Chromedriver Option...")
        options = webdriver.ChromeOptions()
        options.add_argument('--log-level=3')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": self.path_to_downloads,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "plugins.plugins_list": [
                    {"enabled": False, "name": "Chrome PDF Viewer"}
                ],
                "download.extensions_to_open": "applications/pdf",
                "plugins.always_open_pdf_externally": True,
            },
        )

        if self.profile_path and not self.ignore_profile:
            options.add_argument(f"user-data-dir={self.profile_path}")

        if self.headless:
            options.add_argument("headless")

        if self.extensions:
            for ext in self.extensions:
                options.add_extension(ext)

        self.driver = webdriver.Chrome(options=options)

    def _firefox_driver(self, **kwargs) -> None:
        logging.info("...FirefoxDriver Option...")
        options = FirefoxOptions()

        if self.profile_path and not self.ignore_profile:
            options.set_preference("profile", self.profile_path)

        if self.headless:
            options.add_argument("--headless")

        options.log.level = "fatal"
        options.add_argument(
            "--disable-dev-shm-usage"
        )
        options.add_argument(
            "--disable-popup-blocking"
        )
        options.add_argument("--incognito")
        options.add_argument("--disable-gpu")

        # Adiciona preferências específicas do Firefox
        logging.info(f"path_to_downloads: {self.path_to_downloads}")
        options.set_preference("browser.download.dir", self.path_to_downloads)
        options.set_preference("browser.download.manager.showWhenStarting",
                               False)
        options.set_preference("browser.download.folderList", 2)
        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk", "application/pdf"
        )  # Ajuste conforme necessário
        options.set_preference(
            "pdfjs.disabled", True
        )  # Desativa visualizador PDF interno do Firefox
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.download.panel.shown", False)

        self.driver = webdriver.Firefox(options=options)
        
        # argument --start-maximized don't work then using this method
        self.driver.maximize_window()

    def _edge_driver(self, **kwargs) -> None:
        logging.info("...Edgedriver Option...")
        options = webdriver.EdgeOptions()
        options.use_chromium = True
        options.add_argument('--log-level=3')
        options.add_argument("start-maximized")
        if self.profile_path and not self.ignore_profile:
            options.add_argument(f"--user-data-dir={self.profile_path}")

        if self.headless:
            options.add_argument("--headless")

        if self.extensions:
            for ext in self.extensions:
                options.add_extension(ext)

        options.add_experimental_option(
            "prefs", {
                "download.default_directory": f"{self.path_to_downloads}"
            }
        )

        self.driver = webdriver.Edge(options=options)

    def open(self, url: str) -> None:
        self.driver.get(url)

    @retry()
    def get_cookies(self) -> list:
        self.cookies = self.driver.get_cookies()

        if len(self.cookies) == 0:
            raise EmptyCookies(self.cookies)

        for cookie in self.cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])
        return self.cookies

    @retry()
    def get_token_authorization_from_storage(self) -> str:
        script = """
        var token = localStorage.getItem('token');
        console.log(token);
        return token
        """
        token = self.driver.execute_script(script)
        logging.info(token)
        if token is None:
            raise TokenNotFound("No token was found")

        return token

    @staticmethod
    def convert_query_url_to_dict(
            query: str,
            empty_values: bool = True,
            fill_empty_values_by: str = ''
            ) -> dict:
        dict_query = {}
        query_list = query.split('&')
        for param in query_list:
            param_list = param.split('=')
            if not empty_values:
                dict_query[param_list[0]] = param_list[1]
            elif fill_empty_values_by != '':
                if str(param_list[1]).strip() == '':
                    dict_query[param_list[0]] = fill_empty_values_by
            else:
                dict_query[param_list[0]] = ''
        return dict_query

    @staticmethod
    def convert_dict_to_query_url(
            dict_query: dict,
            show_values: bool = False
            ) -> str:
        query_format = []
        for key in dict_query:
            query_format.append(f'{key}={dict_query[key]}')
            if show_values:
                logging.info(f'{key}={dict_query[key]}')
        return '&'.join(query_format)

    def pretty_show_query(self, query: str) -> None:
        dict_query = self.convert_query_url_to_dict(query, False)
        logging.info(json.dumps(dict_query, indent=6))

    def show_kwargs_possible_values(
            self,
            response: Response,
            query_model: str,
            **kwargs
            ) -> None:

        # Create a BeautifulSoup object
        verbose = kwargs.get('verbose', True)
        if verbose:
            soup = BeautifulSoup(response.text, 'html.parser')

            additional_params = self.convert_query_url_to_dict(query_model)
            logging.info('"""')
            logging.info('    :param kwargs:')
            logging.info('    Possible keys include:')
            for key in additional_params:
                try:
                    # Find the input tag
                    input_tag = soup.find('input', attrs={'name': key})

                    if input_tag is not None:
                        # Find the div tag
                        div_tag = input_tag.find_next_sibling('div')
                        if div_tag is not None:
                            # Extract the query parameter name and value
                            param_name = input_tag['name']
                            param_value = (div_tag.text.strip()
                                           .replace('&nbsp;', '')
                                           .replace(' ', ''))

                            # Build the query string
                            query = f'        - {param_name}: {param_value}'

                            logging.info(query)
                except KeyError:
                    pass
                except AttributeError:
                    pass
            logging.info('    :type kwargs: dict')
            logging.info('    :return: None')
            logging.info('"""')

    def _get_value(
            self,
            element: Tag | NavigableString,
            att: str) -> str | None:
        if att == 'value':
            return element.get('value')
        elif att == 'text':
            return element.text
        return None

    def get_input_values_from_html(
            self,
            response: Response,
            attribute: str = 'id',
            **kwargs) -> dict:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all input tags in the HTML
        inputs = soup.find_all('input')
        soup.find

        value = 'value' if 'value' not in kwargs else kwargs.pop('value')

        # Build a dictionary with the ids and values from the input tags
        params = {
            input_tag.get(attribute): self._get_value(input_tag, value)
            for input_tag in inputs
        }
        return params

    def update_query_values(
            self,
            response: Response,
            query_model: str,
            attribute: str = 'id',
            **kwargs
            ) -> str:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all input tags in the HTML
        inputs = soup.find_all('input')

        value = 'value' if 'value' not in kwargs else kwargs.pop('value')

        # Build a dictionary with the ids and values from the input tags
        params = {
            input_tag.get(attribute): self._get_value(input_tag, value)
            for input_tag in inputs
        }

        self.show_kwargs_possible_values(response, query_model, **kwargs)

        unquote_ = kwargs.pop('unquote') if 'unquote' in kwargs else False

        additional_params = self.convert_query_url_to_dict(query_model)
        for key in additional_params:
            try:
                additional_params[key] = params[key]
            except KeyError:
                pass
        for key in kwargs:
            if unquote_:
                additional_params[key] = unquote(str(kwargs[key]))
            else:
                additional_params[key] = kwargs[key]

        # Use urlencode to create the query string
        query = urlencode(additional_params)

        return query

    @staticmethod
    def extract_html_values(
            response: Response,
            keyword_ini: str,
            keyword_fin: str
            ) -> str:
        try:
            decoded_text = html.unescape(response.text)
            logging.info(decoded_text)
            decoded_text = decoded_text.replace('<b>', '').replace('</b>', '')
            index_ini = decoded_text.find(keyword_ini)
            index_fin = decoded_text.find(keyword_fin)
            extracted_val = decoded_text[
                index_ini + len(keyword_ini):index_fin
                ]
        except IndexError as e:
            logging.exception(e)
            extracted_val = None
        return extracted_val

    def request_download(self, url: str, name_file: str) -> Response:
        # get the content
        response = self.session.get(url)
        # write file
        filename = os.path.abspath(
            os.path.join(self.path_to_downloads, name_file))
        with open(filename, "wb") as file:
            file.write(response.content)
        return response

    @retry()
    def click_id_el(self, id: str) -> None:

        script = f"""
        return document.getElementById('{id}').click()
        """
        self.driver.execute_script(script)

    @retry()
    def get_el_by_id(self, id: str) -> WebElement | None:
        script = f"""
        return document.getElementById('{id}')
        """
        return self.driver.execute_script(script)

    @retry()
    def get_els_by_tag(self, tag: str) -> WebElement | None:
        script = f"""
        return document.getElementsByTagName('{tag}')
        """
        return self.driver.execute_script(script)

    @retry()
    def get_el_by_xpath(self, xpath: str) -> WebElement | None:
        return self.driver.find_element(By.XPATH, xpath)


if __name__ == "__main__":
    ...
