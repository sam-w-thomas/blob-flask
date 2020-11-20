import json

from bson import ObjectId
from flask import Flask, request, Response
from datetime import datetime
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('')
database = client.blog
posts_db = database.posts_db


def sanitize_post(post):
    try:
        post['_id'] = str(post['_id'])
        post['date'] = post['date'].strftime("Posted %d%m%Y at %H:%M")
    except Exception as e:
        print("Invalid data sanitization at" + datetime.now().strftime("%m%h%Y, %M:%H") + "Detail: " + str(e))
        raise Exception

    return post

def sanitize_posts(posts):
    if type(posts) is not list:
        return []
    else:
        pass

    sanitized_list = []
    for post in posts:
        sanitized_list.append(sanitize_post(post))

    return sanitized_list


def create_comment(author, message, date=datetime.now()):
    comment = {
        "id": str(ObjectId()),
        "author": author,
        "message": message,
        "date": date,
    }
    return comment

def id_valid(post_id) -> bool:
    """
    Check if ID is valid:
        - Must be 12 character in string form

    :param post_id:
    :return:
    """
    query = str(post_id)
    if len(query) is not 12:
        return False
    else:
        return True


@app.route('/blog/post', methods=['POST'])
def add_post():
    info = request.json
    author = str(info['author'])
    message = str(info['message'])
    title = str(info['title'])
    date = datetime.now()

    if len(message) > 3000 or len(author) > 40 or len(title) > 40: #Check character limit
        return {'error': 'Character count exceeded'}, 400

    post = {
        "author": author,
        "message": message,
        "title": title,
        "date": date,
        "comments": []
    }
    post_id = posts_db.insert_one(post).inserted_id
    return str(post_id),201


@app.route('/blog/comment/<post_id>/', methods=['PUT'])
def add_comment(post_id):
    query = {'_id': ObjectId(str(post_id))}
    comments = posts_db.find_one(query)['comments']

    info = request.json
    author = str(info['author'])
    message = str(info['message'])

    if len(message) > 750 or len(author) > 40: #Check character count limit on comments
        return {'error':'Character count exceeded 750'}, 400

    # Add new comment to comment list
    comment = create_comment(author, message)
    comments.append(comment)

    # Update database
    new_values = {"$set": {"comments": comments}}
    posts_db.update_one(query, new_values)

    return {},201


@app.route('/blog/remove/<post_id>', methods=['DELETE'])
def remove_post(post_id):
    post_id = str(post_id)
    if not id_valid(post_id):
        return {'error': 'Invalid Post ID'}, 400

    obj_id = ObjectId()
    query = {'_id': obj_id}
    posts_db.delete_one(query)
    return {}, 202

@app.route('/blog/post/<post_id>/', methods=['GET'])
def get_post(post_id):
    post_id = str(post_id)
    if not id_valid(post_id):
        return {'error': 'Invalid Post ID'},400

    obj_id = ObjectId(post_id)
    query = {'_id': obj_id}


    post = posts_db.find_one(query)

    if post is None:
        return {}, 404
    else:
        try:
            post = sanitize_post(post)
            return post, 200
        except Exception:
            return {}, 405



@app.route('/blog/posts', methods=['GET'])
def get_posts():
    if 'limit' in request.args:
        limit = int(request.args['limit'])
    else:
        limit = 10 # Default limit 10 pages per page

    if 'page' in request.args:
        page = int(request.args['page'])
    else:
        page = 1 # Default to first page

    posts = list(posts_db.find({}))
    start = (page - 1) * limit
    end = (page * limit)

    try:
        posts = sanitize_posts(posts[start:end])
    except Exception:
        return "", 405

    if len(posts) == 0:
        return {}, 404
    else:
        return_info = {
            "page": page,
            "limit": limit,
            "posts": posts
        }
        return return_info





if __name__ == '__main__':
    app.run()
