from django import template
register = template.Library()

@register.filter
def significantDigits(value, arg):
    arg = int(arg)
    formatter = '%0.' + str(arg) + 'g'
    return float(formatter % (value,))

@register.filter
def as_percentage_of(part, whole):
    if part == whole:
        return '100%'
    try:
        value = part / whole
    except (ValueError, ZeroDivisionError):
        return ''
    else:
        if value > .1:
            return '{0:.1%}'.format(value)
        else:
            return '{0:.2%}'.format(value)
