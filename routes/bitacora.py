from datetime import datetime
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

from models import Bitacora, Usuario


bitacora_bp = Blueprint(
    "bitacora",
    __name__
)


def solo_administrador(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if session.get("rol") != "Administrador":
            flash(
                "No tienes permiso para acceder a la bitácora.",
                "danger"
            )

            return redirect(
                url_for("dashboard.inicio")
            )

        return funcion(*args, **kwargs)

    return funcion_protegida


@bitacora_bp.route("/bitacora")
@solo_administrador
def listar_bitacora():
    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    usuario_id = request.args.get(
        "usuario_id",
        ""
    ).strip()

    fecha = request.args.get(
        "fecha",
        ""
    ).strip()

    consulta = Bitacora.query.outerjoin(
        Usuario,
        Bitacora.usuario_id == Usuario.id
    )

    if busqueda:
        consulta = consulta.filter(
            (
                Bitacora.accion.ilike(
                    f"%{busqueda}%"
                )
            )
            |
            (
                Bitacora.descripcion.ilike(
                    f"%{busqueda}%"
                )
            )
            |
            (
                Usuario.usuario.ilike(
                    f"%{busqueda}%"
                )
            )
            |
            (
                Usuario.nombre.ilike(
                    f"%{busqueda}%"
                )
            )
        )

    if usuario_id:
        try:
            usuario_id_convertido = int(
                usuario_id
            )

            consulta = consulta.filter(
                Bitacora.usuario_id
                == usuario_id_convertido
            )

        except ValueError:
            flash(
                "El usuario seleccionado no es válido.",
                "warning"
            )

    if fecha:
        try:
            fecha_convertida = datetime.strptime(
                fecha,
                "%Y-%m-%d"
            ).date()

            consulta = consulta.filter(
                Bitacora.fecha_hora
                >= datetime.combine(
                    fecha_convertida,
                    datetime.min.time()
                ),
                Bitacora.fecha_hora
                <= datetime.combine(
                    fecha_convertida,
                    datetime.max.time()
                )
            )

        except ValueError:
            flash(
                "La fecha seleccionada no es válida.",
                "warning"
            )

    registros = consulta.order_by(
        Bitacora.fecha_hora.desc()
    ).all()

    usuarios = Usuario.query.order_by(
        Usuario.nombre
    ).all()

    return render_template(
        "bitacora.html",
        registros=registros,
        usuarios=usuarios,
        busqueda=busqueda,
        usuario_seleccionado=usuario_id,
        fecha_seleccionada=fecha
    )