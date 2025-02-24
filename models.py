from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum as PyEnum

Base = declarative_base()

class TipoUsuario(PyEnum):
    PACIENTE = "paciente"
    MEDICO = "medico"

class EstadoCita(PyEnum):
    PROGRAMADA = "programada"
    COMPLETADA = "completada"

class Usuario(Base, UserMixin):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String)
    tipo = Column(Enum(TipoUsuario), nullable=False)
    password_hash = Column(String, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Propiedades requeridas por Flask-Login
    @property
    def is_active(self):
        return True  # Siempre activo en este ejemplo

    @property
    def is_authenticated(self):
        return True  # Devuelve True si el usuario está autenticado

    @property
    def is_anonymous(self):
        return False  # Los usuarios no registrados son anónimos

    def get_id(self):
        return str(self.id)  # Flask-Login requiere que se devuelva un string

class Cita(Base):
    __tablename__ = "citas"
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("usuarios.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_hora = Column(DateTime, nullable=False)
    estado = Column(Enum(EstadoCita), nullable=True)
    motivo = Column(String, nullable=True)

    paciente = relationship("Usuario", foreign_keys=[paciente_id])
    medico = relationship("Usuario", foreign_keys=[medico_id], lazy="joined")  # Relación con lazy='joined'

class Medico(Base):
    __tablename__ = 'medicos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String)
    especialidad = Column(String)