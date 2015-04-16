from subsystems.db.model_zone import Zone


def init_db(x_step, y_step):
    for x in range(0, 360, x_step):
        for y in range(-90, 90, y_step):
            Zone.objects.create(
                sw_lat=y,
                sw_lng=x,
                ne_lat=y+y_step,
                ne_lng=x+x_step
            )