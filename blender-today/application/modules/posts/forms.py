from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField
from wtforms import SelectField
from wtforms import TextAreaField
from wtforms import HiddenField
from wtforms.validators import DataRequired

class PostForm(Form):
    category_id = SelectField('Group', coerce=int)
    post_type_id = SelectField('Post Type', coerce=int)
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content')
    url = StringField('URL')
    picture = FileField('A picture')

class CommentForm(Form):
    content = TextAreaField('Content', validators=[DataRequired()])
    parent_id = HiddenField('Parent')
