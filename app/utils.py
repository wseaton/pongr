from flask import flash
from trueskill import Rating


def remove_whitespace(x):
    try:
        x = "".join(x.split())
    except:
        pass
    return x


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


def rating_df_to_dict(rating_df):
    return {row[1]['alias']: Rating(row[1]['rating'], row[1]['sigma']) for row in rating_df.iterrows()}
