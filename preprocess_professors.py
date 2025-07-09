import json
import re
import os
from typing import Dict, Any, List
from collections import Counter

def classify_degree(degree: str) -> str:
    """
    Clasifica un grado académico en una de las categorías: PhD, Master, Bachelor
    """
    if not degree or degree.strip().lower() in ['no encontrado', 'unknown', '']:
        return 'Bachelor'
    
    degree_lower = degree.lower()
    
    # Patrones para PhD/Doctorado
    phd_patterns = [
        r'\bphd\b', r'\bdoctorado\b', r'\bdoctor\b', r'\bdoctora\b',
        r'\bph\.d\b', r'\bd\.phil\b', r'\bdphil\b', r'\bdoctoral\b'
    ]
    
    # Patrones para Master/Magíster
    master_patterns = [
        r'\bmaster\b', r'\bmagíster\b', r'\bmagister\b', r'\bmaestría\b',
        r'\bmaestria\b', r'\bmáster\b', r'\bm\.s\b', r'\bm\.sc\b',
        r'\bm\.a\b', r'\bmsc\b', r'\bms\b', r'\bmba\b', r'\bm\.eng\b', r'\bmeng\b'
    ]
    
    # Verificar PhD primero (mayor jerarquía)
    for pattern in phd_patterns:
        if re.search(pattern, degree_lower):
            return 'PhD'
    
    # Verificar Master
    for pattern in master_patterns:
        if re.search(pattern, degree_lower):
            return 'Master'
    
    # Si no coincide con PhD o Master, es Bachelor por defecto
    return 'Bachelor'

def extract_specialization(degree: str) -> str:
    """
    Extrae la especialización del grado académico
    """
    if not degree or degree.strip().lower() in ['no encontrado', 'unknown', '']:
        return 'General'
    
    original_degree = degree.strip()
    
    # Casos especiales
    special_cases = {
        'PhD, ISyE': 'Industrial and Systems Engineering',
        'Master\'s degree': 'General',
        'Master of Science': 'General Science',
        'PhD. in Physics': 'Physics',
        'Ingeniero Mecánico': 'Mechanical Engineering'
    }
    
    if original_degree in special_cases:
        return special_cases[original_degree]
    
    # Patrones para extraer especialización
    patterns = [
        r'(?:Doctorado|Doctor|Doctora|PhD|Ph\.D\.?)\s+(?:en|in|de)\s+(.+?)(?:\s*,|$)',
        r'(?:Doctorado|Doctor|Doctora)\s+(.+?)(?:\s*,|$)',
        r'PhD\s*[,.]?\s*(.+?)(?:\s*,|$)',
        r'(?:Magíster|Máster|Master\'?s?\s*(?:Degree)?|Maestría)\s+(?:en|in|de|con\s+mención\s+en)\s+(.+?)(?:\s*,|$)',
        r'(?:Magíster|Máster|Maestría)\s+(.+?)(?:\s*,|$)',
        r'(?:Licenciado|Licenciada|Ingeniero|Ingeniería)\s+(?:en|de)?\s*(.+?)(?:\s*,|$)',
        r'(?:Licenciado|Licenciada)\s+(.+?)(?:\s*,|$)',
        r'(?:Bachelor|B\.S\.?|B\.Sc\.?|B\.A\.?)\s+(?:in|of|en)\s+(.+?)(?:\s*,|$)',
        r'(?:M\.S\.?|M\.Sc\.?|M\.A\.?|MSc|MS)\s+(?:in|of|en)\s+(.+?)(?:\s*,|$)',
    ]
    
    specialization = None
    for pattern in patterns:
        match = re.search(pattern, original_degree, re.IGNORECASE)
        if match:
            specialization = match.group(1).strip()
            break
    
    # Si no se encontró patrón, usar el grado completo pero limpio
    if not specialization:
        specialization = original_degree
        specialization = re.sub(r'^(?:\(c\))?\s*(?:Doctorado|Doctor|Doctora|PhD|Ph\.D\.?|Magíster|Máster|Master\'?s?\s*(?:Degree)?|Maestría|Licenciado|Licenciada|Ingeniero|Bachelor|B\.S\.?|B\.Sc\.?|B\.A\.?|M\.S\.?|M\.Sc\.?|M\.A\.?|MSc|MS)\s*', '', specialization, flags=re.IGNORECASE)
    
    # Limpiar resultado
    specialization = specialization.strip()
    specialization = re.sub(r'\s+', ' ', specialization)
    specialization = specialization.strip('.,')
    
    if len(specialization) < 3:
        return 'General'
    
    return specialization

