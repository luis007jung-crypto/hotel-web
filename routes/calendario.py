from flask import Blueprint, render_template

from models import Habitacion, Reserva


calendario_bp = Blueprint(
    "calendario",
    __name__
)


@calendario_bp.route("/calendario")
def mostrar_calendario():
    habitaciones = Habitacion.query.order_by(
        Habitacion.numero
    ).all()

    reservas_activas = Reserva.query.filter_by(
        estado="Activa"
    ).all()

    reservas_por_habitacion = {
        reserva.habitacion_id: reserva
        for reserva in reservas_activas
    }

    return render_template(
        "calendario.html",
        habitaciones=habitaciones,
        reservas_por_habitacion=reservas_por_habitacion
    )