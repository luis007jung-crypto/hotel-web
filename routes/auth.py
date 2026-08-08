from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models import db, Usuario, Bitacora


auth_bp = Blueprint(
    "auth",
    __name__
)


def registrar_bitacora(
    accion,
    descripcion,
    usuario_id=None
):
    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=usuario_id
    )

    db.session.add(registro)
    db.session.commit()


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if "usuario_id" in session:
        return redirect(
            url_for("dashboard.inicio")
        )

    if request.method == "POST":
        nombre_usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        contrasena = request.form.get(
            "contrasena",
            ""
        )

        usuario = Usuario.query.filter_by(
            usuario=nombre_usuario
        ).first()

        if usuario is None:
            flash(
                "Usuario o contraseña incorrectos.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if not usuario.activo:
            flash(
                "Este usuario está desactivado.",
                "warning"
            )

            return render_template(
                "login.html"
            )

        if not usuario.verificar_contrasena(
            contrasena
        ):
            flash(
                "Usuario o contraseña incorrectos.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        session.clear()

        session["usuario_id"] = usuario.id
        session["usuario"] = usuario.usuario
        session["nombre_usuario"] = usuario.nombre
        session["rol"] = usuario.rol

        registrar_bitacora(
            accion="Inicio de sesión",
            descripcion=(
                f"El usuario {usuario.usuario} "
                "inició sesión."
            ),
            usuario_id=usuario.id
        )

        flash(
            "Inicio de sesión correcto.",
            "success"
        )

        return redirect(
            url_for("dashboard.inicio")
        )

    return render_template(
        "login.html"
    )


@auth_bp.route("/logout")
def logout():
    usuario_id = session.get(
        "usuario_id"
    )

    nombre_usuario = session.get(
        "usuario",
        "Desconocido"
    )

    if usuario_id is not None:
        registrar_bitacora(
            accion="Cierre de sesión",
            descripcion=(
                f"El usuario {nombre_usuario} "
                "cerró sesión."
            ),
            usuario_id=usuario_id
        )

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )