from celery import shared_task

# TODO update func create_order_lemmas_async
@shared_task
def create_order_lemmas_async():
    print("Here will be process of create order_lemmas...")
