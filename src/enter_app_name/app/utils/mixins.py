from .connectors import http_handler
from .error_handling import HttpError


class HttpMixin:
    def get_request(self, params: dict, error: str):
        self.config = {
            'method': 'GET',
            'url': current_app.config['SHARED_URL'],
            'params': dict,
            'verify': False,
            'logger': 'DEFAULT',
            'error': error # to be set by respective methods
        }
        resp = http_handler(self.config)
        return resp

    def post_request(self, payload: dict, data: dict, error: str):
        self.config = {
            'method': 'POST',
            'url': current_app.config['SHARED_URL'],
            'payload': payload,
            'data': data,
            'verify': False,
            'logger': 'DEFAULT',
            'error': error # to be set by respective methods
        }
        resp = http_handler(self.config)
        return resp.json()


class EmailMixin:
    def table_generator(self, content: list):
        # content is a list of rows
        table_headers = ''
        table_rows = ''
        counter = 0

        for row in content:
            table_row = ''
            for key, value in row.items():
                # Generate table headers row
                if counter < 1:
                    table_headers += f'<th>{key}</th>'
            
                # Generate content rows
                table_row += f'<td>{value}</td>'
            
            table_headers = '<tr>' + table_headers + '</tr>'
            table_rows += '<tr>' + table_row + '</tr>'
            counter += 1
        
        html_table = '<table border="1">' + table_headers + table_rows + '</table>'
        return html_table