var app = angular.module('RPi', ['ngRoute']);
//--------------- Rotas ---------------
app.config(function($routeProvider){
   $routeProvider
      .when('/', {
         templateUrl: 'home.php',
         controller: 'ctrHome'
      })
      .when('/sobre', {
         templateUrl: 'sobre.php',
         controller: 'ctrSobre'
      })
      .when('/contato', {
         templateUrl: 'contato.php',
         controller: 'ctrContato'
      })
      .when('/login', {
         templateUrl: 'login.php',
         controller: 'ctrLogin'
      })
      .when('/config', {
         templateUrl: 'config.php',
         controller: 'ctrConfig'
      })
      .when('/network', {
         templateUrl: 'config.php',
         controller: 'ctrConfig'
      })
      .otherwise({
         templateUrl: 'erro-pagina.php',
         controller: 'crtErroPagina'
      });
});
//--------------- Serviços ---------------
app.factory('srvMenu', function(){
   var menu = {};
   menu.limpa = function(){
      var cls = $("li > a.active");
      cls[0].className = "";
   };
   menu.ativa = function (pCls){
      var cls = $(pCls);
      cls[0].className = "active";
   };
   return menu;
});
app.factory('srvLogin', function($http){
   var srvLogin = {};
   srvLogin.logar = function(pLogin){
      var retDados = $http({method: 'POST', url: 'logar.php', data: pLogin});
      return retDados;
   };
   return srvLogin;
});
//--------------- Controles ---------------
app.controller('ctrHome', function($scope){
   //srvMenu.limpa();
   //srvMenu.ativa("#actLogin");
});
app.controller('ctrSobre', function($scope,srvMenu){
   srvMenu.limpa();
   srvMenu.ativa("#actSobre");
});
app.controller('ctrContato', function($scope,srvMenu){
   srvMenu.limpa();
   srvMenu.ativa("#actContato");
});
app.controller('ctrLogin', function($scope,srvLogin){
   $scope.logado = false;
   if($scope.frmLogin.$valid){
      var retReg = srvLogin.logar($scope.frmLogin);
      retReg.success(function(data,status){
         $scope.logado = true;
      });
      retReg.error(function(data,status){
         $scope.logado = false;
      });
   }
});
app.controller('ctrConfig', function($scope,srvMenu){
   srvMenu.limpa();
   srvMenu.ativa("#actConfig");
});
app.controller('erroPaginaCtr', function($scope,srvMenu){
   $scope.message = 'A página solicitada, não existe';
});