from functools import wraps

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


usuarios_bp = Blueprint(
    "usuarios",
    __name__
)


def solo_administrador(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if session.get("rol") != "Administrador":
            flash(
                "No tienes permiso para acceder a esta sección.",
                "danger"
            )

            return redirect(
                url_for("dashboard.inicio")
            )

        return funcion(*args, **kwargs)

    return funcion_protegida


def registrar_bitacora(
    accion,
    descripcion
):
    usuario_id = session.get("usuario_id")

    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=usuario_id
    )

    db.session.add(registro)
    db.session.commit()


@usuarios_bp.route("/usuarios")
@solo_administrador
def listar_usuarios():
    usuarios = Usuario.query.order_by(
        Usuario.nombre
    ).all()

    return render_template(
        "usuarios.html",
        usuarios=usuarios
    )


@usuarios_bp.route(
    "/usuarios/agregar",
    methods=["GET", "POST"]
)
@solo_administrador
def agregar_usuario():
    if request.method == "POST":
        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        nombre_usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        contrasena = request.form.get(
            "contrasena",
            ""
        )

        rol = request.form.get(
            "rol",
            ""
        ).strip()

        activo = request.form.get(
            "activo"
        ) == "1"

        if (
            not nombre
            or not nombre_usuario
            or not contrasena
            or not rol
        ):
            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "agregar_usuario.html"
            )

        if len(contrasena) < 6:
            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "danger"
            )

            return render_template(
                "agregar_usuario.html"
            )

        roles_validos = [
            "Administrador",
            "Recepcionista"
        ]

        if rol not in roles_validos:
            flash(
                "El rol seleccionado no es válido.",
                "danger"
            )

            return render_template(
                "agregar_usuario.html"
            )

        usuario_existente = Usuario.query.filter_by(
            usuario=nombre_usuario
        ).first()

        if usuario_existente:
            flash(
                "Ya existe un usuario con ese nombre de acceso.",
                "danger"
            )

            return render_template(
                "agregar_usuario.html"
            )

        nuevo_usuario = Usuario(
            nombre=nombre,
            usuario=nombre_usuario,
            rol=rol,
            activo=activo
        )

        nuevo_usuario.establecer_contrasena(
            contrasena
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        registrar_bitacora(
            accion="Crear usuario",
            descripcion=(
                f"Se creó el usuario {nombre_usuario} "
                f"con rol {rol}."
            )
        )

        flash(
            "Usuario registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("usuarios.listar_usuarios")
        )

    return render_template(
        "agregar_usuario.html"
    )


@usuarios_bp.route(
    "/usuarios/editar/<int:id>",
    methods=["GET", "POST"]
)
@solo_administrador
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        nombre_usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        nueva_contrasena = request.form.get(
            "contrasena",
            ""
        )

        rol = request.form.get(
            "rol",
            ""
        ).strip()

        activo = request.form.get(
            "activo"
        ) == "1"

        if not nombre or not nombre_usuario or not rol:
            flash(
                "Nombre, usuario y rol son obligatorios.",
                "danger"
            )

            return render_template(
                "editar_usuario.html",
                usuario=usuario
            )

        roles_validos = [
            "Administrador",
            "Recepcionista"
        ]

        if rol not in roles_validos:
            flash(
                "El rol seleccionado no es válido.",
                "danger"
            )

            return render_template(
                "editar_usuario.html",
                usuario=usuario
            )

        usuario_repetido = Usuario.query.filter(
            Usuario.usuario == nombre_usuario,
            Usuario.id != id
        ).first()

        if usuario_repetido:
            flash(
                "Ya existe otro usuario con ese nombre de acceso.",
                "danger"
            )

            return render_template(
                "editar_usuario.html",
                usuario=usuario
            )

        if nueva_contrasena and len(nueva_contrasena) < 6:
            flash(
                "La nueva contraseña debe tener al menos 6 caracteres.",
                "danger"
            )

            return render_template(
                "editar_usuario.html",
                usuario=usuario
            )

        if usuario.id == session.get("usuario_id") and not activo:
            flash(
                "No puedes desactivar tu propia cuenta.",
                "danger"
            )

            return render_template(
                "editar_usuario.html",
                usuario=usuario
            )

        usuario.nombre = nombre
        usuario.usuario = nombre_usuario
        usuario.rol = rol
        usuario.activo = activo

        if nueva_contrasena:
            usuario.establecer_contrasena(
                nueva_contrasena
            )

        db.session.commit()

        registrar_bitacora(
            accion="Editar usuario",
            descripcion=(
                f"Se actualizó el usuario "
                f"{nombre_usuario}."
            )
        )

        flash(
            "Usuario actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("usuarios.listar_usuarios")
        )

    return render_template(
        "editar_usuario.html",
        usuario=usuario
    )


@usuarios_bp.route(
    "/usuarios/eliminar/<int:id>",
    methods=["POST"]
)
@solo_administrador
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if usuario.id == session.get("usuario_id"):
        flash(
            "No puedes eliminar tu propia cuenta.",
            "danger"
        )

        return redirect(
            url_for("usuarios.listar_usuarios")
        )

    nombre_usuario = usuario.usuario

    if usuario.bitacoras:
        usuario.activo = False
        db.session.commit()

        registrar_bitacora(
            accion="Desactivar usuario",
            descripcion=(
                f"Se desactivó el usuario "
                f"{nombre_usuario} porque tiene registros "
                "en la bitácora."
            )
        )

        flash(
            "El usuario tiene historial y fue desactivado.",
            "warning"
        )

        return redirect(
            url_for("usuarios.listar_usuarios")
        )

    db.session.delete(usuario)
    db.session.commit()

    registrar_bitacora(
        accion="Eliminar usuario",
        descripcion=(
            f"Se eliminó el usuario "
            f"{nombre_usuario}."
        )
    )

    flash(
        "Usuario eliminado correctamente.",
        "success"
    )

    return redirect(
        url_for("usuarios.listar_usuarios")
    )