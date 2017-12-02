from flask import g
from flask_restplus import Namespace, Resource, fields, abort
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError
from app import db
from app.models import User, Table, UserTable
from app.rest.Auth import Auth
from app.RandomPhrases import randomPhrase
from datetime import datetime

# Define namespace
api = Namespace('Tables', description='Operations with tables', path='/tables')

# JSON Parsers #

# Find table request JSON fields
table_request = api.parser()
table_request.add_argument('table_key', type=str, required=True,
    help='No table_key provided', location='json')

# JSON Models #

# Creating new table response JSON fields
table_response_fields = api.model('Table response',
{
    'table_key': fields.String(description='Keyword'),
})

# Find table request JSON fields (all fields required)
find_table_request_fields = api.model('UserTable request',
{
    'table_key': fields.String(description='Keyword', required=True),
})

# TablesUsers response JSON template
user_table_response_fields = api.model('UserTable response',
{
    'table_id': fields.Integer(description='Table id', required=True),
    'user_id': fields.Integer(description='User id')
})

# TablesUsers list response item
tables_users_item_fields = api.model('Item TablesUsers response',
{
    'id': fields.Integer(description='User id', required=True),
    'name': fields.String(description='User name', required=True)
})

# TablesUsers list response JSON template
user_table_list_response_fields = api.model('UserTable list request',
{
    'users': fields.List(fields.Nested(tables_users_item_fields)),
})


@api.route('', endpoint='tables')
class Tables(Resource):
    """
    Operations with tables

    :var     method_decorators: Decorators applied to methods
    :vartype method_decorators: list
    """
    method_decorators = [Auth.multi_auth.login_required]

    @api.marshal_with(table_response_fields, code=201)
    @api.doc(responses={
        401: 'Unauthorized access',
        406: 'User already connected with table',
        409: 'Table already exists',
    })
    def post(self):
        """
        Create new table

        :return: New table key phrase
        :rtype:  dict/json
        """

        # Login of authorized user stores in Flask g object
        user = User.query.filter_by(username=g.user.username).first()

        # Create table and add to database
        key = self.newPhraseIfAlreadyExists()
        table = Table(
            table_key=key,
            table_date=datetime.utcnow())

        # TODO: Delete try-except or stop recursive key generation after X tries
        try:
            db.session.add(table)
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="Table '{}' already exist".format(key))

        # Create user-table dependency
        user_table = UserTable(
            user_id=user.id,
            table_id=table.id)

        try:
            db.session.add(user_table)
            db.session.commit()
            # Return JSON using template
            return table, 201
        except IntegrityError:
            db.session.rollback()
            abort(406, message="Username '{}' already connected with table".format(user.username))

    def newPhraseIfAlreadyExists(self):
        """
        Set the first keyword generated does not exist in database

        :return: New key phrase
        :rtype:  str
        """
        keyword = randomPhrase()
        if Table.query.filter_by(table_key=keyword).first() is not None:
            return self.newPhraseIfAlreadyExists()
        else:
            return keyword


@api.route('/users', endpoint='tables_users')
class TablesUsers(Resource):
    """
    Operations with users in table

    :var     method_decorators: Decorators applied to methods
    :vartype method_decorators: list
    """
    method_decorators = [Auth.multi_auth.login_required]

    @api.marshal_with(user_table_list_response_fields)
    @api.doc(responses={
        401: 'Unauthorized access',
        404: 'Username does not connected to any table'
    })
    def get(self):
        """
        Get list of users related to the same table as auth user

        :return: list of users id's and names
        :rtype:  dict/json
        """

        # Login of authorized user stores in Flask g object
        user = User.query.filter_by(username=g.user.username).first()

        try:
            result = {}
            result['users'] = [{
                'id': item.user_id,
                'name': item.user.username
            } for item in user.current_table[0].user_tables]
            return result
        except IndexError:
            abort(404, message="Username '{}' does not connected to any table".format(user.username))

    @api.expect(find_table_request_fields)
    @api.marshal_with(user_table_response_fields, code=201)
    @api.doc(responses={
        400: 'No table_key provided\n\n'
             'Input payload validation failed',
        401: 'Unauthorized access',
        404: 'Table keyword does not exist',
        406: 'Username already connected with table',
    })
    def post(self):
        """
        Add new user to the table

        :return: table and user id's
        :rtype:  dict/json
        """

        # Parsing request JSON fields
        args = table_request.parse_args()

        # Login of authorized user stores in Flask g object
        user = User.query.filter_by(username=g.user.username).first()

        table = Table.query.filter_by(table_key=args['table_key']).first()

        if table is None:
            abort(404, message="Table keyword '{}' does not exist".format(args['table_key']))

        # Create user-table dependency
        user_table = UserTable(
            user_id=user.id,
            table_id=table.id)

        try:
            db.session.add(user_table)
            db.session.commit()
            # Return JSON using template
            return user_table, 201
        except IntegrityError:
            db.session.rollback()
            abort(406, message="Username '{}' already connected with table".format(user.username))

    @api.marshal_with(user_table_response_fields)
    @api.doc(responses={
        400: 'Table does not exist',
        401: 'Unauthorized access',
        404: 'Username does not connected to any table',
    })
    def delete(self):
        """
        Delete user from the table

        :return: table-user dependency
        :rtype:  dict/json
        """

        # Login of authorized user stores in Flask g object
        user = User.query.filter_by(username=g.user.username).first()

        user_table = UserTable.query.filter_by(user_id=user.id).first()

        try:
            db.session.delete(user_table)
            # Return JSON using template
        except UnmappedInstanceError:
            db.session.rollback()
            abort(404, message="Username '{}' does not connected to any table".format(user.username))

        user_table_list = UserTable.query.filter_by(table_id=user_table.table_id).first()
        try:
            if user_table_list is None:
                db.session.delete(user_table.table)
            db.session.commit()
            return user_table
        except (IntegrityError, UnmappedInstanceError):
            db.session.rollback()
            abort(400, message="Table '{}' does not exist".format(user_table.table.table_key))
