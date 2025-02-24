from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from models import Base, Usuario, Cita, TipoUsuario, EstadoCita,Medico
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

# Configuración de la aplicación
app = Flask(__name__)

# Definición de la función get_doctor_info
def get_doctor_info(doctor_id):
    session = SessionLocal()
    try:
        doctor = session.query(Medico).filter(Medico.id == doctor_id).first()  # Obtiene la información del médico por ID
        return doctor
    finally:
        session.close()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Cambia esto a tu URI de base de datos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.secret_key = os.urandom(24)

# Configuración de base de datos
engine = create_engine('sqlite:///health_system.db', echo=True)  # Define 'engine' antes de usarlo
SessionLocal = scoped_session(sessionmaker(bind=engine))

# Crear tablas al inicio
Base.metadata.create_all(bind=engine)  # 'engine' está definido aquí

# Configuración de Login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(Usuario).get(int(user_id))
    db.close()
    return user

# Datos precargados: médicos por defecto
def seed_data():
    db = SessionLocal()
    if not db.query(Usuario).filter_by(tipo=TipoUsuario.MEDICO).first():
        medicos = [
            Usuario(nombre="Dr. Carlos", apellido="Pérez", email="carlos@medico.com", tipo=TipoUsuario.MEDICO, telefono="1234567890"),
            Usuario(nombre="Dra. María", apellido="López", email="maria@medico.com", tipo=TipoUsuario.MEDICO, telefono="0987654321")
        ]
        for medico in medicos:
            medico.set_password("password")
            db.add(medico)
        db.commit()
    db.close()

# Inicializar datos precargados
seed_data()

