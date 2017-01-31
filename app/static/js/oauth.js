var OAuth2Client = (function (self, $) {
	
	// OAuth client id.
	self.client_id = null;
	
	// OAuth client secret.
	self.client_secret = null;
	
	// OAuth access token url.
	self.access_token_url = null;
	
	// OAuth grant type.
	self.grant_type = null;
	
	// Initialize private properties.
	self.init = function (params) {
		self.client_id = params.client_id;
		self.client_secret = params.client_secret;
		self.access_token_url = params.access_token_url;
		self.grant_type = params.grant_type;
		
		return self;
	}
	
	// Fetch token in client credentials flow.
	// Token properties:
	//   - access_token: string
	//   - expires_in: int
	//   - scope: string
	//   - token_type: string
	self.fetchToken = (function() {
		return $.ajax({
			url: self.access_token_url,
			method: "POST",
			data: {
				client_id: self.client_id,
				client_secret: self.client_secret,
				grant_type: self.grant_type
			},
			dataType: "json"
		});
	});
	
	return self;
}(OAuth2Client || {}, jQuery));