import pandas as pd
import json
import re
import unicodedata
from fuzzywuzzy import process
import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore")

# Se eliminan las importaciones de NLP que ya no son necesarias

def map_interest_areas_with_ai(df, method='zero_shot', min_score=0.3):
    """
    Asigna áreas de interés a los profesores usando métodos de IA.
    
    Parámetros:
    - df: DataFrame con información de profesores
    - method: 'zero_shot' o 'similarity_based' 
    - min_score: Score mínimo para asignar una categoría (0.0 - 1.0)
    
    Retorna:
    - DataFrame con nuevas columnas: 'interest_areas' y 'interest_scores'
    """
    print(f"Iniciando asignación de áreas de interés usando método: {method}")
    
    try:
        with open('areas_de_interes.json', 'r', encoding='utf-8') as f:
            interest_dictionary = json.load(f)
    except FileNotFoundError:
        print("Error: El archivo 'areas_de_interes.json' no fue encontrado.")
        df['interest_areas'] = [[] for _ in range(len(df))]
        df['interest_scores'] = [[] for _ in range(len(df))]
        return df
    
    # Preparar categorías y descripciones
    categories = list(interest_dictionary.keys())
    category_descriptions = {}
    
    for category, keywords in interest_dictionary.items():
        # Crear una descripción más rica para cada categoría
        description = f"Investigación y trabajo en {category.lower()}: " + ", ".join(keywords[:5])
        category_descriptions[category] = description
    
    print(f"Categorías disponibles: {len(categories)}")
    print(f"Método de clasificación: {method}")
    print(f"Score mínimo: {min_score}")
    
    if method == 'zero_shot':
        return _classify_with_zero_shot(df, categories, min_score)
    elif method == 'similarity_based':
        return _classify_with_similarity(df, category_descriptions, min_score)
    else:
        raise ValueError("Método no válido. Use 'zero_shot' o 'similarity_based'")

def _classify_with_zero_shot(df, categories, min_score):
    """
    Clasificación usando Zero-Shot Classification con BART
    """
    print("Cargando modelo Zero-Shot (BART)...")
    try:
        # Usar un modelo multilingüe si está disponible, sino usar el inglés estándar
        classifier = pipeline(
            "zero-shot-classification", 
            model="facebook/bart-large-mnli",
            device=0 if __is_gpu_available() else -1
        )
    except Exception as e:
        print(f"Error cargando modelo en GPU, usando CPU: {e}")
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
    
    all_interest_areas = []
    all_interest_scores = []
    
    for index, row in df.iterrows():
        print(f"Procesando profesor {index + 1}/{len(df)}: {row.get('name', 'N/A')}")
        
        # Combinar todo el contenido de texto
        text_content = _extract_text_content(row)
        
        if not text_content.strip():
            all_interest_areas.append([])
            all_interest_scores.append([])
            continue
        
        # Truncar texto si es muy largo (BART tiene límite de tokens)
        if len(text_content) > 1000:
            text_content = text_content[:1000] + "..."
        
        try:
            # Clasificar con múltiples etiquetas
            result = classifier(text_content, categories, multi_label=True)
            
            # Filtrar por score mínimo
            filtered_areas = []
            filtered_scores = []
            
            for label, score in zip(result['labels'], result['scores']):
                if score >= min_score:
                    filtered_areas.append(label)
                    filtered_scores.append(round(float(score), 3))
            
            all_interest_areas.append(filtered_areas)
            all_interest_scores.append(filtered_scores)
            
        except Exception as e:
            print(f"Error procesando profesor {row.get('name', 'N/A')}: {e}")
            all_interest_areas.append([])
            all_interest_scores.append([])
    
    df['interest_areas'] = all_interest_areas
    df['interest_scores'] = all_interest_scores
    print("Clasificación Zero-Shot completada.")
    return df

