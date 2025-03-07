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
        self.password = bcrypt.generate_password_hash(
            new_password).decode('utf-8')

# -------------------- MODELO DE LICENÇAS --------------------


class Licenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(255), nullable=False)
    email_empresa = db.Column(db.String(255), nullable=False)
    ato = db.Column(db.String(100), nullable=False)
    portaria = db.Column(db.String(100), nullable=False)
    data_publicacao = db.Column(db.Date, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    # Corrigindo o relacionamento para evitar conflito de nomes
    condicionantes = db.relationship("Condicionante", back_populates="licenca", cascade="all, delete-orphan")



class Condicionante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    licenca_id = db.Column(db.Integer, db.ForeignKey('licenca.id', ondelete="CASCADE"), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prazo_cumprimento = db.Column(db.Date, nullable=True)
    meta_execucao = db.Column(db.Date, nullable=True)
    situacao = db.Column(db.String(50), nullable=False)
    alerta = db.Column(db.Boolean, default=False)

    # Aqui ajustamos para evitar conflito
    licenca = db.relationship("Licenca", back_populates="condicionantes")


