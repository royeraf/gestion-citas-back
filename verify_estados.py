from app import app
from extensions.database import db
from models.cita_model import Cita
from models.estado_cita_model import EstadoCita

def verify_migration():
    with app.app_context():
        print("--- Verificando migración de estados ---")
        
        # Verificar conteos
        total_citas = Cita.query.count()
        citas_con_estado_id = Cita.query.filter(Cita.estado_id.isnot(None)).count()
        
        print(f"Total citas: {total_citas}")
        print(f"Citas con estado_id: {citas_con_estado_id}")
        
        if total_citas == citas_con_estado_id:
            print("✅ Todas las citas tienen estado_id asignado.")
        else:
            print(f"⚠️ Faltan {total_citas - citas_con_estado_id} citas por migrar.")
            
        # Verificar consistencia
        citas_sample = Cita.query.limit(5).all()
        for cita in citas_sample:
            print(f"Cita ID: {cita.id} | Estado (str): {cita.estado} | Estado (rel): {cita.estado_rel.nombre if cita.estado_rel else 'None'}")
            
if __name__ == "__main__":
    verify_migration()
