from datetime import date

from sqlalchemy import and_, or_

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
    Huesped,
    Reserva,
    Bitacora
)


reservas_bp = Blueprint(
    "reservas",
    __name__
)


def registrar_bitacora(accion, descripcion):
    registro = Bitacora(
        accion=accion,
        descripcion=descripcion,
        usuario_id=session.get("usuario_id")
    )

    db.session.add(registro)

@reservas_bp.route(
    "/checkin",
    methods=["GET", "POST"]
)
def checkin():

    huespedes = Huesped.query.order_by(
        Huesped.nombre
    ).all()

    habitaciones_disponibles = Habitacion.query.filter_by(
        estado="Disponible"
    ).order_by(
        Habitacion.numero
    ).all()

    reservas_pendientes = Reserva.query.filter(
        Reserva.estado == "Reservada"
    ).order_by(
        Reserva.fecha_ingreso
    ).all()

    if request.method == "POST":

        huesped_id = request.form.get(
            "huesped_id",
            ""
        ).strip()

        habitacion_id = request.form.get(
            "habitacion_id",
            ""
        ).strip()

        fecha_ingreso = request.form.get(
            "fecha_ingreso",
            ""
        ).strip()

        fecha_salida = request.form.get(
            "fecha_salida",
            ""
        ).strip()

        # ---------------------------------------------
        # VALIDAR CAMPOS
        # ---------------------------------------------

        if (
            not huesped_id
            or not habitacion_id
            or not fecha_ingreso
            or not fecha_salida
        ):

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
    "checkin.html",
    huespedes=huespedes,
    habitaciones=habitaciones_disponibles,
    reservas_pendientes=reservas_pendientes,
    fecha_actual=date.today().isoformat(),
    hoy=date.today()
)
    

        # ---------------------------------------------
        # CONVERTIR DATOS
        # ---------------------------------------------

        try:

            huesped_id = int(huesped_id)
            habitacion_id = int(habitacion_id)

            fecha_ingreso_convertida = date.fromisoformat(
                fecha_ingreso
            )

            fecha_salida_convertida = date.fromisoformat(
                fecha_salida
            )

        except ValueError:

            flash(
                "Las fechas o los datos seleccionados no son válidos.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # VALIDAR FECHAS
        # ---------------------------------------------

        if fecha_ingreso_convertida < date.today():

            flash(
                "La fecha de ingreso no puede ser anterior a hoy.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        if fecha_salida_convertida <= fecha_ingreso_convertida:

            flash(
                "La fecha de salida debe ser posterior a la fecha de ingreso.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # BUSCAR HUÉSPED Y HABITACIÓN
        # ---------------------------------------------

        huesped = db.session.get(
            Huesped,
            huesped_id
        )

        habitacion = db.session.get(
            Habitacion,
            habitacion_id
        )

        if huesped is None:

            flash(
                "El huésped seleccionado no existe.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        if habitacion is None:

            flash(
                "La habitación seleccionada no existe.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # VERIFICAR ESTADO DE HABITACIÓN
        # ---------------------------------------------

        if habitacion.estado != "Disponible":

            flash(
                "La habitación no está disponible.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # VERIFICAR SI EL HUÉSPED YA TIENE RESERVA
        # ---------------------------------------------

        reserva_huesped = Reserva.query.filter(
            Reserva.huesped_id == huesped.id,
            Reserva.estado.in_(["Activa", "Reservada"])
        ).first()

        if reserva_huesped:

            flash(
                "El huésped ya tiene una reserva activa o futura.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # VERIFICAR CRUCE DE RESERVAS
        # ---------------------------------------------

        reserva_existente = Reserva.query.filter(
            Reserva.habitacion_id == habitacion.id,
            Reserva.estado.in_(["Activa", "Reservada"]),
            or_(
                # Una habitación ocupada actualmente
                Reserva.estado == "Activa",

                # Una reservación futura que se cruza
                and_(
                    Reserva.fecha_ingreso < fecha_salida_convertida,
                    Reserva.fecha_salida.isnot(None),
                    Reserva.fecha_salida > fecha_ingreso_convertida
                )
            )
        ).first()

        if reserva_existente:

            flash(
                "La habitación ya está ocupada o reservada durante esas fechas.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        # ---------------------------------------------
        # DETERMINAR SI ES CHECK-IN O RESERVACIÓN
        # ---------------------------------------------

        if fecha_ingreso_convertida == date.today():

            # El cliente llega hoy
            estado_reserva = "Activa"

            habitacion.estado = "Ocupada"

            accion_bitacora = "Check-In"

            mensaje = "Check-In realizado correctamente."

        else:

            # El cliente llegará en el futuro
            estado_reserva = "Reservada"

            # La habitación todavía NO está ocupada
            habitacion.estado = "Disponible"

            accion_bitacora = "Reservación"

            mensaje = "Reservación futura creada correctamente."

        # ---------------------------------------------
        # CREAR RESERVA
        # ---------------------------------------------

        nueva_reserva = Reserva(
            fecha_ingreso=fecha_ingreso_convertida,
            fecha_salida=fecha_salida_convertida,
            estado=estado_reserva,
            total_pagado=0,
            huesped_id=huesped.id,
            habitacion_id=habitacion.id
        )

        try:

            db.session.add(
                nueva_reserva
            )

            registrar_bitacora(
                accion=accion_bitacora,
                descripcion=(
                    f"{accion_bitacora} para "
                    f"{huesped.nombre} en la habitación "
                    f"{habitacion.numero}. "
                    f"Ingreso: "
                    f"{fecha_ingreso_convertida.strftime('%d/%m/%Y')}. "
                    f"Salida: "
                    f"{fecha_salida_convertida.strftime('%d/%m/%Y')}."
                )
            )

            db.session.commit()

            flash(
                mensaje,
                "success"
            )

            return redirect(
                url_for("reservas.checkin")
            )
        
        except Exception:

            db.session.rollback()

            flash(
                "No fue posible guardar la reservación.",
                "danger"
            )

    return render_template(
        "checkin.html",
        huespedes=huespedes,
        habitaciones=habitaciones_disponibles,
        reservas_pendientes=reservas_pendientes,
        fecha_actual=date.today().isoformat(),
        hoy=date.today()
    )
@reservas_bp.route(
    "/checkin/reserva/<int:id>",
    methods=["POST"]
)
def realizar_checkin_reserva(id):

    reserva = Reserva.query.get_or_404(id)

    # Verificar que sea una reservación futura
    if reserva.estado != "Reservada":

        flash(
            "La reserva seleccionada no está pendiente de Check-In.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkin")
        )

    # Verificar que ya haya llegado la fecha
    if reserva.fecha_ingreso > date.today():

        flash(
            "Todavía no ha llegado la fecha de ingreso de esta reservación.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkin")
        )

    habitacion = reserva.habitacion

    # La habitación debe estar disponible
    if habitacion.estado != "Disponible":

        flash(
            "La habitación no está disponible para realizar el Check-In.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkin")
        )

    # Cambiar la reservación a activa
    reserva.estado = "Activa"

    # Ahora sí la habitación está ocupada
    habitacion.estado = "Ocupada"

    try:

        registrar_bitacora(
            accion="Check-In",
            descripcion=(
                f"Se realizó Check-In de la reservación "
                f"#{reserva.id} para "
                f"{reserva.huesped.nombre} "
                f"en la habitación "
                f"{habitacion.numero}."
            )
        )

        db.session.commit()

        flash(
            "Check-In realizado correctamente.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "No fue posible realizar el Check-In.",
            "danger"
        )

    return redirect(
        url_for("reservas.checkin")
    )

@reservas_bp.route("/checkout")
def checkout():
    reservas_activas = Reserva.query.filter_by(
        estado="Activa"
    ).order_by(
        Reserva.fecha_ingreso
    ).all()

    return render_template(
        "checkout.html",
        reservas=reservas_activas,
        fecha_actual=date.today().isoformat()
    )


@reservas_bp.route(
    "/checkout/<int:id>",
    methods=["POST"]
)
def realizar_checkout(id):
    reserva = Reserva.query.get_or_404(id)

    if reserva.estado != "Activa":
        flash(
            "La reserva seleccionada ya está finalizada.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkout")
        )

    fecha_salida_convertida = date.today()

    if fecha_salida_convertida < reserva.fecha_ingreso:
        flash(
            "La fecha de salida no puede ser anterior a la fecha de ingreso.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkout")
        )

    diferencia_dias = (
        fecha_salida_convertida
        - reserva.fecha_ingreso
    ).days

    noches = max(
        1,
        diferencia_dias
    )

    precio_noche = reserva.habitacion.precio
    total = noches * precio_noche

    nombre_huesped = reserva.huesped.nombre
    numero_habitacion = reserva.habitacion.numero

    reserva.fecha_salida = fecha_salida_convertida
    reserva.estado = "Finalizada"
    reserva.total_pagado = total
    reserva.habitacion.estado = "Disponible"

    try:
        registrar_bitacora(
            accion="Check-Out",
            descripcion=(
                f"Se realizó Check-Out para "
                f"{nombre_huesped} de la habitación "
                f"{numero_habitacion}. "
                f"Noches: {noches}. "
                f"Total pagado: Q{total:.2f}."
            )
        )

        db.session.commit()

        flash(
            "Check-Out realizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "reservas.factura",
                id=reserva.id
            )
        )

    except Exception:
        db.session.rollback()

        flash(
            "No fue posible realizar el Check-Out.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkout")
        )


@reservas_bp.route("/factura/<int:id>")
def factura(id):
    reserva = Reserva.query.get_or_404(id)

    if reserva.fecha_salida is None:
        flash(
            "La reserva aún no tiene una fecha de salida.",
            "danger"
        )

        return redirect(
            url_for("reservas.checkout")
        )

    diferencia_dias = (
        reserva.fecha_salida
        - reserva.fecha_ingreso
    ).days

    noches = max(
        1,
        diferencia_dias
    )

    precio_noche = reserva.habitacion.precio

    total = (
        reserva.total_pagado
        if reserva.total_pagado > 0
        else noches * precio_noche
    )

    return render_template(
        "factura.html",
        reserva=reserva,
        noches=noches,
        precio_noche=precio_noche,
        total=total
    )