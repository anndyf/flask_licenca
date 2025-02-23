from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from datetime import datetime, timedelta
from config import Config
from models import db, User, Licenca, Condicionante
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename
import os
import pandas as pd
from pathlib import Path
from extensions import mail  
from email_service import enviar_email_vencimento
from flask_apscheduler import APScheduler

scheduler = APScheduler()
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# Inicializando a aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)


# Inicializando as extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
mail.init_app(app)


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
    hoje = datetime.utcnow().date()

    # Buscar todas as licenças
    licencas = Licenca.query.all()
    total_licencas = len(licencas)

    # Contar licenças vencendo nos próximos 30 dias
    vencendo_breve = Licenca.query.filter(
        Licenca.vencimento > hoje,  # Ainda não venceu
        Licenca.vencimento <= hoje + timedelta(days=30)
    ).count()

    # Contar licenças expiradas (já passaram da data de vencimento)
    expiradas = Licenca.query.filter(Licenca.vencimento < hoje).count()

    # Lista de licenças próximas ao vencimento com status ajustado
    licencas_vencendo = []
    for licenca in Licenca.query.filter(Licenca.vencimento <= hoje + timedelta(days=30)).all():
        dias_restantes = (licenca.vencimento - hoje).days

        # Definir status correto para cada licença
        if dias_restantes > 0:
            licenca.status = "Próxima ao Vencimento"
        elif dias_restantes == 0:
            licenca.status = "Vence Hoje"
        else:
            licenca.status = "Expirado"

        licenca.dias_restantes = dias_restantes  # Armazena para exibição
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
        try:
            # Criar a licença
            nova_licenca = Licenca(
                empresa=request.form['empresa'],
                email_empresa=request.form['email_empresa'],
                ato=request.form['ato'],
                portaria=request.form['portaria'],
                data_publicacao=datetime.strptime(
                    request.form['data_publicacao'], "%Y-%m-%d"),
                vencimento=datetime.strptime(
                    request.form['vencimento'], "%Y-%m-%d"),
                observacoes=request.form.get('observacoes', '')
            )
            db.session.add(nova_licenca)
            db.session.commit()

            # Recuperar dados das condicionantes
            descricoes = request.form.getlist('condicionante_descricao[]')
            prazos = request.form.getlist('prazo_cumprimento[]')
            metas = request.form.getlist('meta_execucao[]')
            situacoes = request.form.getlist('situacao[]')

            print("Descrições recebidas:", descricoes)  # Debug

            for i in range(len(descricoes)):
                if descricoes[i]:  # Evita salvar condicionantes vazias
                    nova_condicionante = Condicionante(
                        licenca_id=nova_licenca.id,
                        descricao=descricoes[i],
                        prazo_cumprimento=prazos[i] if i < len(
                            prazos) else None,
                        meta_execucao=datetime.strptime(
                            metas[i], "%Y-%m-%d") if metas[i] else None,
                        situacao=situacoes[i] if i < len(situacoes) else None
                    )
                    db.session.add(nova_condicionante)

            db.session.commit()
            flash('Licença cadastrada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            print("Erro ao cadastrar licença:", e)  # Debug
            db.session.rollback()
            flash('Erro ao cadastrar licença.', 'danger')

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
def editar_licenca(id):
    licenca = Licenca.query.get_or_404(id)

    if request.method == 'POST':
        licenca.empresa = request.form['empresa']
        licenca.email_empresa = request.form['email_empresa'] 
        licenca.ato = request.form['ato']
        licenca.portaria = request.form['portaria']
        licenca.data_publicacao = datetime.strptime(
            request.form['data_publicacao'], "%Y-%m-%d")
        licenca.vencimento = datetime.strptime(
            request.form['vencimento'], "%Y-%m-%d")
        licenca.observacoes = request.form.get('observacoes', '')

        # Removendo condicionantes antigas e inserindo novas
        Condicionante.query.filter_by(licenca_id=id).delete()
        db.session.commit()

        descricoes = request.form.getlist('condicionante_descricao[]')
        prazos = request.form.getlist('prazo_cumprimento[]')
        metas = request.form.getlist('meta_execucao[]')
        situacoes = request.form.getlist('situacao[]')

        for i in range(len(descricoes)):
            if descricoes[i]:
                nova_condicionante = Condicionante(
                    licenca_id=id,
                    descricao=descricoes[i],
                    prazo_cumprimento=prazos[i] if i < len(prazos) else None,
                    meta_execucao=datetime.strptime(
                        metas[i], "%Y-%m-%d") if metas[i] else None,
                    situacao=situacoes[i] if i < len(situacoes) else None
                )
                db.session.add(nova_condicionante)

        db.session.commit()
        flash('Licença atualizada com sucesso!', 'success')
        return redirect(url_for('list_licenses'))

    return render_template('editar_licenca.html', licenca=licenca, enumerate=enumerate)


# -------------------- LISTAR LICENCAS --------------------


@app.route('/licencas', methods=['GET', 'POST'])
@login_required
def list_licenses():
    # Captura os parâmetros GET para filtros
    search_query = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)

    # Consulta base
    query = Licenca.query

    # Aplicando filtros de forma independente
    if search_query:
        query = query.filter(Licenca.empresa.ilike(f"%{search_query}%"))

    if status_filter:
        query = query.filter(Licenca.status == status_filter)

    # Paginação
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'listar_licencas.html',
        licencas=pagination.items,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter,
        enumerate=enumerate  # Adiciona enumerate para uso no template
    )

