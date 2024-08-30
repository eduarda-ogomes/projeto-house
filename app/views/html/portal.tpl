<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>>.::Portal (Login)::.</title>
    <link rel="stylesheet" type="text/css" href="/static/css/portal.css">
    <script src="/static/js/portal.js"></script>
</head>
<body>
    <h1>Login</h1>
    % if username:
        % if edited:
            <h4>Usuário logado: {{ username }} (editado) </h4>
        % else:
            <h4>Usuário logado: {{ username }} </h4>
        % end
    % end
    <form action="/portal" method="post">
        <label for="username">Nome:</label>
        <input id="username" name="username" type="text" required /><br>
        <label for="password">Senha:</label>
        <input id="password" name="password" type="password" required /><br>
        </br>
        <input value="Login" type="submit" />
    </form>
    % if username:
      <div class= "button-container">
        <form action="/logout" method="post">
            <button type="submit">Logout</button>
        </form>
        <form action="/edit" method="get">
            <button type="submit">Editar usuário</button>
        </form>
        <form action="/chat" method="get">
            <button type="submit">Área de mensagens</button>
        </form>
      </div>
    % end
</body>
</html>
