# O arquivo __init__.py é um arquivo especial do Python que é executado quando um pacote é importado. Ele é útil para definir variáveis
# e funções que serão utilizadas em outros arquivos do pacote.
# Neste caso, estamos definindo a conexão com o banco de dados e a sessão para interagir com o banco de dados. 
# Isso é feito utilizando o SQLAlchemy, que é uma biblioteca de mapeamento objeto-relacional (ORM) para Python.
# O SQLAlchemy permite interagir com o banco de dados utilizando objetos Python em vez de escrever SQL diretamente, como exemplificado na mensagem do Telegram.
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Aqui nós definimos qual o driver de banco de dados a ser utilizado, repare que estamos utilizando o SQLite
# O SQLite é um banco de dados que não necessita de instalação de servidor, ele é um banco de dados local
# Ele perde um pouco em performance e concorrência, mas por enquanto é suficiente. Depois é fácil migrar para um banco de dados melhor (como postgres)
engine = create_engine('sqlite:///convites.db', echo=True)  # O echo=True é útil para debugar

# Base para os modelos de classes
Base = declarative_base()

# Sessão para interagir com o banco de dados, é o equivalente à aquele seu trecho de código gerado pelo chatgpt que
# retorna uma sessão do banco de dados (Linha 6 do arquivo bot.py))
Session = sessionmaker(bind=engine)
session = Session()