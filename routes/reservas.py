from datetime import date

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

    if request.method == "POST":
        huesped_id = request.form.get(
            "huesped_id",
            ""
        ).strip()

        habitacion_id = request.form.get(
            "habitacion_id",
            ""
        ).strip()

        if not huesped_id or not habitacion_id:
            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return render_template(
                "checkin.html",
                huespedes=huespedes,
                habitaciones=habitaciones_disponibles,
                fecha_actual=date.today().isoformat()
            )

        try:
            huesped_id = int(huesped_id)
            habitacion_id = int(habitacion_id)

            fecha_ingreso_convertida = date.today()

        except ValueError:
            flash(
                "Los datos del Check-In no son válidos.",
                "danger"
            )

            return render_template(
                "checkin.html",
                huespedes=huespedes,
                habitaciones=habitaciones_disponibles,
                fecha_actual=date.today().isoformat()
            )

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

        if habitacion.estado != "Disponible":
            flash(
                "La habitación ya no está disponible.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        reserva_activa = Reserva.query.filter_by(
            huesped_id=huesped.id,
            estado="Activa"
        ).first()

        if reserva_activa:
            flash(
                "El huésped ya tiene una reserva activa.",
                "danger"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        nueva_reserva = Reserva(
            fecha_ingreso=fecha_ingreso_convertida,
            fecha_salida=None,
            estado="Activa",
            total_pagado=0,
            huesped_id=huesped.id,
            habitacion_id=habitacion.id
        )

        habitacion.estado = "Ocupada"

        try:
            db.session.add(
                nueva_reserva
            )

            registrar_bitacora(
                accion="Check-In",
                descripcion=(
                    f"Se realizó Check-In para "
                    f"{huesped.nombre} en la habitación "
                    f"{habitacion.numero}, con fecha "
                    f"{fecha_ingreso_convertida.strftime('%d/%m/%Y')}."
                )
            )

            db.session.commit()

            flash(
                "Check-In realizado correctamente.",
                "success"
            )

            return redirect(
                url_for("reservas.checkin")
            )

        except Exception:
            db.session.rollback()

            flash(
                "No fue posible realizar el Check-In.",
                "danger"
            )

    return render_template(
        "checkin.html",
        huespedes=huespedes,
        habitaciones=habitaciones_disponibles,
        fecha_actual=date.today().isoformat()
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