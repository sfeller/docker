''' controller and routes for components '''
import os
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import app, mongo
from app.schemas import validate_task, validate_task_update
import logger

#Added to converrt pymongo cursor objects to json
from bson.json_util import dumps

ROOT_PATH = os.environ.get('ROOT_PATH')
LOG = logger.get_root_logger(
    __name__, filename=os.path.join(ROOT_PATH, 'output.log'))

@app.route('/components', methods=['GET', 'POST', 'DELETE', 'PATCH'])
# @jwt_required
##
# \brief Implement component interface
# This function handle requests for the components interface it manages
# GET, POST, DELETE, and PATCH requests. This function will send a JSON
# array with all entries that match they query
#
# GET: The provided arguments are converted to a dictionary that is used 
# for a query. All components that meet teh query are returned.
def components():
    #Handle GET Requests
    print("REQUEST")
    if request.method == 'GET':
        query = request.args.to_dict()
        print("QUERYL"+str(query))

        #Perform the query and dump the output into a Json array
        data = dumps(mongo.db.components.find(query))
        return jsonify({'ok': True, 'data': data}), 200

    # For non-GET actions, we need to get 
    data = request.get_json()

    if request.method == 'POST':
        user = get_jwt_identity()
        data['email'] = user['email']
        data = validate_component(data)
        if data['ok']:
            db_response = mongo.db.components.insert_one(data['data'])
            return_data = mongo.db.components.find_one(
                {'_id': db_response.inserted_id})
            return jsonify({'ok': True, 'data': return_data}), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400

    if request.method == 'DELETE':
        if data.get('id', None) is not None:
            db_response = mongo.db.components.delete_one(
                {'_id': ObjectId(data['id'])})
            if db_response.deleted_count == 1:
                response = {'ok': True, 'message': 'record deleted'}
            else:
                response = {'ok': True, 'message': 'no record found'}
            return jsonify(response), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400

    if request.method == 'PATCH':
        data = validate_component_update(data)
        if data['ok']:
            data = data['data']
            mongo.db.components.update_one(
                {'_id': ObjectId(data['id'])}, {'$set': data['payload']})
            return jsonify({'ok': True, 'message': 'record updated'}), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400


@app.route('/list/component', methods=['GET'])
# @jwt_required
def list_components():
    ''' route to get all the components for a user '''
    # user = get_jwt_identity()
    user = {'email': 'riken.mehta03@gmail.com'}
    if request.method == 'GET':
        query = request.args
        data = mongo.db.components.find({'email': user['email']})
        if query.get('group', None):
            return_data = {}
            for component in data:
                try:
                    return_data[component['status']].append(component)
                except:
                    return_data[component['status']] = [component]
        else:
            return_data = list(data)
        return jsonify({'ok': True, 'data': return_data})
