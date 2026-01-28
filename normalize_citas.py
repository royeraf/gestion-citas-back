from extensions.database import db
from app import app
from sqlalchemy import text
from models.cita_model import Cita
from models.area_model import Area
from models.estado_cita_model import EstadoCita

def normalize_citas():
    with app.app_context():
        print("Iniciando normalización de la tabla 'citas'...")
        try:
            # 1. Asegurar que area_id y estado_id estén poblados
            # Sincronizar area_id basado en el string 'area' si está vacío
            db.session.execute(text("""
                UPDATE citas 
                SET area_id = (SELECT id FROM areas WHERE areas.nombre = citas.area)
                WHERE area_id IS NULL AND area IS NOT NULL
            """))
            
            # Sincronizar estado_id basado en el string 'estado' si está vacío
            db.session.execute(text("""
                UPDATE citas 
                SET estado_id = (SELECT id FROM estados_cita WHERE estados_cita.nombre = citas.estado)
                WHERE estado_id IS NULL AND estado IS NOT NULL
            """))
            db.session.commit()
            print("Sincronización de IDs completada.")

            # 2. Eliminar columnas redundantes
            # Eliminamos 'area' (string) y 'estado' (string)
            db.session.execute(text("ALTER TABLE citas DROP COLUMN IF EXISTS area CASCADE"))
            db.session.execute(text("ALTER TABLE citas DROP COLUMN IF EXISTS estado CASCADE"))
            db.session.commit()
            print("Columnas redundantes 'area' y 'estado' eliminadas.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la normalización: {e}")

if __name__ == "__main__":
    normalize_citas()
