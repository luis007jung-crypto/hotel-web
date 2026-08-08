from flask import (
    Flask,
    redirect,
    url_for,
    request,
    session
)

from config import Config
from models import (
    db,
    Habitacion,
    Usuario
)

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.habitaciones import habitaciones_bp
from routes.huespedes import huespedes_bp
from routes.reservas import reservas_bp
from routes.reportes import reportes_bp
from routes.calendario import calendario_bp
from routes.usuarios import usuarios_bp
from routes.bitacora import bitacora_bp

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(habitaciones_bp)
app.register_blueprint(huespedes_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(calendario_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(bitacora_bp)


@app.before_request
def proteger_sistema():
    rutas_publicas = {
        "auth.login",
        "static"
    }

    if request.endpoint is None:
        return None

    if request.endpoint in rutas_publicas:
        return None

    if "usuario_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    return None


def crear_habitaciones_iniciales():
    if Habitacion.query.count() > 0:
        return

    for numero in range(1, 6):
        db.session.add(
            Habitacion(
                numero=numero,
                tipo="Económica",
                precio=500,
                estado="Disponible"
            )
        )

    for numero in range(6, 9):
        db.session.add(
            Habitacion(
                numero=numero,
                tipo="Estándar",
                precio=1000,
                estado="Disponible"
            )
        )

    for numero in range(9, 11):
        db.session.add(
            Habitacion(
                numero=numero,
                tipo="Ejecutiva",
                precio=1500,
                estado="Disponible"
            )
        )

    db.session.commit()


def crear_usuarios_iniciales():
    administrador = Usuario.query.filter_by(
        usuario="admin"
    ).first()

    if administrador is None:
        administrador = Usuario(
            nombre="Administrador General",
            usuario="admin",
            rol="Administrador",
            activo=True
        )

        administrador.establecer_contrasena(
            "admin123"
        )

        db.session.add(
            administrador
        )

    recepcionista = Usuario.query.filter_by(
        usuario="recepcion"
    ).first()

    if recepcionista is None:
        recepcionista = Usuario(
            nombre="Recepcionista",
            usuario="recepcion",
            rol="Recepcionista",
            activo=True
        )

        recepcionista.establecer_contrasena(
            "recepcion123"
        )

        db.session.add(
            recepcionista
        )

    db.session.commit()


with app.app_context():
    db.create_all()
    crear_habitaciones_iniciales()
    crear_usuarios_iniciales()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )