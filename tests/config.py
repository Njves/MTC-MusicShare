class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'test'
    TESTING = True
    SQLALCHEMY_ECHO = True
    LOGIN_DISABLED = True