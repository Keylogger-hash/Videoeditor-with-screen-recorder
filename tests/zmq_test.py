import zmq, json, time


def send():
    context = zmq.Context()
    publisher = context.socket(zmq.REQ)
    publisher.connect("tcp://127.0.0.1:6555")
    data = {"method":"cancel","link":"https://www.youtube.com/watch?v=125n_JB-gVU"}
    publisher.send_json(data)
    message = publisher.recv()
    print(f"Request: 1 - [{message}]")



send()
