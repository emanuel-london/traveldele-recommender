var KAPI = (function (self, $) {
	
	// API endpoints.
	self.endpoints = {};
	
	// Initialize private properties.
	self.init = function(params) {
		self.endpoints = params.endpoints;
		
		return self;
	};
	
	// Get a question that has no reaction.
	self.getInactionStatement = function(token) {
		return $.ajax({
			url: self.endpoints.get_inaction_statement,
			method: "GET",
			headers: {
				"Authorization": "{0} {1}".format(
						token.token_type, token.access_token)
			},
			dataType: "json"
		});
	};
	
	// Post a reaction to the recommender system.
	self.postReaction = function(token, data) {
		return $.ajax({
			url: self.endpoints.post_reaction,
			method: "POST",
			headers: {
				"Authorization": "{0} {1}".format(
						token.token_type, token.access_token),
				"Content-Type": "application/json"
			},
			data: JSON.stringify(data),
			dataType: "json"			
		});
	};
	
	return self;
}(KAPI || {}, jQuery));