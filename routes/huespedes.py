from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models import db, Huesped, Bitacora


huespedes_bp = Blueprint(
    "huespedes",
    __name__
)


def registrar_bitacora(accion, descripcion):
    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=session.get("usuario_id")
    )

    db.session.add(registro)


@huespedes_bp.route("/huespedes")
def listar_huespedes():
    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    consulta = Huesped.query

    if busqueda:
        consulta = consulta.filter(
            db.or_(
                Huesped.nombre.ilike(
                    f"%{busqueda}%"
                ),
                Huesped.dpi.ilike(
                    f"%{busqueda}%"
                ),
                Huesped.telefono.ilike(
                    f"%{busqueda}%"
                )
            )
        )

    huespedes = consulta.order_by(
        Huesped.nombre
    ).all()

    return render_template(
        "huespedes.html",
        huespedes=huespedes,
        busqueda=busqueda
    )


@huespedes_bp.route(
    "/huespedes/agregar",
    methods=["GET", "POST"]
)
def agregar_huesped():
    if request.method == "POST":
        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        dpi = request.form.get(
            "dpi",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        if not nombre or not dpi or not telefono:
            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )

        if not dpi.isdigit() or len(dpi) != 13:
            flash(
                "El DPI debe contener exactamente 13 dígitos.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )

        if not telefono.isdigit() or len(telefono) != 8:
            flash(
                "El teléfono debe contener exactamente 8 dígitos.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )

        huesped_existente = Huesped.query.filter_by(
            dpi=dpi
        ).first()

        if huesped_existente:
            flash(
                "Ya existe un huésped registrado con ese DPI.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )

        nuevo_huesped = Huesped(
            nombre=nombre,
            dpi=dpi,
            telefono=telefono
        )

        try:
            db.session.add(nuevo_huesped)

            registrar_bitacora(
                accion="Crear huésped",
                descripcion=(
                    f"Se registró al huésped {nombre}, "
                    f"con DPI {dpi}."
                )
            )

            db.session.commit()

            flash(
                "Huésped registrado correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "huespedes.listar_huespedes"
                )
            )

        except Exception:
            db.session.rollback()

            flash(
                "No fue posible registrar al huésped.",
                "danger"
            )

    return render_template(
        "agregar_huesped.html"
    )


@huespedes_bp.route(
    "/huespedes/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_huesped(id):
    huesped = Huesped.query.get_or_404(id)

    if request.method == "POST":
        nombre_anterior = huesped.nombre
        dpi_anterior = huesped.dpi
        telefono_anterior = huesped.telefono

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        dpi = request.form.get(
            "dpi",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        if not nombre or not dpi or not telefono:
            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )

        if not dpi.isdigit() or len(dpi) != 13:
            flash(
                "El DPI debe contener exactamente 13 dígitos.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )

        if not telefono.isdigit() or len(telefono) != 8:
            flash(
                "El teléfono debe contener exactamente 8 dígitos.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )

        dpi_repetido = Huesped.query.filter(
            Huesped.dpi == dpi,
            Huesped.id != id
        ).first()

        if dpi_repetido:
            flash(
                "Ya existe otro huésped con ese DPI.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )

        huesped.nombre = nombre
        huesped.dpi = dpi
        huesped.telefono = telefono

        try:
            registrar_bitacora(
                accion="Editar huésped",
                descripcion=(
                    f"Se actualizó al huésped {nombre_anterior}. "
                    f"Nombre: {nombre_anterior} → {nombre}; "
                    f"DPI: {dpi_anterior} → {dpi}; "
                    f"teléfono: {telefono_anterior} → {telefono}."
                )
            )

            db.session.commit()

            flash(
                "Huésped actualizado correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "huespedes.listar_huespedes"
                )
            )

        except Exception:
            db.session.rollback()

            flash(
                "No fue posible actualizar al huésped.",
                "danger"
            )

    return render_template(
        "editar_huesped.html",
        huesped=huesped
    )


@huespedes_bp.route(
    "/huespedes/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar_huesped(id):
    huesped = Huesped.query.get_or_404(id)

    # Conservamos el historial: no se elimina un huésped
    # que tenga reservas activas o finalizadas.
    if huesped.reservas:
        flash(
            (
                "No se puede eliminar este huésped porque "
                "tiene reservas registradas."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "huespedes.listar_huespedes"
            )
        )

    nombre = huesped.nombre
    dpi = huesped.dpi

    try:
        db.session.delete(huesped)

        registrar_bitacora(
            accion="Eliminar huésped",
            descripcion=(
                f"Se eliminó al huésped {nombre}, "
                f"con DPI {dpi}."
            )
        )

        db.session.commit()

        flash(
            "Huésped eliminado correctamente.",
            "success"
        )

    except Exception:
        db.session.rollback()

        flash(
            "No fue posible eliminar al huésped.",
            "danger"
        )

    return redirect(
        url_for(
            "huespedes.listar_huespedes"
        )
    )