# Rutas de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        db = SessionLocal()
        try:
            # Verificar si el email ya está registrado
            email_existente = db.query(Usuario).filter_by(email=request.form['email']).first()
            if email_existente:
                flash('El correo electrónico ya está registrado. Intenta con otro.', 'danger')
                return render_template('registro.html')

            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                email=request.form['email'],
                tipo=TipoUsuario[request.form['tipo'].upper()],
                telefono=request.form['telefono']
            )
            nuevo_usuario.set_password(request.form['password'])
            
            db.add(nuevo_usuario)
            db.commit()
            flash('Registro exitoso', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash(f'Error en el registro: {str(e)}', 'danger')
        finally:
            db.close()
    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = SessionLocal()
        usuario = db.query(Usuario).filter_by(email=request.form['email']).first()

        if usuario and usuario.check_password(request.form['password']):
            login_user(usuario)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard_user' if usuario.tipo == TipoUsuario.PACIENTE else 'dashboard_doctor'))
        else:
            flash('Credenciales inválidas', 'danger')

        db.close()
    return render_template('login.html')


@app.route('/perfil_usuario')
@login_required
def dashboard_user():
    db = SessionLocal()
    citas = db.query(Cita).filter(Cita.paciente_id == current_user.id).all()
    db.close()
    return render_template('profile.html', citas=citas)

@app.route('/dashboard_doctor', methods=['GET'])
@login_required
def dashboard_doctor():
    # Supongamos que tienes un objeto doctor
    doctor = current_user  # O la forma en que obtienes el médico actual
    citas_pendientes = []  # Aquí deberías obtener las citas pendientes
    citas_finalizadas = []  # Aquí deberías obtener las citas finalizadas

    return render_template('doctor_dashboard.html', doctor=doctor, citas_pendientes=citas_pendientes, citas_finalizadas=citas_finalizadas)

@app.route('/doctor_profile/<int:doctor_id>', methods=['GET'])
@login_required
def doctor_profile(doctor_id):
    doctor_info = get_doctor_info(doctor_id)  # Llama a la función pasando el doctor_id
    if doctor is None:
        flash("Médico no encontrado.", "error")
        return redirect(url_for('some_error_page'))  # Ahora esto funcionará  # Redirige a la página de inicio o a otra página adecuada
        pass
    
    return render_template('doctor_profile.html', doctor=doctor_info)




@app.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
def agendar_cita():
    db = SessionLocal()
    if request.method == 'POST':
        try:
            tipo_cita = request.form['tipo_cita']
            medico_id = int(request.form['medico_id'])
            fecha_hora = datetime.strptime(request.form['fecha'], '%Y-%m-%dT%H:%M')
            nueva_cita = Cita(
                paciente_id=current_user.id,
                medico_id=medico_id,
                fecha_hora=fecha_hora,
                estado=EstadoCita.PROGRAMADA,
                motivo=tipo_cita
            )
            db.add(nueva_cita)
            db.commit()
            flash('Cita agendada exitosamente', 'success')
            return redirect(url_for('dashboard_user'))
        except Exception as e:
            db.rollback()
            flash(f'Error al agendar cita: {str(e)}', 'danger')
        finally:
            db.close()

    medicos = db.query(Usuario).filter_by(tipo=TipoUsuario.MEDICO).all()
    db.close()
    return render_template('agendar_cita.html', medicos=medicos)

@app.route('/citas_paciente')
@login_required
def my_appointments():
    db = SessionLocal()
    citas = db.query(Cita).options(joinedload(Cita.medico)).filter(Cita.paciente_id == current_user.id).all()
    db.close()
    return render_template('citas_paciente.html', citas=citas)

@app.route('/cancelar_cita', methods=['GET', 'POST'])
@login_required
def cancelar_cita():
    db = SessionLocal()
    try:
        citas = (
            db.query(Cita)
            .options(joinedload(Cita.medico))
            .filter(Cita.paciente_id == current_user.id)
            .all()
        )

        if request.method == 'POST':
            cita_id = request.form['cita_id']
            cita = db.query(Cita).filter_by(id=cita_id, paciente_id=current_user.id).first()
            if cita:
                db.delete(cita)
                db.commit()
                flash('Cita cancelada exitosamente', 'success')
            else:
                flash('Cita no encontrada o no autorizada', 'danger')

            # Redirige al perfil correspondiente
            if current_user.tipo == 'PACIENTE':
                return redirect(url_for('user_profile'))  # Perfil del paciente
            else:
                return redirect(url_for('doctor_profile'))  # Perfil del doctor
    finally:
        db.close()

    return render_template('cancelar_cita.html', citas=citas)

@app.route('/modify_appointment', methods=['GET', 'POST'])
@login_required
def modify_appointment():
     # Crear una nueva sesión
    session = SessionLocal()
    
    try:
        # Realiza la consulta a la base de datos
        citas = session.query(Cita).filter(Cita.paciente_id == current_user.id).all()
        
        # Resto de tu lógica para modificar citas...
        
        return render_template('modify_appointment.html', citas=citas)
    finally:
        # Cerrar la sesión
        session.close()
    if request.method == 'POST':
        # Lógica para modificar la cita
        cita_id = request.form.get('cita_id')
        nueva_fecha = request.form.get('nueva_fecha')
        # Aquí deberías buscar la cita en la base de datos y actualizar su fecha

        flash('Cita modificada con éxito', 'success')
        return redirect(url_for('my_appointments'))
    
    # Obtener las citas del usuario para mostrarlas en el formulario
    citas = db.query(Cita).filter(Cita.paciente_id == current_user.id).all()
    return render_template('modificar_cita.html', citas=citas)

@app.route('/doctor_profile/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def doctor_profile_edit(doctor_id):
    session = SessionLocal()
    doctor = session.query(Medico).filter(Medico.id == doctor_id).first()

    if doctor is None:
        flash("Médico no encontrado.", "error")
        return redirect(url_for('some_error_page'))  # Redirige a una página de error

    if request.method == 'POST':
        doctor.nombre = request.form['nombre']
        doctor.especialidad = request.form['especialidad']
        doctor.email = request.form['email']  # Asegúrate de que el modelo tenga este campo
        session.commit()
        flash("Perfil actualizado exitosamente.")
        return redirect(url_for('doctor_profile', doctor_id=doctor.id))

    return render_template('doctor_profile.html', doctor=doctor)

@app.route('/dashboard/doctor/citas')
@login_required
def doctor_citas():
    session = SessionLocal()
    # Verifica el ID del usuario actual
    print(f"Current User ID: {current_user.id}")  # Agrega esta línea para depuración

    # Obtén el médico actual
    doctor = session.query(Medico).filter(Medico.id == current_user.id).first()

    if doctor is None:
        flash("Lo sentimos, no se pudo encontrar el médico solicitado.", "error")
        return redirect(url_for('some_error_page'))

    # Obtén las citas del médico
    citas = session.query(Cita).filter(Cita.medico_id == doctor.id).all()

    return render_template('doctor_citas.html', doctor=doctor, citas=citas)

@app.route('/error')
def some_error_page():
    return render_template('error.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
