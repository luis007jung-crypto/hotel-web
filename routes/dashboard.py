from datetime import datetime

from flask import Blueprint, render_template

from models import Habitacion, Huesped, Reserva


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/")
def inicio():
    # ==========================================
    # ESTADÍSTICAS GENERALES
    # ==========================================

    total = Habitacion.query.count()

    disponibles = Habitacion.query.filter_by(
        estado="Disponible"
    ).count()

    ocupadas = Habitacion.query.filter_by(
        estado="Ocupada"
    ).count()

    mantenimiento = Habitacion.query.filter_by(
        estado="Mantenimiento"
    ).count()

    total_huespedes = Huesped.query.count()

    reservas_activas = Reserva.query.filter_by(
        estado="Activa"
    ).count()

    reservas_finalizadas = Reserva.query.filter_by(
        estado="Finalizada"
    ).count()

    economicas = Habitacion.query.filter_by(
        tipo="Económica"
    ).count()

    estandar = Habitacion.query.filter_by(
        tipo="Estándar"
    ).count()

    ejecutivas = Habitacion.query.filter_by(
        tipo="Ejecutiva"
    ).count()

    ultimas_reservas = Reserva.query.order_by(
        Reserva.id.desc()
    ).limit(5).all()

    # ==========================================
    # GRÁFICA 1: INGRESOS POR MES
    # ==========================================

    nombres_meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    ingresos_mensuales = [
        0.0
        for _ in range(12)
    ]

    anio_actual = datetime.now().year

    reservas_finalizadas_anio = Reserva.query.filter(
        Reserva.estado == "Finalizada",
        Reserva.fecha_salida.isnot(None)
    ).all()

    for reserva in reservas_finalizadas_anio:
        if reserva.fecha_salida.year != anio_actual:
            continue

        numero_mes = reserva.fecha_salida.month

        ingresos_mensuales[
            numero_mes - 1
        ] += float(
            reserva.total_pagado or 0
        )

    ingresos_mensuales = [
        round(valor, 2)
        for valor in ingresos_mensuales
    ]

    # ==========================================
    # GRÁFICA 2: HABITACIONES MÁS UTILIZADAS
    # ==========================================

    habitaciones = Habitacion.query.order_by(
        Habitacion.numero
    ).all()

    uso_habitaciones = []

    for habitacion in habitaciones:
        cantidad_reservas = len(
            habitacion.reservas
        )

        uso_habitaciones.append({
            "numero": habitacion.numero,
            "cantidad": cantidad_reservas
        })

    uso_habitaciones.sort(
        key=lambda elemento: elemento["cantidad"],
        reverse=True
    )

    cinco_habitaciones = uso_habitaciones[:5]

    etiquetas_habitaciones = [
        f"Habitación {elemento['numero']}"
        for elemento in cinco_habitaciones
    ]

    valores_habitaciones = [
        elemento["cantidad"]
        for elemento in cinco_habitaciones
    ]

    # ==========================================
    # GRÁFICA 3: TIPOS MÁS RESERVADOS
    # ==========================================

    tipos_reservados = {
        "Económica": 0,
        "Estándar": 0,
        "Ejecutiva": 0
    }

    todas_las_reservas = Reserva.query.all()

    for reserva in todas_las_reservas:
        tipo = reserva.habitacion.tipo

        if tipo in tipos_reservados:
            tipos_reservados[tipo] += 1

    etiquetas_tipos_reservados = list(
        tipos_reservados.keys()
    )

    valores_tipos_reservados = list(
        tipos_reservados.values()
    )

    # ==========================================
    # ENVIAR INFORMACIÓN AL DASHBOARD
    # ==========================================

    return render_template(
        "index.html",

        # Estadísticas generales
        total=total,
        disponibles=disponibles,
        ocupadas=ocupadas,
        mantenimiento=mantenimiento,
        total_huespedes=total_huespedes,
        reservas_activas=reservas_activas,
        reservas_finalizadas=reservas_finalizadas,
        economicas=economicas,
        estandar=estandar,
        ejecutivas=ejecutivas,
        ultimas_reservas=ultimas_reservas,

        # Ingresos mensuales
        anio_actual=anio_actual,
        nombres_meses=nombres_meses,
        ingresos_mensuales=ingresos_mensuales,

        # Habitaciones más utilizadas
        etiquetas_habitaciones=etiquetas_habitaciones,
        valores_habitaciones=valores_habitaciones,

        # Tipos de habitación más reservados
        etiquetas_tipos_reservados=(
            etiquetas_tipos_reservados
        ),
        valores_tipos_reservados=(
            valores_tipos_reservados
        )
    )