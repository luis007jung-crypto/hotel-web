from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models import (
    db,
    Habitacion,
    Reserva,
    Bitacora
)


habitaciones_bp = Blueprint(
    "habitaciones",
    __name__
)


# =========================================================
# BITÁCORA
# =========================================================
def registrar_bitacora(accion, descripcion):
    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=session.get("usuario_id")
    )

    db.session.add(registro)


# =========================================================
# LISTAR HABITACIONES
# =========================================================
@habitaciones_bp.route("/habitaciones")
def listar_habitaciones():

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    tipo = request.args.get(
        "tipo",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        ""
    ).strip()

    consulta = Habitacion.query

    # -----------------------------------------------------
    # BÚSQUEDA
    # -----------------------------------------------------
    if busqueda:

        try:
            numero = int(busqueda)

            consulta = consulta.filter(
                Habitacion.numero == numero
            )

        except ValueError:

            consulta = consulta.filter(
                Habitacion.tipo.ilike(
                    f"%{busqueda}%"
                )
            )

    # -----------------------------------------------------
    # FILTRO POR TIPO
    # -----------------------------------------------------
    if tipo:

        consulta = consulta.filter(
            Habitacion.tipo == tipo
        )

    # -----------------------------------------------------
    # FILTRO POR ESTADO
    # -----------------------------------------------------
    if estado:

        consulta = consulta.filter(
            Habitacion.estado == estado
        )

    # -----------------------------------------------------
    # OBTENER HABITACIONES
    # -----------------------------------------------------
    habitaciones = consulta.order_by(
        Habitacion.numero
    ).all()

    # -----------------------------------------------------
    # OBTENER RESERVACIONES FUTURAS
    # -----------------------------------------------------
    reservas_futuras = Reserva.query.filter(
        Reserva.estado == "Reservada"
    ).order_by(
        Reserva.fecha_ingreso
    ).all()

    # Diccionario:
    #
    # {
    #     habitacion_id: [reserva1, reserva2, ...]
    # }
    #
    reservas_por_habitacion = {}

    for reserva in reservas_futuras:

        if reserva.habitacion_id not in reservas_por_habitacion:
            reservas_por_habitacion[
                reserva.habitacion_id
            ] = []

        reservas_por_habitacion[
            reserva.habitacion_id
        ].append(
            reserva
        )

    return render_template(
        "habitaciones.html",
        habitaciones=habitaciones,
        busqueda=busqueda,
        tipo_seleccionado=tipo,
        estado_seleccionado=estado,
        reservas_por_habitacion=reservas_por_habitacion
    )


