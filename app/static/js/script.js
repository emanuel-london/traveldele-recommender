(function ($) {
	var bc = $("body").attr('class').split(" ");

	// Profile edit page.
	if ($.inArray("bp-dash", bc) > -1 && $.inArray("ep-profile", bc) > -1 ) {
		// Custom OAuth2 client.
		var oauthClient = OAuth2Client.init({
			client_id: "yRqhlcLFiD0n8st",
			client_secret: "dDOfeqgqdHE7tldCGcfALMuwd67Thf",
			access_token_url: Flask.url_for("oauth.access_token", {"_external": true}),
			grant_type: "client_credentials"
		});

		// Kooyara Recommender System API.
		var api = KAPI.init({
			endpoints: {
				get_inaction_statement: Flask.url_for(
						"api_v1_0.get_inaction_statement",
						{"_external": true, "_id": FlaskData.pid}),
				post_reaction: Flask.url_for(
						"api_v1_0.post_reaction", {"_external": true})
			}
		});

		if (FlaskData.pushed == "True") {
			getInactionStatement();
		}
	}


	function getInactionStatement () {
		oauthClient.fetchToken().done(function (token) {
			api.getInactionStatement(token).done(function (data) {
				showInactionStatement(data.result);
			});
		});
	}// end getInactionStatement.


	function showInactionStatement (statement) {
		
	}// end showInactionStatment.


	function postAnswer(answer) {
		oauthClient.fetchToken().done(function (token) {
			api.postAnswer(token, answer).done(function (data) {
				getInactionStatement();
			});
		});
	}// end postAnswer.
})(jQuery);