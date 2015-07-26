import hashlib
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save
from conf.settings_game import model_classes
from subsystems.api.utils import JSONResponse
from subsystems.db.model_bookmark import Bookmark
from subsystems.gcm.models import Device


def capture_check_sum(sender, instance, **kwargs):
    ctype = ContentType.objects.get_for_model(sender)
    for b in Bookmark.objects.filter(content_type=ctype, object_id=instance.pk):
        m = hashlib.md5()
        m.update(instance.check_sum.encode('utf-8'))
        if b.push_check_sum == m.hexdigest():
            continue
        devices = Device.objects.filter(user=b.user)
        postfix = '_new' if not instance.pk else '_changed'
        push = JSONResponse.serialize_push(str(ctype) + postfix, b.content_object, aas=str(ctype), status=200,
                                           return_type=JSONResponse.RETURN_TYPE_DICT)
        devices.send_message(push)

for model_class in model_classes:
    pre_save.connect(capture_check_sum, sender=model_class, dispatch_uid="att_post_save_"+model_class.__name__)