def _classify_with_similarity(df, category_descriptions, min_score):
    """
    Clasificación basada en similitud semántica usando Sentence Transformers
    """
    print("Cargando modelo de embeddings semánticos...")
    try:
        # Usar un modelo multilingüe
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    except Exception as e:
        print(f"Error cargando modelo multilingüe, usando modelo en inglés: {e}")
        model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Crear embeddings para las descripciones de categorías
    categories = list(category_descriptions.keys())
    category_embeddings = model.encode(list(category_descriptions.values()))
    
    all_interest_areas = []
    all_interest_scores = []
    
    for index, row in df.iterrows():
        print(f"Procesando profesor {index + 1}/{len(df)}: {row.get('name', 'N/A')}")
        
        # Combinar todo el contenido de texto
        text_content = _extract_text_content(row)
        
        if not text_content.strip():
            all_interest_areas.append([])
            all_interest_scores.append([])
            continue
        
        try:
            # Crear embedding del contenido del profesor
            content_embedding = model.encode([text_content])
            
            # Calcular similitudes
            similarities = cosine_similarity(content_embedding, category_embeddings)[0]
            
            # Filtrar por score mínimo y ordenar
            filtered_areas = []
            filtered_scores = []
            
            for i, similarity in enumerate(similarities):
                if similarity >= min_score:
                    filtered_areas.append(categories[i])
                    filtered_scores.append(round(float(similarity), 3))
            
            # Ordenar por score descendente
            if filtered_areas:
                sorted_pairs = sorted(zip(filtered_areas, filtered_scores), 
                                    key=lambda x: x[1], reverse=True)
                filtered_areas, filtered_scores = zip(*sorted_pairs)
                filtered_areas = list(filtered_areas)
                filtered_scores = list(filtered_scores)
            
            all_interest_areas.append(filtered_areas)
            all_interest_scores.append(filtered_scores)
            
        except Exception as e:
            print(f"Error procesando profesor {row.get('name', 'N/A')}: {e}")
            all_interest_areas.append([])
            all_interest_scores.append([])
    
    df['interest_areas'] = all_interest_areas
    df['interest_scores'] = all_interest_scores
    print("Clasificación por similitud semántica completada.")
    return df

def _extract_text_content(row):
    """
    Extrae y combina todo el contenido textual relevante de un profesor
    """
    text_parts = []
    
    # Información básica
    if pd.notna(row.get('degree')):
        text_parts.append(f"Grado académico: {row['degree']}")
    
    if pd.notna(row.get('university')):
        text_parts.append(f"Universidad: {row['university']}")
    
    # Información scrapeada
    if row.get('scraped_info') and isinstance(row['scraped_info'], list):
        for info in row['scraped_info']:
            if isinstance(info, dict) and info.get('content'):
                content = info['content']
                # Limpiar contenido básico
                content = re.sub(r'\s+', ' ', content).strip()
                if len(content) > 20:  # Solo agregar contenido sustancial
                    text_parts.append(content)
    
    return ' '.join(text_parts)