def get_university_normalization_mapping() -> Dict[str, str]:
    """
    Mapping de normalización de universidades
    """
    return {
        # Universidades Peruanas
        'pontificia universidad católica del perú': 'PUCP',
        'pucp': 'PUCP',
        'universidad nacional de ingeniería': 'UNI Peru',
        'national university of engineering': 'UNI Peru',
        'universidad de ingeniería y tecnología - utec, lima, perú': 'UTEC',
        'utec': 'UTEC',
        'universidad nacional de educación': 'UNE',
        'universidad nacional de san agustín': 'UNSA',
        'esan graduate school of business': 'ESAN',
        
        # Universidades Mexicanas
        'universidad nacional autónoma de méxico': 'UNAM',
        'unam': 'UNAM',
        'tec de monterrey': 'Tecnológico de Monterrey',
        'tecnológico de monterrey': 'Tecnológico de Monterrey',
        
        # Universidades Estadounidenses
        'georgia tech': 'Georgia Institute of Technology',
        'georgia institute of technology': 'Georgia Institute of Technology',
        'university of california, berkeley': 'UC Berkeley',
        'uc berkeley': 'UC Berkeley',
        'universidad de california, berkeley': 'UC Berkeley',
        'florida international university': 'Florida International University',
        'northeastern university': 'Northeastern University',
        'university of alberta': 'University of Alberta',
        'university of oxford': 'University of Oxford',
        'simon fraser university': 'Simon Fraser University',
        'universidad texas a&m (eeuu)': 'Texas A&M University',
        'texas a&m university': 'Texas A&M University',
        
        # Universidades Europeas
        'université laval': 'Université Laval',
        'universidad técnica de lisboa': 'Technical University of Lisbon',
        'universitat de valència': 'University of Valencia',
        'universidad de valencia': 'University of Valencia',
        'universidad de toulouse iii': 'University of Toulouse III',
        'universidad de zaragoza': 'University of Zaragoza',
        'eindhoven university of technology': 'Eindhoven University of Technology',
        'sorbonne université': 'Sorbonne University',
        'universidad de oviedo': 'University of Oviedo',
        'albert-ludwigs-universität freiburg im breisgau': 'University of Freiburg',
        
        # Universidades Brasileñas
        'universidad de sao paulo (usp)': 'University of São Paulo',
        'universidade de são paulo': 'University of São Paulo',
        'usp': 'University of São Paulo',
        'universidade federal de minas gerais': 'Federal University of Minas Gerais',
        'ufmg': 'Federal University of Minas Gerais',
        
        # Universidades de otros países
        'universidad de puerto rico-mayaguez': 'University of Puerto Rico at Mayagüez',
        'universidad nacional de singapur': 'National University of Singapore',
        'nus': 'National University of Singapore',
        'instituto de matemática pura e aplicada (impa)': 'IMPA Brazil',
        'impa': 'IMPA Brazil',
        'instituto de física y tecnología de moscú, rusia': 'Moscow Institute of Physics and Technology',
    }

