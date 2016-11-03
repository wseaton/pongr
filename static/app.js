var app = angular.module("app", []);

app.controller("AppCtrl", function($http) {
  var app = this;

  $http.get("/api/game").success(function (data) {
    app.games = data.objects;
  })

  app.addGame = function () {
    $http.post("/api/game", {"player_a":"test", "player_b":"other", "score_a":"test", "score_b":"test"})
      .succes(function (data){
        app.games.push(data);
      })
  }

app.deleteGame = function () {
  $http.delete("/api/game/" + game.id).success(function (response) {
    app.games.splice(app.games.indexOf(game), 1)
  })
}

})
