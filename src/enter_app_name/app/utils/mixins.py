from .requests import init_http_session
from .error_handlers import HTTPFailure


class HTTPMixin:
    def get_request(self, params: dict, error: str):
        self.config = {
            'METHOD': 'GET',
            'URL': current_app.config['SHARED_URL'],
            'PARAMS': dict,
            'VERIFY': False,
            'LOGGER': 'DEFAULT',
            'ERROR': error # to be set by respective methods
        }
        resp = init_http_session(self.config)
        return resp

    def post_request(self, payload: dict, data: dict, error: str):
        self.config = {
            'METHOD': 'POST',
            'URL': current_app.config['SHARED_URL'],
            'PAYLOAD': payload,
            'DATA': data,
            'VERIFY': False,
            'LOGGER': 'DEFAULT',
            'ERROR': error # to be set by respective methods
        }
        resp = init_http_session(self.config)
        return resp.json()


class EmailMixin:
    corr_id = 'TEST_CORR_ID'

    def email_table_generator(self, content: list):
        # content is a list of rows
        table_headers = ''
        table_rows = ''
        added_headers = False

        for row in content:
            table_row = ''
            for key, value in row.items():
                # Generate table headers row
                if not added_headers:
                    table_headers += f'<th>{key}</th>'
            
                # Generate content rows
                table_row += f'<td>{value}</td>'
            
            if not added_headers:
                table_headers = '<tr>' + table_headers + '</tr>'
            table_rows += '<tr>' + table_row + '</tr>'
            added_headers = True
        
        html_table = '<table border="1">' + table_headers + table_rows + '</table>'
        return html_table