def __is_gpu_available():
    """
    Verifica si hay GPU disponible para PyTorch
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

# Función legacy mantenida para compatibilidad
def map_interest_areas_from_dictionary(df):
    """
    Función legacy que usa el nuevo método de IA por defecto
    """
    print("ADVERTENCIA: Esta función está obsoleta. Use map_interest_areas_with_ai() en su lugar.")
    return map_interest_areas_with_ai(df, method='zero_shot', min_score=0.3)

def main():
    """
    Función principal para orquestar el preprocesamiento de datos.
    """
    df_profesores = preprocess_csv_data('profesores_data.csv')
    df_scraped = preprocess_scraped_data('scrapping_teacher_utec.json')
    df_merged = merge_data(df_profesores, df_scraped)
    df_with_scraped = df_merged[df_merged['scraped_info'].notna()].copy()

    def filter_scraped_info_by_score(scraped_info_list):
        if not isinstance(scraped_info_list, list): return []
        return [info for info in scraped_info_list if isinstance(info, dict) and info.get('score', 0) > 0.6]

    df_with_scraped['scraped_info'] = df_with_scraped['scraped_info'].apply(filter_scraped_info_by_score)
    df_final = df_with_scraped[df_with_scraped['scraped_info'].apply(lambda x: len(x) > 0)].copy().reset_index(drop=True)

    if not df_final.empty:
        # Usar el nuevo método de IA con configuración personalizable
        print("\n" + "="*60)
        print("CONFIGURACIÓN DE CLASIFICACIÓN DE ÁREAS DE INTERÉS")
        print("="*60)
        print("Método disponibles:")
        print("1. 'zero_shot' - Usa BART para clasificación directa")
        print("2. 'similarity_based' - Usa embeddings semánticos")
        print("="*60)
        
        # Configuración por defecto - puedes cambiar estos valores
        method = 'zero_shot'  # o 'similarity_based'
        min_score = 0.3       # Ajustar según necesidades (0.1 más permisivo, 0.5 más estricto)
        
        print(f"Usando método: {method}")
        print(f"Score mínimo: {min_score}")
        print("="*60)
        
        df_final = map_interest_areas_with_ai(df_final, method=method, min_score=min_score)

    # Contar research papers
    if 'scraped_info' in df_final.columns:
        df_final['research_papers'] = df_final['scraped_info'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        print("Columna 'research_papers' añadida con el conteo de publicaciones.")

    # Eliminar columnas que ya no son necesarias para el JSON final
    df_final.drop(columns=['normalized_name', 'normalized_scraped_name'], inplace=True, errors='ignore')
    
    df_final = df_final.replace({np.nan: None})
    
    output_path = 'profesores_completos.json'
    df_final.to_json(output_path, orient='records', indent=4, force_ascii=False)
    
    print(f"\nPreprocesamiento completado. Se han guardado {len(df_final)} registros en '{output_path}'.")
    if not df_final.empty:
        print("\nResumen de los datos finales (con áreas de interés y scores):")
        sample_data = df_final[['name', 'interest_areas', 'interest_scores']].head(10)
        for _, row in sample_data.iterrows():
            print(f"\n{row['name']}:")
            if row['interest_areas']:
                for area, score in zip(row['interest_areas'], row['interest_scores']):
                    print(f"  - {area}: {score}")
            else:
                print("  - Sin áreas de interés asignadas")

# ... (El resto de las funciones de soporte como preprocess_csv_data, etc. se mantienen)
# Asegurémonos de que las funciones necesarias están presentes

def preprocess_csv_data(filepath):
    df = pd.read_csv(filepath, sep=';')
    df.drop_duplicates(subset=['name'], keep='first', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['normalized_name'] = df['name'].apply(normalize_name)
    return df

def extract_name_from_title(title):
    title = re.sub(r'[\u202a\u202b\u202c]', '', title)
    name = re.split(r'\s*-\s*|\s*\|\s*', title)[0]
    return name.strip()

def preprocess_scraped_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    professors_list = []
    for professor_results in scraped_data:
        if not professor_results: continue
        best_name = None
        for result in professor_results:
            candidate_name = extract_name_from_title(result['title'])
            if candidate_name and (best_name is None or len(candidate_name) > len(best_name)):
                best_name = candidate_name
        if best_name:
            professors_list.append({
                'scraped_name': best_name,
                'normalized_scraped_name': normalize_name(best_name),
                'scraped_info': professor_results,
            })
    df = pd.DataFrame(professors_list)
    df.drop_duplicates(subset=['normalized_scraped_name'], keep='first', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def merge_data(df_base, df_scraped):
    scraped_names = df_scraped['normalized_scraped_name'].tolist()
    merged_data = []
    for _, row in df_base.iterrows():
        base_name = row['normalized_name']
        best_match, score = process.extractOne(base_name, scraped_names)
        merged_row = row.to_dict()
        if score >= 80:
            scraped_row = df_scraped[df_scraped['normalized_scraped_name'] == best_match].iloc[0]
            merged_row.update(scraped_row.to_dict())
        else:
            merged_row.update({'scraped_name': None, 'normalized_scraped_name': None, 'scraped_info': None})
        merged_data.append(merged_row)
    return pd.DataFrame(merged_data)

def normalize_name(name):
    if not isinstance(name, str): return ''
    nfkd_form = unicodedata.normalize('NFKD', name)
    name = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    name = name.lower()
    name = re.sub(r'[^a-z\s]', '', name)
    name = " ".join(name.split())
    return name

if __name__ == '__main__':
    main() 