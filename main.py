from olMEGA_DataService_Server import olMEGA_DataService_Server as app

# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
develServer = True

if __name__ == "__main__":
    Server = app.olMEGA_DataService_Server()
    Server.run()