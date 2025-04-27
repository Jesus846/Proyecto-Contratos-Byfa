from contratos_flask_app import db, app

with app.app_context():
    db.create_all()
    print("Base de datos y tablas creadas correctamente.")
