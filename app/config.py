import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    PROJECT_NAME = 'vietbus'

    @staticmethod
    def init_app(app):
        pass

class ProductionConfig(Config):

    SECRET_KEY = os.environ.get('SECRET_KEY')

class DevelopmentConfig(Config):

    DEBUG = True
    SECRET_KEY = 'very secret key'

    MONGO_URI = 'mongodb://localhost:27017/vietbus_dev'

    CACHE_TYPE = 'simple'

class HerokuConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        pass

    MONGO_URI = os.environ.get('MONGOLAB_URI')

    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 60
    CACHE_REDIS_URL = os.environ.get('REDISCLOUD_URL')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,

    'default': DevelopmentConfig,
}
