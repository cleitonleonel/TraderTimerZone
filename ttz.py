import re
import ssl
import json
import pycolors
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    allowed_methods=["HEAD", "POST", "PUT", "GET", "OPTIONS"]
)

BASE_URL = 'https://tradertimerzone.com/'


class CipherSuiteAdapter(HTTPAdapter):
    __attrs__ = [
        'ssl_context',
        'max_retries',
        'config',
        '_pool_connections',
        '_pool_maxsize',
        '_pool_block',
        'source_address'
    ]

    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')

        if self.source_address:
            if isinstance(self.source_address, str):
                self.source_address = (self.source_address, 0)

            if not isinstance(self.source_address, tuple):
                raise TypeError(
                    "source_address must be IP address string or (ip, port) tuple"
                )

        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket
            self.ssl_context.wrap_socket = self.wrap_socket

            if self.server_hostname:
                self.ssl_context.server_hostname = self.server_hostname

            self.ssl_context.set_ecdh_curve(self.ecdhCurve)

            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    def wrap_socket(self, *args, **kwargs):
        if hasattr(self.ssl_context, 'server_hostname') and self.ssl_context.server_hostname:
            kwargs['server_hostname'] = self.ssl_context.server_hostname
            self.ssl_context.check_hostname = False
        else:
            self.ssl_context.check_hostname = True

        return self.ssl_context.orig_wrap_socket(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)


class Browser(Session):

    def __init__(self, *args, **kwargs):
        self.response = None
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ssl_context = kwargs.pop('ssl_context', None)

        super(Browser, self).__init__()

        self.mount(
            'https://',
            CipherSuiteAdapter(
                ecdhCurve=self.ecdhCurve,
                server_hostname=self.server_hostname,
                source_address=self.source_address,
                ssl_context=self.ssl_context,
                max_retries=retry_strategy
            )
        )

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        response = self.request(method, url, **kwargs)
        return response


class TraderTimerZoneAPI(Browser):

    def __init__(self):
        super().__init__()
        self.dict_colors = None
        self._html = None
        self.initialize()

    def initialize(self):
        self.response = self.send_request(
            'GET',
            BASE_URL,
            headers=self.get_headers()
        )

    def handle(self, period=None, frame=515):
        if frame == 1:
            frame = 60300
        payload = {
            'datap': period if period else '',
            'action': 'crypto2',
            'zone': 'America/Sao_Paulo',
            'button': frame
        }
        self.response = self.send_request(
            'POST',
            f'{BASE_URL}/handle.php',
            data=payload
        )
        if self.response:
            return self.response
        return False

    def fancy(self):
        payload = self.response.text
        self.response = self.send_request(
            'GET',
            f'{BASE_URL}/fancy.php',
            params=payload
        )
        self._html = self.response

    def get_operations(self):
        match = re.compile(
            r'<td class="T(.*?)" style="text-align: center;background-color:(.*?)">.*?</td>'
        ).findall(self._html.text)
        return {f"{values[0][:2]}:{values[0][2:]}": self.get_color(key) for *values, key in match}

    def get_color(self, tag):
        self.dict_colors = {
            '#00B050': 'Verde',
            '#ED3237': 'Vermelho',
            '#842d2f': 'Vermelho escuro',
            '#A8CF45': 'Verde claro',
            '#01B0F1': 'Azul',
            '#f3eb0c': 'Amarelo',
            '#ADFF2F': 'Amarelo esverdeado',
        }
        return self.dict_colors.get(tag, '')


if __name__ == '__main__':
    ttz = TraderTimerZoneAPI()
    ttz.handle(period='2024/07/05', frame=1)
    ttz.fancy()
    operations = ttz.get_operations()
    print(json.dumps(operations, indent=4))
    color = operations.get('10:00')
    if color:
        params = {"name": color}
        pycolors.colors_view(params)
