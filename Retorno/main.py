import re

from datetime import datetime, timezone
from threading import Timer

import telebot
from telebot import types

from sqlalchemy import func

from db import session
from db.models import TelegramUser, TelegramInvite, TelegramUserRelation, InviteConfirmation


# Token do bot fornecido pelo BotFather
TOKEN = '6801747573:AAE4glSvhIeJjewJorEm9fNYRPwEYKmdk9o'
bot = telebot.TeleBot(TOKEN)

# Verifica se um usuário está no chat mencionado
def check_user_membership(chat_id, user_id):
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        # A propriedade 'status' pode ser 'creator', 'administrator', 'member', 'restricted', 'left' ou 'kicked'
        if chat_member.status in ['creator', 'administrator', 'member', 'restricted']:
            print(f"O usuário {user_id} é membro do chat {chat_id}.")
            return True
        else:
            print(f"O usuário {user_id} não é membro do chat {chat_id}.")
            return False
    except Exception as e:
        print(f"Ocorreu um erro ao verificar a associação: {e}")
        return False


# Inicialização do bot pelo usuário, que realiza o cadastro do mesmo.
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id  # Extração da ID do usuário do objeto Message
    existing_user = session.query(TelegramUser).filter_by(id=user_id).first()  # Verificação se o usuário já existe no banco de dados
    if not existing_user:  # Se o usuário não existir, ele é cadastrado
        nome_completo = ''
        if message.from_user.first_name:
            nome_completo += message.from_user.first_name
        if message.from_user.last_name:
            nome_completo += f" {message.from_user.last_name}"
        celular = None
        # if message.from_user.phone_number:
        #    celular = '00' # A forma de captura desse dado precisa ser revista
        new_user = TelegramUser(id=user_id, nome_completo=nome_completo, username=message.from_user.username, celular=celular, created_at=datetime.now(timezone.utc))
        session.add(new_user)
        session.commit()
        try:
            bot.send_message(message.chat.id, "Você foi cadastrado com sucesso!\n\nUtilize o comando /gerar para obter o seu link de convite. Caso você tenha sido convidado por alguém, por favor, me envie o link de convite que você recebeu.", parse_mode="HTML") 
        except:
            pass
    else:
        try:
            bot.send_message(message.chat.id, "Você já está cadastrado. Você deve utilizar o comando /gerar para obter seu link de convite. Se você foi convidado por alguém, me envie o link de convite pelo qual você foi convidado para eu o validar.", parse_mode="HTML")
        except:
            pass

# Responde ao comando /gerar com um link de convite do grupo
@bot.message_handler(commands=['gerar'])
def handle_generate(message):
    # Verifica se o comando foi enviado em um chat privado e ignora caso não seja
    if not message.chat.type == 'private':
        return
    user_id = message.from_user.id
    chat_id = -1001961959701  # ID do grupo Telegram
    try:
        status = check_user_membership(chat_id, user_id)
        if not status:
            try:
                bot.send_message(message.chat.id, "Você deve ser membro do grupo para gerar um link de convite.")
            except:
                pass
            return
        # Verificamos se já existe um convite para este usuário
        existing_invite = session.query(TelegramInvite).filter_by(user_id=user_id).first()
        if not existing_invite:  # Se não existir, criamos um novo link de convite para o atribuir ao usuário.
            invite_link_response = bot.create_chat_invite_link(chat_id)
            invite_link = invite_link_response.invite_link

            # Cria um novo registro no banco de dados para salvar esse link de convite
            new_invite = TelegramInvite(user_id=user_id, invite_code=invite_link)
            session.add(new_invite)
            session.commit()
            try:
                bot.send_message(message.chat.id, f"Seu link de convite foi cadastrado e é: {invite_link}", parse_mode="HTML")
            except:
                pass
        else:  # Se já existir, retornamos o link de convite já existente
            try:
                bot.send_message(message.chat.id, f"Seu link de convite já foi gerado anteriormente e é: {existing_invite.invite_code}\n\nCaso ele não esteja funcionando, notifique a administração pois aconteceu uma limitação do Telegram!", parse_mode="HTML")
            except:
                pass

    except Exception as e:
        try:
            bot.send_message(message.chat.id, f"Erro ao criar link de convite (notificar a administração): {str(e)}")
        except:
            pass


