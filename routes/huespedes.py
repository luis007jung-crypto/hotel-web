from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from difflib import SequenceMatcher

from models import db, Huesped, Bitacora


huespedes_bp = Blueprint(
    "huespedes",
    __name__
)


# =========================================================
# FUNCIÓN PARA REGISTRAR ACCIONES EN LA BITÁCORA
# =========================================================
def registrar_bitacora(accion, descripcion):
    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=session.get("usuario_id")
    )

    db.session.add(registro)


# =========================================================
# LISTAR HUÉSPEDES
# =========================================================
@huespedes_bp.route("/huespedes")
def listar_huespedes():

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    consulta = Huesped.query

    # Buscar por nombre, DPI o teléfono
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


# =========================================================
# AGREGAR HUÉSPED
# =========================================================
@huespedes_bp.route(
    "/huespedes/agregar",
    methods=["GET", "POST"]
)
def agregar_huesped():

    if request.method == "POST":

        # Obtener información del formulario
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


        # -------------------------------------------------
        # VALIDAR CAMPOS VACÍOS
        # -------------------------------------------------
        if not nombre or not dpi or not telefono:

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )


        # -------------------------------------------------
        # VALIDAR DPI
        # -------------------------------------------------
        if not dpi.isdigit() or len(dpi) != 13:

            flash(
                "El DPI debe contener exactamente 13 dígitos.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )


        # -------------------------------------------------
        # VALIDAR TELÉFONO
        # -------------------------------------------------
        if not telefono.isdigit() or len(telefono) != 8:

            flash(
                "El teléfono debe contener exactamente 8 dígitos.",
                "danger"
            )

            return render_template(
                "agregar_huesped.html"
            )


        # -------------------------------------------------
        # VERIFICAR DPI REPETIDO
        # -------------------------------------------------
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


        # -------------------------------------------------
        # VERIFICAR NOMBRES IGUALES O MUY SIMILARES
        # -------------------------------------------------
        huespedes_registrados = Huesped.query.all()

        for huesped in huespedes_registrados:

            similitud = SequenceMatcher(
                None,
                huesped.nombre.lower().strip(),
                nombre.lower().strip()
            ).ratio()

            # 0.90 significa 90 % de similitud
            if similitud >= 0.90:

                flash(
                    (
                        "Ya existe un huésped con un nombre "
                        f"igual o muy similar: {huesped.nombre}."
                    ),
                    "danger"
                )

                return render_template(
                    "agregar_huesped.html"
                )


        # -------------------------------------------------
        # CREAR NUEVO HUÉSPED
        # -------------------------------------------------
        nuevo_huesped = Huesped(
            nombre=nombre,
            dpi=dpi,
            telefono=telefono
        )

        try:

            db.session.add(
                nuevo_huesped
            )

            registrar_bitacora(
                accion="Agregar huésped",
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


# =========================================================
# EDITAR HUÉSPED
# =========================================================
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


        # -------------------------------------------------
        # VALIDAR CAMPOS VACÍOS
        # -------------------------------------------------
        if not nombre or not dpi or not telefono:

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )


        # -------------------------------------------------
        # VALIDAR DPI
        # -------------------------------------------------
        if not dpi.isdigit() or len(dpi) != 13:

            flash(
                "El DPI debe contener exactamente 13 dígitos.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )


        # -------------------------------------------------
        # VALIDAR TELÉFONO
        # -------------------------------------------------
        if not telefono.isdigit() or len(telefono) != 8:

            flash(
                "El teléfono debe contener exactamente 8 dígitos.",
                "danger"
            )

            return render_template(
                "editar_huesped.html",
                huesped=huesped
            )


        # -------------------------------------------------
        # VERIFICAR DPI REPETIDO
        # -------------------------------------------------
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


        # -------------------------------------------------
        # VERIFICAR NOMBRE IGUAL O MUY SIMILAR
        # -------------------------------------------------
        otros_huespedes = Huesped.query.filter(
            Huesped.id != id
        ).all()

        for otro_huesped in otros_huespedes:

            similitud = SequenceMatcher(
                None,
                otro_huesped.nombre.lower().strip(),
                nombre.lower().strip()
            ).ratio()

            if similitud >= 0.90:

                flash(
                    (
                        "Ya existe otro huésped con un nombre "
                        f"igual o muy similar: "
                        f"{otro_huesped.nombre}."
                    ),
                    "danger"
                )

                return render_template(
                    "editar_huesped.html",
                    huesped=huesped
                )


        # -------------------------------------------------
        # ACTUALIZAR INFORMACIÓN
        # -------------------------------------------------
        huesped.nombre = nombre
        huesped.dpi = dpi
        huesped.telefono = telefono

        try:

            registrar_bitacora(
                accion="Editar huésped",
                descripcion=(
                    f"Se actualizó al huésped "
                    f"{nombre_anterior}. "
                    f"Nombre: {nombre_anterior} → {nombre}; "
                    f"DPI: {dpi_anterior} → {dpi}; "
                    f"teléfono: "
                    f"{telefono_anterior} → {telefono}."
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


# =========================================================
# ELIMINAR HUÉSPED
# =========================================================
@huespedes_bp.route(
    "/huespedes/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar_huesped(id):

    huesped = Huesped.query.get_or_404(id)

    # No permitir eliminar huéspedes con reservas
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

        db.session.delete(
            huesped
        )

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