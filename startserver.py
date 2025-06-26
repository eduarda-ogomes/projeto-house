from app.controllers.application import Application
from bottle import TEMPLATE_PATH
import os

# Adiciona a pasta onde estão os .tpl
TEMPLATE_PATH.insert(0, os.path.abspath('./app/views/html'))

# Inicialize a aplicação
app = Application()


# executa a aplicação
if __name__ == '__main__':

    import eventlet
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app.wsgi_app)
