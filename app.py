from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from datetime import datetime, timedelta
from config import Config
from models import db, User, Licenca
from flask import jsonify
# Inicializando a aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializando as extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- ROTAS DO SISTEMA --------------------

@app.route('/')
def index():
    # Direciona diretamente para o dashboard
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Login inválido!', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------------------- DASHBOARD --------------------

@app.route('/dashboard')
@login_required
def dashboard():
    licencas = Licenca.query.all()

    total_licencas = len(licencas)
    vencendo_breve = Licenca.query.filter(Licenca.vencimento <= datetime.utcnow().date() + timedelta(days=30)).count()
    expiradas = Licenca.query.filter(Licenca.vencimento < datetime.utcnow().date()).count()

    # Calculando os dias restantes para cada licença
    licencas_vencendo = []
    for licenca in Licenca.query.filter(Licenca.vencimento <= datetime.utcnow().date() + timedelta(days=30)).all():
        # Converter `licenca.vencimento` (date) para `datetime`
        vencimento_datetime = datetime.combine(licenca.vencimento, datetime.min.time())
        licenca.dias_restantes = (vencimento_datetime - datetime.utcnow()).days
        licencas_vencendo.append(licenca)

    return render_template(
        'dashboard.html',
        licencas_vencendo=licencas_vencendo,
        total_licencas=total_licencas,
        vencendo_breve=vencendo_breve,
        expiradas=expiradas
    )
# -------------------- CADASTRO DE LICENÇAS --------------------


@app.route('/cadastrar_licenca', methods=['GET', 'POST'])
@login_required
def cadastrar_licenca():
    if request.method == 'POST':
        empresa = request.form['empresa']
        ato = request.form['ato']
        portaria = request.form['portaria']
        data_publicacao = datetime.strptime(
            request.form['data_publicacao'], "%Y-%m-%d")
        vencimento = datetime.strptime(request.form['vencimento'], "%Y-%m-%d")
        condicionantes = request.form.get('condicionantes', '')
        prazo_cumprimento = request.form.get('prazo_cumprimento', '')
        status = request.form.get('status', 'Ativa')
        observacoes = request.form.get('observacoes', '')

        nova_licenca = Licenca(
            empresa=empresa,
            ato=ato,
            portaria=portaria,
            data_publicacao=data_publicacao,
            vencimento=vencimento,
            condicionantes=condicionantes,
            prazo_cumprimento=prazo_cumprimento,
            status=status,
            observacoes=observacoes
        )

        db.session.add(nova_licenca)
        db.session.commit()
        flash('Licença cadastrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('cadastrar_licenca.html')


# -------------------- GERENCIAMENTO DE USUÁRIOS --------------------

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash("Acesso negado! Apenas administradores podem criar usuários.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == "on"

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
            return redirect(url_for('create_user'))

        new_user = User(username=username, email=email, is_admin=is_admin)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Novo usuário criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('criar_usuario.html')


@app.route('/trocar_senha', methods=['GET', 'POST'])
@login_required
def trocar_senha():
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if not current_user.check_password(senha_atual):
            flash('Senha atual incorreta!', 'danger')
        elif nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem!', 'danger')
        else:
            current_user.update_password(nova_senha)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('trocar_senha.html')


@app.route('/admin/trocar_senha/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_trocar_senha(user_id):
    if not current_user.is_admin:
        flash("Acesso negado!", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem!', 'danger')
        else:
            user.update_password(nova_senha)
            db.session.commit()
            flash(f'Senha de {user.username} alterada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('admin_trocar_senha.html', user=user)

# -------------------- EDITAR LICENCAS --------------------


@app.route('/editar_licenca/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_license(id):
    licenca = Licenca.query.get_or_404(id)

    if request.method == 'POST':
        licenca.empresa = request.form['empresa']
        licenca.ato = request.form['ato']
        licenca.portaria = request.form['portaria']
        licenca.data_publicacao = datetime.strptime(
            request.form['data_publicacao'], '%Y-%m-%d')
        licenca.vencimento = datetime.strptime(
            request.form['vencimento'], '%Y-%m-%d')
        licenca.condicionantes = request.form['condicionantes']
        licenca.prazo_cumprimento = request.form['prazo_cumprimento']
        licenca.status = request.form['status']
        licenca.observacoes = request.form['observacoes']

        db.session.commit()
        flash('Licença atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('editar_licenca.html', licenca=licenca)

# -------------------- LISTAR LICENCAS --------------------


@app.route('/licencas')
@login_required
def list_licenses():
    licencas = Licenca.query.all()
    return render_template('listar_licencas.html', licencas=licencas)

# -------------------- LICENCAS VENCENDO --------------------


@app.route('/licencas/vencendo')
@login_required
def expiring_licenses():
    hoje = datetime.utcnow().date()
    # Licenças que vencem nos próximos 30 dias
    prazo_alerta = hoje + timedelta(days=30)
    licencas_vencendo = Licenca.query.filter(
        Licenca.vencimento <= prazo_alerta, Licenca.vencimento >= hoje).all()

    return render_template('licencas_vencendo.html', licencas=licencas_vencendo)

# -------------------- EXCLUIR LICENCAS --------------------

@app.route('/delete_license/<int:id>', methods=['POST'])
@login_required
def delete_license(id):
    licenca = Licenca.query.get(id)
    if not licenca:
        flash("Licença não encontrada.", "danger")
        return redirect(url_for('list_licenses'))

    try:
        db.session.delete(licenca)
        db.session.commit()
        flash("Licença excluída com sucesso!", "success")  # Mensagem de sucesso
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir a licença.", "danger")

    return redirect(url_for('list_licenses'))


# -------------------- OUTRAS PÁGINAS --------------------

@app.route('/painel')
def painel():
    return render_template('dashboard.html')


@app.route('/documentos')
def documentos():
    return render_template('documentos.html')

# -------------------- LISTAR USUARIOS --------------------


@app.route('/admin/list_users')
@login_required
def list_users():
    if not current_user.is_admin:
        flash("Acesso negado! Apenas administradores podem visualizar usuários.", "danger")
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('list_users.html', users=users)


# -------------------- EXECUÇÃO DO SERVIDOR --------------------

if __name__ == '__main__':
    app.run(debug=True)
