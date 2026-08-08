from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


db = SQLAlchemy()


class Habitacion(db.Model):
    __tablename__ = "habitaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    numero = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    precio = db.Column(
        db.Float,
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="Disponible"
    )

    reservas = db.relationship(
        "Reserva",
        backref="habitacion",
        lazy=True
    )

    def __repr__(self):
        return f"<Habitacion {self.numero}>"


class Huesped(db.Model):
    __tablename__ = "huespedes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    dpi = db.Column(
        db.String(13),
        unique=True,
        nullable=False
    )

    telefono = db.Column(
        db.String(8),
        nullable=False
    )

    reservas = db.relationship(
        "Reserva",
        backref="huesped",
        lazy=True
    )

    def __repr__(self):
        return f"<Huesped {self.nombre}>"


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha_ingreso = db.Column(
        db.Date,
        nullable=False
    )

    fecha_salida = db.Column(
        db.Date,
        nullable=True
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="Activa"
    )

    total_pagado = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    huesped_id = db.Column(
        db.Integer,
        db.ForeignKey("huespedes.id"),
        nullable=False
    )

    habitacion_id = db.Column(
        db.Integer,
        db.ForeignKey("habitaciones.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Reserva {self.id}>"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    usuario = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    contrasena_hash = db.Column(
        db.String(255),
        nullable=False
    )

    rol = db.Column(
        db.String(20),
        nullable=False,
        default="Recepcionista"
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    bitacoras = db.relationship(
        "Bitacora",
        backref="usuario_registro",
        lazy=True
    )

    def establecer_contrasena(self, contrasena):
        self.contrasena_hash = generate_password_hash(
            contrasena
        )

    def verificar_contrasena(self, contrasena):
        return check_password_hash(
            self.contrasena_hash,
            contrasena
        )

    def __repr__(self):
        return f"<Usuario {self.usuario}>"


class Bitacora(db.Model):
    __tablename__ = "bitacora"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    accion = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255),
        nullable=False
    )

    fecha_hora = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    def __repr__(self):
        return f"<Bitacora {self.accion}>"