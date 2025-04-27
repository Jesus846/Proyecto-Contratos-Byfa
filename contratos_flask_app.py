from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from datetime import date
import pandas as pd
from werkzeug.utils import secure_filename
import os
from flask import render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contratos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelo de datos
class Contratado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_registro = db.Column(db.Date, nullable=False)
    cedis = db.Column(db.String(100), nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    puesto = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=True)
    # Quitar la línea de personal_id

class Baja(db.Model):
    __tablename__ = 'bajas'
    id = db.Column(db.Integer, primary_key=True)
    contratado_id = db.Column(db.Integer, db.ForeignKey('contratado.id'), nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    fecha_baja = db.Column(db.Date, nullable=False)
    registrado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Aquí puedes agregar los campos del contratado que quieres guardar
    cedis = db.Column(db.String(100), nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    puesto = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=True)

    contratado = db.relationship('Contratado', backref=db.backref('bajas', lazy=True))




class Cedis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Relación entre Cedis y Personal
    personal = db.relationship('Personal', backref='cedis', lazy=True)

class Personal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cedis_id = db.Column(db.Integer, db.ForeignKey('cedis.id'), nullable=False)


# Ruta para mostrar el formulario y guardar datos
@app.route('/', methods=['GET', 'POST'])
def index():
    cedis_list = Cedis.query.all()
    if request.method == 'POST':
        contratado = Contratado(
            fecha_registro=datetime.strptime(request.form['fecha_registro'], '%Y-%m-%d'),
            cedis=request.form['cedis'],
            sexo=request.form['sexo'],
            nombre=request.form['nombre'],
            puesto=request.form['puesto'],
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d'),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d') if request.form['fecha_fin'] else None
        )
        db.session.add(contratado)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('formulario.html', cedis_list=cedis_list)

@app.route('/personal2')
def personal2():
    return render_template('personal.html')

@app.route('/cedis2')
def cedis2():
    return render_template('cedis.html')

@app.route('/historico')
def historico():
    cedis_nombre = request.args.get('cedis')
    cedis_list = Cedis.query.all()

    contratos = []
    if cedis_nombre:
        contratos = Contratado.query.filter_by(cedis=cedis_nombre).all()

    return render_template('historico.html', contratos=contratos, cedis_list=cedis_list, selected_cedis=cedis_nombre)

@app.route('/baja_personal', methods=['GET', 'POST'])
def baja_personal():
    cedis = Cedis.query.all()
    empleados = []

    if request.method == 'POST':
        cedis_id = request.form['cedis_id']
        cedis_seleccionado = Cedis.query.get(cedis_id)  # <--- Buscas el nombre
        if cedis_seleccionado:
            empleados = Contratado.query.filter_by(cedis=cedis_seleccionado.nombre).all()

    return render_template('baja_personal.html', cedis=cedis, empleados=empleados)

# Ruta para mostrar contratos próximos a vencer en 15 días
@app.route('/proximos')
def proximos():
    cedis_nombre = request.args.get('cedis')
    hoy = date.today()
    en_15_dias = hoy + timedelta(days=15)

    query = Contratado.query.filter(
        Contratado.fecha_fin != None,
        Contratado.fecha_fin >= hoy,
        Contratado.fecha_fin <= en_15_dias
    )

    if cedis_nombre:
        query = query.filter(Contratado.cedis == cedis_nombre)

    contratos = query.all()
    cedis_list = Cedis.query.all()

    return render_template(
        'proximos.html',
        contratos=contratos,
        cedis_list=cedis_list,
        selected_cedis=cedis_nombre
    )

@app.route('/cedis', methods=['GET', 'POST'])
def registrar_cedis():
    if request.method == 'POST':
        nuevo_cedis = request.form['nombre']
        if nuevo_cedis:
            cedis = Cedis(nombre=nuevo_cedis)
            db.session.add(cedis)
            db.session.commit()
            return redirect(url_for('registrar_cedis'))
    
    cedis_existentes = Cedis.query.all()
    return render_template('cedis.html', cedis=cedis_existentes)

