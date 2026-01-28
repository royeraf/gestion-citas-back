"""
Script de migración para normalizar la tabla 'historial_estado_citas'.

Nuevos campos:
- estado_anterior_id: FK a estados_cita
- estado_nuevo_id: FK a estados_cita

Pasos:
1. Agregar las nuevas columnas.
2. Mapear los nombres de estados existentes a sus IDs correspondientes.
3. Actualizar los registros actuales.
4. (Opcional) Eliminar las columnas de texto antiguas.

Ejecutar:
    python migrate_historial.py
"""

from app import app
from extensions.database import db
from models.estado_cita_model import EstadoCita

def run_migration():
    print("=" * 60)
    print("  MIGRACIÓN: Normalizar tabla 'historial_estado_citas'")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 1. Agregar nuevas columnas
            print("\n[1/3] Agregando nuevas columnas de ID...")
            statements = [
                "ALTER TABLE historial_estado_citas ADD COLUMN IF NOT EXISTS estado_anterior_id INTEGER REFERENCES estados_cita(id)",
                "ALTER TABLE historial_estado_citas ADD COLUMN IF NOT EXISTS estado_nuevo_id INTEGER REFERENCES estados_cita(id)"
            ]
            
            for stmt in statements:
                try:
                    db.session.execute(db.text(stmt))
                    db.session.commit()
                    print(f"  ✓ {stmt[:60]}...")
                except Exception as e:
                    print(f"  ⚠ {str(e)[:100]}")

            # 2. Migrar datos existentes
            print("\n[2/3] Mapeando estados de texto a IDs...")
            estados = EstadoCita.query.all()
            estado_map = {e.nombre.lower(): e.id for e in estados}
            
            if not estado_map:
                print("  ⚠ No se encontraron estados en la tabla 'estados_cita'.")
                print("  Por favor, asegúrese de que la tabla 'estados_cita' tenga datos.")
                return

            # Obtener registros para procesar
            result = db.session.execute(db.text("SELECT id, estado_anterior, estado_nuevo FROM historial_estado_citas"))
            registros = result.fetchall()
            
            actualizados = 0
            for reg in registros:
                reg_id, ant_nome, nue_nome = reg
                ant_id = estado_map.get(ant_nome.lower()) if ant_nome else None
                nue_id = estado_map.get(nue_nome.lower()) if nue_nome else None
                
                if ant_id or nue_id:
                    update_stmt = db.text("""
                        UPDATE historial_estado_citas 
                        SET estado_anterior_id = :ant_id, 
                            estado_nuevo_id = :nue_id 
                        WHERE id = :id
                    """)
                    db.session.execute(update_stmt, {"ant_id": ant_id, "nue_id": nue_id, "id": reg_id})
                    actualizados += 1
            
            db.session.commit()
            print(f"  ✓ Se actualizaron {actualizados} registros con sus respectivos IDs.")

            # 3. Mostrar resumen
            print("\n[3/3] Resumen de la estructura:")
            columns_result = db.session.execute(db.text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'historial_estado_citas'
                ORDER BY ordinal_position
            """))
            
            print("-" * 50)
            for col in columns_result:
                print(f"  {col[0]:25} | {col[1]}")
            
            print("\n" + "=" * 60)
            print("  ✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error en migración: {e}")
            raise

if __name__ == "__main__":
    run_migration()
