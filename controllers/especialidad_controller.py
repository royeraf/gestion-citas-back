from flask import jsonify
from extensions.database import db
from models.especialidad_model import Especialidad

class EspecialidadController:

    @staticmethod
    def get_all():
        try:
            especialidades = Especialidad.query.order_by(Especialidad.id.desc()).all()
            return jsonify([e.to_dict() for e in especialidades]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def create(data):
        try:
            nombre = data.get("nombre")
            if not nombre:
                return jsonify({"error": "El nombre es obligatorio"}), 400

            existing = Especialidad.query.filter_by(nombre=nombre).first()
            if existing:
                return jsonify({"error": "La especialidad ya existe"}), 409

            nueva_esp = Especialidad(
                nombre=nombre,
                descripcion=data.get("descripcion"),
                activo=data.get("activo", True)
            )

            db.session.add(nueva_esp)
            db.session.commit()

            return jsonify({
                "message": "Especialidad creada correctamente",
                "data": nueva_esp.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def update(id, data):
        try:
            especialidad = Especialidad.query.get(id)
            if not especialidad:
                return jsonify({"error": "Especialidad no encontrada"}), 404

            if "nombre" in data:
                existing = Especialidad.query.filter_by(nombre=data["nombre"]).first()
                if existing and existing.id != id:
                    return jsonify({"error": "El nombre de la especialidad ya existe"}), 409
                especialidad.nombre = data["nombre"]

            if "descripcion" in data:
                especialidad.descripcion = data["descripcion"]
            
            if "activo" in data:
                especialidad.activo = data["activo"]

            db.session.commit()

            return jsonify({
                "message": "Especialidad actualizada correctamente",
                "data": especialidad.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def delete(id):
        try:
            especialidad = Especialidad.query.get(id)
            if not especialidad:
                return jsonify({"error": "Especialidad no encontrada"}), 404

            # Opcional: Verificar si hay médicos asociados antes de eliminar
            # if especialidad.medicos.count() > 0:
            #     return jsonify({"error": "No se puede eliminar porque tiene médicos asociados"}), 400

            db.session.delete(especialidad)
            db.session.commit()

            return jsonify({"message": "Especialidad eliminada correctamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
