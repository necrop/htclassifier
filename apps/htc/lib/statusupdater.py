from ..models import Sense


def update_status(request):
    id = request.GET.get('id')
    try:
        sense = Sense.objects.get(id=id)
    except Sense.DoesNotExist:
        pass
    else:
        count = int(request.GET.get('count'))
        status_value = request.GET.get('value')

        if count == 1:
            sense.checkbox1 = status_value
        elif count == 2:
            sense.checkbox2 = status_value
        elif count == 3:
            sense.checkbox3 = status_value

        checkbox_values = set((sense.checkbox1, sense.checkbox2, sense.checkbox3))
        if 'c' in checkbox_values:
            overall_status = 'c' # at least one correct
        elif 'p' in checkbox_values:
            overall_status = 'p' # at least one partially correct
        elif all([c == 'i' for c in checkbox_values]):
            overall_status = 'i' # all incorrect
        elif all([c is None for c in checkbox_values]):
            overall_status = '0' # unclassified- this should not arise!
        else:
            overall_status = '1' # classified but unmarked
        sense.status = overall_status

        sense.save_with_user(request)
