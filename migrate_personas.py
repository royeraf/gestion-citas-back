from app import app
from extensions.database import db
from sqlalchemy import text
from models.persona_model import Persona

def run_migration():
    with app.app_context():
        # 1. Crear tabla personas si no existe
        print("Creando tabla 'personas'...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS personas (
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
            );
        """))
        db.session.commit()

        # 2. Añadir persona_id a pacientes y usuarios si no existen
        print("Añadiendo columnas de referencia...")
        try:
            db.session.execute(text("ALTER TABLE pacientes ADD COLUMN persona_id INTEGER REFERENCES personas(id);"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Columna persona_id en pacientes ya existe u otro error: {e}")

        try:
            db.session.execute(text("ALTER TABLE usuarios ADD COLUMN persona_id INTEGER REFERENCES personas(id);"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Columna persona_id en usuarios ya existe u otro error: {e}")

        # 3. Migrar datos de pacientes -> personas
        print("Migrando pacientes a personas...")
        pacientes = db.session.execute(text("SELECT id, dni, nombres, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, telefono, email, direccion FROM pacientes")).all()
        
        for p in pacientes:
            # Buscar si ya existe la persona (por si acaso)
            persona = Persona.query.filter_by(dni=p.dni).first()
            if not persona:
                persona = Persona(
                    dni=p.dni,
                    nombres=p.nombres,
                    apellido_paterno=p.apellido_paterno,
                    apellido_materno=p.apellido_materno,
                    fecha_nacimiento=p.fecha_nacimiento,
                    sexo=p.sexo,
                    telefono=p.telefono,
                    email=p.email,
                    direccion=p.direccion
                )
                db.session.add(persona)
                db.session.flush() # Para obtener ID
            
            # Actualizar persona_id en pacientes
            db.session.execute(text("UPDATE pacientes SET persona_id = :pid WHERE id = :id"), {"pid": persona.id, "id": p.id})
        
        db.session.commit()
        print(f"Migrados {len(pacientes)} pacientes.")

        # 4. Migrar datos de usuarios -> personas
        print("Migrando usuarios a personas...")
        usuarios = db.session.execute(text("SELECT id, dni, nombres_completos FROM usuarios")).all()
        
        for u in usuarios:
            persona = Persona.query.filter_by(dni=u.dni).first()
            if not persona:
                # Si no existe (no era paciente), crear con lo que tengamos
                # nombres_completos suele ser "Nombres ApellidoP ApellidoM"
                parts = u.nombres_completos.split() if u.nombres_completos else ["Usuario"]
                nombres = parts[0]
                ap = parts[1] if len(parts) > 1 else ""
                am = parts[2] if len(parts) > 2 else ""
                
                persona = Persona(
                    dni=u.dni,
                    nombres=nombres,
                    apellido_paterno=ap,
                    apellido_materno=am
                )
                db.session.add(persona)
                db.session.flush()
            
            db.session.execute(text("UPDATE usuarios SET persona_id = :pid WHERE id = :id"), {"pid": persona.id, "id": u.id})
        
        db.session.commit()
        print(f"Migrados {len(usuarios)} usuarios.")
        
        print("Migración de Personas completada exitosamente.")

if __name__ == "__main__":
    run_migration()
