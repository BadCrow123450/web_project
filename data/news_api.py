import flask

from . import db_session
from .news import News

blueprint = flask.Blueprint(
    'news_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/news')
def get_news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    print([item.to_dict(only=('title', 'content')) for item in news])
    return "q"