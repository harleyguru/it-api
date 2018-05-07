"""
Socian API
"""
import os
from bson import json_util
from pymongo import MongoClient, errors
from chalice import Chalice, Response, BadRequestError

app = Chalice(app_name='socian', debug=True)

@app.route('/', cors=True)
def index():
    """index view"""
    return Response(body="Welcome to Socian API!", status_code=200, headers={'Content-Type': 'text/plain'})


@app.route('/introspec', methods=['GET'], cors=True)
def introspec():
    """introspec view

    This will show the introspec of current request

    Returns:
        dict -- JSON string of introspec
    """

    return app.current_request.to_dict()


@app.route('/search', methods=['GET'], cors=True)
def search():
    """search view

    Returns:
        dict -- JSON string of user profiles searched
    """

    # parse query parameters and validate
    fmin = 0
    fmax = 0
    engagement = 0
    platforms = ['instagram', 'facebook', 'twitter']
    keywords = None
    skip = 0
    limit = 50

    try:
        params = app.current_request.to_dict()['query_params']

        if 'fmin' in params:
            fmin = params['fmin']
            fmin = int(fmin)
        if 'fmax' in params:
            fmax = params['fmax']
            fmax = int(fmax)
        if fmin < 0 or fmax < 0:
            raise BadRequestError("fmin or fmax should have greater value than 0")
        if fmin > fmax and fmax > 0:
            raise BadRequestError("fmax should have greater value than fmin")

        if 'engagement' in params:
            engagement = params['engagement']
            engagement = float(engagement)
        if engagement < 0:
            raise BadRequestError("engagement should have greater value than 0!")
        
        if 'platforms' in params:
            platforms = params['platforms']
            platforms = [platform.strip().lower() for platform in platforms.split(',')]

        if 'keywords' in params:
            keywords = params['keywords']
            keywords = [keyword.strip().lower() for keyword in keywords.split(',')]

        if 'skip' in params:
            skip = params['skip']
            skip = int(skip)
        if 'limit' in params:
            limit = params['limit']
            limit = int(limit)
        if skip < 0 or limit < 0:
            raise BadRequestError("skip or limit should have greater value than 0")
    except TypeError:
        pass
    except ValueError:
        raise BadRequestError("Invalid parameters")

    # search profiles based on the parameters
    try:
        DB_HOST = os.getenv('DB_HOST')
        DB_USERNAME = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_PORT = os.getenv('DB_PORT')
        
        mongo_client = MongoClient(f'mongodb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}')

        collection = mongo_client['aggregation']['profiles']

        # filter by platforms, keywords, fmin/fmax and engagement
        users = []
        query = {'engagement_rate': {'$gte': engagement}}

        if fmin > 0:
            query['followers'] = {'$gte': fmin}
        if fmax > 0:
            query['followers'] = {'$lte': fmax}

        if platforms is not None:
            query['platform'] = {'$in': platforms}

        if keywords is not None:
            query['keywords'] = {'$in': keywords}

        cursor = collection.find(query, {'_id': False}).skip(skip).limit(limit)
        users += list(cursor)

        return Response(body=json_util.dumps({"status": "success", "status_code": 200, "results": users}))

    except errors.PyMongoError as e:
        raise BadRequestError(str(e))
    except Exception as e:
        raise BadRequestError(str(e))
