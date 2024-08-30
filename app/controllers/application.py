from app.controllers.datarecord import UserRecord, MessageRecord
from bottle import template, redirect, request, response


class Application():

    def __init__(self):

        self.pages = {
            'portal': self.portal,
            'pagina': self.pagina,
            'chat': self.chat,
            'edit': self.edit
        }
        self.__users= UserRecord()
        self.__messages= MessageRecord()
        self.edited= False


    def render(self,page,parameter=None):
        content = self.pages.get(page, self.portal)
        if not parameter:
            return content()
        return content(parameter)


    def getCurrentUserBySessionId(self):
        session_id= request.get_cookie('session_id')
        return self.__users.getCurrentUser(session_id)


    def edit(self):
        current_user= self.getCurrentUserBySessionId()
        return template('app/views/html/edit', user=current_user)


    def portal(self):
        current_user= self.getCurrentUserBySessionId()
        if current_user:
            portal_render= template('app/views/html/portal', \
                username= current_user.username, edited= self.edited)
            self.edited= False
            return portal_render
        portal_render= template('app/views/html/portal', \
        username= None, edited= self.edited)
        self.edited= False
        return portal_render


    def pagina(self):
        current_user= self.getCurrentUserBySessionId()
        if current_user:
            return template('app/views/html/pagina', \
            transfered=True, current_user=current_user)
        return template('app/views/html/pagina', \
        transfered=False)


    def is_authenticated(self, username):
        current_user= self.getCurrentUserBySessionId()
        if current_user:
            return username == current_user.username
        return False


    def authenticate_user(self, username, password):
        session_id = self.__users.checkUser(username, password)
        if session_id:
            self.logout_user()
            response.set_cookie('session_id', session_id, httponly=True, \
            secure=True, max_age=3600)
            redirect('/pagina')
        redirect('/portal')


    def login(self):
        return template('app/views/html/login')


    def update_user(self, username, password):
        self.__users.setUser(username, password)
        self.edited= True
        redirect('/portal')


    def logout_user(self):
        session_id = request.get_cookie('session_id')
        self.__users.logout(session_id)
        response.delete_cookie('session_id')


    def chat(self):
        current_user= self.getCurrentUserBySessionId()
        if current_user:
            messages= self.__messages.getUsersMessages()
            return template('app/views/html/chat', current_user=current_user, \
            messages=messages)
        redirect('/portal')


    def newMessage(self,message):
        content= message.encode('latin-1').decode('utf-8')
        current_user= self.getCurrentUserBySessionId()
        return self.__messages.book(current_user.username,content)
