import json
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
        while page:
            params['page'] = page
            r = request_function(url, params=params)
            try:
                data = r.json()
            except json.decoder.JSONDecodeError:
                print(r)
                print (r.text)
                raise
            if filter:
                filtered_results = [result for result in data['results'] if filter(result)]
                results.extend(filtered_results)
                if len(filtered_results) < len(data['results']):
                    break
            else:
                for result in data['results']:
                    yield result

            if data['pagination']:
                page = data['pagination']['next_page']
            else:
                page = None


    def _get_paginated_oauth(self, url, params, filter=None):
        return self._get_paginated_base(self.oauth.get, url, params, filter)

    def _get_paginated(self, url, params, filter=None):
        params = params.copy()
        params['api_key'] = self.client_key
        return self._get_paginated_base(requests.get, url, params, filter)

    def get_transactions(self, shop_id, since=None):
        url = ETSY_URL_BASE + "shops/{shop_id}/transactions".format(shop_id=shop_id)
        if since:
            for result in self._get_paginated_oauth(url, {}, lambda result: result['creation_tsz'] >= since):
                yield result
        else:
            for result in self._get_paginated_oauth(url, {}):
                yield result

    def get_listings(self, shop_id, include_private=False):
        url = ETSY_URL_BASE + "shops/{shop_id}/listings/active".format(shop_id=shop_id)
        return self._get_paginated(url, {'include_private': include_private})

    def get_variations(self, listing_id):
        url = ETSY_URL_BASE + "listings/{listing_id}/variations".format(listing_id=listing_id)
        return self._get_paginated(url, {})

    def check_scopes(self):
        r = self.oauth.get("https://openapi.etsy.com/v2/oauth/scopes")
        return r.json()