import unittest
import logging
import os
from flask import current_app, json
from enter_app_name.app import create_app

logger = logging.getLogger(__name__)


class FlaskInstacapTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def attach_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'  # needed for request.json to work
        }

    def test_post_endpoint(self):
        payload = json.dumps({'payload': 'testing'})
        resp = self.client.post('/place/endpoint/here', headers=self.attach_headers(), data=payload)
        self.assertEqual(resp.status_code, 200)
        json_resp = json.loads(resp.get_data(as_text=True))
        



    




    
    
    