def normalize_university(university: str, mapping: Dict[str, str]) -> str:
    """
    Normaliza el nombre de una universidad
    """
    if not university or university.strip() == '':
        return 'Unknown'
    
    univ_lower = university.lower().strip()
    
    # Buscar coincidencia exacta
    if univ_lower in mapping:
        return mapping[univ_lower]
    
    # Buscar coincidencias parciales por palabras clave
    university_keywords = {
        'pucp': 'PUCP',
        'católica del perú': 'PUCP',
        'pontificia católica': 'PUCP',
        'uni peru': 'UNI Peru',
        'ingeniería peru': 'UNI Peru',
        'utec': 'UTEC',
        'unam': 'UNAM',
        'autónoma méxico': 'UNAM',
        'monterrey': 'Tecnológico de Monterrey',
        'georgia tech': 'Georgia Institute of Technology',
        'berkeley': 'UC Berkeley',
        'california berkeley': 'UC Berkeley',
        'oxford': 'University of Oxford',
        'laval': 'Université Laval',
        'toulouse': 'University of Toulouse III',
        'valencia': 'University of Valencia',
        'zaragoza': 'University of Zaragoza',
        'eindhoven': 'Eindhoven University of Technology',
        'sorbonne': 'Sorbonne University',
        'oviedo': 'University of Oviedo',
        'freiburg': 'University of Freiburg',
        'são paulo': 'University of São Paulo',
        'sao paulo': 'University of São Paulo',
        'minas gerais': 'Federal University of Minas Gerais',
        'puerto rico': 'University of Puerto Rico at Mayagüez',
        'singapur': 'National University of Singapore',
        'singapore': 'National University of Singapore',
        'northeastern': 'Northeastern University',
        'alberta': 'University of Alberta',
        'texas a&m': 'Texas A&M University',
        'florida international': 'Florida International University',
        'simon fraser': 'Simon Fraser University',
        'impa': 'IMPA Brazil',
        'moscú': 'Moscow Institute of Physics and Technology',
        'moscow': 'Moscow Institute of Physics and Technology',
    }
    
    for keyword, normalized in university_keywords.items():
        if keyword in univ_lower:
            return normalized
    
    # Si no se encuentra, retornar el nombre original con formato título
    return university.title()

def get_normalization_mapping() -> Dict[str, str]:
    """
    Mapping de normalización de especializaciones
    """
    return {
        # Ingeniería y Tecnología
        'mechanics': 'Mechanical Engineering',
        'mechanical engineering': 'Mechanical Engineering',
        'ingeniería mecánica': 'Mechanical Engineering',
        'mecánica': 'Mechanical Engineering',
        'design mechanics': 'Mechanical Engineering',
        'mechanics, with a specialization in design mechanics': 'Mechanical Engineering',
        
        'civil engineering': 'Civil Engineering', 
        'ingeniería civil': 'Civil Engineering',
        'civil': 'Civil Engineering',
        
        'electrical engineering': 'Electrical Engineering',
        'ingeniería electrónica': 'Electrical Engineering',
        'electronic engineering': 'Electrical Engineering',
        'electrónica': 'Electrical Engineering',
        'ciencias con mención en ingeniería electrónica': 'Electrical Engineering',
        
        'biomedical engineering': 'Biomedical Engineering',
        'ingeniería biomédica': 'Biomedical Engineering',
        'biomédica': 'Biomedical Engineering',
        
        'computer science': 'Computer Science',
        'ciencias de la computación': 'Computer Science',
        'ciencia de la computación': 'Computer Science',
        'informática': 'Computer Science',
        'computer engineering': 'Computer Science',
        'informática y robótica': 'Computer Science',
        'matemática aplicada e informática': 'Computer Science',
        
        'industrial engineering': 'Industrial Engineering',
        'industrial and systems engineering': 'Industrial Engineering',
        'ingeniería industrial': 'Industrial Engineering',
        'isye': 'Industrial Engineering',
        'systems engineering': 'Industrial Engineering',
        
        'chemical engineering': 'Chemical Engineering',
        'ingeniería química': 'Chemical Engineering',
        'química': 'Chemical Engineering',
        
        'energy engineering': 'Energy Engineering',
        'ingeniería de la energía': 'Energy Engineering',
        'energía': 'Energy Engineering',
        'tecnología, diversificación, calidad y ahorro energético': 'Energy Engineering',
        'ingeniería térmica avanzada y optimización energética': 'Energy Engineering',
        
        'robotics': 'Robotics and Mechatronics',
        'mechatronics': 'Robotics and Mechatronics',
        'mecatrónica': 'Robotics and Mechatronics',
        'ciencias mecánicas y robótica': 'Robotics and Mechatronics',
        
        # Ciencias Básicas
        'physics': 'Physics',
        'física': 'Physics',
        'physical sciences': 'Physics',
        
        'mathematics': 'Mathematics',
        'matemáticas': 'Mathematics',
        'matemáticas aplicadas': 'Applied Mathematics',
        'applied mathematics': 'Applied Mathematics',
        'mathematical sciences': 'Mathematics',
        
        'chemistry': 'Chemistry',
        'química': 'Chemistry',
        'ciencias naturales': 'Natural Sciences',
        
        # Administración y Negocios
        'management science': 'Management and Business',
        'business administration': 'Management and Business',
        'administration': 'Management and Business',
        'administración': 'Management and Business',
        'ciencias de la administración': 'Management and Business',
        'management': 'Management and Business',
        'business': 'Management and Business',
        'engineering management': 'Management and Business',
        
        # Humanidades y Artes
        'art history': 'Humanities and Arts',
        'historia del arte': 'Humanities and Arts',
        'literature': 'Humanities and Arts',
        'literatura': 'Humanities and Arts',
        'lengua y literaturas hispánicas': 'Humanities and Arts',
        'humanities': 'Humanities and Arts',
        
        # Ciencias Sociales
        'sociology': 'Social Sciences',
        'sociología': 'Social Sciences',
        'gender studies': 'Social Sciences',
        'estudios interdisciplinarios de género': 'Social Sciences',
        'estudios de género': 'Social Sciences',
        
        # Educación
        'education': 'Education',
        'educación': 'Education',
        'ciencias de la educación': 'Education',
        'pedagogía': 'Education',
        
        # Otros campos técnicos
        'naval architecture': 'Naval and Marine Engineering',
        'arquitectura naval': 'Naval and Marine Engineering',
        'marine engineering': 'Naval and Marine Engineering',
        'ingeniería marina': 'Naval and Marine Engineering',
        'arquitectura naval e ingeniería marina': 'Naval and Marine Engineering',
        
        'thermal engineering': 'Energy and Thermal Systems',
        'ingeniería térmica': 'Energy and Thermal Systems',
        'optimización energética': 'Energy and Thermal Systems',
        
        'fonoaudiología': 'Health Sciences',
        'speech therapy': 'Health Sciences',
        
        # Casos generales
        'general': 'General',
        'general science': 'General Science',
    }

