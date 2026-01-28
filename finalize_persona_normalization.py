import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")

def finalize_normalization():
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("--- Iniciando limpieza final de columnas redundantes ---")

        # 1. Eliminar columnas de 'usuarios'
        print("Limpiando tabla 'usuarios'...")
        columns_to_drop_usuarios = ['dni', 'nombres_completos']
        for col in columns_to_drop_usuarios:
            try:
                cur.execute(f"ALTER TABLE usuarios DROP COLUMN IF EXISTS {col};")
                print(f"  - Columna '{col}' eliminada de 'usuarios'")
            except Exception as e:
                print(f"  ! Error al eliminar '{col}' de 'usuarios': {e}")
                conn.rollback()

        # 2. Eliminar columnas de 'pacientes'
        print("\nLimpiando tabla 'pacientes'...")
        columns_to_drop_pacientes = [
            'dni', 'nombres', 'apellido_paterno', 'apellido_materno', 
            'fecha_nacimiento', 'sexo', 'telefono', 'email', 'direccion'
        ]
        for col in columns_to_drop_pacientes:
            try:
                cur.execute(f"ALTER TABLE pacientes DROP COLUMN IF EXISTS {col};")
                print(f"  - Columna '{col}' eliminada de 'pacientes'")
            except Exception as e:
                print(f"  ! Error al eliminar '{col}' de 'pacientes': {e}")
                conn.rollback()

        conn.commit()
        print("\n--- Normalización finalizada con éxito ---")

    except Exception as e:
        print(f"Error general: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    finalize_normalization()
