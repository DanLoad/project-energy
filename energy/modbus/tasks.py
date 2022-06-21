# modbus/tasks.py
from energy.celery import app


@app.task(name='modbus_loop', bind=True)
def modbus_loop(self):
    module()
    return True


def module():
    print("OK")
