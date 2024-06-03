import argparse
import shutil
import os
from alembic.config import Config
from alembic import command
from db import engine, Base
from db.models import *

def remove_migrations_folder():
    """Remove a pasta 'migrations' se existir."""
    if os.path.exists("migrations"):
        shutil.rmtree("migrations")
    print("Pasta 'migrations' removida.")

def init_alembic():
    """Inicializa o Alembic criando uma nova pasta 'migrations'."""
    os.system("alembic init migrations")
    print("Alembic inicializado e migrations criadas.")

def init_db():
    """Cria as tabelas do banco de dados baseadas nos modelos declarados."""
    Base.metadata.create_all(engine)
    print("Banco de dados inicializado com os modelos.")

def main():
    parser = argparse.ArgumentParser(description="Gerencia as migrações do banco de dados e setup inicial.")
    parser.add_argument("command", choices=['upgrade', 'downgrade', 'initdb', 'reset'],
                        help="Especifica o comando a ser executado. 'upgrade' para aplicar a migração mais recente ao banco de dados, "
                             "'downgrade' para reverter a última migração aplicada, 'initdb' para inicializar o banco de dados com "
                             "as tabelas dos modelos, e 'reset' para remover e reconfigurar o Alembic (caso você tenha errado feio nos models).")
    
    
    args = parser.parse_args()

    if args.command == 'upgrade':
        if not os.path.exists("migrations"):
            print("Pasta 'migrations' não encontrada. Execute o comando 'reset' para recriar o banco de dados.")
            return
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    elif args.command == 'downgrade':
        if not os.path.exists("migrations"):
            print("Pasta 'migrations' não encontrada. Execute o comando 'reset' para recriar o banco de dados.")
            return
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, "-1")
    elif args.command == 'initdb':
        init_db()
    elif args.command == 'reset':
        remove_migrations_folder()
        init_alembic()

if __name__ == "__main__":
    main()
