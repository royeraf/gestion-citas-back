from factory import create_app
from extensions.database import db
from models.especialidad_model import Especialidad

def seed_especialidades():
    app = create_app()
    with app.app_context():
        especialidades = [
            {"nombre": "Medicina General", "descripcion": "Atención médica primaria y preventiva."},
            {"nombre": "Pediatría", "descripcion": "Atención médica para bebés, niños y adolescentes."},
            {"nombre": "Ginecología", "descripcion": "Salud del sistema reproductivo femenino y obstetricia."},
            {"nombre": "Odontología", "descripcion": "Salud oral, prevención y tratamiento de enfermedades dentales."},
            {"nombre": "Psicología", "descripcion": "Evaluación y tratamiento de procesos mentales y del comportamiento."},
            {"nombre": "Nutrición", "descripcion": "Asesoramiento sobre alimentación y hábitos saludables."},
            {"nombre": "Cardiología", "descripcion": "Estudio y tratamiento de enfermedades del corazón."},
            {"nombre": "Dermatología", "descripcion": "Enfermedades de la piel y sus anexos."},
            {"nombre": "Oftalmología", "descripcion": "Cuidado de la visión y tratamiento de enfermedades oculares."},
            {"nombre": "Traumatología", "descripcion": "Lesiones del aparato locomotor (huesos, articulaciones)."}
        ]

        inserted = 0
        skipped = 0

        for item in especialidades:
            existing = Especialidad.query.filter_by(nombre=item["nombre"]).first()
            if not existing:
                nueva = Especialidad(
                    nombre=item["nombre"],
                    descripcion=item["descripcion"],
                    activo=True
                )
                db.session.add(nueva)
                inserted += 1
            else:
                skipped += 1
        
        db.session.commit()
        print(f"Propagación terminada: {inserted} especialidades insertadas, {skipped} ya existían.")

if __name__ == "__main__":
    seed_especialidades()