# =========================================================
# AGREGAR HABITACIÓN
# =========================================================
@habitaciones_bp.route(
    "/habitaciones/agregar",
    methods=["GET", "POST"]
)
def agregar_habitacion():

    if request.method == "POST":

        numero = request.form.get(
            "numero",
            ""
        ).strip()

        tipo = request.form.get(
            "tipo",
            ""
        ).strip()

        estado = request.form.get(
            "estado",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDAR CAMPOS
        # -------------------------------------------------
        if not numero or not tipo or not estado:

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        # -------------------------------------------------
        # VALIDAR NÚMERO
        # -------------------------------------------------
        try:

            numero = int(numero)

        except ValueError:

            flash(
                "El número de habitación no es válido.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        if numero <= 0:

            flash(
                "El número debe ser mayor que cero.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        # -------------------------------------------------
        # VERIFICAR HABITACIÓN REPETIDA
        # -------------------------------------------------
        habitacion_existente = Habitacion.query.filter_by(
            numero=numero
        ).first()

        if habitacion_existente:

            flash(
                "Ya existe una habitación con ese número.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        # -------------------------------------------------
        # PRECIOS
        # -------------------------------------------------
        precios = {
            "Económica": 500,
            "Estándar": 1000,
            "Ejecutiva": 1500
        }

        estados_validos = [
            "Disponible",
            "Ocupada",
            "Mantenimiento"
        ]

        # -------------------------------------------------
        # VALIDAR TIPO
        # -------------------------------------------------
        if tipo not in precios:

            flash(
                "El tipo de habitación no es válido.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        # -------------------------------------------------
        # VALIDAR ESTADO
        # -------------------------------------------------
        if estado not in estados_validos:

            flash(
                "El estado seleccionado no es válido.",
                "danger"
            )

            return render_template(
                "agregar_habitacion.html"
            )

        # -------------------------------------------------
        # CREAR HABITACIÓN
        # -------------------------------------------------
        nueva_habitacion = Habitacion(
            numero=numero,
            tipo=tipo,
            precio=precios[tipo],
            estado=estado
        )

        try:

            db.session.add(
                nueva_habitacion
            )

            registrar_bitacora(
                accion="Crear habitación",
                descripcion=(
                    f"Se creó la habitación {numero}, "
                    f"tipo {tipo}, "
                    f"con estado {estado}."
                )
            )

            db.session.commit()

            flash(
                "Habitación registrada correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "habitaciones.listar_habitaciones"
                )
            )

        except Exception:

            db.session.rollback()

            flash(
                "No fue posible registrar la habitación.",
                "danger"
            )

    return render_template(
        "agregar_habitacion.html"
    )


# =========================================================
# EDITAR HABITACIÓN
# =========================================================
@habitaciones_bp.route(
    "/habitaciones/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_habitacion(id):

    habitacion = Habitacion.query.get_or_404(
        id
    )

    if request.method == "POST":

        numero_anterior = habitacion.numero
        tipo_anterior = habitacion.tipo
        estado_anterior = habitacion.estado

        numero = request.form.get(
            "numero",
            ""
        ).strip()

        tipo = request.form.get(
            "tipo",
            ""
        ).strip()

        estado = request.form.get(
            "estado",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDAR CAMPOS
        # -------------------------------------------------
        if not numero or not tipo or not estado:

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        # -------------------------------------------------
        # VALIDAR NÚMERO
        # -------------------------------------------------
        try:

            numero = int(numero)

        except ValueError:

            flash(
                "El número de habitación no es válido.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        if numero <= 0:

            flash(
                "El número debe ser mayor que cero.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        # -------------------------------------------------
        # VERIFICAR NÚMERO REPETIDO
        # -------------------------------------------------
        habitacion_repetida = Habitacion.query.filter(
            Habitacion.numero == numero,
            Habitacion.id != id
        ).first()

        if habitacion_repetida:

            flash(
                "Ya existe otra habitación con ese número.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        # -------------------------------------------------
        # PRECIOS
        # -------------------------------------------------
        precios = {
            "Económica": 500,
            "Estándar": 1000,
            "Ejecutiva": 1500
        }

        estados_validos = [
            "Disponible",
            "Ocupada",
            "Mantenimiento"
        ]

        # -------------------------------------------------
        # VALIDAR TIPO
        # -------------------------------------------------
        if tipo not in precios:

            flash(
                "El tipo de habitación no es válido.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        # -------------------------------------------------
        # VALIDAR ESTADO
        # -------------------------------------------------
        if estado not in estados_validos:

            flash(
                "El estado seleccionado no es válido.",
                "danger"
            )

            return render_template(
                "editar_habitacion.html",
                habitacion=habitacion
            )

        # -------------------------------------------------
        # ACTUALIZAR HABITACIÓN
        # -------------------------------------------------
        habitacion.numero = numero
        habitacion.tipo = tipo
        habitacion.precio = precios[tipo]
        habitacion.estado = estado

        try:

            registrar_bitacora(
                accion="Editar habitación",
                descripcion=(
                    f"Se actualizó la habitación "
                    f"{numero_anterior}. "
                    f"Número: "
                    f"{numero_anterior} → {numero}; "
                    f"tipo: "
                    f"{tipo_anterior} → {tipo}; "
                    f"estado: "
                    f"{estado_anterior} → {estado}."
                )
            )

            db.session.commit()

            flash(
                "Habitación actualizada correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "habitaciones.listar_habitaciones"
                )
            )

        except Exception:

            db.session.rollback()

            flash(
                "No fue posible actualizar la habitación.",
                "danger"
            )

    return render_template(
        "editar_habitacion.html",
        habitacion=habitacion
    )


# =========================================================
# ELIMINAR HABITACIÓN
# =========================================================
@habitaciones_bp.route(
    "/habitaciones/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar_habitacion(id):

    habitacion = Habitacion.query.get_or_404(
        id
    )

    # -----------------------------------------------------
    # NO ELIMINAR SI TIENE RESERVAS
    # -----------------------------------------------------
    if habitacion.reservas:

        flash(
            (
                "No se puede eliminar esta habitación porque "
                "tiene reservas registradas. "
                "Puedes cambiar su estado a Mantenimiento."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "habitaciones.listar_habitaciones"
            )
        )

    numero = habitacion.numero
    tipo = habitacion.tipo

    try:

        db.session.delete(
            habitacion
        )

        registrar_bitacora(
            accion="Eliminar habitación",
            descripcion=(
                f"Se eliminó la habitación {numero}, "
                f"tipo {tipo}."
            )
        )

        db.session.commit()

        flash(
            "Habitación eliminada correctamente.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "No fue posible eliminar la habitación.",
            "danger"
        )

    return redirect(
        url_for(
            "habitaciones.listar_habitaciones"
        )
    )