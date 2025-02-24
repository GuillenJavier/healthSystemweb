from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, Usuario, Cita, TipoUsuario, EstadoCita

# Configuración de base de datos
engine = create_engine('sqlite:///health_system.db', echo=True)  # Define 'engine' antes de usarla
SessionLocal = scoped_session(sessionmaker(bind=engine))

# Crear tablas al inicio
Base.metadata.create_all(bind=engine)
