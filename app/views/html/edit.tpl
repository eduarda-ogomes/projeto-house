<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edição</title>
    <link rel="stylesheet" type="text/css" href="/static/css/edit.css">
    <script src="/static/js/edit.js"></script>
</head>
<body>
    <h1>Página de edição de Usuários:</h1>
    % if user:
        <h4>Usuário logado: {{ user.username }} </h4>
          <form action="/edit" method="post">
            <label for="username">Nome:</label>
            <input id="username" name="username" type="text"
              value="{{ user.username }}" readonly /><br>
            <label for="password">Senha:</label>
            <input id="password" name="password" type="password" required /><br>
          </br>
            <div class= "button-container">
              <input value="Editar" type="submit" />
              <form action="/logout" method="post">
                <button type="submit">Logout</button>
              </form>
              <form action="/portal" method="post">
                <button type="submit">Portal</button>
              </form>
            </div>
          </form>
    % else:
      <h3>Realize seu LOGIN em '/portal'</h3>
      <form action="/portal" method="post">
        <button type="submit">Portal</button>
      </form>
    % end
</body>
</html>
