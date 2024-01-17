import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from werkzeug.exceptions import HTTPException
import traceback

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        try:
            selection = Category.query.order_by(Category.id).all()

            if len(selection) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'categories': {str(category.id): category.type for category in selection}
            })
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        try:
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            if len(current_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'totalQuestions': len(Question.query.all()),
                'categories': {str(category.id): category.type for category in Category.query.all()}
            })
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question_or_search():
        try:
            body = request.get_json()

            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_difficulty = body.get('difficulty', None)
            new_category = body.get('category', None)
            searchTerm = body.get('searchTerm', None)

            if searchTerm:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(searchTerm.lower())))

                return jsonify({
                    'success': True,
                    'questions': [question.format() for question in selection],
                    'totalQuestions': len(Question.query.all()),
                    'currentCategory': None
                })
            else:
                if new_question is None or new_answer is None or new_category is None or new_difficulty is None:
                    abort(422)

                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty,
                                    category=new_category)
                question.insert()

                return jsonify({
                    'success': True,
                })
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_from_category(category_id):
        try:
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            selection = Question.query.order_by(Question.id).filter(
                Question.category == category_id)

            if selection.count() == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': [question.format() for question in selection],
                'totalQuestions': Question.query.count(),
                'currentCategory': category.type,
            })
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.route('/quizzes', methods=['POST'])
    def get_questions_for_quiz():
        try:
            body = request.get_json()

            previous_questions = body.get('previous_questions', None)
            quiz_category = body.get('quiz_category', None)

            if quiz_category["id"] == 0:
                selection = Question.query.filter(
                    Question.id.not_in(previous_questions))
            else:
                selection = Question.query.filter(
                    Question.category == quiz_category["id"],
                    Question.id.not_in(previous_questions)
                )

            if selection.count() == 0:
                abort(404)

            random_question = random.choice(list(selection))

            return jsonify({
                'success': True,
                'question': random_question.format()
            })
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    return app
