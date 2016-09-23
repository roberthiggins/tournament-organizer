exports.transform = function(responseFromDAO) {
    var asJSON = JSON.parse(responseFromDAO),
        slug = function(tournament, entry, suffix) {
            var slug = "";
            if (tournament) {
                slug = slug + "/tournament/" + tournament;
            }
            if (entry) {
                slug = slug + "/entry/" + entry;
            }
            if (suffix) {
                slug = slug + "/" + suffix;
            }
            return slug;
        };

    asJSON.forEach(function formatCategory(cat) {
        cat.actions.forEach(function formatAction(act) {
            switch (act.action) {
                case "create_tournament":
                    act.href = slug(null, null, "tournament/create");
                    break;
                case "enter_game_score":
                    act.href = slug(act.tournament, act.username,
                        "entergamescore");
                    break;
                case "enter_tournament_score":
                    act.href = slug(act.tournament, act.username, "enterscore");
                    break;
                case "get_draw":
                    act.href = slug(act.tournament, null,
                        "round/" + act.round + "/draw");
                    break;
                case "get_rankings":
                    act.href = slug(act.tournament, null, "rankings");
                    break;
                case "get_tournament_entries":
                    act.href = slug(act.tournament, null, "entries");
                    break;
                case "next_game":
                    act.href = slug(act.tournament, act.username, "nextgame");
                    break;
                case "place_feedback":
                    act.href = "/feedback";
                    break;
                case "register":
                    act.href = slug(act.tournament, null, null);
                    break;
                case "set_missions":
                    act.href = slug(act.tournament, null, "missions");
                    break;
                case "set_rounds":
                    act.href = slug(act.tournament, null, "rounds");
                    break;
                case "set_score_categories":
                    act.href = slug(act.tournament, null, "categories");
                    break;
                case "tournament_list":
                    act.href = slug(null, null, "tournaments");
                    break;
            }
            delete act.action;
            delete act.tournament;
            delete act.username;
            delete act.round;
        });
    });

    return asJSON;
};
