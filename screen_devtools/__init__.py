import requests
import urllib
import functools
from .exceptions import UrlParseError, ChromeProtocolNotDefended, EventHandlerNotSet
from .worker import ListenEvents


# ignore warnings (for asyncio.coroutine)
__import__("warnings").filterwarnings("ignore")


class ScreenDevtools:
    """
    It's main library class
    :param host: chrome devtools protocol hostname in format "http://localhost:9222"
    """
    def __init__(self, host="http://localhost:9222"):
        parsed_url = urllib.parse.urlparse(host)
        self.http_protocol = parsed_url.scheme
        self.http_host = parsed_url.hostname
        self.http_port = parsed_url.port

        if (parsed_url.path and parsed_url.path != "/") or parsed_url.params:
            raise UrlParseError(host)

        self._app_initialize()
        self._events_controller = ListenEvents(self._hostname)

    @property
    def _hostname(self):
        return "{}://{}:{}".format(self.http_protocol, self.http_host, self.http_port)

    def _app_initialize(self):
        try:
            browser_info = requests.get(self._hostname + "/json/version").json()
        except requests.exceptions.ConnectionError:
            raise ChromeProtocolNotDefended(self._hostname)

        self.browser_websocket_url = browser_info["webSocketDebuggerUrl"]

    def event_handler(self, f):
        self._events_controller.set_user_call_function(f)

        @functools.wraps(f)
        def wrapper(*args):
            f(*args)
        return wrapper

    def run(self):
        if not hasattr(self._events_controller, "raise_event"):
            raise EventHandlerNotSet("@event_handler")
        self._events_controller.run_worker()
