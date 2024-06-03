# Para este projeto, optei por não fazer a declaração de modelos em arquivos separados, mas sim em um único arquivo models.py.
# Se o projeto crescer, pode ser útil isolar os modelos em arquivos separados para facilitar a manutenção e isolar lógicas.

from sqlalchemy import Column, BIGINT, Integer, Boolean, String, DateTime, ForeignKey, Index, Enum  # Importar os tipos de colunas que iremos utilizar, são os campos de dados, de forma simplificada
from . import Base  # Importar a Base que definimos no __init__.py
from sqlalchemy.orm import relationship  # Importar a relação entre tabelas
from datetime import datetime, timezone  # Importar a biblioteca datetime para obter a data e hora atuais


# Modelo de usuários do Telegram, discriminado desta forma pois você pode eventualmente querer lidar com um aplicativo externo ou site.
class TelegramUser(Base):
    """
    Representa um usuário do Telegram que interagiu com o bot.

    Atributos:
        id (int): Chave primária única para cada usuário, corresponde à ID do usuário no Telegram.
        username (str): Nome de usuário no Telegram. Pode ser nulo, pois nem todos os usuários definem um nome de usuário.
        nome_completo (str): Nome completo do usuário, se fornecido. Pode ser nulo, pois nem todos os usuários fornecem um nome completo.
        celular (str): Número de celular do usuário, se fornecido. Pode ser nulo, pois nem todos os usuários fornecem um número de celular.
        is_bot_owner (bool): Define se o usuário é o dono do bot. Pode ser falso, pois nem todos os usuários são donos do bot.
        is_bot_admin (bool): Define se o usuário é um administrador do bot. Pode ser falso, pois nem todos os usuários são administradores do bot.
        created_at (datetime): Data e hora em que o registro do usuário foi criado no sistema, usando UTC.
        updated_at (datetime): Data e hora da última atualização do registro do usuário, atualizada automaticamente.
        telegram_invites (relationship): Lista de convites gerados pelo usuário.
        invited_users (relationship): Lista de relações de usuários que este usuário convidou.
        messages (relationship): Mensagens enviadas para o usuário através do bot (exemplo de expansão, não ativado).

    A tabela armazena informações sobre os usuários para facilitar a gestão de interações, convites, e comunicações.
    """
    __tablename__ = 'telegram_users'

    id = Column(BIGINT, primary_key=True)  # Normalmente em banco de dados utiliza-se um campo id como chave primária, e é autoincrementável,
    # no caso do Telegram, vamos utilizar o a id do usuário entregue pelo próprio Telegram como nossa id.
    username = Column(String, nullable=True, default='Usuário sem @!')  # O nome de usuário do Telegram, como o Telegram permite que o usuário não tenha um nome de usuário, vamos permitir que seja nulo.
    nome_completo = Column(String, nullable=True, default='Usuário sem nome de conta.')  # O campo nome_completo é uma string que pode ser nula, ou seja, o usuário não queira fornecer seu nome em algum momento que isso possa ser pedido pelo bot.
    celular = Column(String, nullable=True, default='Usuário sem número de celular público!')  # O campo celular é uma string que pode ser nula, ou seja, o usuário pode não ter um celular cadastrado.
    is_bot_owner = Column(Boolean, default=False)  # O campo is_bot_owner é um booleano que define se o usuário é o dono do bot, ou seja, o administrador principal.
    is_bot_admin = Column(Boolean, default=False)  # O campo is_bot_admin é um booleano que define se o usuário é um administrador do bot, ou seja, um administrador secundário.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Importante: Repare a diferença entre DateTime e datetime, são coisas diferentes!
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))  # O campo updated_at será atualizado automaticamente

    # Relacionamento com o modelo de convites
    telegram_invites = relationship("TelegramInvite", back_populates="user")
    invited_users = relationship("TelegramUserRelation", foreign_keys="TelegramUserRelation.inviter_id", back_populates="inviter")

    # Ignore o campo abaixo, ele existe e é comentado para exemplificar como você pode expandir a aplicação, ele relaciona as mensagens enviadas pelo bot por comando.
    # # messages = relationship("TelegramMessage", back_populates="user")

    def __repr__(self):
        return f"<TelegramUser(id='{self.id}', username='{self.username}', created_at='{self.created_at}', updated_at='{self.updated_at}')>"


