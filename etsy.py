from requests_oauthlib import OAuth1Session
import requests

ETSY_URL_BASE = "https://openapi.etsy.com/v2/"

class Etsy(object):
	def __init__(self, config):
		self.client_key = config.app_key
		self.oauth = OAuth1Session(config.app_key,
                   client_secret=config.app_secret,
                   resource_owner_key=config.oauth_token,
                   resource_owner_secret=config.oauth_token_secret)

	def _get_paginated_base(self, request_function, url, params, filter=None):
		results = []
		page = 1
		# Make a copy so we don't modify our parameter
		params = params.copy()
		params['api_key'] = self.client_key
		while page:
			params['page'] = page
			r = self.oauth.get(url, params=params)
			data = r.json()
			if filter:
				filtered_results = [result for result in data['results'] if filter(result)]
				results.extend(filtered_results)
				if len(filtered_results) < len(data['results']):
					break
			else:
				results.extend(data['results'])
			if data['pagination']:
				page = data['pagination']['next_page']
			else:
				page = None
		return results

	def _get_paginated_oauth(self, url, params, filter=None):
		return self._get_paginated_base(self.oauth, url, params, filter)

	def _get_paginated(self, url, params, filter=None):
		return self._get_paginated_base(requests.get, url, params, filter)

	def get_transactions(self, shop_id, since=None):
		url = ETSY_URL_BASE + "shops/{shop_id}/transactions".format(shop_id = shop_id)
		if since:
			return self._get_paginated_oauth(url, {}, lambda result: result['creation_tsz'] >= since)
		else:
			return self._get_paginated_oauth(url, {})

	def get_listings(self, shop_id, include_private=False):
		url = ETSY_URL_BASE + "shops/{shop_id}/listings/active".format(shop_id=shop_id)
		return self._get_paginated(url, {'include_private': include_private})

	def get_variations(self, listing_id):
		url = ETSY_URL_BASE + "listings/{listing_id}/variations".format(listing_id=listing_id)
		return self._get_paginated(url, {})