import time
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, make_response, abort,
    jsonify, json
)

blueprint = Blueprint('debug', __name__, url_prefix='/debug')


@blueprint.route('setting')
def get_debug_setting():
    setting = {
        'performanceRecording': current_app.config.get('DEBUG_PERFORMANCE_RECORDING', False),
    }
    return jsonify(setting)


@blueprint.route('add_traces', methods=['POST'])
def add_traces():
    data = json.loads(request.get_data())
    s = str(data)
    current_app.logger.debug(f"add trace: {s[:30]}...")
    current_app.mongo.db.traces.insert_one({'traces': data, 'created_at': time.time() * 1000})
    return make_response()


@blueprint.route('traces')
def view_traces():
    return render_template('debug/traces.html')


@blueprint.route('get_traces', methods=['GET'])
def get_traces():
    since = request.args.get('since')
    traces = current_app.mongo.db.traces.find({'created_at': {'$gt': float(since)}})
    return jsonify({
        'data': [{'traces': t['traces'],
                  'created_at': t['created_at']
                  } for t in traces]
    })


@blueprint.route('delete_all_traces')
def delete_all_traces():
    current_app.mongo.db.traces.remove({})
