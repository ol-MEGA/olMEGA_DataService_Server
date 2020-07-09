from olMEGA_DataService_Server import olMEGA_DataService_Server as app

# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

if __name__ == "__main__":
    Server = app.olMEGA_DataService_Server('olMEGA_DataService_Server', debug = True, cert = 'devel_cert.pem', key = 'devel_key.pem')
    Server.run()