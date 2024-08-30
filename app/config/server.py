from bottle import Bottle



class ServerHTTP(Bottle):


    def __init__(self):

        self.app= Bottle()
        self.setup_app()


    def setup_app(self):
        # Defina o local para Português (Brasil)
        self.app.config['default_locale'] = 'pt_BR'
         # Defina o conjunto de caracteres para lidar com decodificações em UTF-8
        self.app.config['charset'] = 'utf-8'
