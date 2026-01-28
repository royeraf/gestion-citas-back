from extensions.database import db
from app import app
from sqlalchemy import text
from models.persona_model import Persona
from models.cita_model import Cita

def migrate_acompanantes():
    with app.app_context():
        print("Iniciando migración de acompañantes a la tabla 'personas'...")
        try:
            # 1. Agregar columna acompanante_persona_id if not exists
            db.session.execute(text("ALTER TABLE citas ADD COLUMN IF NOT EXISTS acompanante_persona_id INTEGER REFERENCES personas(id)"))
            db.session.commit()
            
            # 2. Migrar datos
            # Obtener citas que tengan datos de acompañante pero no ID
            rows = db.session.execute(text("SELECT id, dni_acompanante, nombre_acompanante, telefono_acompanante FROM citas WHERE dni_acompanante IS NOT NULL AND acompanante_persona_id IS NULL")).all()
            
            for row in rows:
                cita_id, dni, nombre, telefono = row
                if not dni: continue
                
                # Buscar o crear Persona
                persona = Persona.query.filter_by(dni=dni).first()
                if not persona:
                    # Dividir nombre simple (asumiendo que viene como un solo string)
                    persona = Persona(
                        dni=dni,
                        nombres=nombre,
                        apellido_paterno=".", # Valores por defecto para campos obligatorios en normalización
                        apellido_materno=".",
                        telefono=telefono
                    )
                    db.session.add(persona)
                    db.session.flush()
                
                # Actualizar cita
                db.session.execute(text("UPDATE citas SET acompanante_persona_id = :p_id WHERE id = :c_id"), {"p_id": persona.id, "c_id": cita_id})
            
            db.session.commit()
            print(f"Migrados {len(rows)} acompañantes.")

            # 3. Eliminar columnas antiguas
            db.session.execute(text("ALTER TABLE citas DROP COLUMN IF EXISTS dni_acompanante CASCADE"))
            db.session.execute(text("ALTER TABLE citas DROP COLUMN IF EXISTS nombre_acompanante CASCADE"))
            db.session.execute(text("ALTER TABLE citas DROP COLUMN IF EXISTS telefono_acompanante CASCADE"))
            db.session.commit()
            print("Columnas antiguas de acompañante eliminadas exitosamente.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración de acompañantes: {e}")

if __name__ == "__main__":
    migrate_acompanantes()
