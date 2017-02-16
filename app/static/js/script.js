(function ($) {
	var bc = $("body").attr('class').split(" ");

	// Profile edit page.
	if ($.inArray("bp-dash", bc) > -1 && $.inArray("ep-profile", bc) > -1 ) {
		// Custom OAuth2 client.
		var oauthClient = OAuth2Client.init({
			client_id: FlaskData.oauth_client_id,
			client_secret: FlaskData.oauth_client_secret,
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
						"api_v1_0.post_reaction", {"_external": true}),
				get_matches: Flask.url_for(
						"api_v1_0.get_matches",
						{"_external": true, "_id": FlaskData.pid})
			}
		});
		
		// Slider.
		var aSlider = $("#k-ua-slider");
		aSlider.slider({
			min: 1,
			max: 5,
			value: 3
		}).slider("pips", {
			rest: "label",
			labels: [1, 2, 3, 4, 5]
		});
		
		var submit = $("#k-ua-buttons .answer");
		submit.on("click", function (e) {
			data = {
				profile: FlaskData.pid,
				statement: FlaskData.statement,
				reaction: aSlider.slider("option", "value")
			}
			
			postReaction(data);
		});
		
		var skip = $("#k-ua-buttons .skip");
		skip.on("click", function (e) {
			data = {
				profile: FlaskData.pid,
				statement: FlaskData.statement,
				reaction: -1
			}
			
			postReaction(data);
		});

		if (FlaskData.pushed == "True") {
			getInactionStatement();
		}		
	}


	function getInactionStatement () {
		oauthClient.fetchToken().done(function (token) {
			api.getInactionStatement(token).done(function (data) {
				showInactionStatement(data.result);
				getMatches();
			});
		});
	}// end getInactionStatement.


	function showInactionStatement (statement) {
		$("#k-ua-statement").html("")
		$("#k-ua-statement").html(statement.statement);
		aSlider.slider("value", 3);
		FlaskData.statement = statement._id;
	}// end showInactionStatment.


	function postReaction(reaction) {
		oauthClient.fetchToken().done(function (token) {
			api.postReaction(token, reaction).done(function (data) {
				getInactionStatement();
			});
		});
	}// end postAnswer.

	function getMatches () {
		oauthClient.fetchToken().done(function (token) {
			api.getMatches(token).done(function (data) {
				var table = $("#matches-container table tbody");
				table.html("");
				
				data.result.forEach(function (e, i, a) {
					var row = $('<tr><td><a href="{0}">{1}</a></td><td>{2}%</td></tr>'.format(
							Flask.url_for(
									"dash.profile",
									{"pid": e.external_id}
							), e.name, (e.similarity * 100).toFixed(1)));
					table.append(row);
				});
			});
		});
	}// end getMatches.
})(jQuery);