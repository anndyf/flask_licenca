import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env, se existir
load_dotenv()

class Config:
    # Chave secreta para sessões e criptografia; defina em ambiente de produção
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')

    # Configuração do banco de dados; use DATABASE_URL para ambiente de produção
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://flask_user:12345@localhost/flask_licencas')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuração do Flask-Mail para Gmail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'eneaslima2010@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'byev lslx guca opwp')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'eneaslima2010@gmail.com')
