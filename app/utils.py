from flask import flash

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
