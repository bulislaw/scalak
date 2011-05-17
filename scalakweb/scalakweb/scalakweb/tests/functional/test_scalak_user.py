from scalakweb.tests import *

class TestScalakUserController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='scalak_user', action='index'))
        # Test response...
