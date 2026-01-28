from app import app
from extensions.database import db
from models.cita_model import Cita
from models.estado_cita_model import EstadoCita
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # 1. Crear tabla estados_cita si no existe y añadir columna estado_id
        try:
            with db.engine.connect() as conn:
                print("Creando tabla 'estados_cita'...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS estados_cita (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(50) UNIQUE NOT NULL,
                        descripcion TEXT,
                        color VARCHAR(20),
                        activo BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                print("Añadiendo columna 'estado_id' a tabla 'citas'...")
                # SQLite no soporta IF NOT EXISTS en ADD COLUMN en versiones antiguas
                # Postgres sí, pero para compatibilidad intentamos agregar y capturamos error si ya existe
                try:
                    conn.execute(text("ALTER TABLE citas ADD COLUMN estado_id INTEGER REFERENCES estados_cita(id);"))
                    conn.commit()
                except Exception as e:
                    print(f"Nota: Columna estado_id podría ya existir o error: {e}")
                    # Continuar, ya que si falla por existir, está bien.
        except Exception as e:
            print(f"Error en estructura DB: {e}")

        # 2. Poblar estados
        estados_iniciales = [
            {"nombre": "pendiente", "descripcion": "Cita registrada esperando atención", "color": "blue"},
            {"nombre": "confirmada", "descripcion": "Paciente ha confirmado su asistencia", "color": "green"},
            {"nombre": "atendida", "descripcion": "Cita realizada exitosamente", "color": "teal"},
            {"nombre": "cancelada", "descripcion": "Cita cancelada", "color": "red"},
            {"nombre": "no_asistio", "descripcion": "Paciente no se presentó", "color": "gray"},
            {"nombre": "referido", "descripcion": "Paciente referido a otra especialidad", "color": "purple"}
        ]

        print("Poblando tabla 'estados_cita'...")
        estados_map = {}
        for est_data in estados_iniciales:
            try:
                # Intentar buscar primero
                estado = EstadoCita.query.filter_by(nombre=est_data["nombre"]).first()
                if not estado:
                    estado = EstadoCita(
                        nombre=est_data["nombre"],
                        descripcion=est_data["descripcion"],
                        color=est_data["color"]
                    )
                    db.session.add(estado)
                    db.session.commit() # Commit inmediato para asegurar ID y manejar errores por item
                    print(f"Creado estado: {estado.nombre}")
                estados_map[estado.nombre] = estado.id
            except Exception as e:
                db.session.rollback()
                # Intentar recuperar si falló por concurrencia o duplicado no detectado
                print(f"Error o duplicado al crear {est_data['nombre']}: {e}. Intentando recuperar.")
                estado = EstadoCita.query.filter_by(nombre=est_data["nombre"]).first()
                if estado:
                    estados_map[estado.nombre] = estado.id
        
        # 3. Migrar datos de citas
        print("Migrando estados de citas existentes...")
        citas = Cita.query.filter(Cita.estado_id == None).all()
        count = 0
        for cita in citas:
            if cita.estado and cita.estado in estados_map:
                cita.estado_id = estados_map[cita.estado]
                count += 1
            else:
                # Si el estado no coincide, asignar pendiente por defecto
                cita.estado_id = estados_map["pendiente"]
                print(f"Advertencia: Cita {cita.id} con estado '{cita.estado}' desconocido. Asignando 'pendiente'.")
                count += 1
        
        db.session.commit()
        print(f"Migración completada. {count} citas actualizadas.")

if __name__ == "__main__":
    run_migration()