def normalize_specialization(specialization: str, mapping: Dict[str, str]) -> str:
    """
    Normaliza una especialización usando el mapping manual
    """
    spec_lower = specialization.lower().strip()
    
    # Buscar coincidencia exacta
    if spec_lower in mapping:
        return mapping[spec_lower]
    
    # Buscar coincidencia parcial más inteligente
    best_match = None
    best_score = 0
    
    for key, normalized in mapping.items():
        key_words = set(key.split())
        spec_words = set(spec_lower.split())
        
        # Calcular similitud por palabras en común
        common_words = key_words.intersection(spec_words)
        if common_words:
            score = len(common_words) / max(len(key_words), len(spec_words))
            if score > best_score and score > 0.3:  # Al menos 30% de similitud
                best_score = score
                best_match = normalized
    
    if best_match:
        return best_match
    
    # Buscar por palabras clave específicas
    keyword_mapping = {
        'mecánic': 'Mechanical Engineering',
        'mechanic': 'Mechanical Engineering',
        'civil': 'Civil Engineering',
        'electr': 'Electrical Engineering',
        'biomédic': 'Biomedical Engineering',
        'biomedic': 'Biomedical Engineering',
        'comput': 'Computer Science',
        'informát': 'Computer Science',
        'industri': 'Industrial Engineering',
        'físic': 'Physics',
        'physic': 'Physics',
        'matemát': 'Mathematics',
        'mathemat': 'Mathematics',
        'químic': 'Chemical Engineering',
        'chemic': 'Chemical Engineering',
        'energ': 'Energy Engineering',
        'robot': 'Robotics and Mechatronics',
        'mecatron': 'Robotics and Mechatronics',
        'administr': 'Management and Business',
        'management': 'Management and Business',
        'histori': 'Humanities and Arts',
        'literatur': 'Humanities and Arts',
        'sociolog': 'Social Sciences',
        'género': 'Social Sciences',
        'gender': 'Social Sciences',
        'educac': 'Education',
        'education': 'Education',
        'naval': 'Naval and Marine Engineering',
        'marino': 'Naval and Marine Engineering',
        'marine': 'Naval and Marine Engineering',
        'térmico': 'Energy and Thermal Systems',
        'thermal': 'Energy and Thermal Systems',
        'fonoaudi': 'Health Sciences'
    }
    
    for keyword, category in keyword_mapping.items():
        if keyword in spec_lower:
            return category
    
    # Si no se encuentra, retornar la especialización original con formato title case
    return specialization.title()

