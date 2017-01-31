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
				get_unanswered_question: Flask.url_for(
						"api_v1_0.get_unanswered_question",
						{"_external": true, "_id": FlaskData.pid}),
				post_answer: Flask.url_for(
						"api_v1_0.post_answer", {"_external": true})
			}
		});

		if (FlaskData.pushed == "True") {
			getUnansweredQuestion();
		}
	}


	function getUnansweredQuestion () {
		oauthClient.fetchToken().done(function (token) {
			api.getUnansweredQuestion(token).done(function (data) {
				showUnansweredQuestion(data.result);
			});
		});
	}// end getUnansweredQuestion.


	function showUnansweredQuestion (question) {
		var container = $("#k-ua-container");
		container.html("");
		
		var qp = $("<p></p>").append("{0}?".format(question.question));
		
		var form = $('<form class="form" role="form"></form>');
		question.options.split("\n").forEach(function (e, i, a) {
			div = $('<div class="radio"></div>');
			label = $("<label></label>");
			input = $('<input type="radio" name="optionsRadios" id="k-ua-{0}" value="{0}">'.format(e));
			
			label.append(input);
			label.append(e);
			div.append(label);
			
			form.append(div);
		});
		
		var save = $('<input type="button" id="k-ua-save-answer" class="btn btn-default" value="Save">');
		save.on("click", function () {
			if (form.serializeArray().length == 0) {
				alert("Please select an answer.")
				return;
			}
			
			formData = {};
			form.serializeArray().forEach(function (e) {
				formData[e.name] = e.value;
			});
			
			
			data = {
				profile: FlaskData.pid,
				question: question._id,
				answer: formData.optionsRadios
			};
			
			postAnswer(data);
		});
		form.append(save);
		
		var skip = $('<input type="button" id="k-ua-skip" class="btn btn-default" value="Skip">');
		skip.on("click", function () {
			alert("skip clicked.");
		});
		form.append(skip);
		
		container.append(qp);
		container.append(form);
	}// end showUnansweredQuestion.


	function postAnswer(answer) {
		oauthClient.fetchToken().done(function (token) {
			api.postAnswer(token, answer).done(function (data) {
				getUnansweredQuestion();
			});
		});
	}// end postAnswer.
})(jQuery);