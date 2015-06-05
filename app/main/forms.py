from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

class FindBus(Form):
    source = StringField('Điểm bắt đầu', validators=[Required()])
    destin = StringField('Điểm kết thúc', validators=[Required()])
    submit = SubmitField('Tìm kiếm')