@app.route('/personal', methods=['GET', 'POST'])
def registrar_personal():
    cedis_list = Cedis.query.all()
    selected_cedis_id = request.args.get('cedis_id')
    personal = []

    if request.method == 'POST':
        nombre = request.form['nombre']
        cedis_id = request.form['cedis_id']

        if nombre and cedis_id:
            persona = Personal(nombre=nombre, cedis_id=int(cedis_id))
            db.session.add(persona)
            db.session.commit()
            return redirect(url_for('registrar_personal', cedis_id=cedis_id))  # Redirige con filtro activo

    if selected_cedis_id:
        personal = Personal.query.filter_by(cedis_id=selected_cedis_id).all()

    return render_template('personal.html', personal=personal, cedis_list=cedis_list, selected_cedis_id=selected_cedis_id)

@app.route('/obtener_personal/<int:cedis_id>')
def obtener_personal(cedis_id):
    personal = Personal.query.filter_by(cedis_id=cedis_id).all()
    resultado = [{'id': p.id, 'nombre': p.nombre} for p in personal]
    return jsonify(resultado)

@app.route('/cargar_excel', methods=['GET', 'POST'])
def cargar_excel():
    cedis_list = Cedis.query.all()

    if request.method == 'POST':
        archivo = request.files['archivo']
        cedis_id = request.form['cedis_id']

        if archivo and archivo.filename.endswith('.xlsx') and cedis_id:
            filename = secure_filename(archivo.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            archivo.save(path)

            # Leer el archivo Excel
            df = pd.read_excel(path)

            # Leer nombres desde la columna A (asumimos sin encabezado)
            for index, row in df.iterrows():
                nombre = str(row[0])  # columna A
                if nombre and nombre.strip():
                    persona = Personal(nombre=nombre.strip(), cedis_id=int(cedis_id))
                    db.session.add(persona)
            db.session.commit()
            return redirect(url_for('registrar_personal'))

    return render_template('cargar_excel.html', cedis_list=cedis_list)

@app.route('/confirmar_baja/<int:empleado_id>', methods=['GET', 'POST'])
def confirmar_baja(empleado_id):
    # Obtener el empleado de la base de datos
    empleado = Contratado.query.get(empleado_id)
    
    if not empleado:
        return "Empleado no encontrado", 404

    if request.method == 'POST':
        motivo = request.form['motivo']
        fecha_baja = request.form['fecha_baja']
        fecha_baja = datetime.strptime(fecha_baja, '%Y-%m-%d')

        # Insertamos el registro de baja con todos los datos del contratado
        baja = Baja(
            contratado_id=empleado.id,
            motivo=motivo,
            fecha_baja=fecha_baja,
            cedis=empleado.cedis,  # Guardamos los datos del contratado
            sexo=empleado.sexo,
            nombre=empleado.nombre,
            puesto=empleado.puesto,
            fecha_inicio=empleado.fecha_inicio,
            fecha_fin=empleado.fecha_fin
        )
        db.session.add(baja)

        # Eliminar el registro de Contratado
        db.session.delete(empleado)

        # Eliminar también el registro de Personal (si existe)
        personal = Personal.query.filter_by(cedis_id=empleado.cedis).first()  # Usa el nombre de cedis en lugar de cedis_id
        if personal:
            db.session.delete(personal)

        # Guardamos los cambios
        db.session.commit()

        # Redirigir a la página de bajas
        return redirect(url_for('baja_personal'))  

    return render_template('confirmar_baja.html', empleado=empleado)

@app.route('/historico_bajas')
def historico_bajas():
    buscar = request.args.get('buscar', '')

    if buscar:
        bajas = Baja.query.filter(Baja.nombre.ilike(f'%{buscar}%')).all()
    else:
        bajas = Baja.query.all()

    return render_template('historicos_bajas.html', bajas=bajas)

@app.route('/editar_contrato/<int:contrato_id>', methods=['GET', 'POST'])
def editar_contrato(contrato_id):
    contrato = Contratado.query.get_or_404(contrato_id)
    cedis_list = Cedis.query.all()  # <--- Agregamos esta línea para traer todos los CEDIS

    if request.method == 'POST':
        contrato.nombre = request.form['nombre']
        contrato.puesto = request.form['puesto']
        contrato.fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')

        fecha_fin = request.form['fecha_fin']
        contrato.fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None

        contrato.cedis = request.form['cedis']  # <--- Agregamos que se pueda actualizar el CEDIS

        db.session.commit()
        return redirect(url_for('historico'))

    return render_template('editar_contrato.html', contrato=contrato, cedis_list=cedis_list)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
