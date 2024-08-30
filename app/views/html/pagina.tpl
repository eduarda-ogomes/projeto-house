<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>>.::Pagina::.</title>
    <link rel="stylesheet" type="text/css" href="/static/css/pagina.css">
    <script src="/static/js/pagina.js"></script>
</head>
<body>

    <h1>Minha página com interação de modelos :)</h1>
    % if transfered:
        <div>
            <h2>Dados do Usuário:</h2>
            <p>Username: {{current_user.username}} </p>
            <p>Password: {{current_user.password}} </p>
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
                <form action="/portal" method="get">
                    <button type="submit">Portal</button>
                </form>
            </div>
        </div>
    % else:
        <h2>Realize o LOGIN para ter acesso aos seus dados pessoais. Acesse nosso portal em '/portal' :) </h2>
    % end
</body>
</html>
