import os
from flask import Flask, jsonify, request

app = Flask(__name__)

config = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/version', methods=['GET'])
def get_version():
    version = os.getenv('APP_VERSION', '1.0.0')
    return jsonify({"version": version}), 200

@app.route('/env', methods=['GET'])
def get_environment():
    value = os.getenv('ENVIRONMENT', 'development')
    return jsonify({"environment": value}), 200

@app.route('/config', methods=['POST'])
def post_config():
    name = request.json.get('name')
    value = request.json.get('value')
    if not name or not value:
        return jsonify({"error": "Missing 'name' or 'value' in request body"}), 400
    config[name] = value
    return jsonify({"name": name, "value": value}), 200

@app.route('/config/<name>', methods=['GET'])
def get_config(name):
    value = config.get(name)
    if value is None:
        return jsonify({"error": f"Configuration '{name}' not found"}), 404
    return jsonify({"name": name, "value": value}), 200

@app.route('/config/<name>', methods=['DELETE'])
def delete_config(name):
    if name in config:
        del config[name]
        return jsonify({"deleted": True}), 200
    else:
        return jsonify({"deleted": False}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

