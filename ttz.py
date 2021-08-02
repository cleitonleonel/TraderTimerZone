import requests
import re

BASE_URL = 'https://br.tradertimerzone.com/'


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 200:
            return response
        return None


class TraderTimerZoneAPI(Browser):

    def __init__(self):
        self.dict_colors = {}
        super().__init__()

    def open_url(self):
        data = {
            'zone': 'America/Sao_Paulo',
            'button': 515
        }
        self.response = self.send_request('GET',
                                          BASE_URL + 'fancy.php',
                                          params=data,
                                          headers=self.headers
                                          )
        if self.response:
            return self.response
        return False

    def get_operations(self):
        html = self.open_url()
        match = re.compile(
            r'<td class="T(.*?)" style="text-align: center;background-color:(.*?)">.*?</td>'
        ).findall(html.text)

        return {f"{values[0][:2]}:{values[0][2:]}": self.get_color(key) for *values, key in match}

    def get_color(self, tag):
        self.dict_colors = {
            '#00B050': 'Verde',
            '#ED3237': 'Vermelho',
            '#A8CF45': 'Verde Claro',
            '#01B0F1': 'Azul',
            '#ADFF2F': 'Amarelo Esverdeado',
        }
        return self.dict_colors.get(tag, '')


if __name__ == '__main__':
    ttz = TraderTimerZoneAPI()
    operations = ttz.get_operations()
    color = operations['10:55']
    print(color)