# -------------------- LICENCAS VENCENDO --------------------


@app.route('/licencas/vencendo')
@login_required
def expiring_licenses():
    hoje = datetime.utcnow().date()
    prazo_alerta = hoje + timedelta(days=30)

    licencas_vencendo = Licenca.query.filter(
        Licenca.vencimento <= prazo_alerta, Licenca.vencimento >= hoje).all()

    return render_template('licencas_vencendo.html', licencas=licencas_vencendo, hoje=hoje)

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
        flash("Licença excluída com sucesso!",
              "success")  # Mensagem de sucesso
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

# -------------------- EDITAR USUARIOS --------------------
@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if not current_user.is_admin:
        flash("Acesso negado! Apenas administradores podem editar usuários.", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']

        if request.form['password']:
            user.set_password(request.form['password'])  # Certifique-se que `set_password` faz hash da senha

        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for('list_users'))

    return render_template('edit_user.html', user=user)


# -------------------- UPLOAD DAS PLANILHAS --------------------
def allowed_file(filename):
    return Path(filename).suffix.lower() in {'.xls', '.xlsx'}


@app.route('/upload_licencas', methods=['POST'])
def upload_licencas():
    if 'file_upload' not in request.files:
        flash('Nenhum arquivo enviado!', 'danger')
        return redirect(request.referrer)

    file = request.files['file_upload']

    if file.filename == '':
        flash('Nenhum arquivo selecionado!', 'danger')
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        try:
            # Lendo a planilha diretamente da requisição
            df = pd.read_excel(file)

            # Iterando sobre as linhas e cadastrando no banco de dados
            for _, row in df.iterrows():
                nova_licenca = Licenca(
                    empresa=row.get('Empresa', ''),
                    ato=row.get('Ato', ''),
                    portaria=row.get('Portaria Nº', ''),
                    data_publicacao=pd.to_datetime(
                        row.get('Data de Publicação', ''), errors='coerce').date(),
                    vencimento=pd.to_datetime(
                        row.get('Vencimento', ''), errors='coerce').date(),
                    condicionantes=row.get('Condicionantes Ambientais', ''),
                    prazo_cumprimento=row.get('Prazo de Cumprimento', ''),
                    status=row.get('Status', ''),
                    observacoes=row.get('Observações', '')
                )

                # Adiciona a licença ao banco apenas se os dados essenciais estiverem preenchidos
                if nova_licenca.empresa and nova_licenca.ato and nova_licenca.portaria:
                    db.session.add(nova_licenca)

            # Commitando as mudanças no banco de dados
            db.session.commit()
            flash('Licenças importadas com sucesso!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar a planilha: {str(e)}', 'danger')

        return redirect(url_for('list_licenses'))

    flash('Formato de arquivo inválido. Envie um arquivo .xls ou .xlsx.', 'danger')
    return redirect(request.referrer)

# -------------------- ENVIO DE EMAIL --------------------
def verificar_licencas_vencendo():
    hoje = datetime.today()
    proximos_30_dias = hoje + timedelta(days=30)

    licencas_vencendo = Licenca.query.filter(Licenca.vencimento <= proximos_30_dias, Licenca.vencimento >= hoje).all()

    for licenca in licencas_vencendo:
        dias_para_vencimento = (licenca.vencimento - hoje.date()).days
        
        # Enviar email apenas se faltarem 30, 25, 20, 15, 10, 5, ou 0 dias para o vencimento
        if dias_para_vencimento % 5 == 0 or dias_para_vencimento == 0:
            enviar_email_vencimento(licenca)  # Envia o e-mail

@scheduler.task('interval', hours=24)  # Executa a cada 24 horas
def job_verificar_licencas():
    verificar_licencas_vencendo()

scheduler.init_app(app)
scheduler.start()

# -------------------- EXECUÇÃO DO SERVIDOR --------------------


if __name__ == '__main__':
    app.run(debug=True)
