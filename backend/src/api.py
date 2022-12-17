import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# CORS Headers

@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization,true')
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PUT,POST,PATCH,DELETE,OPTIONS')
    return response

@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    formatted_drinks = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    if drinks is None:
        abort(404)

    drink = [drink.long() for drink in drinks]

    return jsonify({
        "success": True,
        "drinks": drink
    })

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    try:
        title = body['title']
        recipe = json.dumps(body['recipe'])

        drink = Drink(title=title, recipe=recipe)
        drink.insert()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })

    except Exception:
        abort(422)

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id: int):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    body = request.get_json()
    title = body['title']
    recipe = json.dumps(body['recipe'])

    drink.title = title
    drink.recipe = recipe

    drink.update()

    drinks = [drink.long()]
    return jsonify({
        "success": True,
        "drinks": drinks
    })

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id: int):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    try:
        if drink is None:
            abort(404)

        drink.delete()
        return jsonify({
            "success": True,
            "delete": id
        })
    except Exception:
        abort(422)

#----------------------------------------------------------------------------#
# Error Handlers
#----------------------------------------------------------------------------#


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "method not allowed"
    }), 405


@app.errorhandler(404)
def not_found(error):
    jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(403)
def forbidden(error):
    jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }), 403


@app.errorhandler(401)
def unauthorized(error):
    jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(AuthError)
def not_authenticated(AuthError):
    return jsonify({
        "success": False,
        "error": AuthError.status_code,
        "message": AuthError.error
    })
