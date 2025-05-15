from flask import Blueprint, jsonify

from models import Question, Answer

api_bp = Blueprint('api', __name__)


@api_bp.route('/questions', methods=['GET'])
def api_questions():
    questions = Question.query.all()
    return jsonify([{
        'id': q.id,
        'title': q.title,
        'body': q.body,
        'user': q.user.username,
        'rating': q.rating
    } for q in questions])


@api_bp.route('/question/<int:question_id>/answers', methods=['GET'])
def api_answers(question_id):
    answers = Answer.query.filter_by(question_id=question_id).all()
    return jsonify([{
        'id': a.id,
        'body': a.body,
        'user': a.user.username,
        'rating': a.rating
    } for a in answers])
