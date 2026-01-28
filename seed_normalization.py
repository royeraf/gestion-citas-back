from app import app
from extensions.database import db
from models.rol_model import Rol
from models.especialidad_model import Especialidad
from models.area_model import Area

def seed():
    with app.app_context():
        # Asegurar que las tablas existan
        db.create_all()
        
        # 1. Crear Roles por defecto
        roles = [
            {'id': 1, 'nombre': 'Administrador', 'descripcion': 'Acceso total al sistema'},
            {'id': 2, 'nombre': 'Profesional', 'descripcion': 'Médicos y profesionales de salud'},
            {'id': 3, 'nombre': 'Asistente', 'descripcion': 'Personal de recepción y apoyo'}
        ]
        
        for r_data in roles:
            rol = Rol.query.get(r_data['id'])
            if not rol:
                rol = Rol(**r_data)
                db.session.add(rol)
                print(f"Rol {r_data['nombre']} creado.")
            else:
                print(f"Rol {r_data['nombre']} ya existe.")

        # 2. Migrar Areas a Especialidades (Opcional pero recomendado para normalización)
        # Por ahora crearemos algunas especialidades base si no existen
        especialidades = ['Medicina General', 'Pediatría', 'Ginecología', 'Odontología', 'Psicología']
        for esp_nombre in especialidades:
            esp = Especialidad.query.filter_by(nombre=esp_nombre).first()
            if not esp:
                esp = Especialidad(nombre=esp_nombre)
                db.session.add(esp)
                print(f"Especialidad {esp_nombre} creada.")

        try:
            db.session.commit()
            print("Sembrado de normalización completado.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al sembrar: {e}")

if __name__ == "__main__":
    seed()