# Modelo de convites
class TelegramInvite(Base):
    """
    Representa um convite gerado por um usuário do Telegram para convidar outros usuários para participar de um grupo.

    Atributos:
        id (int): Chave primária única para cada convite, autoincrementável.
        user_id (int): Chave estrangeira referenciando o ID do usuário que criou o convite. Relaciona-se com a tabela 'telegram_users'.
        invite_code (str): Código único do convite, utilizado para rastrear a utilização e garantir que convites sejam únicos.
        created_at (datetime): Data e hora de criação do convite, usando UTC. Define quando o convite foi gerado.
        usages (relationship): Relação que rastreia todas as utilizações deste convite, ligando a quem e quando o convite foi usado.

    Este modelo ajuda a gerenciar e rastrear os convites gerados pelos usuários, permitindo uma análise detalhada de como os usuários estão promovendo o bot ou eventos/grupos associados.
    """
    __tablename__ = 'telegram_invites'
    __table_args__ = (Index('ix_invite_code', 'invite_code'), )  # Aqui estamos criando um índice para o campo invite_code, para melhorar a performance de consultas, esta será a tabela mais utilizada.

    id = Column(Integer, primary_key=True, autoincrement=True)  # Aqui temos a id autoincremental que eu comentei anteriormente
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)  # Aqui é a id do usuário que criou o convite, e é uma chave estrangeira para a tabela de usuários
    invite_code = Column(String, unique=True, nullable=False)  # O código do convite é único, ou seja, não pode haver códigos iguais
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # O campo created_at é a data e hora de criação do convite
    # Os campos abaixo são novamente ideias de como você pode expandir o modelo de dados, mas não são demandados pelo projeto.
    # Vai da sua criatividade e necessidade, poderia por exemplo até monetizar privilégios de convites gerados...
    # user_limit = Column(Integer, default=1)  # O número de usuários que podem ser convidados por este convite
    # expires_at = Column(DateTime, nullable=True)  # A data de expiração do convite, se for nulo, o convite não expira

    # Se você quiser expandir este bot para integrar outros grupos, você pode adicionar um campo para o grupo associado ao convite, por exemplo.
    # Para este exemplo abaixo seria necessário criar o modelo de grupos e adicionar o relacionamento entre os modelos.
    # group_id = Column(Integer, ForeignKey('telegram_groups.id'), nullable=True)  # A id do grupo associado ao convite.

    # Relacionamento com o modelo User
    user = relationship("TelegramUser", back_populates="telegram_invites")

    # Rastreio de uso do convite
    usages = relationship("TelegramUserRelation", back_populates="invite")

    def __repr__(self):
        return f"<TelegramInvite(id='{self.id}', user_id='{self.user_id}', invite_code='{self.invite_code}', created_at='{self.created_at}')>"


# Modelo para pendência de convites
class InviteConfirmation(Base):
    __tablename__ = 'invite_confirmations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    invite_id = Column(Integer, ForeignKey('telegram_invites.id'), nullable=False)
    status = Column(Enum('pendente', 'confirmado', 'negado'), default='pendente', nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("TelegramUser", foreign_keys=[user_id])
    invite = relationship("TelegramInvite", foreign_keys=[invite_id])

    def __repr__(self):
        return f"<InviteConfirmation(id={self.id}, user_id={self.user_id}, invite_id={self.invite_id}, status='{self.status}')>"

# Adicionando a relação entre os modelos de usuários e convites para permitir o rastreio que é o que você deseja neste ponto do projeto.
class TelegramUserRelation(Base):
    """
    Representa a relação de convite entre usuários no contexto do bot do Telegram, detalhando quem convidou quem e através de qual convite.

    Atributos:
        id (int): Chave primária única para cada relação de convite, autoincrementável.
        inviter_id (int): Chave estrangeira que referencia o ID do usuário que enviou o convite (inviter). Relaciona-se com a tabela 'telegram_users'.
        invited_id (int): Chave estrangeira que referencia o ID do usuário que foi convidado (invited). Relaciona-se com a tabela 'telegram_users'.
        invite_id (int): Chave estrangeira que referencia o ID do convite usado na relação. Relaciona-se com a tabela 'telegram_invites'.
        joined_at (datetime): Data e hora em que o usuário convidado aceitou o convite, usando UTC.

    Este modelo é crucial para rastrear como os usuários estão conectados através de convites e para analisar a rede de usuários formada através das interações com o bot.
    """
    __tablename__ = 'telegram_hierarchy'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Novamente, uma id própria para o relacionamento de dados.
    inviter_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)  # A id do usuário que convidou
    invited_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)  # A id do usuário convidado
    invite_id = Column(Integer, ForeignKey('telegram_invites.id'), nullable=False)  # A id do convite utilizado
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # A data e hora que o usuário convidado aceitou o convite (identificado pelo bot)

    # Relacionamentos
    inviter = relationship("TelegramUser", foreign_keys=[inviter_id], back_populates="invited_users")
    invited = relationship("TelegramUser", foreign_keys=[invited_id])
    invite = relationship("TelegramInvite", back_populates="usages")

    def __repr__(self):
        return f"<TelegramUserRelation(inviter_id='{self.inviter_id}', invited_id='{self.invited_id}', invite_id='{self.invite_id}', joined_at='{self.joined_at}')>"


# O modelo abaixo é apenas um exemplo de como você pode expandir a aplicação, ele é uma ideia para o gerenciamento de mensagens no privado de usuários através do bot.
# Este modelo não é refinado, e é integrado com o modelo de usuários, como comentado acima.
# Se for descomentar para criar a tabela, deve-se descomentar o relacionamento no modelo users, e adicionar a funcionalidade no bot.py.
# # class TelegramMessage(Base):
# #     raise NotImplementedError("Este modelo (TelegramMessage) é um exemplo de expansão e não foi implementado, remova este erro quando implementar o modelo. (descomentar o código no modelo de usuário)")
# #     __tablename__ = 'telegram_messages'

# #     id = Column(Integer, primary_key=True, autoincrement=True)
# #     user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
# #     text = Column(String, nullable=False)
# #     status = Column(Enum('enviada', 'recebida', 'bloqueado', 'erro'), default='enviada', nullable=False)
# #     sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# #     # Relacionamento com o modelo User
# #     user = relationship("TelegramUser", back_populates="messages")

# #     def __repr__(self):
# #         return f"<Message(id='{self.id}', user_id='{self.user_id}', text='{self.text}', status='{self.status}', sent_at='{self.sent_at}')>"
