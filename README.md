Gestión de habitaciones - Hotel

Pequeña aplicación en Python para registrar, consultar, modificar y eliminar habitaciones.

Instalación

Requiere Python 3.8+ (no hay dependencias externas).

Uso (ejemplos):

Inicializar la base de datos:

python main.py init

Agregar una habitación:

python main.py add --number 101 --type "Doble" --price 75.0 --available yes --notes "Con vista"

Listar habitaciones:

python main.py list

Ver habitación por número:

python main.py get --number 101

Modificar:

python main.py update --number 101 --price 80.0 --notes "Actualizada"

Eliminar:

python main.py delete --number 101

Cambiar disponibilidad:

python main.py set-availability --number 101 --available no

Filtrar por tipo:

python main.py list-by-type --type "Doble"

Archivos relevantes:

db.py: helper SQLite
models.py: lógica CRUD
main.py: CLI
Pestaña de Pruebas: instrucciones rápidas

Inicializa la base de datos y ejecuta una secuencia simple de pruebas (crear, listar, consultar, actualizar, cambiar disponibilidad, eliminar):
python3 main.py init
python3 main.py add --number 101 --type "Doble" --price 75.0 --available yes --notes "Con vista"
python3 main.py list
python3 main.py get --number 101
python3 main.py update --number 101 --price 80.0 --notes "Actualizada"
python3 main.py get --number 101
python3 main.py set-availability --number 101 --available no
python3 main.py list-by-type --type "Doble"
python3 main.py delete --number 101
python3 main.py list
Si prefieres ejecutar todo en una sola línea (Linux/macOS/zsh):
python3 main.py init && python3 main.py add --number 101 --type "Doble" --price 75.0 --available yes --notes "Con vista" && python3 main.py list && python3 main.py get --number 101 && python3 main.py update --number 101 --price 80.0 --notes "Actualizada" && python3 main.py get --number 101 && python3 main.py set-availability --number 101 --available no && python3 main.py list-by-type --type "Doble" && python3 main.py delete --number 101 && python3 main.py list
Notas

Usa Python 3.8+.
Los comandos crean una base de datos SQLite local llamada hotel.db en el mismo directorio.
