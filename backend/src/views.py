from flask import Blueprint
from flask import jsonify
from flask import request
from sqlalchemy import func
from .models import *
from werkzeug.exceptions import abort
bp = Blueprint('views', __name__)

#######################
# ACCESSING TUTORIALS #
#######################

# get all short form unpublished tutorials
# Only returns tutorials not yet published
# since they were last changed.
@bp.route('/unpublished', methods=['GET'])
def get_unpublished_list():
    query = Unpublished_Tutorial.query.filter_by(under_review=True).all()
    if not query:
        abort(404)
    result = [tut.short() for tut in query]
    return jsonify({
        'success': True,
        'tutorials': result
        }), 200
    
#get long form of unpublished tutorial
@bp.route('/unpublished/<int:tutorial_id>', methods=['GET'])
def get_unpublished_tutorial(tutorial_id):
    query = Unpublished_Tutorial.query.get_or_404(tutorial_id)
    result = query.long()
    return jsonify({
        'success': True,
        'tutorial': result
    }), 200

#get all short form published tutorials
@bp.route('/published', methods=['GET'])
def get_published_list():
    query = Published_Tutorial.query.all()
    result = [tut.short() for tut in query]
    return jsonify({
        'success': True,
        'tutorials': result
        }), 200

#get long form of published tutorial
@bp.route('/published/<int:tutorial_id>', methods=['GET'])
def get_published_tutorial(tutorial_id):
    result = Published_Tutorial.query.get_or_404(tutorial_id).long()
    return jsonify({
        'success': True,
        'tutorial': result
    }), 200


#get all short form published tutorials from specific user
@bp.route('/published/by-author/<int:author_id>', methods=['GET'])
def get_published_list_by_author(author_id):
    tutorials = User.query.get_or_404(author_id).published
    result = [tut.short() for tut in tutorials]
    return jsonify({
        'success': True,
        'tutorials': result
        }), 200

#get all shortform list by tag
@bp.route('/published/tags/<string:tag>', methods=['GET'])
def get_published_by_tag(tag):
    search = "%{}%".format(tag)
    tutorials = Tag.query.filter(Tag.name.ilike(search)).first_or_404().published_tutorials
    result = [tut.short() for tut in tutorials]
    return jsonify({
        'success': True,
        'tutorials': result
        }), 200

#get all shortform list by tags
@bp.route('/published/tags/<string:tag1>/<string:tag2>', methods=['GET'])
def get_published_by_tags(tag1,tag2):
    search1 = "%{}%".format(tag1)
    search2 = "%{}%".format(tag2)
    
    #Not happy about this, but flask-sqlalchemy does not seem to allow
    #calling ilike on a relationship: no way to call on Published_Tutorial.tags
    res1 = Tag.query.filter(Tag.name.ilike(search1)).first_or_404().published_tutorials
    res2 = Tag.query.filter(Tag.name.ilike(search2)).first_or_404().published_tutorials
    tutorials = [tut for tut in res1 if tut in res2]
  
    result = [tut.short() for tut in tutorials]
    return jsonify({
        'success': True,
        'tutorials': result
        }), 200 
   

########################
# PUBLISHING TUTORIALS #
########################

#For regular user:
#submit tutorial
@bp.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    tutorial = Unpublished_Tutorial(
            author_id=data.get('author_id'),
            title=data.get('title'),
            text=data.get('text'),
            under_review=True
            )
    for tag_name in data.get('tags'):
        tag = Tag.query.filter(
                func.lower(Tag.name) == func.lower(tag_name)
                )
        tag = tag.one_or_none()
        if not tag:
            tag = Tag(name=tag_name)
            tag.insert()
        tutorial.tags.append(tag)
    tutorial.insert()
    result = tutorial.long()
    return jsonify({
        'success': True,
        'tutorial': result
    }), 200
        
            
#For Admin/Moderator:
#create or update published tutorial by copying unpublished
#returns newly published tutorial
@bp.route('/publish/<int:tutorial_id>', methods=['GET'])
def publish(tutorial_id):
    unpublished = Unpublished_Tutorial.query.get_or_404(tutorial_id)
    
    #No or_404 because we are testing for None
    published = Published_Tutorial.query.get(tutorial_id)
    
    try:
        #if it doesn't exist create it
        update = False
        if published:
            update = True
        else:
            published = Published_Tutorial(id=unpublished.id)
        
        #make updates
        published.author_id = unpublished.author_id
        published.title = unpublished.title
        published.text = unpublished.text
        published.tags = unpublished.tags
        unpublished.under_review = False
        unpublished.update()
        
        #update or insert depending on whether it exists
        if update:
            published.update()
        else:
            published.insert()
    except:
        abort(500)
    
    #return newly published tutorial
    result = Published_Tutorial.query.get_or_404(tutorial_id).long()
    return jsonify({
        'success': True,
        'updated': update,
        'tutorial': result
        }), 200

##################
# ADMINISTRATION #
##################

#create a user
@bp.route('/admin/user', methods=['POST'])
def create_user():
    data = request.get_json()
    try:
        user = User(
                auth0_id=data.get('auth0_id'),
                username=data.get('username')
                )
        user.insert()
        return jsonify({
            'success': True,
            'user_id': user.id
            })
    except:
        abort(500)

#list users
@bp.route('/admin/users', methods=['GET'])
def list_users():
    try:
        users = User.query.all()
        if len(users) == 0:
            abort(404)
        result = [user.description() for user in users]
        return jsonify({
            'success': True,
            'users': result
            }), 200
    except:
        abort(500)

#get specific user data
@bp.route('/admin/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': user.description()
        }), 200

#delete user
@bp.route('/admin/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        
        unpublished = user.unpublished
        published = user.published
        
        if len(unpublished) > 0:
            for tutorial in unpublished:
                tutorial.delete()
        if len(published) > 0:
            for tutorial in published:
                tutorial.delete()
        
        user.delete()
        return jsonify({
            'success': True,
            'deleted_id': user.id
            }), 200
    except:
        abort(500)

# delete tutorial
# The reason for this atypical endpoint is that it deletes both
# published and unpublished tutorials
@bp.route('/admin/tutorial/<int:tutorial_id>', methods=['DELETE'])
def delete_tutorials(tutorial_id):
    unpublished = Unpublished_Tutorial.query.get_or_404(tutorial_id)
    published = Published_Tutorial.query.get_or_404(tutorial_id)
    try:
        unpublished.delete()
        published.delete()
        return jsonify({
            'success': True,
            'deleted_id': tutorial_id
            }), 200
    except:
        abort(500)