def main():
    """
    Función principal que procesa todos los datos de profesores
    """
    input_file = 'profesores_completos.json'
    
    try:
        print("🔄 Iniciando preprocesamiento de datos de profesores...")
        
        # Cargar datos originales
        if not os.path.exists(input_file):
            print(f"❌ Error: No se encontró el archivo '{input_file}'")
            return
            
        with open(input_file, 'r', encoding='utf-8') as f:
            professors_data = json.load(f)
        
        print(f"📊 Procesando {len(professors_data)} profesores...")
        
        # Procesar cada profesor
        specialization_mapping = get_normalization_mapping()
        university_mapping = get_university_normalization_mapping()
        
        for professor in professors_data:
            degree = professor.get('degree', '')
            university = professor.get('university', '')
            
            # Clasificar nivel de grado
            degree_level = classify_degree(degree)
            professor['degree_level'] = degree_level
            professor['original_degree'] = degree
            
            # Extraer y normalizar especialización
            specialization = extract_specialization(degree)
            normalized_specialization = normalize_specialization(specialization, specialization_mapping)
            
            professor['specialization'] = specialization
            professor['normalized_specialization'] = normalized_specialization
            
            # Normalizar universidad
            professor['original_university'] = university
            professor['normalized_university'] = normalize_university(university, university_mapping)
        
        # Analizar distribuciones
        degree_distribution = Counter([p.get('degree_level', 'Unknown') for p in professors_data])
        spec_distribution = Counter([p.get('normalized_specialization', 'Unknown') for p in professors_data])
        university_distribution = Counter([p.get('normalized_university', 'Unknown') for p in professors_data])
        
        # Mostrar resultados
        print("\n=== 🎓 DISTRIBUCIÓN DE GRADOS ACADÉMICOS ===")
        for degree_level, count in degree_distribution.most_common():
            percentage = (count / len(professors_data)) * 100
            print(f"{degree_level}: {count} ({percentage:.1f}%)")
        
        print(f"\n=== 🔬 ESPECIALIZACIONES NORMALIZADAS ({len(spec_distribution)}) ===")
        for spec, count in spec_distribution.most_common():
            print(f"{count:2d}x {spec}")
            
        print(f"\n=== 🏛️ UNIVERSIDADES NORMALIZADAS ({len(university_distribution)}) ===")
        for univ, count in university_distribution.most_common():
            print(f"{count:2d}x {univ}")
            
        # Mostrar algunos ejemplos de normalización de universidades
        print(f"\n=== 🔄 EJEMPLOS DE NORMALIZACIÓN DE UNIVERSIDADES ===")
        examples_shown = set()
        for prof in professors_data:
            original = prof.get('original_university', '')
            normalized = prof.get('normalized_university', '')
            if original != normalized and original not in examples_shown and len(examples_shown) < 10:
                print(f"'{original}' → '{normalized}'")
                examples_shown.add(original)
        
        # Guardar datos procesados (reemplazando el archivo original)
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(professors_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Datos procesados y guardados en: {input_file}")
        
        # Limpiar archivos temporales
        temp_files = [
            'profesores_con_grados_clasificados.json',
            'profesores_con_especializaciones_normalizadas.json'
        ]
        
        cleaned_files = []
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                cleaned_files.append(temp_file)
        
        if cleaned_files:
            print(f"🧹 Archivos temporales eliminados: {', '.join(cleaned_files)}")
        
        print("\n🎉 Preprocesamiento completado exitosamente!")
        print(f"📁 Tu archivo final está en: {input_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{input_file}'")
    except json.JSONDecodeError:
        print("❌ Error: El archivo JSON no es válido")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main() 