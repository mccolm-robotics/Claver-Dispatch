from celery import Celery

#Format: transport://userid:password@hostname:port/virtual_host
app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y