# Envia o ranking dos top 5 usuários que mais convidaram manualmente
@bot.message_handler(commands=['ranking'])
def handle_manual_ranking(message):
    user_id = message.from_user.id
    # Verificamos se já existe um convite para este usuário
    usuario = session.query(TelegramUser).filter_by(id=user_id).first()
    if not usuario:
        bot.send_message(message.chat.id, "Você não está cadastrado no sistema. Utilize o comando /start para se cadastrar.")
        return
    if usuario.is_bot_owner or usuario.is_bot_admin:
        top_users = session.query(
        TelegramUser.id,
        TelegramUser.nome_completo,
        TelegramUser.username,
        func.count(TelegramInvite.id).label('invite_count')
        ).join(TelegramInvite, TelegramUser.id == TelegramInvite.user_id) \
        .join(InviteConfirmation, TelegramInvite.id == InviteConfirmation.invite_id) \
        .filter(InviteConfirmation.status == 'confirmada') \
        .group_by(TelegramUser.id, TelegramUser.nome_completo, TelegramUser.username) \
        .order_by(func.count(TelegramInvite.id).desc()) \
        .limit(5).all()

        if not top_users:
            bot.send_message(message.chat.id, "Não há dados suficientes para exibir o ranking.")
            return

        leaderboard_text = "🏆 Top Convidadores 🏆\n\n" + "\n".join([f'<a href="tg://user?id={user.id}">{user.nome_completo} ({user.username})</a>: {user.invite_count}' for user in top_users])

        try:
            bot.send_message(chat_id=message.chat.id, text=leaderboard_text, parse_mode='HTML')
        except:
            pass

timer = None # Segurança para previnir instancias duplicadas futuramente.

# Envia o ranking dos top 5 usuários que mais convidaram periodicamente
def send_leaderboard():
    global timer
    if timer is not None:
        timer.cancel()  # Cancelar o temporizador atual para evitar instâncias duplicadas
    # Buscar os top 5 usuários
    top_users = session.query(
    TelegramUser.id,
    TelegramUser.nome_completo,
    TelegramUser.username,
    func.count(TelegramInvite.id).label('invite_count')
    ).join(TelegramInvite, TelegramUser.id == TelegramInvite.user_id) \
    .join(InviteConfirmation, TelegramInvite.id == InviteConfirmation.invite_id) \
    .filter(InviteConfirmation.status == 'confirmada') \
    .group_by(TelegramUser.id, TelegramUser.nome_completo, TelegramUser.username) \
    .order_by(func.count(TelegramInvite.id).desc()) \
    .limit(5).all()

    # Esta condicional verifica se existem usuários para enviar o ranking
    if top_users is None:
        timer = Timer(7200, send_leaderboard)  # Resetar o temporizador
        timer.start()
        return

    leaderboard_text = "🏆 Top Convidadores 🏆\n\n" + "\n".join([f'<a href="tg://user?id={user.id}">{user.nome_completo} ({user.username})</a>: {user.invite_count}' for user in top_users])
    try:
        bot.send_message(chat_id=-1001961959701, text=leaderboard_text, parse_mode='HTML')  # envio da mensagem
    except:
        pass

    timer = Timer(7200, send_leaderboard) # Resetar o temporizador
    timer.start()  # Reiniciar o temporizador

send_leaderboard()  # Inicializar a primeira chamada do ranking automaticamente

