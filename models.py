from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

# Inicialização dos módulos
bcrypt = Bcrypt()
db = SQLAlchemy()

# -------------------- MODELO DE USUÁRIO --------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Define uma senha criptografada"""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.check_password_hash(self.password, password)

    def update_password(self, new_password):
        """Atualiza a senha do usuário"""
        self.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

# -------------------- MODELO DE LICENÇAS --------------------

class Licenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(200), nullable=False)
    ato = db.Column(db.String(200), nullable=False)
    portaria = db.Column(db.String(50), nullable=False)
    data_publicacao = db.Column(db.Date, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    condicionantes = db.Column(db.Text, nullable=True)
    prazo_cumprimento = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    def esta_proxima_do_vencimento(self):
        """Retorna True se a licença estiver a menos de 30 dias do vencimento"""
        return self.vencimento <= datetime.utcnow().date() + timedelta(days=30)
