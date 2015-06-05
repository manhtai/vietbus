from flask import render_template, flash

from app.main import main
from app.main.forms import FindBus
from app.data.search import create_map, get_near, to_lat_lon

@main.route('/', methods=['GET', 'POST'])
def index():
    form = FindBus()
    result = lambda x: x
    if form.validate_on_submit():
        source = get_near(form.source.data)
        destin = get_near(form.destin.data)
        result.source = to_lat_lon(form.source.data)
        result.destin = to_lat_lon(form.destin.data)
        result.path = create_map(source, destin)
        if result.path is None: flash('Không tìm thấy tuyến')
        return render_template('index.html', form=form, result=result)
    return render_template('index.html', form=form)

