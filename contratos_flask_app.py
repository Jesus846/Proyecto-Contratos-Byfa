from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contratos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    fecha_fin = db.Column(db.Date, nullable=True)  # Puede ser NULL si es indefinido

# Ruta para mostrar el formulario y guardar datos
@app.route('/', methods=['GET', 'POST'])
def index():
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
    return render_template('formulario.html')

# Ruta para mostrar contratos próximos a vencer en 15 días
@app.route('/proximos')
def proximos():
    hoy = datetime.today().date()
    limite = hoy + timedelta(days=15)
    contratos = Contratado.query.filter(
        Contratado.fecha_fin != None,
        Contratado.fecha_fin <= limite,
        Contratado.fecha_fin >= hoy
    ).all()
    return render_template('proximos.html', contratos=contratos)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

