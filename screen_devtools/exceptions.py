class UrlParseError(Exception):
    """
    Raised for errors like parse url
    """
    def __init__(self, message):
        self.message = "Url \"{}\" hostname can't be parsed"
        super().__init__(self.message.format(message))


class ChromeProtocolNotDefended(Exception):
    """
    Raised after error of Chrome Devtools not found on host
    """
    def __init__(self, message):
        self.message = "Chrome Devtools Protocol service not found for \"{}\""
        super().__init__(self.message.format(message))


class ChromeProtocolDevtoolsClosed(Exception):
    """
    Raised after error like Chrome closed
    """
    def __init__(self, message):
        self.message = "Google Chrome Devtools had closed on host \"{}\""
        super().__init__(self.message.format(message))


class EventHandlerNotSet(Exception):
    """
    Raised if ScreenDevtools.event_handler had not set
    """
    def __init__(self, message):
        self.message = "Set app handler: \"{}\""
        super().__init__(self.message.format(message))
