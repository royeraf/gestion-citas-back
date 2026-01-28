import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

uri = os.getenv("SQLALCHEMY_DATABASE_URI")
if not uri:
    print("SQLALCHEMY_DATABASE_URI not found in environment")
    exit(1)

engine = create_engine(uri)

queries = [
    # 1. Crear tabla de personas
    """CREATE TABLE IF NOT EXISTS personas (
        id SERIAL PRIMARY KEY,
        dni VARCHAR(8) UNIQUE NOT NULL,
        nombres VARCHAR(100) NOT NULL,
        apellido_paterno VARCHAR(100),
        apellido_materno VARCHAR(100),
        fecha_nacimiento DATE,
        sexo VARCHAR(1),
        telefono VARCHAR(15),
        email VARCHAR(120),
        direccion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""",
    
    # 2. Agregar persona_id a usuarios y pacientes
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS persona_id INTEGER REFERENCES personas(id);",
    "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS persona_id INTEGER REFERENCES personas(id);",
    
    # 3. Estados de citas
    """CREATE TABLE IF NOT EXISTS estados_cita (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(50) UNIQUE NOT NULL,
        descripcion TEXT,
        color VARCHAR(20),
        activo BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS estado_id INTEGER REFERENCES estados_cita(id);",
    
    # 4. Columnas de roles (asegurar)
    "ALTER TABLE roles ADD COLUMN IF NOT EXISTS descripcion TEXT;",
    "ALTER TABLE roles ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE roles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    
    # 5. Otras tablas maestras y relaciones
    "CREATE TABLE IF NOT EXISTS especialidades (id SERIAL PRIMARY KEY, nombre VARCHAR(100) UNIQUE NOT NULL, descripcion TEXT, activo BOOLEAN DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
    "CREATE TABLE IF NOT EXISTS medico_especialidad (medico_id INTEGER REFERENCES usuarios(id), especialidad_id INTEGER REFERENCES especialidades(id), PRIMARY KEY (medico_id, especialidad_id));"
]

with engine.connect() as conn:
    for query in queries:
        try:
            print(f"Executing: {query}")
            conn.execute(text(query))
            conn.commit()
            print("Done.")
        except Exception as e:
            print(f"Error executing {query}: {e}")

print("Database schema synchronization finished.")
