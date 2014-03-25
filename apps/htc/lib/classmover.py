import re
from ..models import Sense, ThesaurusClass, Level2Class


def move_class(request, senseid, classid, count):
    try:
        sense = Sense.objects.get(id=senseid)
    except Sense.DoesNotExist:
        pass
    else:
        try:
            thesclass = ThesaurusClass.objects.get(id=classid)
        except ThesaurusClass.DoesNotExist:
            pass
        else:
            # The selected class has to be at or below wordclass level!
            if thesclass.wordclass:
                if count == 1:
                    sense.thesclass1 = thesclass
                    sense.checkbox1 = 'c'
                    level2_id = thesclass.ancestor(level=2).id
                    sense.level2branch = Level2Class.objects.get(id=level2_id)
                elif count == 2:
                    sense.thesclass2 = thesclass
                    sense.checkbox2 = 'c'
                elif count == 3:
                    sense.thesclass3 = thesclass
                    sense.checkbox2 = 'c'
                sense.save_with_user(request)


def classid_cleaner(input_text):
    input_text = input_text.strip()
    match = re.search(r'^(\d+)$', input_text)
    if match is not None:
        return int(match.group(1))
    else:
        match = re.search(r'classid=(\d+)', input_text)
        if match is not None:
            return int(match.group(1))
        else:
            return 0