# Verifica mensagens de texto no privado para procurar links de convite do Telegram
@bot.message_handler(content_types=['text'])
def handle_message(message):
    # Verifica se a mensagem foi enviada em um chat privado
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    text = message.text

    # Verificar se a mensagem contém um link de convite do Telegram
    invite_link = re.search(r'https://t\.me/\S+', text)
    if invite_link:
        status = check_user_membership(-1001961959701, user_id)
        if not status:
            try:
                bot.send_message(message.chat.id, "Você deve ser membro do grupo para confirmar um convite. Clique no link.")
            except:
                pass
            return
        link = invite_link.group(0)

        # Verificar se o link de convite é registrado e pertence à um membro do grupo
        inviter = session.query(TelegramInvite).filter_by(invite_code=link).first()
        if not inviter:
            try:
                bot.reply_to(message, "Este link de convite não é válido.")
            except:
                pass
            return
        # Verificar a id do link de convite
        invite_id = inviter.id
        if inviter.user_id == user_id:
            try:
                bot.reply_to(message, "Você não pode confirmar um convite gerado por você mesmo.")
            except:
                pass
            return
        # Adição de um novo registro de relação entre o usuário e o link de convite para que este seja confirmado
        confirmation = InviteConfirmation(user_id=user_id, invite_id=invite_id)
        session.add(confirmation)
        session.commit()

        confirmation = session.query(InviteConfirmation).filter_by(user_id=user_id, invite_id=invite_id).first()

        # Teclado que pode ser customizado, gera uma callback para confirmar ou negar o vínculo
        markup = types.InlineKeyboardMarkup(row_width=1)
        yes_button = types.InlineKeyboardButton("Sim, este foi o usuário que me convidou!", callback_data=f"confirmar_{confirmation.id}")
        no_button = types.InlineKeyboardButton("Não, eu não reconheço este usuário!", callback_data=f"negar_{confirmation.id}")
        markup.add(yes_button, no_button)

        # Obter as informações do usuário que gerou o convite
        inviter_user = session.query(TelegramUser).filter_by(id=inviter.user_id).first()
        try:
            bot.send_message(
                chat_id=message.chat.id,
                text=f'Este link foi gerado por <a href="tg://user?id={inviter_user.id}">{inviter_user.nome_completo} ({inviter_user.username})</a>. Deseja confirmar o vínculo? Clique abaixo!',
                reply_markup=markup,
                parse_mode="HTML"
            )
        except:
            pass

# Manipulação de callbacks para confirmar ou negar o vínculo
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    action, confirmation_id = call.data.split("_")
    confirmation = session.query(InviteConfirmation).filter_by(id=int(confirmation_id)).first()
    # Buscar o usuário responsável pelo convite
    invite = session.query(TelegramInvite).filter_by(id=confirmation.invite_id).first()
    # Buscar informações do usuário convidado
    invited_user = session.query(TelegramUser).filter_by(id=confirmation.user_id).first()

    # Verificar se já existe uma confirmação efetivada para este usuário
    existing_confirmation = session.query(InviteConfirmation).filter_by(user_id=confirmation.user_id, status='confirmada').first()
    if existing_confirmation:
        try:
            bot.answer_callback_query(call.id, "Você já confirmou um convite anteriormente! Cada usuário pode confirmar apenas um convite.")
        except:
            pass
        return  # Interrompe a execução para evitar confirmações duplicadas

    status = check_user_membership(-1001961959701, confirmation.user_id)
    if not status:
        try:
            bot.answer_callback_query(call.id, "Você deve ser membro do grupo para confirmar um convite. Retorne ao grupo ou entre primeiro clicando no link.")
        except:
            pass
        return

    if action == 'confirmar':
        confirmation.status = 'confirmada'
        try:
            bot.answer_callback_query(call.id, "Vínculo confirmado!\n\nQue tal você mesmo gerar seu link de convite para você participar também? Utilize o comando /gerar!")
        except:
            pass
        # Cria a relação de convite no banco de dados
        new_relation = TelegramUserRelation(
            inviter_id=invite.user_id,
            invited_id=invited_user.id,
            invite_id=confirmation.invite_id,
            joined_at=datetime.now(timezone.utc)
        )
        session.add(new_relation)

        try:
            bot.send_message(invite.user_id, f'Seu convite para <a href="tg://user?id={confirmation.user_id}">{invited_user.nome_completo} ({invited_user.username})</a> foi confirmado!')
        except Exception as e:
            print(f"Erro ao enviar mensagem para o usuário {invite.user_id}: {str(e)}")
    elif action == 'negar':
        confirmation.status = 'negada'
        try:
            bot.answer_callback_query(call.id, "Vínculo negado! Você pode tentar novamente com outro link de convite.")
        except:
            pass
        try:
            bot.send_message(invite.user_id, f'O usuário <a href="tg://user?id={confirmation.user_id}">{invited_user.nome_completo} ({invited_user.username})</a> tentou utilizar o seu link de convite mas negou a confirmação!')
        except Exception as e:
            print(f"Erro ao enviar mensagem para o usuário {invite.user_id}: {str(e)}")

    session.commit()
    try:
        bot.edit_message_text(
            text=f"Status do convite: {confirmation.status}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    except:
        pass


if __name__ == '__main__':
    bot.polling(none_stop=True)
