import json
from typing import Dict, Any, List

def clean_professor_data(professors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Limpia los datos de profesores eliminando campos redundantes e innecesarios
    """
    
    # Campos esenciales que debemos mantener
    essential_fields = {
        'name',                      # Nombre del profesor
        'research_papers',           # Número de publicaciones
        'interest_areas',            # Áreas de interés
        'interest_scores',           # Puntuaciones de interés
        'degree_level',              # Nivel académico (PhD, Master, Bachelor)
        'normalized_specialization', # Especialización normalizada
        'normalized_university'      # Universidad normalizada
    }
    
    # Campos opcionales útiles (mantener si se quiere información adicional)
    optional_fields = {
        'url_image',                 # URL de imagen del profesor
        'original_degree',           # Grado académico original (referencia)
        'original_university',       # Universidad original (referencia)
        'specialization'             # Especialización sin normalizar
    }
    
    # Campos a eliminar (redundantes o innecesarios)
    fields_to_remove = {
        'degree',                    # Redundante con original_degree
        'university',                # Redundante con original_university
        'scraped_info',              # Información muy detallada innecesaria
        'scraped_name'               # Redundante con name
    }
    
    cleaned_data = []
    
    for professor in professors_data:
        # Crear nuevo diccionario solo con campos necesarios
        cleaned_professor = {}
        
        # Agregar campos esenciales
        for field in essential_fields:
            if field in professor:
                cleaned_professor[field] = professor[field]
        
        # Agregar campos opcionales útiles
        for field in optional_fields:
            if field in professor:
                cleaned_professor[field] = professor[field]
        
        cleaned_data.append(cleaned_professor)
    
    return cleaned_data

def analyze_size_reduction(original_data: List[Dict], cleaned_data: List[Dict]) -> None:
    """
    Analiza la reducción de tamaño después de la limpieza
    """
    def calculate_size(data):
        return len(json.dumps(data, ensure_ascii=False))
    
    original_size = calculate_size(original_data)
    cleaned_size = calculate_size(cleaned_data)
    reduction = original_size - cleaned_size
    reduction_percentage = (reduction / original_size) * 100
    
    print(f"📊 ANÁLISIS DE REDUCCIÓN DE TAMAÑO:")
    print(f"Tamaño original: {original_size:,} bytes")
    print(f"Tamaño limpio: {cleaned_size:,} bytes")
    print(f"Reducción: {reduction:,} bytes ({reduction_percentage:.1f}%)")

def show_field_comparison(original_data: List[Dict], cleaned_data: List[Dict]) -> None:
    """
    Muestra comparación de campos antes y después
    """
    original_fields = set(original_data[0].keys()) if original_data else set()
    cleaned_fields = set(cleaned_data[0].keys()) if cleaned_data else set()
    
    removed_fields = original_fields - cleaned_fields
    kept_fields = original_fields.intersection(cleaned_fields)
    
    print(f"\n📝 COMPARACIÓN DE CAMPOS:")
    print(f"Campos originales: {len(original_fields)}")
    print(f"Campos mantenidos: {len(kept_fields)}")
    print(f"Campos eliminados: {len(removed_fields)}")
    
    print(f"\n✅ CAMPOS MANTENIDOS ({len(kept_fields)}):")
    for field in sorted(kept_fields):
        print(f"  • {field}")
    
    print(f"\n❌ CAMPOS ELIMINADOS ({len(removed_fields)}):")
    for field in sorted(removed_fields):
        print(f"  • {field}")

def main():
    """
    Función principal que limpia los datos de profesores
    """
    input_file = 'profesores_completos.json'
    
    try:
        print("🧹 Iniciando limpieza de datos...")
        
        # Cargar datos originales
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        print(f"📚 Procesando {len(original_data)} profesores...")
        
        # Limpiar datos
        cleaned_data = clean_professor_data(original_data)
        
        # Mostrar comparaciones
        show_field_comparison(original_data, cleaned_data)
        analyze_size_reduction(original_data, cleaned_data)
        
        # Verificar que no perdimos información esencial
        print(f"\n🔍 VERIFICACIÓN DE DATOS ESENCIALES:")
        sample_prof = cleaned_data[0] if cleaned_data else {}
        essential_check = {
            'name': sample_prof.get('name', 'N/A'),
            'degree_level': sample_prof.get('degree_level', 'N/A'),
            'normalized_specialization': sample_prof.get('normalized_specialization', 'N/A'),
            'normalized_university': sample_prof.get('normalized_university', 'N/A'),
            'research_papers': sample_prof.get('research_papers', 'N/A')
        }
        
        for key, value in essential_check.items():
            print(f"  • {key}: {value}")
        
        # Guardar datos limpios
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Datos limpios guardados en: {input_file}")
        print("🎉 Limpieza completada exitosamente!")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{input_file}'")
    except json.JSONDecodeError:
        print("❌ Error: El archivo JSON no es válido")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main() 