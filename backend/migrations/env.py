import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Import your models
try:
    from db.models import Base
    target_metadata = Base.metadata
    print("✅ Successfully imported models from db.models")
except ImportError as e:
    print(f"❌ Could not import models: {e}")
    print(f"Backend directory: {backend_dir}")
    print(f"Python path: {sys.path}")
    # List available files to debug
    db_path = os.path.join(backend_dir, 'db')
    if os.path.exists(db_path):
        print(f"Files in db/: {os.listdir(db_path)}")
    raise

# this is the Alembic Config object
config = context.config

# Set the database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
    print(f"✅ Using DATABASE_URL: {database_url[:50]}...")
else:
    raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file.")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Fix the configuration section issue
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()