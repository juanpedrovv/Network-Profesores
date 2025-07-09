from flask import Flask, jsonify, render_template, request
import json
import pandas as pd

app = Flask(__name__)

# Cargar datos de profesores
try:
    profesores_df = pd.read_json('profesores_completos.json')
    profesores_df['id'] = profesores_df['name'] # Usar el nombre como id
except FileNotFoundError:
    profesores_df = pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graph-data')
def graph_data():
    group_by = request.args.get('groupBy', 'interest_areas')

    if profesores_df.empty:
        return jsonify({"nodes": [], "groups": []})

    nodes = profesores_df.to_dict('records')
    
    groups = {}
    if group_by == 'interest_areas':
        for _, professor in profesores_df.iterrows():
            for area in professor['interest_areas']:
                if area not in groups:
                    groups[area] = []
                groups[area].append(professor['id'])
    elif group_by == 'specialization':
        for _, professor in profesores_df.iterrows():
            spec = professor['normalized_specialization']
            if spec not in groups:
                groups[spec] = []
            groups[spec].append(professor['id'])

    group_list = [{"name": name, "members": members} for name, members in groups.items()]

    return jsonify({"nodes": nodes, "groups": group_list})

if __name__ == '__main__':
    app.run(debug=True, port=5001) 