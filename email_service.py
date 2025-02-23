from flask_mail import Message
from app import mail  # Importando a configuração do Flask-Mail

def enviar_email_vencimento(licenca):
    """Função para enviar notificação de vencimento de licença."""
    destinatarios = ["eneaslima2010@gmail.com"]  # Email do administrador

    # Se a empresa tem um e-mail cadastrado, adiciona à lista de destinatários
    if licenca.email_empresa:
        destinatarios.append(licenca.email_empresa)

    assunto = f"⚠️ Alerta de Vencimento de Licença - {licenca.empresa}"
    
    mensagem = Message(assunto, recipients=destinatarios)
    mensagem.body = f"""
    Prezado(a),

    A licença da empresa {licenca.empresa} está próxima do vencimento.

    📌 **Detalhes da Licença**:
    - **Empresa:** {licenca.empresa}
    - **Ato:** {licenca.ato}
    - **Vencimento:** {licenca.vencimento.strftime('%d/%m/%Y')}

    ⚠️ **Ação necessária**: Atualize ou renove a licença para evitar problemas.

    Atenciosamente,  
    Lima - Consultoria Ambiental
    """

    try:
        mail.send(mensagem)
        print(f"E-mail enviado para {destinatarios}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
