import os, sys
from Test import Test
from qa import utils


class delete_test_data(Test):
    """
    Removes the test data found in config from the plc db
    """

    def call(self):
	
	api = self.config.api
        auth = self.config.auth
	
	site_login_base = self.config.TEST_SITE_LOGIN_BASE
	
	# Deleting the site should delete everything associated with it
	api.DeleteSite(auth, site_login_base)
	if self.config.verbose:
	    utils.header("Test data deleted")

	return 1 
	
if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    delete_test_data(*args)		
